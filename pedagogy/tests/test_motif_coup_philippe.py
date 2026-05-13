"""Tests for :class:`pedagogy.motifs.coup_philippe.CoupPhilippeDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_philippe import CoupPhilippeDetector


def test_detector_name() -> None:
    assert CoupPhilippeDetector().name == "coup_philippe"


def test_detect_returns_none_without_captures() -> None:
    det = CoupPhilippeDetector()
    quiet = Move(path=(32, 27))
    assert det.detect(empty_state(), quiet, empty_state()) is None


def test_detect_returns_none_for_single_capture() -> None:
    det = CoupPhilippeDetector()
    move = Move(path=(32, 23), captures=(28,))  # single capture, not a rafle
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_when_first_capture_is_in_center() -> None:
    det = CoupPhilippeDetector()
    # First captured square 22 is in CENTER_EXTENDED, not a wing.
    move = Move(path=(28, 17, 28), captures=(22, 23))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_flags_rafle_whose_first_capture_is_on_left_wing() -> None:
    det = CoupPhilippeDetector()
    # First captured square 11 is in LEFT_WING.
    move = Move(path=(17, 6, 17), captures=(11, 12))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_philippe"
    assert match.role == "played"
    assert match.metadata["wing"] == "left"
    assert match.metadata["first_capture"] == 11
    assert match.metadata["captures_count"] == 2


def test_detect_flags_rafle_whose_first_capture_is_on_right_wing() -> None:
    det = CoupPhilippeDetector()
    # First captured square 25 is in RIGHT_WING.
    move = Move(path=(20, 30, 19), captures=(25, 24))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.metadata["wing"] == "right"
    assert match.metadata["first_capture"] == 25


def test_detect_severity_scales_with_captures() -> None:
    det = CoupPhilippeDetector()
    short = Move(path=(17, 6, 17), captures=(11, 12))
    long_ = Move(path=(17, 6, 17, 28, 17), captures=(11, 12, 22, 23, 27))
    a = det.detect(empty_state(), short, empty_state())
    b = det.detect(empty_state(), long_, empty_state())
    assert a is not None and b is not None
    assert a.severity < b.severity


def test_detect_missed_flags_unplayed_wing_rafle() -> None:
    det = CoupPhilippeDetector()
    played = Move(path=(32, 27))  # quiet
    best = Move(path=(17, 6, 17), captures=(11, 12))
    match = det.detect_missed(empty_state(), best, ["17x6x17"], played)
    assert match is not None
    assert match.role == "missed"


def test_detect_missed_returns_none_when_player_played_it() -> None:
    det = CoupPhilippeDetector()
    move = Move(path=(17, 6, 17), captures=(11, 12))
    assert det.detect_missed(empty_state(), move, ["17x6x17"], move) is None
