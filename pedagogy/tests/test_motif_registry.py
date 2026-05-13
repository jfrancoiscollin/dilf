"""Tests for the motif registry and the ``detect_all`` orchestrators."""

from __future__ import annotations

from pedagogy.game import GameState, Move, empty_state, state_from_pieces
from pedagogy.motifs import (
    ALL_DETECTORS,
    CoupDeTalonDetector,
    CoupRoyalDetector,
    CoupTurcDetector,
    EnvoiADameDetector,
    PriseMaxRateeDetector,
    SacrificeDetector,
    detect_all,
    detect_all_missed,
)

from .conftest import MockEngine
from .fixtures.coup_royal import NOT_ROYAL_QUIET, ROYAL_CLASSIC_SIX_PROMO


def test_all_detectors_registered() -> None:
    assert CoupRoyalDetector in ALL_DETECTORS
    assert CoupTurcDetector in ALL_DETECTORS
    assert CoupDeTalonDetector in ALL_DETECTORS
    assert EnvoiADameDetector in ALL_DETECTORS
    assert SacrificeDetector in ALL_DETECTORS
    assert PriseMaxRateeDetector in ALL_DETECTORS


def test_registry_names_are_unique() -> None:
    names = [cls.name for cls in ALL_DETECTORS]
    assert len(names) == len(set(names))


def test_each_detector_exposes_a_name() -> None:
    for cls in ALL_DETECTORS:
        assert isinstance(cls.name, str) and cls.name


def test_detect_all_empty_when_quiet_move_and_no_engine() -> None:
    state = empty_state()
    assert detect_all(state, NOT_ROYAL_QUIET, state) == []


def test_detect_all_collects_coup_royal_match() -> None:
    # The classical 6-capture rafle zigzags through center so it triggers
    # both `coup_royal` and `coup_de_talon` (the path has a direction
    # change). detect_all returns every matching detector, by design.
    state = empty_state()
    matches = detect_all(state, ROYAL_CLASSIC_SIX_PROMO, state)
    motifs = {m.motif for m in matches}
    assert "coup_royal" in motifs


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
    motifs = {m.motif for m in matches}
    assert "coup_royal" in motifs
    assert all(m.role == "missed" for m in matches)


def test_detect_all_missed_empty_when_best_is_quiet() -> None:
    state = empty_state()
    quiet1 = Move(path=(32, 28))
    quiet2 = Move(path=(33, 28))
    assert detect_all_missed(state, quiet1, [], quiet2) == []


def test_detect_all_combines_sacrifice_and_envoi_a_dame() -> None:
    """An envoi à dame is by construction also a sacrifice; both fire."""
    state_before: GameState = state_from_pieces(
        white_men=[31, 32, 33, 7], black_men=[1, 2], turn="white"
    )
    state_after: GameState = state_from_pieces(
        white_men=[31, 33, 7], black_men=[1, 2], turn="black"
    )
    move = Move(path=(32, 28))
    pv = ["1-6", "7-3"]  # white promotes on 3.
    matches = detect_all(state_before, move, state_after, pv=pv, scan_score_after=0.5)
    motifs = sorted(m.motif for m in matches)
    assert "sacrifice" in motifs
    assert "envoi_a_dame" in motifs
