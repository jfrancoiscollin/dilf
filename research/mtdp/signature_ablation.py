"""Controlled signature ablation against exact FMJD legal-action agreement.

Ablations compare fixed coarse features to piece counts and king counts.
No best-move or strategic equivalence claims are made.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.legal_collision_audit import _legal_fingerprint
from research.mtdp.metrics import compute_spatial_metrics
from research.mtdp.pdn import PdnGame, read_games, validated_trajectory
from research.mtdp.spatial_dynamics import _FIELDS


def audit_ablation(games: list[PdnGame], engine: Any) -> dict[str, Any]:
    variants: dict[str, dict[tuple[Any, ...], dict[str, frozenset[tuple]]]] = {
        name: defaultdict(dict)
        for name in ("coarse_turn", "plus_piece_counts", "plus_king_counts", "exact_occupancy")
    }
    observations = 0
    for game in games:
        trajectory = validated_trajectory(game, engine)
        observations += len(trajectory)
        for _, _, state in trajectory:
            m = compute_spatial_metrics(state)
            base = tuple(getattr(m, field) for field in _FIELDS) + (state.turn,)
            counts = (len(state.white_men) + len(state.white_kings),
                      len(state.black_men) + len(state.black_kings))
            kings = (len(state.white_kings), len(state.black_kings))
            occupancy = tuple(
                tuple(sorted(getattr(state, name)))
                for name in ("white_men", "white_kings", "black_men", "black_kings")
            )
            keys = {
                "coarse_turn": base,
                "plus_piece_counts": base + counts,
                "plus_king_counts": base + counts + kings,
                "exact_occupancy": base + counts + kings + occupancy,
            }
            legal = _legal_fingerprint(engine, state)
            for name, key in keys.items():
                existing = variants[name][key].get(m.fen)
                if existing is not None and existing != legal:
                    raise AssertionError("Inconsistent legal moves for canonical FEN")
                variants[name][key][m.fen] = legal

    results = {}
    for name, groups in variants.items():
        pairs = 0
        unequal = 0
        colliding_groups = 0
        for positions in groups.values():
            values = list(positions.values())
            if len(values) > 1:
                colliding_groups += 1
            for i, a in enumerate(values):
                for b in values[i + 1:]:
                    pairs += 1
                    unequal += int(a != b)
        results[name] = {
            "distinct_signatures": len(groups),
            "collision_groups": colliding_groups,
            "distinct_fen_pairs": pairs,
            "different_legal_move_set_pairs": unequal,
            "identical_legal_move_set_pairs": pairs - unequal,
        }
    return {
        "schema_version": "mtdp-signature-ablation-v1",
        "games": len(games),
        "observations": observations,
        "variants": results,
        "interpretation": (
            "Descriptive within-corpus ablation; exact occupancy is a "
            "lossless control, not dimensionality reduction. Equal legal "
            "sets do not imply equivalent best moves."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdn", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_ablation(read_games(args.pdn), create_engine())
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
