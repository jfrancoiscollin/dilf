"""Tests for :class:`pedagogy.motifs.coup_express.CoupExpressDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_express import CoupExpressDetector, _path_is_straight


def test_path_is_straight_returns_true_for_pure_diagonal() -> None:
    # 50 (row 10, col 9) -> 39 (row 8, col 7) -> 28 (row 6, col 5) -> 17 -> 6
    # all moving up-left in the same direction.
    assert _path_is_straight((50, 39, 28, 17, 6)) is True


def test_path_is_straight_returns_false_when_direction_changes() -> None:
    # 50 -> 39 (up-left), then 39 -> 30 (up-right) -> direction changed.
    assert _path_is_straight((50, 39, 30)) is False


def test_path_is_straight_returns_true_for_very_short_path() -> None:
    assert _path_is_straight((40, 29)) is True


def test_detector_name() -> None:
    assert CoupExpressDetector().name == "coup_express"


def test_detect_returns_none_for_short_rafle() -> None:
    det = CoupExpressDetector()
    move = Move(path=(40, 29, 18, 7), captures=(34, 23, 12))  # 3 captures, < 5
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_for_non_straight_long_rafle() -> None:
    det = CoupExpressDetector()
    # 5 captures but path zig-zags.
    move = Move(
        path=(40, 29, 18, 27, 38, 49),
        captures=(34, 23, 22, 33, 44),
    )
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_flags_5_captures_in_straight_line() -> None:
    det = CoupExpressDetector()
    # Six consecutive main-diagonal squares, all moving in the (-1, +1)
    # direction. Captures are placed off-path; the dataclass does not
    # validate physical realism.
    move = Move(
        path=(46, 41, 37, 32, 28, 23),
        captures=(45, 40, 36, 31, 27),
    )
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_express"
    assert match.role == "played"
    assert match.metadata["captures_count"] == 5
    assert match.metadata["path_length"] == 6


def test_detect_severity_grows_with_captures() -> None:
    det = CoupExpressDetector()
    five = Move(
        path=(46, 41, 37, 32, 28, 23),
        captures=(45, 40, 36, 31, 27),
    )
    six = Move(
        path=(46, 41, 37, 32, 28, 23, 19),
        captures=(45, 40, 36, 31, 27, 22),
    )
    a = det.detect(empty_state(), five, empty_state())
    b = det.detect(empty_state(), six, empty_state())
    assert a is not None and b is not None
    assert a.severity < b.severity


def test_detect_missed_flags_unplayed_express() -> None:
    det = CoupExpressDetector()
    played = Move(path=(32, 27))
    best = Move(
        path=(46, 41, 37, 32, 28, 23),
        captures=(45, 40, 36, 31, 27),
    )
    match = det.detect_missed(empty_state(), best, ["46x23"], played)
    assert match is not None
    assert match.role == "missed"
