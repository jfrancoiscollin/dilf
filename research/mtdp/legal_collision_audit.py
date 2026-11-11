"""Test whether same-turn spatial collisions preserve exact legal move sets.

This is a deliberately strict, descriptive counterexample search, not proof
of strategic equivalence or move-quality prediction.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from pedagogy.protocols import EngineProtocol
from research.mtdp.metrics import compute_spatial_metrics
from research.mtdp.pdn import PdnGame, read_games, validated_trajectory
from research.mtdp.spatial_dynamics import _FIELDS
from research.mtdp.trajectories import _load_engine


def _legal_fingerprint(engine: EngineProtocol, state: Any) -> frozenset[tuple]:
    return frozenset(
        (tuple(move.path), tuple(sorted(move.captures)), bool(move.promotion))
        for move in engine.legal_moves(state)
    )


def audit_legal_collisions(games: list[PdnGame], engine: EngineProtocol) -> dict[str, Any]:
    groups: dict[tuple[Any, ...], dict[str, tuple[frozenset[tuple], set[str]]]] = (
        defaultdict(dict)
    )
    for game in games:
        # Complete game validation before using any of its positions.
        trajectory = validated_trajectory(game, engine)
        for _, _, state in trajectory:
            metrics = compute_spatial_metrics(state)
            signature = tuple(getattr(metrics, field) for field in _FIELDS)
            key = signature + (state.turn,)
            legal = _legal_fingerprint(engine, state)
            fen = metrics.fen
            if fen in groups[key]:
                prior_legal, provenance = groups[key][fen]
                if prior_legal != legal:
                    raise AssertionError("Same canonical FEN has inconsistent legal moves")
                provenance.add(str(game.index))
            else:
                groups[key][fen] = (legal, {str(game.index)})

    distinct_pairs = 0
    equal_pairs = 0
    unequal_pairs = 0
    cross_game_pairs = 0
    examples: list[dict[str, Any]] = []
    for key, positions in sorted(groups.items()):
        items = sorted(positions.items())
        for i, (fen_a, (legal_a, games_a)) in enumerate(items):
            for fen_b, (legal_b, games_b) in items[i + 1:]:
                distinct_pairs += 1
                equal = legal_a == legal_b
                equal_pairs += int(equal)
                unequal_pairs += int(not equal)
                cross_game_pairs += int(len(games_a | games_b) > 1)
                if not equal and len(examples) < 10:
                    examples.append({
                        "fen_a": fen_a,
                        "fen_b": fen_b,
                        "turn": key[-1],
                        "legal_moves_a": len(legal_a),
                        "legal_moves_b": len(legal_b),
                        "games_a": sorted(games_a),
                        "games_b": sorted(games_b),
                    })
    return {
        "schema_version": "mtdp-legal-collision-v1",
        "games": len(games),
        "turn_conditioned_collision_pairs": distinct_pairs,
        "identical_legal_move_set_pairs": equal_pairs,
        "different_legal_move_set_pairs": unequal_pairs,
        "cross_game_collision_pairs": cross_game_pairs,
        "counterexamples": examples,
        "interpretation": (
            "Exact square-indexed legal-action equality is a necessary "
            "screen for reuse of untransformed moves, not a sufficient "
            "condition for equivalent strategic value. Dependent pairs."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="FMJD legal action collision audit")
    parser.add_argument("--pdn", type=Path, required=True)
    parser.add_argument("--engine-factory", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_legal_collisions(read_games(args.pdn), _load_engine(args.engine_factory))
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
