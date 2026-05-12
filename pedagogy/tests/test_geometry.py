"""Tests for board geometry helpers."""

from __future__ import annotations

import pytest

from pedagogy.features.geometry import (
    CENTER_CORE,
    CENTER_EXTENDED,
    LEFT_WING,
    MAIN_DIAGONAL,
    NO_MAN_DISTANCE,
    RIGHT_WING,
    coords_to_square,
    diagonal_neighbors,
    min_promotion_distance,
    promotion_distance,
    row_of,
    square_to_coords,
    squares_between,
)
from pedagogy.game import initial_state, state_from_pieces


def test_corners_have_expected_coordinates() -> None:
    assert square_to_coords(1) == (1, 2)   # top-left dark
    assert square_to_coords(5) == (1, 10)  # top-right
    assert square_to_coords(46) == (10, 1)  # bottom-left
    assert square_to_coords(50) == (10, 9)  # bottom-right dark


def test_square_to_coords_is_bijection() -> None:
    for sq in range(1, 51):
        r, c = square_to_coords(sq)
        assert coords_to_square(r, c) == sq


def test_coords_to_square_rejects_light_squares() -> None:
    # (1, 1) is the light top-left corner of the physical board.
    with pytest.raises(ValueError):
        coords_to_square(1, 1)
    # (2, 2) is also light: row even -> dark cols are odd.
    with pytest.raises(ValueError):
        coords_to_square(2, 2)


def test_coords_to_square_rejects_out_of_board() -> None:
    with pytest.raises(ValueError):
        coords_to_square(0, 1)
    with pytest.raises(ValueError):
        coords_to_square(11, 2)


def test_row_of_matches_spec() -> None:
    assert row_of(1) == 1
    assert row_of(5) == 1
    assert row_of(6) == 2
    assert row_of(46) == 10
    assert row_of(50) == 10


def test_diagonal_neighbors_centre_square_has_four() -> None:
    # 28 is a fully interior square.
    neighbors = diagonal_neighbors(28)
    assert sorted(neighbors) == sorted([22, 23, 32, 33])


def test_diagonal_neighbors_corner_has_one() -> None:
    # Square 1 (top-left dark): its only dark neighbor is below-right.
    # (1, 2) -> only valid diagonal step inside the board is (2, 1) or (2, 3).
    neighbors = diagonal_neighbors(1)
    assert sorted(neighbors) == sorted([6, 7])


def test_diagonal_neighbors_edge_has_two_or_three() -> None:
    # Square 5 is the top-right dark square (1, 10). Only one diagonal step
    # is in-board: (2, 9) -> square 10.
    assert diagonal_neighbors(5) == [10]
    # Square 6 (2, 1) has neighbors (1, 2) -> 1 and (3, 2) -> 11.
    assert sorted(diagonal_neighbors(6)) == [1, 11]


def test_main_diagonal_constant_matches_spec() -> None:
    assert MAIN_DIAGONAL == (5, 10, 14, 19, 23, 28, 32, 37, 41, 46)
    # All sit on the same geometric anti-diagonal (row + col == 11 here).
    for sq in MAIN_DIAGONAL:
        r, c = square_to_coords(sq)
        assert r + c == 11


def test_squares_between_along_main_diagonal() -> None:
    assert squares_between(5, 46) == [10, 14, 19, 23, 28, 32, 37, 41]
    assert squares_between(46, 5) == [41, 37, 32, 28, 23, 19, 14, 10]


def test_squares_between_adjacent_returns_empty() -> None:
    assert squares_between(28, 22) == []
    assert squares_between(28, 33) == []


def test_squares_between_rejects_non_diagonal_pair() -> None:
    with pytest.raises(ValueError):
        squares_between(28, 30)  # 30 is not on a diagonal of 28
    with pytest.raises(ValueError):
        squares_between(28, 28)  # equal squares


def test_center_constants_match_spec() -> None:
    assert CENTER_CORE == frozenset({22, 23, 27, 28})
    assert CENTER_CORE.issubset(CENTER_EXTENDED)
    assert len(CENTER_EXTENDED) == 16


def test_left_and_right_wings_are_disjoint_and_match_spec_sizes() -> None:
    assert LEFT_WING.isdisjoint(RIGHT_WING)
    assert len(LEFT_WING) == 9
    assert len(RIGHT_WING) == 10


def test_promotion_distance_for_each_side() -> None:
    # Square 31 lives on row 7 -> white promotes in 6.
    assert promotion_distance(31, "white") == 6
    # Square 31 -> black promotes in 10 - 7 = 3.
    assert promotion_distance(31, "black") == 3
    # Square 5 (row 1) -> white already on promotion row.
    assert promotion_distance(5, "white") == 0
    # Square 46 (row 10) -> black already on promotion row.
    assert promotion_distance(46, "black") == 0


def test_promotion_distance_rejects_invalid_side() -> None:
    with pytest.raises(ValueError):
        promotion_distance(31, "blue")  # type: ignore[arg-type]


def test_min_promotion_distance_in_initial_state() -> None:
    s = initial_state()
    assert min_promotion_distance(s, "white") == 6
    assert min_promotion_distance(s, "black") == 6


def test_min_promotion_distance_excludes_kings_and_returns_sentinel() -> None:
    s = state_from_pieces(white_kings=[28])
    assert min_promotion_distance(s, "white") == NO_MAN_DISTANCE
    # Adding a black man closer to its row: row(46) == 10 -> 0.
    s2 = state_from_pieces(white_kings=[28], black_men=[46])
    assert min_promotion_distance(s2, "black") == 0
