"""Turn-conditioned collision audit: prevent conflating opposite players to move.

A spatial signature is not an equivalence relation for legal decisions when
side to move differs. This module quantifies the confound without claiming
that same-turn signatures imply strategic equivalence.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from research.mtdp.spatial_dynamics import _FIELDS
from research.mtdp.summary import load_jsonl


def turn_conditioned_audit(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    coarse: dict[tuple[Any, ...], dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    conditioned: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    games: set[str] = set()
    observations = 0
    for row in records:
        if row.get("source") != "pcblues_game_pdn":
            raise ValueError("Expected validated PC Blues trajectories")
        if row["metadata"].get("king_detection_verified") is not True:
            raise ValueError("Unverified king status")
        metrics = row["metrics"]
        turn = metrics["turn"]
        if turn not in ("white", "black"):
            raise ValueError(f"Invalid side to move: {turn!r}")
        fen = metrics["fen"]
        if not isinstance(fen, str) or not fen:
            raise ValueError("Missing FEN")
        signature = tuple(metrics[field] for field in _FIELDS)
        coarse[signature][turn].add(fen)
        conditioned[signature + (turn,)].add(fen)
        games.add(row["source_id"])
        observations += 1

    mixed_turn_groups = sum(
        bool(sides.get("white")) and bool(sides.get("black"))
        for sides in coarse.values()
    )
    conditioned_collision_groups = sum(
        len(fens) > 1 for fens in conditioned.values()
    )
    distinct_fens_in_conditioned_collisions = sum(
        len(fens) for fens in conditioned.values() if len(fens) > 1
    )
    return {
        "schema_version": "mtdp-turn-control-v1",
        "observations": observations,
        "games": len(games),
        "coarse_signatures": len(coarse),
        "mixed_turn_coarse_signature_groups": mixed_turn_groups,
        "turn_conditioned_signatures": len(conditioned),
        "turn_conditioned_collision_groups": conditioned_collision_groups,
        "distinct_fens_in_turn_conditioned_collisions":
            distinct_fens_in_conditioned_collisions,
        "interpretation": (
            "Opposite turns must not be pooled for move-choice equivalence. "
            "Same-turn descriptor collisions still do not prove identical "
            "legal actions or strategic value."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit MTDP side-to-move confounding")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = turn_conditioned_audit(load_jsonl(args.input))
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
