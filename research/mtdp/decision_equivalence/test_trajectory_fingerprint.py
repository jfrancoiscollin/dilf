"""Synthetic identity tests; no FMJD or Scan outcome claims."""
import pytest
from research.mtdp.decision_equivalence.trajectory_fingerprint import trajectory_fingerprint as fp


def test_deterministic_and_list_tuple_equivalence():
    assert fp("W:W31:B20", ["31-26", "20-25"]) == fp("W:W31:B20", ("31-26", "20-25"))


def test_order_and_initial_position_matter():
    a = fp("W:W31:B20", ["31-26", "20-25"])
    assert a != fp("W:W31:B20", ["20-25", "31-26"])
    assert a != fp("B:W31:B20", ["31-26", "20-25"])


def test_token_boundaries_not_ambiguous():
    assert fp("fen", ["1", "23"]) != fp("fen", ["12", "3"])
    assert fp("fen", []) != fp("fen", ["1"])


@pytest.mark.parametrize("fen,moves", [
    ("", []), (" ", []), (None, []), ("fen", None),
    ("fen", "31-26"), ("fen", [""]), ("fen", [None]),
    ("fen", [True]), ("fen", [1]),
])
def test_reject_untrusted_metadata(fen, moves):
    with pytest.raises(ValueError):
        fp(fen, moves)
