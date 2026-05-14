"""Tests for :class:`pedagogy.motifs.coup_napoleon.CoupNapoleonDetector`."""

from __future__ import annotations

from pedagogy.game import GameState, Move, state_from_pieces
from pedagogy.motifs.coup_napoleon import (
    CoupNapoleonDetector,
    _is_capture_notation,
    _last_square_of_notation,
    _matches_napoleon_pv,
)


def _state_white_sacrifice() -> tuple[GameState, GameState]:
    before = state_from_pieces(
        white_men=(32, 33),
        black_men=(18, 22, 28),
        turn="white",
    )
    after = state_from_pieces(
        white_men=(33,),
        black_men=(18, 22, 32),
        turn="black",
    )
    return before, after


def test_detector_name() -> None:
    assert CoupNapoleonDetector().name == "coup_napoleon"


def test_is_capture_notation_distinguishes_slides_and_rafles() -> None:
    assert _is_capture_notation("32x21") is True
    assert _is_capture_notation("32-28") is False


def test_last_square_of_notation_handles_capture_and_slide() -> None:
    assert _last_square_of_notation("40x29x18") == 18
    assert _last_square_of_notation("32-28") == 28
    assert _last_square_of_notation("") is None


def test_matches_napoleon_pv_requires_three_plies() -> None:
    assert _matches_napoleon_pv("white", ["32-28", "18x29"]) is None


def test_matches_napoleon_pv_requires_opponent_to_capture() -> None:
    pv = ["32-28", "18-23", "33x24x5"]  # opp slides — no deflection
    assert _matches_napoleon_pv("white", pv) is None


def test_matches_napoleon_pv_requires_landing_on_promotion_row() -> None:
    pv = ["32-28", "18x29", "33-24"]  # follow-up not on row 1..5
    assert _matches_napoleon_pv("white", pv) is None


def test_matches_napoleon_pv_returns_promotion_square_for_white() -> None:
    pv = ["32-28", "18x29", "33x24x4"]
    assert _matches_napoleon_pv("white", pv) == 4


def test_matches_napoleon_pv_uses_correct_row_for_black() -> None:
    pv = ["19-23", "33x24", "27x47"]
    assert _matches_napoleon_pv("black", pv) == 47


def test_detect_returns_none_when_no_pv() -> None:
    det = CoupNapoleonDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    assert det.detect(before, move, after, pv=None) is None


def test_detect_returns_none_when_move_is_not_a_sacrifice() -> None:
    # equal-material state on both sides → delta=0 → not a sacrifice
    det = CoupNapoleonDetector()
    same = state_from_pieces(white_men=(32,), black_men=(18,), turn="white")
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x4"]
    assert det.detect(same, move, same, pv=pv) is None


def test_detect_returns_none_when_played_move_is_itself_promotion() -> None:
    det = CoupNapoleonDetector()
    before = state_from_pieces(white_men=(7, 33), black_men=(18,), turn="white")
    after = state_from_pieces(
        white_kings=(2,), white_men=(33,), black_men=(18,), turn="black"
    )
    move = Move(path=(7, 2), promotion=True)
    pv = ["7-2", "18x29", "33x24x4"]
    assert det.detect(before, move, after, pv=pv) is None


def test_detect_returns_none_when_scan_score_collapsed() -> None:
    det = CoupNapoleonDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x4"]
    assert (
        det.detect(before, move, after, pv=pv, scan_score_after=-2.0) is None
    )


def test_detect_returns_match_when_full_signature_holds() -> None:
    det = CoupNapoleonDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x4"]
    match = det.detect(before, move, after, pv=pv, scan_score_after=0.2)
    assert match is not None
    assert match.motif == "coup_napoleon"
    assert match.role == "played"
    assert match.metadata["promotion_square"] == 4
    assert match.metadata["material_loss"] == 1
    assert match.pv == pv
    assert 4 in match.squares  # promotion square highlighted
