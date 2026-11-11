"""Controlled signature ablation against exact FMJD legal-action agreement.

Compare coarse descriptors, material counts, and geometric information.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from pedagogy.features.geometry import BOARD_SQUARES, square_to_coords
from pedagogy.game import Side
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.legal_collision_audit import _legal_fingerprint
from research.mtdp.metrics import compute_spatial_metrics
from research.mtdp.pdn import PdnGame, read_games, validated_trajectory
from research.mtdp.spatial_dynamics import _FIELDS


_PIECE_TYPES = ("white_men", "white_kings", "black_men", "black_kings")
_COORDS = {square: square_to_coords(square) for square in BOARD_SQUARES}
_SQUARE_AT = {coords: square for square, coords in _COORDS.items()}
_ROWS = tuple(
    frozenset(square for square, (row, _) in _COORDS.items() if row == rank)
    for rank in range(1, 11)
)
_ROW_PAIRS = tuple(_ROWS[i] | _ROWS[i + 1] for i in range(0, 10, 2))
_QUADRANTS = tuple(
    frozenset(
        square for square, (row, col) in _COORDS.items()
        if (row > 5) == lower and (col > 5) == right
    )
    for lower in (False, True) for right in (False, True)
)


def _regional_counts(
    pieces: tuple[frozenset[int], ...], regions: tuple[frozenset[int], ...]
) -> tuple[int, ...]:
    return tuple(len(squares & region) for squares in pieces for region in regions)


def _quiet_man_key(
    turn: Side, men: frozenset[int], opponents: frozenset[int]
) -> tuple[Side, frozenset[int], frozenset[int]] | None:
    """Keep the mover's men and enemy blockers on their forward diagonals."""
    occupied = men | opponents
    forward = -1 if turn == "white" else 1
    blocked: set[int] = set()
    for origin in men:
        row, col = _COORDS[origin]
        for dr in (-1, 1):
            for dc in (-1, 1):
                neighbor = _SQUARE_AT.get((row + dr, col + dc))
                if neighbor is None or neighbor not in opponents:
                    continue
                landing = _SQUARE_AT.get((row + 2 * dr, col + 2 * dc))
                if landing is not None and landing not in occupied:
                    return None  # A first jump exists, so the quiet key does not apply.
                if dr == forward:
                    blocked.add(neighbor)
    return turn, men, frozenset(blocked)


def audit_ablation(games: list[PdnGame], engine: Any) -> dict[str, Any]:
    variants: dict[str, dict[tuple[Any, ...], list[str]]] = {
        name: defaultdict(list)
        for name in (
            "coarse_turn", "plus_piece_counts", "plus_king_counts",
            "plus_quadrants", "plus_row_pairs", "plus_rows",
            "plus_mover_occupancy", "quiet_man_geometry", "exact_occupancy",
        )
    }
    legal_by_fen: dict[str, frozenset[tuple]] = {}
    games_by_fen: dict[str, set[int]] = defaultdict(set)
    observations = 0
    quiet_man_fens = 0
    for game in games:
        trajectory = validated_trajectory(game, engine)
        observations += len(trajectory)
        for _, _, state in trajectory:
            m = compute_spatial_metrics(state)
            fen = m.fen
            legal = _legal_fingerprint(engine, state)
            games_by_fen[fen].add(game.index)
            if fen in legal_by_fen:
                if legal_by_fen[fen] != legal:
                    raise AssertionError("Inconsistent legal moves for canonical FEN")
                continue
            legal_by_fen[fen] = legal

            base = tuple(getattr(m, field) for field in _FIELDS) + (state.turn,)
            counts = (len(state.white_men) + len(state.white_kings),
                      len(state.black_men) + len(state.black_kings))
            kings = (len(state.white_kings), len(state.black_kings))
            typed = base + counts + kings
            pieces = tuple(getattr(state, name) for name in _PIECE_TYPES)
            if state.turn == "white":
                mover, opponent = pieces[:2], pieces[2:]
            else:
                mover, opponent = pieces[2:], pieces[:2]
            quiet = None if mover[1] else _quiet_man_key(
                state.turn, mover[0], opponent[0] | opponent[1]
            )
            if not mover[1] and (quiet is None) != any(move[1] for move in legal):
                raise AssertionError(f"Capture classification differs from FMJD for {fen}")
            quiet_man_fens += int(quiet is not None)
            quiet_key = (
                ("quiet", *quiet) if quiet is not None else ("exact", state.turn, *pieces)
            )
            keys = {
                "coarse_turn": base,
                "plus_piece_counts": base + counts,
                "plus_king_counts": typed,
                "plus_quadrants": typed + _regional_counts(pieces, _QUADRANTS),
                "plus_row_pairs": typed + _regional_counts(pieces, _ROW_PAIRS),
                "plus_rows": typed + _regional_counts(pieces, _ROWS),
                "plus_mover_occupancy": typed + mover,
                "quiet_man_geometry": quiet_key,
                "exact_occupancy": typed + pieces,
            }
            for name, key in keys.items():
                variants[name][key].append(fen)

    results = {}
    for name, groups in variants.items():
        pairs = 0
        unequal = 0
        colliding_groups = 0
        cross_game_pairs = 0
        unequal_cross_game_pairs = 0
        for positions in groups.values():
            if len(positions) > 1:
                colliding_groups += 1
            for fen_a, fen_b in combinations(positions, 2):
                pairs += 1
                different = legal_by_fen[fen_a] != legal_by_fen[fen_b]
                unequal += int(different)
                if len(games_by_fen[fen_a] | games_by_fen[fen_b]) > 1:
                    cross_game_pairs += 1
                    unequal_cross_game_pairs += int(different)
        results[name] = {
            "distinct_signatures": len(groups),
            "collision_groups": colliding_groups,
            "distinct_fen_pairs": pairs,
            "different_legal_move_set_pairs": unequal,
            "identical_legal_move_set_pairs": pairs - unequal,
            "cross_game_collision_pairs": cross_game_pairs,
            "different_legal_move_set_cross_game_pairs": unequal_cross_game_pairs,
        }
    return {
        "schema_version": "mtdp-signature-ablation-v1",
        "games": len(games),
        "observations": observations,
        "distinct_fens": len(legal_by_fen),
        "quiet_man_fens": quiet_man_fens,
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
