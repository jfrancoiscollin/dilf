"""Tests for :class:`pedagogy.motifs.coup_raphael.CoupRaphaelDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_raphael import CoupRaphaelDetector


def test_detector_name() -> None:
    assert CoupRaphaelDetector().name == "coup_raphael"


def test_detect_returns_none_for_non_capture() -> None:
    det = CoupRaphaelDetector()
    quiet = Move(path=(28, 22))
    assert det.detect(empty_state(), quiet, empty_state()) is None


def test_detect_returns_none_for_short_rafle() -> None:
    det = CoupRaphaelDetector()
    # Right start/end but only two captures — Raphaël needs 3+.
    move = Move(path=(28, 17, 6), captures=(22, 11))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_when_start_is_not_in_raphael_set() -> None:
    det = CoupRaphaelDetector()
    move = Move(path=(32, 16, 6), captures=(27, 21, 11))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_none_when_landing_is_not_a_promotion_square() -> None:
    det = CoupRaphaelDetector()
    # Starts at 28 but lands on 8, not in promotion row.
    move = Move(path=(28, 17, 8), captures=(22, 13, 12))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_flags_white_28_to_6_pattern() -> None:
    det = CoupRaphaelDetector()
    move = Move(path=(28, 17, 6), captures=(22, 13, 12))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_raphael"
    assert match.role == "played"
    assert match.metadata["side"] == "white"
    assert match.metadata["start_square"] == 28
    assert match.metadata["land_square"] == 6


def test_detect_flags_white_23_to_5_pattern() -> None:
    det = CoupRaphaelDetector()
    move = Move(path=(23, 14, 5), captures=(18, 9, 4))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.metadata["side"] == "white"
    assert match.metadata["land_square"] == 5


def test_detect_flags_black_mirror_to_45_or_46() -> None:
    det = CoupRaphaelDetector()
    # Mirror of 28x6: 23x45 on the black side.
    move = Move(path=(23, 34, 45), captures=(28, 39, 40))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.metadata["side"] == "black"
    assert match.metadata["land_square"] == 45


def test_detect_missed_flags_unplayed_raphael() -> None:
    det = CoupRaphaelDetector()
    played = Move(path=(32, 27))
    best = Move(path=(28, 17, 6), captures=(22, 13, 12))
    match = det.detect_missed(empty_state(), best, ["28x17x6"], played)
    assert match is not None
    assert match.role == "missed"
