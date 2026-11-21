"""Exhaustive board-geometry invariants (synthetic; NOT FMJD move legality).

Independent inverse coordinates detect off-by-one/parity errors on all 50
playable squares. Pairwise geometry is tested without any Scan scores.
"""
import pytest

from research.mtdp.decision_equivalence.fmjd_diagonal_geometry import (
    square_coordinates, validate_diagonal_path,
)


def _inverse(row, col):
    if not (0 <= row < 10 and 0 <= col < 10 and (row + col) % 2 == 1):
        raise ValueError("not a playable FMJD square")
    return 5 * row + col // 2 + 1


def test_all_50_squares_round_trip_and_unique():
    coords = [square_coordinates(s) for s in range(1, 51)]
    assert len(set(coords)) == 50
    assert all(_inverse(r, c) == s for s, (r, c) in enumerate(coords, 1))


def test_all_2500_origin_destination_pairs_diagonal_or_rejected():
    for start in range(1, 51):
        r1, c1 = square_coordinates(start)
        for end in range(1, 51):
            if start == end:
                continue
            r2, c2 = square_coordinates(end)
            diagonal = abs(r2 - r1) == abs(c2 - c1)
            token = f"{start}-{end}"
            if diagonal:
                assert validate_diagonal_path(token) == token
            else:
                with pytest.raises(ValueError):
                    validate_diagonal_path(token)


def test_all_diagonal_capture_pairs_require_at_least_two_rows():
    for start in range(1, 51):
        r1, c1 = square_coordinates(start)
        for end in range(1, 51):
            if start == end:
                continue
            r2, c2 = square_coordinates(end)
            possible = abs(r2 - r1) == abs(c2 - c1) and abs(r2 - r1) >= 2
            token = f"{start}x{end}"
            if possible:
                assert validate_diagonal_path(token) == token
            else:
                with pytest.raises(ValueError):
                    validate_diagonal_path(token)


def test_reverse_diagonal_geometry_is_symmetric_not_move_legality():
    for start in range(1, 51):
        r1, c1 = square_coordinates(start)
        for end in range(1, 51):
            if start == end:
                continue
            r2, c2 = square_coordinates(end)
            if abs(r2 - r1) == abs(c2 - c1):
                assert validate_diagonal_path(f"{start}-{end}")
                assert validate_diagonal_path(f"{end}-{start}")
    # Men are direction-constrained; geometric symmetry cannot establish legality.
