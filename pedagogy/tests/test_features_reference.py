"""Cross-reference tests that walk every fixture position and verify all
PR 1 features (material, geometry, promotion distance) at once.

Each fixture is exercised through a single parametrized test so that adding a
new reference position is one entry in ``fixtures/positions.py`` rather than
a new test function.
"""

from __future__ import annotations

import pytest

from pedagogy.features.geometry import (
    CENTER_EXTENDED,
    LEFT_WING,
    RIGHT_WING,
    min_promotion_distance,
)
from pedagogy.features.material import count_material
from pedagogy.game import parse_fen

from .fixtures.positions import ALL_POSITIONS, ReferencePosition


@pytest.mark.parametrize("position", ALL_POSITIONS, ids=lambda p: p["name"])
def test_reference_position_material(position: ReferencePosition) -> None:
    state = parse_fen(position["fen"])
    counts = count_material(state)
    assert counts["white_men"] == position["white_men"]
    assert counts["white_kings"] == position["white_kings"]
    assert counts["black_men"] == position["black_men"]
    assert counts["black_kings"] == position["black_kings"]
    assert counts["balance"] == position["balance"]


@pytest.mark.parametrize("position", ALL_POSITIONS, ids=lambda p: p["name"])
def test_reference_position_center_and_wings(position: ReferencePosition) -> None:
    state = parse_fen(position["fen"])
    white = state.pieces_of("white")
    black = state.pieces_of("black")
    assert len(white & CENTER_EXTENDED) == position["center_count_white"]
    assert len(black & CENTER_EXTENDED) == position["center_count_black"]
    assert len(white & LEFT_WING) == position["left_wing_white"]
    assert len(white & RIGHT_WING) == position["right_wing_white"]
    assert len(black & LEFT_WING) == position["left_wing_black"]
    assert len(black & RIGHT_WING) == position["right_wing_black"]


@pytest.mark.parametrize("position", ALL_POSITIONS, ids=lambda p: p["name"])
def test_reference_position_promotion_distance(position: ReferencePosition) -> None:
    state = parse_fen(position["fen"])
    assert min_promotion_distance(state, "white") == position["white_promotion_distance"]
    assert min_promotion_distance(state, "black") == position["black_promotion_distance"]
