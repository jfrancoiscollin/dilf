"""Tests for the formation registry, phase detection and the
:func:`compute_features` aggregator."""

from __future__ import annotations

import pytest

from pedagogy.features.formations import (
    KNOWN_FORMATIONS,
    compute_features,
    detect_formations,
    determine_phase,
)
from pedagogy.game import Move, initial_state, parse_fen, state_from_pieces
from pedagogy.types import Phase

from .conftest import MockEngine
from .fixtures.positions import ALL_POSITIONS, ReferencePosition


def test_known_formations_contains_spec_signatures() -> None:
    assert KNOWN_FORMATIONS["classique_blancs"] == frozenset({32, 37, 41})
    assert KNOWN_FORMATIONS["classique_noirs"] == frozenset({10, 14, 19})
    assert KNOWN_FORMATIONS["roozenburg_blancs"] == frozenset({28, 32, 37})
    assert KNOWN_FORMATIONS["roozenburg_noirs"] == frozenset({14, 19, 23})
    assert KNOWN_FORMATIONS["ghestem_blancs"] == frozenset({27, 32, 38})


def test_detect_formations_on_initial_position_finds_both_classicals() -> None:
    # The 3-square classical signatures are subsets of the initial layout;
    # this is intentionally noisy at PR-2 (motif layer will refine).
    assert detect_formations(initial_state()) == ["classique_blancs", "classique_noirs"]


def test_detect_formations_isolated_position() -> None:
    s = state_from_pieces(white_men=[28, 32, 37])
    assert detect_formations(s) == ["roozenburg_blancs"]


def test_detect_formations_requires_correct_colour() -> None:
    # Black pieces on the white-classique signature must NOT trigger it.
    s = state_from_pieces(black_men=[32, 37, 41])
    assert detect_formations(s) == []


def test_determine_phase_opening_below_half_move_12() -> None:
    assert determine_phase(initial_state(), half_move=1) == Phase.OPENING
    assert determine_phase(initial_state(), half_move=12) == Phase.OPENING


def test_determine_phase_middlegame_default() -> None:
    assert determine_phase(initial_state(), half_move=13) == Phase.MIDDLEGAME


def test_determine_phase_endgame_low_material() -> None:
    s = state_from_pieces(white_men=[1, 2], black_men=[49, 50])
    assert determine_phase(s, half_move=50) == Phase.ENDGAME


def test_determine_phase_endgame_kings_on_both_sides() -> None:
    s = state_from_pieces(
        white_men=[31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
        white_kings=[28],
        black_men=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        black_kings=[23],
    )
    # 22 pieces total but kings on both sides -> endgame.
    assert determine_phase(s, half_move=30) == Phase.ENDGAME


@pytest.mark.parametrize("position", ALL_POSITIONS, ids=lambda p: p["name"])
def test_compute_features_matches_reference_structure(position: ReferencePosition) -> None:
    state = parse_fen(position["fen"])
    features = compute_features(state, half_move=20)  # past opening
    assert features.isolated_pawns_white == position["isolated_pawns_white"]
    assert features.isolated_pawns_black == position["isolated_pawns_black"]
    assert features.backward_pawns_white == position["backward_pawns_white"]
    assert features.backward_pawns_black == position["backward_pawns_black"]
    assert features.holes_white == position["holes_white"]
    assert features.holes_black == position["holes_black"]
    assert features.outposts_white == position["outposts_white"]
    assert features.outposts_black == position["outposts_black"]


@pytest.mark.parametrize("position", ALL_POSITIONS, ids=lambda p: p["name"])
def test_compute_features_matches_reference_formations(position: ReferencePosition) -> None:
    state = parse_fen(position["fen"])
    features = compute_features(state, half_move=20)
    assert features.formations == position["formations"]


def test_compute_features_full_initial_position() -> None:
    s = initial_state()
    f = compute_features(s, half_move=0)
    # Material
    assert f.white_men == 20 and f.black_men == 20 and f.material_balance == 0
    # Center / wings — from PR 1 fixture values.
    assert f.center_count_white == 4 and f.center_count_black == 4
    assert f.left_wing_white == 4 and f.right_wing_white == 4
    assert f.left_wing_black == 3 and f.right_wing_black == 4
    # Phase: half_move=0 -> opening.
    assert f.phase == Phase.OPENING
    # Mobility omitted (no engine) -> 0 by convention.
    assert f.white_legal_moves == 0
    assert f.black_legal_moves == 0


def test_compute_features_uses_engine_for_mobility() -> None:
    s = initial_state()
    engine = MockEngine()
    engine.set_legal(s, [Move(path=(32, 28)), Move(path=(33, 28))])
    flipped = state_from_pieces(
        white_men=s.white_men,
        black_men=s.black_men,
        turn="black",
    )
    engine.set_legal(flipped, [Move(path=(18, 23))])
    f = compute_features(s, half_move=0, engine=engine)
    assert f.white_legal_moves == 2
    assert f.black_legal_moves == 1
