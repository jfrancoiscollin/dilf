"""Tests for the structural feature detectors."""

from __future__ import annotations

from pedagogy.features.structure import (
    find_backward_pawns,
    find_holes,
    find_isolated_pawns,
    find_outposts,
)
from pedagogy.game import initial_state, state_from_pieces


def test_isolated_pawn_alone_on_board() -> None:
    s = state_from_pieces(white_men=[28])
    assert find_isolated_pawns(s, "white") == [28]
    assert find_isolated_pawns(s, "black") == []


def test_isolated_pawn_supported_by_friend() -> None:
    # 22 and 28 are diagonal neighbours (both diagonals away).
    s = state_from_pieces(white_men=[22, 28])
    assert find_isolated_pawns(s, "white") == []


def test_isolated_pawn_supported_by_king_only() -> None:
    # 33 supports 28 even when the friend is a king.
    s = state_from_pieces(white_men=[28], white_kings=[33])
    assert find_isolated_pawns(s, "white") == []


def test_initial_position_has_no_isolated_pawns() -> None:
    s = initial_state()
    assert find_isolated_pawns(s, "white") == []
    assert find_isolated_pawns(s, "black") == []


def test_backward_pawn_isolated_on_starting_row() -> None:
    # A lone white man on 50 has no diagonal-forward friend (44, 45 empty).
    s = state_from_pieces(white_men=[50])
    assert find_backward_pawns(s, "white") == [50]


def test_backward_pawn_supported_is_not_flagged() -> None:
    # Support on sq 45 (forward of 50) -> not backward.
    s = state_from_pieces(white_men=[50, 45])
    assert find_backward_pawns(s, "white") == []


def test_backward_pawn_only_men_on_starting_row_count() -> None:
    # A king on row 10 is not a pawn and must be ignored.
    s = state_from_pieces(white_kings=[50])
    assert find_backward_pawns(s, "white") == []


def test_initial_position_has_no_backward_pawns() -> None:
    s = initial_state()
    assert find_backward_pawns(s, "white") == []
    assert find_backward_pawns(s, "black") == []


def test_hole_detected_with_three_friendly_neighbours() -> None:
    # Empty 28 surrounded by friends on 22, 23, 32 (3 of 4 diagonals).
    s = state_from_pieces(white_men=[22, 23, 32])
    assert 28 in find_holes(s, "white")


def test_hole_not_detected_with_only_two_friendly_neighbours() -> None:
    s = state_from_pieces(white_men=[22, 23])
    assert find_holes(s, "white") == []


def test_outpost_advanced_supported_safe() -> None:
    # White man on 17 (row 4), supported by 22 (row 5), no enemy men around.
    s = state_from_pieces(white_men=[17, 22])
    assert find_outposts(s, "white") == [17]


def test_outpost_not_advanced_enough() -> None:
    # White man on 32 (row 7) is on its own half: not advanced.
    s = state_from_pieces(white_men=[32, 37])
    assert find_outposts(s, "white") == []


def test_outpost_capturable_by_enemy_man_disqualifies() -> None:
    # Black 12 can jump 17 to 21 (empty). The square 21 is on-board and dark.
    s = state_from_pieces(white_men=[17, 22], black_men=[12])
    assert find_outposts(s, "white") == []


def test_outpost_for_black_uses_lower_half() -> None:
    # Black man on 33 (row 7) supported by 28 (row 6).
    s = state_from_pieces(black_men=[33, 28])
    assert find_outposts(s, "black") == [33]
