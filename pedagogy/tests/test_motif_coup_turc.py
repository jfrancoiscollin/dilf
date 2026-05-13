"""Tests for :class:`pedagogy.motifs.coup_turc.CoupTurcDetector`."""

from __future__ import annotations

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_turc import CoupTurcDetector, _is_turc_signature


def test_signature_detects_repeated_square_in_path() -> None:
    assert _is_turc_signature((40, 29, 18, 29, 7)) is True


def test_signature_returns_false_for_unique_path() -> None:
    assert _is_turc_signature((40, 29, 18, 7)) is False


def test_detector_name() -> None:
    assert CoupTurcDetector().name == "coup_turc"


def test_detect_returns_none_without_captures() -> None:
    det = CoupTurcDetector()
    quiet = Move(path=(32, 28, 32))  # revisits 32 but no captures
    assert det.detect(empty_state(), quiet, empty_state()) is None


def test_detect_returns_none_for_single_capture() -> None:
    # A single capture cannot form a meaningful rafle.
    det = CoupTurcDetector()
    move = Move(path=(32, 21), captures=(27,))
    assert det.detect(empty_state(), move, empty_state()) is None


def test_detect_returns_motif_when_path_revisits_square() -> None:
    det = CoupTurcDetector()
    move = Move(path=(40, 29, 18, 29, 7), captures=(34, 23, 24, 12))
    match = det.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.motif == "coup_turc"
    assert match.role == "played"
    assert match.metadata["captures_count"] == 4
    assert match.metadata["path_length"] == 5


def test_severity_scales_with_captures() -> None:
    det = CoupTurcDetector()
    short = Move(path=(40, 29, 18, 29), captures=(34, 23, 24))
    long = Move(
        path=(40, 29, 18, 29, 7, 18, 22, 18, 11),
        captures=(34, 23, 24, 12, 13, 15, 16, 17),
    )
    s_short = det.detect(empty_state(), short, empty_state())
    s_long = det.detect(empty_state(), long, empty_state())
    assert s_short is not None and s_long is not None
    assert s_long.severity > s_short.severity
    assert s_long.severity <= 1.0


def test_detect_missed_flags_unplayed_coup_turc() -> None:
    det = CoupTurcDetector()
    best = Move(path=(40, 29, 18, 29, 7), captures=(34, 23, 24, 12))
    played = Move(path=(32, 28))
    match = det.detect_missed(empty_state(), best, [], played)
    assert match is not None
    assert match.role == "missed"
    assert match.severity == 1.0


def test_detect_missed_returns_none_when_player_did_play_it() -> None:
    det = CoupTurcDetector()
    move = Move(path=(40, 29, 18, 29, 7), captures=(34, 23, 24, 12))
    assert det.detect_missed(empty_state(), move, [], move) is None
