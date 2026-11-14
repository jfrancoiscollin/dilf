"""Fixed-depth Scan audit of best-move transfer between MTDP positions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from pedagogy.game import GameState, state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.pdn import PdnReplayError, read_games, validated_trajectory
from research.mtdp.successor_audit import _action_key, _quiet_signature

DEFAULT_DEPTH = 8
Action = tuple[tuple[int, ...], tuple[int, ...], bool]


class Scan:
    def __init__(self, binary: Path, depth: int = DEFAULT_DEPTH):
        if depth < 1:
            raise ValueError("Scan depth must be positive")
        self.depth = depth
        self.binary = binary.resolve()
        self.lines: Queue[str | None] = Queue()

    def __enter__(self):
        self.proc = subprocess.Popen(
            [str(self.binary), "hub"], cwd=self.binary.parent,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )

        def read():
            for line in self.proc.stdout:
                self.lines.put(line.strip())
            self.lines.put(None)

        Thread(target=read, daemon=True).start()
        try:
            self.send("hub")
            hello = list(self.until("wait"))
            if not any(line.startswith("id name=Scan version=3.1 ") for line in hello):
                raise RuntimeError(f"Unexpected Scan identification: {hello}")
            self.send(
                "set-param name=variant value=normal",
                "set-param name=book value=false",
                "set-param name=bb-size value=0",
                "set-param name=tt-size value=18",
                "set-param name=threads value=1",
                "init",
            )
            list(self.until("ready"))
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc):
        self.proc.kill()
        self.proc.wait(timeout=5)
        self.proc.stdin.close()
        self.proc.stdout.close()

    def send(self, *commands):
        self.proc.stdin.write("\n".join(commands) + "\n")
        self.proc.stdin.flush()

    def until(self, marker):
        while True:
            try:
                line = self.lines.get(timeout=20)
            except Empty as exc:
                raise RuntimeError(f"Scan did not respond while waiting for {marker}") from exc
            if line is None or line.startswith("error"):
                raise RuntimeError(f"Scan failed while waiting for {marker}: {line}")
            if line.split(maxsplit=1)[0:1] == [marker]:
                return
            yield line

    def score(self, state: GameState) -> int:
        board = ["e"] * 50
        for piece, squares in (
            ("w", state.white_men), ("W", state.white_kings),
            ("b", state.black_men), ("B", state.black_kings),
        ):
            for square in squares:
                board[square - 1] = piece
        position = state.turn[0].upper() + "".join(board)
        self.send("new-game", f"pos pos={position}", f"level depth={self.depth}", "go analyze")
        pattern = re.compile(rf"^info depth={self.depth}\b.*?\bscore=(-?\d+\.\d+)\b")
        scores = [
            int(Decimal(match[1]) * 100)
            for line in self.until("done") if (match := pattern.search(line))
        ]
        if not scores:
            raise RuntimeError(f"No depth-{self.depth} score for {state_to_fen(state)}")
        return scores[-1]


def load_positions(paths, engine, seen_games, *, plies_by_game=None, game_audit=None):
    states = {}
    games_by_fen = defaultdict(set)
    inputs = []
    for path in paths:
        games = read_games(path)
        source = {
            "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "games": len(games), "accepted": 0, "duplicates": 0, "rejected": [],
        }
        inputs.append(source)
        for game in games:
            game_id = f"{path.name}:{game.index}"
            try:
                trajectory = validated_trajectory(game, engine)
            except PdnReplayError as exc:
                source["rejected"].append({"game": game.index, "error": str(exc)})
                if game_audit is not None:
                    game_audit[game_id] = {"status": "rejected", "error": str(exc)}
                continue
            fens = tuple(state_to_fen(state) for _, _, state in trajectory)
            duplicate = fens in seen_games
            if game_audit is not None:
                game_audit[game_id] = {
                    "status": "duplicate" if duplicate else "accepted",
                    "validated_plies": len(trajectory) - 1,
                    "trajectory_sha256": hashlib.sha256("\n".join(fens).encode()).hexdigest(),
                }
            if duplicate:
                source["duplicates"] += 1
                continue
            seen_games.add(fens)
            source["accepted"] += 1
            for fen, (ply, _, state) in zip(fens, trajectory, strict=True):
                states[fen] = state
                games_by_fen[fen].add(game_id)
                if plies_by_game is not None:
                    plies_by_game.setdefault(fen, {}).setdefault(game_id, []).append(ply)
    return states, games_by_fen, inputs


def group_positions(states):
    grouped = defaultdict(list)
    for fen, state in sorted(states.items()):
        signature = _quiet_signature(state)
        if signature is not None:
            grouped[signature].append(fen)
    return grouped


def compare_scores(a: dict[Action, int], b: dict[Action, int]) -> dict:
    best_a = max(a.values())
    best_b = max(b.values())
    optimal_a = sorted(action for action, score in a.items() if score == best_a)
    optimal_b = sorted(action for action, score in b.items() if score == best_b)

    def transfer(destination_best, transferred):
        def category(score):
            return "win" if score > 8000 else "loss" if score < -8000 else "ordinary"

        return {
            "best_centimen": destination_best, "transferred_centimen": transferred,
            "ordinary_regret_centimen": (
                destination_best - transferred
                if category(destination_best) == category(transferred) == "ordinary"
                else None
            ),
            "best_category": category(destination_best),
            "transferred_category": category(transferred),
        }

    return {
        "same_pick": optimal_a[0] == optimal_b[0],
        "optimal_sets_overlap": bool(set(optimal_a) & set(optimal_b)),
        "optimal_a": optimal_a,
        "optimal_b": optimal_b,
        "a_to_b": transfer(best_b, b[optimal_a[0]]),
        "b_to_a": transfer(best_a, a[optimal_b[0]]),
    }


def audit(baseline, holdouts, engine, scan, exclusions=()):
    seen = set()
    base, base_games, base_inputs = load_positions([baseline], engine, seen)
    excluded, _, excluded_inputs = load_positions(exclusions, engine, seen)
    held, held_games, held_inputs = load_positions(holdouts, engine, seen)
    novel = {fen: state for fen, state in held.items() if fen not in base and fen not in excluded}
    base_groups, novel_groups = group_positions(base), group_positions(novel)
    states = base | novel
    scores = {}

    def score_moves(fen, moves):
        if fen not in scores:
            scores[fen] = {}
            for action, move in sorted(moves.items()):
                successor = engine.apply_move(states[fen], move)
                score = -scan.score(successor) if engine.legal_moves(successor) else 10000
                scores[fen][action] = score
        return scores[fen]

    def compare(pairs, left_games, right_games):
        rows = []
        for a, b in sorted(pairs):
            legal_a = {_action_key(move): move for move in engine.legal_moves(states[a])}
            legal_b = {_action_key(move): move for move in engine.legal_moves(states[b])}
            row = {
                "fen_a": a, "fen_b": b,
                "games_a": sorted(left_games[a]), "games_b": sorted(right_games[b]),
            }
            if legal_a.keys() != legal_b.keys():
                row["status"] = "different_legal_actions"
            elif len(legal_a) < 2:
                row["status"] = "terminal" if not legal_a else "forced_move"
            else:
                row["status"] = "scored"
                row.update(compare_scores(score_moves(a, legal_a), score_moves(b, legal_b)))
            rows.append(row)
        return rows

    holdout_pairs = (
        (a, b) for group in novel_groups.values() for a, b in combinations(group, 2)
        if held_games[a].isdisjoint(held_games[b])
    )
    transfer_pairs = (
        (a, b) for key, group in novel_groups.items()
        for a in base_groups.get(key, ()) for b in group
    )
    primary = compare(holdout_pairs, held_games, held_games)
    transfer = compare(transfer_pairs, base_games, held_games)
    report = {
        "schema": "mtdp-best-move-v1", "scan_successor_depth": scan.depth,
        "baseline_inputs": base_inputs, "holdout_inputs": held_inputs,
        "baseline_fens": len(base), "holdout_fens": len(held),
        "overlapping_fens": len(held) - len(novel), "novel_holdout_fens": len(novel),
        "novel_quiet_fens": sum(map(len, novel_groups.values())),
        "holdout_pairs": primary, "pcblues_transfer_pairs": transfer,
        "action_scores_centimen": {
            fen: [{"action": action, "score": score} for action, score in moves.items()]
            for fen, moves in sorted(scores.items())
        },
    }
    if excluded_inputs:
        report["exclusion_inputs"] = excluded_inputs
        report["prior_holdout_only_overlap_fens"] = len((held.keys() & excluded.keys()) - base.keys())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--holdout", required=True, action="append", type=Path)
    parser.add_argument("--exclude-previous", type=Path, action="append", default=[],
                        help="prior holdout PDN whose trajectories and positions are excluded")
    parser.add_argument("--scan", required=True, type=Path)
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH,
                        help="Scan successor depth; default 8")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = [args.baseline, *args.holdout, *args.exclude_previous]
    if len({p.name for p in paths}) != len(paths):
        parser.error("PDN filenames must be distinct to identify game sources")
    if args.depth < 1:
        parser.error("--depth must be positive")
    with Scan(args.scan, depth=args.depth) as scan:
        report = audit(args.baseline, args.holdout, create_engine(), scan, args.exclude_previous)
    report["scan_binary_sha256"] = hashlib.sha256(args.scan.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
