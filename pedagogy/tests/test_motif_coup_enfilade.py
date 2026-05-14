"""Tests for :class:`pedagogy.motifs.coup_enfilade.CoupEnfiladeDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_enfilade import (
    CoupEnfiladeDetector,
    _path_is_single_diagonal,
    _step_signs,
)


def test_detector_name() -> None:
    assert CoupEnfiladeDetector().name == "coup_enfilade"


def test_detector_does_not_require_pv() -> None:
    assert CoupEnfiladeDetector.requires_pv is False


def test_step_signs_up_left() -> None:
    # 50 (row 10, col 9) → 39 (row 8, col 7): rows decrease, cols decrease.
    assert _step_signs(50, 39) == (-1, -1)


def test_step_signs_down_right() -> None:
    # 6 (row 2, col 1) → 17 (row 4, col 3): rows increase, cols increase.
    assert _step_signs(6, 17) == (1, 1)


def test_path_is_single_diagonal_straight_rafle() -> None:
    assert _path_is_single_diagonal((50, 39, 28, 17)) is True


def test_path_is_single_diagonal_returns_false_for_heel() -> None:
    # 40 → 29 → 18 → 22: last hop changes col direction.
    assert _path_is_single_diagonal((40, 29, 18, 22)) is False


def test_detect_returns_none_for_quiet_move() -> None:
    det = CoupEnfiladeDetector()
    move = Move(path=(32, 28))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_for_two_capture_rafle() -> None:
    det = CoupEnfiladeDetector()
    move = Move(path=(50, 39, 28), captures=(44, 33))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_for_heel_motion_rafle() -> None:
    det = CoupEnfiladeDetector()
    move = Move(path=(40, 29, 18, 22), captures=(34, 23, 17))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_fires_on_straight_three_capture_rafle() -> None:
    det = CoupEnfiladeDetector()
    move = Move(path=(50, 39, 28, 17), captures=(44, 33, 22))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_enfilade"
    assert match.role == "played"
    assert match.metadata == {"captures_count": 3, "path_length": 4}
    assert match.severity == 3 / 5.0


def test_detect_severity_caps_at_one() -> None:
    det = CoupEnfiladeDetector()
    move = Move(
        path=(50, 39, 28, 17, 6),
        captures=(44, 33, 22, 11),
    )
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.severity == min(1.0, 4 / 5.0)


def test_detect_missed_flags_unplayed_enfilade() -> None:
    det = CoupEnfiladeDetector()
    best = Move(path=(50, 39, 28, 17), captures=(44, 33, 22))
    played = Move(path=(32, 28))
    match = det.detect_missed(empty_state(), best, [], played)
    assert match is not None
    assert match.role == "missed"
    assert match.severity == 1.0


def test_detect_missed_returns_none_when_player_played_it() -> None:
    det = CoupEnfiladeDetector()
    move = Move(path=(50, 39, 28, 17), captures=(44, 33, 22))
    assert det.detect_missed(empty_state(), move, [], move) is None
