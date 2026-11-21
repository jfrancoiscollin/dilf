"""Adversarial score-blind checks for D1 lexical identity (not FMJD legality)."""
import pytest
from research.mtdp.decision_equivalence.lexical_trajectory_gate import lexical_trajectory_fingerprint as gate


def test_trajectory_boundaries_are_unambiguous():
    # JSON serialization must distinguish concatenations and move boundaries.
    fen = "W:W31:B20"
    assert gate(fen, ["12x23x34", "31-26"]) != gate(fen, ["12x23", "34-31", "31-26"])
    assert gate(fen, ["31-26", "12x23x34"]) != gate(fen, ["12x23x34", "31-26"])


def test_same_endpoints_distinct_capture_paths_not_merged():
    # A lexical distinction only; both paths may be illegal on this FEN.
    fen = "W:W31:B20"
    paths = ["12x18x34", "12x23x34", "12x29x34"]
    assert len({gate(fen, [p]) for p in paths}) == len(paths)


@pytest.mark.parametrize("bad", [
    "0-1", "1-51", "01-2", "1-02", "1-1", "12x23x12",
    "12x23-34", "12-23x34", "12--23", "12xx23",
    "12X23", "１２-２３", "12-23\n", " 12-23", "12-23 ",
    "12-23\x00", "12/23", "12x23x23", "12-23-34",
])
def test_malformed_tokens_fail_closed(bad):
    with pytest.raises(ValueError):
        gate("W:W31:B20", ["31-26", bad])


def test_hash_does_not_establish_legality():
    # 1-50 is lexically valid but not a legal quiet diagonal on a 10x10 board.
    assert gate("W:W31:B20", ["1-50"]).startswith("sha256:")
