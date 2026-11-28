"""Audit collisions of coarse spatial signatures across validated FMJD positions.

Collision means identical descriptor counts, NOT equivalent legal actions.
The unit of provenance is a game; repeated positions are deduplicated by FEN.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from research.mtdp.spatial_dynamics import _FIELDS
from research.mtdp.summary import load_jsonl


def collision_audit(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return reproducible collision statistics without observation-level pair enumeration."""
    by_signature: dict[tuple[Any, ...], dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    fen_games: dict[str, set[str]] = defaultdict(set)
    rows_count = 0
    games: set[str] = set()
    for row in records:
        if row.get("source") != "pcblues_game_pdn":
            raise ValueError("Only validated PC Blues trajectories are accepted")
        meta = row["metadata"]
        if meta.get("king_detection_verified") is not True:
            raise ValueError("Unverified king status")
        fen = row["metrics"]["fen"]
        game = row["source_id"]
        if not fen or not isinstance(fen, str):
            raise ValueError("Missing canonical FEN")
        signature = tuple(row["metrics"][field] for field in _FIELDS)
        by_signature[signature][fen].add(game)
        fen_games[fen].add(game)
        games.add(game)
        rows_count += 1

    collision_groups = 0
    distinct_colliding_fens = 0
    cross_game_groups = 0
    cross_game_distinct_pairs = 0
    same_game_distinct_pairs = 0
    examples: list[dict[str, Any]] = []
    for signature, positions in sorted(by_signature.items()):
        if len(positions) < 2:
            continue
        collision_groups += 1
        distinct_colliding_fens += len(positions)
        game_ids = set().union(*positions.values())
        if len(game_ids) > 1:
            cross_game_groups += 1
        # Count pairs of distinct FENs, never two occurrences of the same FEN.
        # Count a pair as cross-game if any game memberships differ.
        fens = sorted(positions)
        # Count pair membership via game sets without enumerating FEN pairs.
        # For each game, count distinct-FEN pairs sharing that game once;
        # a pair may appear in multiple games, so use set arithmetic below.
        # Corpus is small, but a signature may be frequent: enumerate only
        # the pairs of unique FENs, never observation-level pairs.
        for i, a in enumerate(fens):
            for b in fens[i + 1:]:
                if positions[a] & positions[b]:
                    same_game_distinct_pairs += 1
                if len(positions[a] | positions[b]) > 1:
                    cross_game_distinct_pairs += 1
        if len(examples) < 10:
            examples.append({
                "signature": list(signature),
                "distinct_fens": len(fens),
                "games": len(game_ids),
                "example_fens": fens[:2],
            })
    return {
        "schema_version": "mtdp-signature-collisions-v1",
        "observations": rows_count,
        "games": len(games),
        "distinct_fens": len(fen_games),
        "distinct_signatures": len(by_signature),
        "collision_groups": collision_groups,
        "distinct_fens_in_collision_groups": distinct_colliding_fens,
        "cross_game_collision_groups": cross_game_groups,
        "same_game_distinct_fen_pairs": same_game_distinct_pairs,
        "cross_game_distinct_fen_pairs": cross_game_distinct_pairs,
        "examples": examples,
        "interpretation": (
            "Collisions are representational only. They do not establish "
            "legal-move or strategic equivalence. Pairs may be dependent."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit MTDP spatial signature collisions")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collision_audit(load_jsonl(args.input))
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
