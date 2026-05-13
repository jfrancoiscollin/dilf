"""Tests for :class:`pedagogy.motifs.prise_max_ratee.PriseMaxRateeDetector`.

The detector requires an engine to enumerate the legal moves available in
``state_before``; tests use the in-process MockEngine.
"""

from __future__ import annotations

from pedagogy.game import Move, state_from_pieces
from pedagogy.motifs.prise_max_ratee import PriseMaxRateeDetector

from .conftest import MockEngine


def _state() -> "state_from_pieces":  # type: ignore[name-defined]
    """Tiny placeholder state. The detector ignores its content."""
    return state_from_pieces(white_men=[32], black_men=[27])


def test_detector_name_and_no_pv_required() -> None:
    det = PriseMaxRateeDetector()
    assert det.name == "prise_max_ratee"
    assert det.requires_pv is False


def test_returns_none_for_quiet_move() -> None:
    det = PriseMaxRateeDetector()
    quiet = Move(path=(32, 28))
    state = _state()
    engine = MockEngine()
    engine.set_legal(state, [quiet])
    assert det.detect(state, quiet, state, engine=engine) is None


def test_returns_none_when_no_engine_supplied() -> None:
    det = PriseMaxRateeDetector()
    move = Move(path=(32, 21), captures=(27,))
    assert det.detect(_state(), move, _state(), engine=None) is None


def test_detects_when_played_capture_is_shorter_than_max() -> None:
    det = PriseMaxRateeDetector()
    state = _state()
    played = Move(path=(32, 21), captures=(27,))
    longer = Move(path=(32, 21, 11), captures=(27, 16))
    engine = MockEngine()
    engine.set_legal(state, [played, longer])
    match = det.detect(state, played, state, engine=engine)
    assert match is not None
    assert match.motif == "prise_max_ratee"
    assert match.role == "played"
    assert match.severity == 1.0
    assert match.metadata == {"captures_played": 1, "captures_possible": 2}
    assert match.squares == [32, 21]
    assert match.pv == []


def test_returns_none_when_player_already_took_maximum() -> None:
    det = PriseMaxRateeDetector()
    state = _state()
    longest = Move(path=(32, 21, 11), captures=(27, 16))
    engine = MockEngine()
    engine.set_legal(state, [longest])
    assert det.detect(state, longest, state, engine=engine) is None


def test_default_detect_missed_returns_none() -> None:
    det = PriseMaxRateeDetector()
    state = _state()
    move = Move(path=(32, 21), captures=(27,))
    assert det.detect_missed(state, move, [], move) is None
