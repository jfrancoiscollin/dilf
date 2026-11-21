"""Synthetic necessary-geometry tests; these do not replay a legal FMJD game."""
import pytest
from research.mtdp.decision_equivalence.fmjd_diagonal_geometry import (
    square_coordinates, validate_diagonal_path,
)


def test_coordinates_edges():
    assert square_coordinates(1) == (0, 1)
    assert square_coordinates(5) == (0, 9)
    assert square_coordinates(6) == (1, 0)
    assert square_coordinates(50) == (9, 8)


@pytest.mark.parametrize("square", [0, 51, True, 1.0, "1"])
def test_coordinates_reject_invalid_type_or_bounds(square):
    with pytest.raises(ValueError):
        square_coordinates(square)


@pytest.mark.parametrize("token", ["31-26", "31-22", "12x23x34", "1x12x23"])
def test_necessary_geometry_accepts_diagonal_paths(token):
    assert validate_diagonal_path(token) == token


@pytest.mark.parametrize("token", ["1-50", "31-21", "12x23x35", "31x26", "1x6"])
def test_necessary_geometry_rejects_impossible_paths(token):
    with pytest.raises(ValueError):
        validate_diagonal_path(token)


def test_geometry_is_not_legality():
    # Geometrically valid even on a position with no piece at square 31.
    assert validate_diagonal_path("31-26") == "31-26"
