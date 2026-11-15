"""Fail-closed metered Jass TSV contract tests (no mocked playing results)."""
import pytest

from research.mtdp.jass_benchmark.metered_probe_adapter import parse_receipt


FEN = "W:W31,32:B1,2"
FIELDS = [
    "mtdp-probe-v1", "probe", FEN, "1000", "45", "1", "31-26",
    "8", "-31000", "31000", "exact", "none", "1", "2", "31-26,32-28",
]


def receipt(fields=None, *, mode="probe", requested_move="31-26", limit=1000):
    values = FIELDS if fields is None else fields
    return parse_receipt("\t".join(values) + "\n", mode=mode, fen=FEN,
                         issued_limit=limit, requested_move=requested_move,
                         expected_legal_order=["31-26", "32-28"])


def test_exact_single_root_action_verified():
    row = receipt()
    assert (row["completed"], row["nodes"], row["score"], row["move"]) == (
        True, 45, 8, "31-26")
    assert row["native_order"] == ["31-26", "32-28"]


def test_preliminary_must_cover_whole_live_catalogue():
    values = list(FIELDS)
    values[1], values[6], values[12] = "preliminary", "32-28", "2"
    row = receipt(values, mode="preliminary", requested_move=None)
    assert row["winner"] == "32-28" and row["visited"] == row["legal_count"]


@pytest.mark.parametrize("idx,invalid", [
    (0, "wrong-version"), (2, "different-FEN"), (3, "999"),
    (4, "1001"), (4, "-1"), (4, "floating"), (5, "True"),
    (7, "31000"), (8, "-31001"), (9, "31001"),
    (10, "lower"), (11, "nodes"), (12, "2"),
    (13, "1"), (14, "31-26,31-26"),
])
def test_fabricated_or_nonexact_probe_receipts_rejected(idx, invalid):
    values = list(FIELDS)
    values[idx] = invalid
    with pytest.raises(ValueError):
        receipt(values)


def test_interrupted_probe_must_never_expose_exact_score():
    values = list(FIELDS)
    values[5], values[7], values[10], values[11] = "0", "123", "none", "nodes"
    row = receipt(values)
    assert row["completed"] is False and row["score"] is None


def test_missing_or_multiple_output_lines_rejected():
    for raw in ("", "\n", "\t".join(FIELDS) + "\n" + "\t".join(FIELDS) + "\n"):
        with pytest.raises(ValueError):
            parse_receipt(raw, mode="probe", fen=FEN, issued_limit=1000,
                          requested_move="31-26")


def test_native_order_mismatch_rejected():
    with pytest.raises(ValueError, match="Live legal order"):
        parse_receipt("\t".join(FIELDS), mode="probe", fen=FEN, issued_limit=1000,
                      requested_move="31-26", expected_legal_order=["32-28", "31-26"])


def test_illegal_or_wrong_requested_move_rejected():
    with pytest.raises(ValueError, match="Probe action"):
        receipt(requested_move="32-28")


def test_preliminary_incomplete_cannot_claim_winner():
    values = list(FIELDS)
    values[1], values[5], values[10], values[11] = "preliminary", "0", "none", "nodes"
    with pytest.raises(ValueError, match="cannot certify a winner"):
        receipt(values, mode="preliminary", requested_move=None)
    values[6] = "-"
    row = receipt(values, mode="preliminary", requested_move=None)
    assert row["winner"] is None and row["score"] is None


def test_probe_must_not_accept_nonpositive_or_boolean_issued_budget():
    for bad in (0, -1, True, 1.0):
        with pytest.raises(ValueError, match="issued"):
            receipt(limit=bad)
