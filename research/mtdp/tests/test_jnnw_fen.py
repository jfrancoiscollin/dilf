"""FMJD square mapping tests; no actual engine replay."""
import pytest

from research.mtdp.jnnw_fen import bitboards_to_fen


def test_initial_position_and_boundaries():
    white = sum(1 << i for i in range(30, 50))
    black = sum(1 << i for i in range(20))
    assert bitboards_to_fen(white, 0, black, 0, 0) == (
        "W:W" + ",".join(map(str, range(31, 51))) + ":B" +
        ",".join(map(str, range(1, 21))))
    assert bitboards_to_fen(0, 1 << 49, 1, 0, 1) == "B:WK50:B1"


def test_reject_overlap_invalid_square_and_stm():
    with pytest.raises(ValueError, match="overlapping"):
        bitboards_to_fen(1, 1, 0, 0, 0)
    with pytest.raises(ValueError, match="50-square"):
        bitboards_to_fen(1 << 50, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="side"):
        bitboards_to_fen(0, 0, 0, 0, 2)
