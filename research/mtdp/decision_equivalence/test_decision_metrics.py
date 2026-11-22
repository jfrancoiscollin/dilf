"""Deterministic unit tests for D1 decision diagnostics (synthetic, not a cohort)."""
import pytest
from research.mtdp.decision_equivalence.decision_metrics import compare_rankings


def test_perfect_ranking():
    result = compare_rankings({"a": 30, "b": 20, "c": 0}, {"a": 3, "b": 2, "c": 1}, top_k=2)
    assert result["top1_match"] is True
    assert result["regret"] == 0
    assert result["topk_recall"] == 1
    assert result["strict_pair_concordance"] == 1


def test_bad_ranking_regret_and_pairs():
    result = compare_rankings({"a": 30, "b": 20, "c": 0}, {"a": 0, "b": 1, "c": 2}, top_k=2)
    assert result["top1_match"] is False
    assert result["regret"] == 30
    assert result["topk_recall"] == 0.5
    assert result["strict_pair_concordance"] == 0


def test_tied_reference_is_reported():
    result = compare_rankings({"a": 10, "b": 10}, {"a": 0, "b": 1})
    assert result["reference_top1_tied"] is True
    assert result["regret"] == 0
    assert result["strict_pair_concordance"] is None


@pytest.mark.parametrize("reference,proposed", [
    ({}, {}),
    ({"a": 1}, {"b": 1}),
    ({"a": float("nan")}, {"a": 1}),
    ({"a": 1}, {"a": float("inf")}),
    ({"a": True}, {"a": 1}),
    ({"": 1}, {"": 1}),
])
def test_fail_closed(reference, proposed):
    with pytest.raises(ValueError):
        compare_rankings(reference, proposed)
