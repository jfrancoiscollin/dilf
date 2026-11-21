"""Audit the preregistered typed diagonal radius-two MTDP refinement."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path

from pedagogy.game import GameState, parse_fen
from research.mtdp.best_move_audit import load_positions
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.signature_ablation import _COORDS, _SQUARE_AT
from research.mtdp.successor_audit import _action_key, _quiet_signature

_DIRECTIONS = tuple(product((-1, 1), repeat=2))
_PAIR_COHORTS = ("holdout_pairs", "pcblues_transfer_pairs")


def typed_radius_two(state: GameState) -> tuple | None:
    quiet = _quiet_signature(state)
    if quiet is None:
        return None

    mover = state.turn
    opponent = "black" if mover == "white" else "white"
    occupants = {
        square: label
        for label, squares in (
            ("own_man", state.men_of(mover)),
            ("own_king", state.kings_of(mover)),
            ("enemy_man", state.men_of(opponent)),
            ("enemy_king", state.kings_of(opponent)),
        )
        for square in squares
    }
    neighborhood = []
    for origin in sorted(state.men_of(state.turn)):
        row, col = _COORDS[origin]
        cells = []
        for dr, dc in _DIRECTIONS:
            for distance in (1, 2):
                square = _SQUARE_AT.get((row + dr * distance, col + dc * distance))
                occupant = "off_board" if square is None else occupants.get(square, "empty")
                cells.append((dr, dc, distance, occupant))
        neighborhood.append((origin, tuple(cells)))
    return "typed-radius-two-v1", quiet, tuple(neighborhood)


def pcblues_audit(path, engine):
    states, _, inputs = load_positions([path], engine, set())
    groups = {"quiet": defaultdict(list), "radius_two": defaultdict(list)}
    legal = {}
    successors = {}
    for fen, state in sorted(states.items()):
        refined = typed_radius_two(state)
        if refined is None:
            continue
        groups["quiet"][refined[1]].append(fen)
        groups["radius_two"][refined].append(fen)

    results = {}
    for name, buckets in groups.items():
        signature = _quiet_signature if name == "quiet" else typed_radius_two
        stats = Counter()
        for fens in buckets.values():
            for a, b in combinations(fens, 2):
                stats["pairs"] += 1
                for fen in (a, b):
                    if fen not in legal:
                        legal[fen] = {_action_key(m): m for m in engine.legal_moves(states[fen])}
                        successors[fen] = {
                            key: engine.apply_move(states[fen], move)
                            for key, move in legal[fen].items()
                        }
                if legal[a].keys() != legal[b].keys():
                    stats["different_legal_actions"] += 1
                elif not legal[a]:
                    stats["terminal_pairs"] += 1
                elif any(signature(successors[a][move]) != signature(successors[b][move])
                         for move in legal[a]):
                    stats["different_successor_signatures"] += 1
        results[name] = {
            "eligible_fens": sum(map(len, buckets.values())),
            "distinct_eligible_signatures": len(buckets),
            "collision_groups": sum(len(fens) > 1 for fens in buckets.values()),
            **{key: stats[key] for key in (
                "pairs", "different_legal_actions", "terminal_pairs",
                "different_successor_signatures",
            )},
        }
    return {"inputs": inputs, "distinct_fens": len(states), "variants": results}


def summarize_pairs(report):
    if report["schema"] != "mtdp-best-move-v1" or report["scan_successor_depth"] != 12:
        raise ValueError("Expected a depth-12 best-move audit")

    keys = {}
    cohorts = {}
    for name in _PAIR_COHORTS:
        groups = {"retained": [], "removed": []}
        for row in report[name]:
            a, b = row["fen_a"], row["fen_b"]
            for fen in (a, b):
                if fen not in keys:
                    keys[fen] = typed_radius_two(parse_fen(fen))
            if a == b or keys[a] is None or keys[b] is None or keys[a][1] != keys[b][1]:
                raise ValueError("Pair does not share a distinct baseline quiet signature")
            group = "retained" if keys[a] == keys[b] else "removed"
            groups[group].append(row)

        def summarize(rows):
            scored = [row for row in rows if row["status"] == "scored"]
            costs = {}
            for direction in ("a_to_b", "b_to_a"):
                transfers = [row[direction] for row in scored]
                ordinary = [
                    t["ordinary_regret_centimen"] for t in transfers
                    if t["ordinary_regret_centimen"] is not None
                ]
                switches = Counter(
                    f'{t["best_category"]}->{t["transferred_category"]}' for t in transfers
                    if t["best_category"] != t["transferred_category"]
                )
                costs[direction] = {
                    "ordinary": len(ordinary),
                    "at_least_50_centimen": sum(cost >= 50 for cost in ordinary),
                    "maximum_ordinary_centimen": max(ordinary, default=None),
                    "category_switches": dict(sorted(switches.items())),
                }
            return {
                "pairs": len(rows),
                "statuses": dict(sorted(Counter(row["status"] for row in rows).items())),
                "disjoint_optima": sum(not row["optimal_sets_overlap"] for row in scored),
                "costs": costs,
            }

        cohorts[name] = {
            "all": summarize(report[name]),
            **{group: summarize(rows) for group, rows in groups.items()},
        }
    return cohorts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--best-move-report", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    comparison = {}
    for path in args.best_move_report:
        raw = path.read_bytes()
        comparison[path.name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "cohorts": summarize_pairs(json.loads(raw)),
        }
    report = {
        "schema": "mtdp-local-neighborhood-v1",
        "pcblues": pcblues_audit(args.baseline, create_engine()),
        "best_move_comparison": comparison,
    }
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
