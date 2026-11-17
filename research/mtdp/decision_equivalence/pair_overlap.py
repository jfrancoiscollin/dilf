"""Score-blind, deterministic comparison of LCB and Q matched position pairs.

This compares *pairs of distinct canonical FENs*, not signature counts.
It never reads engine scores, and does not infer strategic equivalence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable

from research.mtdp.decision_equivalence.score_blind_audit import _canonical_actions, _stable


def compare_pairs(records: Iterable[dict[str, Any]], *, max_examples: int = 12) -> dict[str, Any]:
    if max_examples < 0:
        raise ValueError("max_examples must be nonnegative")
    by_fen: dict[str, dict[str, Any]] = {}
    observations = 0
    for row in records:
        observations += 1
        if not isinstance(row, dict):
            raise ValueError("row must be an object")
        fen, game = row.get("fen"), row.get("game_id")
        signatures = row.get("signatures")
        if not isinstance(fen, str) or not fen.strip():
            raise ValueError("missing fen")
        if not isinstance(game, str) or not game.strip():
            raise ValueError("missing game_id")
        if not isinstance(signatures, dict) or any(
            k not in signatures or signatures[k] is None for k in ("E", "L", "LCB", "Q")
        ):
            raise ValueError("missing E/L/LCB/Q signature")
        actions = _canonical_actions(row.get("actions"))
        keys = {k: _stable(signatures[k]) for k in ("E", "L", "LCB", "Q")}
        if fen in by_fen:
            prior = by_fen[fen]
            if prior["actions"] != actions or prior["keys"] != keys:
                raise ValueError("contradictory duplicate FEN: " + fen)
            prior["games"].add(game)
        else:
            by_fen[fen] = {"actions": actions, "keys": keys, "games": {game}}

    if len({v["keys"]["E"] for v in by_fen.values()}) != len(by_fen):
        raise ValueError("E signature collides between distinct FENs")
    groups: dict[str, dict[str, list[str]]] = {
        key: defaultdict(list) for key in ("LCB", "Q")
    }
    for fen, data in by_fen.items():
        for key in groups:
            groups[key][data["keys"][key]].append(fen)
    pairs = {}
    for key, grouping in groups.items():
        pairs[key] = {
            (a, b) for group in grouping.values()
            for a, b in combinations(sorted(group), 2)
        }
    buckets = {
        "common": pairs["LCB"] & pairs["Q"],
        "lcb_only": pairs["LCB"] - pairs["Q"],
        "q_only": pairs["Q"] - pairs["LCB"],
    }
    result: dict[str, Any] = {
        "schema_version": "mtdp-d1-pair-overlap-v1",
        "observations": observations,
        "distinct_fens": len(by_fen),
        "distinct_signatures": {key: len(group) for key, group in groups.items()},
        "buckets": {},
        "limitations": [
            "Same signature or legal actions do not imply the same successor, best move, or minimax value",
            "Cross-game provenance does not prove sample independence",
            "Historical score-blind diagnostic only; no Scan ranking, regret, or Jass strength measured",
        ],
    }
    for name, matched in buckets.items():
        legal_mismatch = 0
        cross_game = 0
        strict_cross_game = 0
        examples = []
        for a, b in sorted(matched):
            left, right = by_fen[a], by_fen[b]
            mismatch = left["actions"] != right["actions"]
            cross = len(left["games"] | right["games"]) > 1
            strict_cross = left["games"].isdisjoint(right["games"])
            legal_mismatch += int(mismatch)
            cross_game += int(cross)
            strict_cross_game += int(strict_cross)
            if len(examples) < max_examples:
                examples.append({
                    "fen_a": a, "fen_b": b,
                    "different_legal_actions": mismatch,
                    "cross_game_provenance": cross,
                    "disjoint_owning_games": strict_cross,
                })
        result["buckets"][name] = {
            "distinct_fen_pairs": len(matched),
            "different_legal_action_pairs": legal_mismatch,
            "cross_game_provenance_pairs": cross_game,
            "disjoint_owning_games_pairs": strict_cross_game,
            "examples": examples,
        }
    assert sum(v["distinct_fen_pairs"] for v in result["buckets"].values()) == len(
        pairs["LCB"] | pairs["Q"]
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        result = compare_pairs(json.loads(line) for line in stream if line.strip())
    encoded = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
