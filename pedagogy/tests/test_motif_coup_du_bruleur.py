"""Tests for :class:`pedagogy.motifs.coup_du_bruleur.CoupDuBruleurDetector`."""

from __future__ import annotations

from pedagogy.game import Move, state_from_pieces
from pedagogy.motifs.coup_du_bruleur import (
    CoupDuBruleurDetector,
    _forward_diagonals,
    _is_blocked_man,
)


def test_detector_name() -> None:
    assert CoupDuBruleurDetector().name == "coup_du_bruleur"


def test_detector_does_not_require_pv() -> None:
    assert CoupDuBruleurDetector.requires_pv is False


def test_forward_diagonals_white_returns_up_neighbors() -> None:
    # Square 22 (row 5, col 4): up = row 4 = squares 17, 18.
    assert sorted(_forward_diagonals(22, "white")) == [17, 18]


def test_forward_diagonals_black_returns_down_neighbors() -> None:
    # Square 22 (row 5): down = row 6 = squares 27, 28.
    assert sorted(_forward_diagonals(22, "black")) == [27, 28]


def test_forward_diagonals_handles_edge_squares() -> None:
    # Square 6 (row 2, col 1): for white only one up-neighbor (sq 1).
    fwd = _forward_diagonals(6, "white")
    assert fwd == [1]


def test_is_blocked_man_returns_false_when_a_forward_is_free() -> None:
    state = state_from_pieces(white_men=(22,), black_men=(17,), turn="black")
    # 17 is occupied, 18 is empty → not blocked.
    assert _is_blocked_man(state, 22, "white") is False


def test_is_blocked_man_returns_true_when_both_forwards_occupied() -> None:
    state = state_from_pieces(white_men=(22, 17, 18), turn="black")
    assert _is_blocked_man(state, 22, "white") is True


def test_is_blocked_man_treats_off_board_as_blocked() -> None:
    # Square 6 row 2 col 1: only forward is sq 1.
    state = state_from_pieces(white_men=(6,), black_men=(1,), turn="white")
    assert _is_blocked_man(state, 6, "white") is True


def test_detect_returns_none_for_capture_moves() -> None:
    det = CoupDuBruleurDetector()
    before = state_from_pieces(white_men=(32,), black_men=(27,), turn="white")
    after = state_from_pieces(white_men=(21,), turn="black")
    move = Move(path=(32, 21), captures=(27,))
    assert det.detect(before, move, after) is None


def test_detect_returns_none_when_fewer_than_two_men_burned() -> None:
    det = CoupDuBruleurDetector()
    # Before: white men on (31, 33); black man on 24 (row 5). Black 24's
    # forwards are sq 29, 30 — both empty → not blocked.
    before = state_from_pieces(
        white_men=(31, 33),
        black_men=(24,),
        turn="white",
    )
    # After: white pushed 31 → 27 and 33 → 28; black 24's forwards now are
    # 29 (empty) and 30 (empty) — still not blocked. Synthetic state with
    # only ONE burned man.
    after = state_from_pieces(
        white_men=(29, 30),  # block black 24
        black_men=(24,),
        black_kings=(),
        turn="black",
    )
    move = Move(path=(31, 27))
    # Only 24 became blocked (1 burn) → below threshold.
    assert det.detect(before, move, after) is None


def test_detect_fires_when_two_or_more_opponent_men_become_blocked() -> None:
    det = CoupDuBruleurDetector()
    # Before: black men on 23 and 24 (row 5), both with forward squares (28,
    # 29 for 23; 29, 30 for 24) initially empty → neither blocked.
    before = state_from_pieces(
        white_men=(31, 33),
        black_men=(23, 24),
        turn="white",
    )
    # After: walls of white men on row 6 (28, 29, 30) plus 31 → both 23 and
    # 24 now have both forward diagonals occupied → both burned.
    after = state_from_pieces(
        white_men=(28, 29, 30, 31),
        black_men=(23, 24),
        turn="black",
    )
    move = Move(path=(33, 29))  # synthetic move — only state delta matters
    match = det.detect(before, move, after)
    assert match is not None, "expected coup_du_bruleur match"
    assert match.motif == "coup_du_bruleur"
    assert match.role == "played"
    assert sorted(match.metadata["burned_squares"]) == [23, 24]
    assert match.metadata["burned_count"] == 2
    assert match.severity > 0


def test_severity_scales_with_burned_count() -> None:
    det = CoupDuBruleurDetector()
    before = state_from_pieces(
        white_men=(31,),
        black_men=(22, 23, 24),  # row 5
        turn="white",
    )
    # Fully wall row 6: sq 27, 28, 29, 30.
    after = state_from_pieces(
        white_men=(27, 28, 29, 30),
        black_men=(22, 23, 24),
        turn="black",
    )
    move = Move(path=(31, 27))
    match = det.detect(before, move, after)
    assert match is not None
    assert match.metadata["burned_count"] == 3
    assert match.severity == min(1.0, 3 / 4.0)
