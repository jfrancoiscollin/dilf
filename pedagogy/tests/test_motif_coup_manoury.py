"""Tests for :class:`pedagogy.motifs.coup_manoury.CoupManouryDetector`."""

from __future__ import annotations

from pedagogy.game import GameState, Move, state_from_pieces
from pedagogy.motifs.coup_manoury import (
    CoupManouryDetector,
    _capture_count,
    _followup_capture_count,
)


def _state_white_sacrifice() -> tuple[GameState, GameState]:
    # Synthetic states: white_men loses one piece (balance: -2 → -3 from
    # white's POV → delta = -1 → single-piece sacrifice). The detector only
    # looks at material delta, not at move legality.
    before = state_from_pieces(
        white_men=(32, 33),
        black_men=(18, 22, 27, 28),
        turn="white",
    )
    after = state_from_pieces(
        white_men=(33,),
        black_men=(18, 22, 27, 28),
        turn="black",
    )
    return before, after


def test_detector_name() -> None:
    assert CoupManouryDetector().name == "coup_manoury"


def test_capture_count_handles_slides_and_rafles() -> None:
    assert _capture_count("32-28") == 0
    assert _capture_count("40x29") == 1
    assert _capture_count("40x29x18x7x16") == 4


def test_followup_capture_count_requires_three_plies() -> None:
    assert _followup_capture_count(None) == 0
    assert _followup_capture_count([]) == 0
    assert _followup_capture_count(["32-28", "18x29"]) == 0


def test_followup_capture_count_reads_third_entry() -> None:
    pv = ["32-28", "18x29", "33x24x13x4x15"]
    assert _followup_capture_count(pv) == 4


def test_detect_returns_none_without_pv() -> None:
    det = CoupManouryDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    assert det.detect(before, move, after, pv=None) is None


def test_detect_returns_none_when_followup_too_short() -> None:
    det = CoupManouryDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x13"]  # only 3 captures in pv[2]
    assert det.detect(before, move, after, pv=pv) is None


def test_detect_returns_none_when_move_is_not_a_sacrifice() -> None:
    det = CoupManouryDetector()
    same = state_from_pieces(white_men=(32,), black_men=(18,), turn="white")
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x13x4x15"]
    assert det.detect(same, move, same, pv=pv) is None


def test_detect_returns_none_when_score_collapsed() -> None:
    det = CoupManouryDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x13x4x15"]
    assert (
        det.detect(before, move, after, pv=pv, scan_score_after=-3.0) is None
    )


def test_detect_fires_on_full_signature() -> None:
    det = CoupManouryDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x13x4x15"]
    match = det.detect(before, move, after, pv=pv, scan_score_after=0.1)
    assert match is not None
    assert match.motif == "coup_manoury"
    assert match.role == "played"
    assert match.metadata["followup_captures"] == 4
    assert match.metadata["material_loss"] == 1
    assert match.metadata["followup_notation"] == "33x24x13x4x15"
    assert match.severity == min(1.0, 4 / 6.0)


def test_detect_severity_caps_at_one_for_long_rafles() -> None:
    det = CoupManouryDetector()
    before, after = _state_white_sacrifice()
    move = Move(path=(32, 28))
    pv = ["32-28", "18x29", "33x24x13x4x15x26x37"]  # 6 captures
    match = det.detect(before, move, after, pv=pv, scan_score_after=0.1)
    assert match is not None
    assert match.severity == 1.0


def test_detect_missed_requires_engine() -> None:
    det = CoupManouryDetector()
    before, _ = _state_white_sacrifice()
    best = Move(path=(32, 28))
    played = Move(path=(33, 29))
    pv = ["32-28", "18x29", "33x24x13x4x15"]
    assert (
        det.detect_missed(before, best, pv, played, engine=None) is None
    )
