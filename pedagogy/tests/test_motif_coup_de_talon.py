"""Tests for :class:`pedagogy.motifs.coup_de_talon.CoupDeTalonDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_de_talon import CoupDeTalonDetector, _has_heel_motion


def test_heel_returns_false_for_short_path() -> None:
    assert _has_heel_motion((40, 29)) is False


def test_heel_returns_false_for_straight_diagonal() -> None:
    # 50 -> 39 -> 28 -> 17 all go up-left in (down=False, right=False).
    assert _has_heel_motion((50, 39, 28, 17)) is False


def test_heel_returns_true_on_direction_change() -> None:
    # 50 (10,9) -> 39 (8,7) is up-left; 39 -> 30 (6,9) is up-right -> heel.
    assert _has_heel_motion((50, 39, 30)) is True


def test_detector_name() -> None:
    assert CoupDeTalonDetector().name == "coup_de_talon"


def test_detect_returns_none_without_captures() -> None:
    det = CoupDeTalonDetector()
    quiet = Move(path=(40, 29, 18, 22))
    assert det.detect(empty_state(), quiet, empty_state()) is None


def test_detect_returns_none_for_single_capture() -> None:
    det = CoupDeTalonDetector()
    move = Move(path=(32, 21), captures=(27,))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_for_straight_rafle() -> None:
    det = CoupDeTalonDetector()
    move = Move(path=(50, 39, 28, 17), captures=(44, 33, 22))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_motif_when_path_reverses_direction() -> None:
    det = CoupDeTalonDetector()
    move = Move(path=(40, 29, 18, 22), captures=(34, 23, 17))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_de_talon"
    assert match.role == "played"
    assert match.metadata == {"captures_count": 3, "path_length": 4}


def test_detect_missed_flags_unplayed_heel_motion() -> None:
    det = CoupDeTalonDetector()
    best = Move(path=(40, 29, 18, 22), captures=(34, 23, 17))
    played = Move(path=(32, 28))
    match = det.detect_missed(empty_state(), best, [], played)
    assert match is not None
    assert match.role == "missed"
    assert match.severity == 1.0


def test_detect_missed_returns_none_when_player_played_it() -> None:
    det = CoupDeTalonDetector()
    move = Move(path=(40, 29, 18, 22), captures=(34, 23, 17))
    assert det.detect_missed(empty_state(), move, [], move) is None
