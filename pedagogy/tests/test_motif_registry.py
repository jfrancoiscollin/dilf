"""Tests for the motif registry and the ``detect_all`` orchestrators."""

from __future__ import annotations

from pedagogy.game import Move, empty_state, state_from_pieces
from pedagogy.motifs import (
    ALL_DETECTORS,
    CoupRoyalDetector,
    PriseMaxRateeDetector,
    detect_all,
    detect_all_missed,
)

from .conftest import MockEngine
from .fixtures.coup_royal import NOT_ROYAL_QUIET, ROYAL_CLASSIC_SIX_PROMO


def test_all_detectors_registered() -> None:
    assert CoupRoyalDetector in ALL_DETECTORS
    assert PriseMaxRateeDetector in ALL_DETECTORS


def test_each_detector_exposes_a_name() -> None:
    for cls in ALL_DETECTORS:
        assert isinstance(cls.name, str) and cls.name


def test_detect_all_empty_when_quiet_move_and_no_engine() -> None:
    state = empty_state()
    assert detect_all(state, NOT_ROYAL_QUIET, state) == []


def test_detect_all_collects_coup_royal_match() -> None:
    state = empty_state()
    matches = detect_all(state, ROYAL_CLASSIC_SIX_PROMO, state)
    assert len(matches) == 1
    assert matches[0].motif == "coup_royal"


def test_detect_all_with_engine_can_collect_prise_max_ratee() -> None:
    state = state_from_pieces(white_men=[32], black_men=[27, 16])
    played = Move(path=(32, 21), captures=(27,))
    longer = Move(path=(32, 21, 11), captures=(27, 16))
    engine = MockEngine()
    engine.set_legal(state, [played, longer])
    matches = detect_all(state, played, state, engine=engine)
    motifs = sorted(m.motif for m in matches)
    assert motifs == ["prise_max_ratee"]


def test_detect_all_missed_returns_coup_royal_when_best_is_royal() -> None:
    state = empty_state()
    matches = detect_all_missed(state, ROYAL_CLASSIC_SIX_PROMO, [], NOT_ROYAL_QUIET)
    assert len(matches) == 1
    assert matches[0].motif == "coup_royal"
    assert matches[0].role == "missed"


def test_detect_all_missed_empty_when_best_is_quiet() -> None:
    state = empty_state()
    quiet1 = Move(path=(32, 28))
    quiet2 = Move(path=(33, 28))
    assert detect_all_missed(state, quiet1, [], quiet2) == []
