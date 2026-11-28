"""Synthetic D1 paired audit invariants; no real cohort or engine scores."""
import itertools
import pytest

from research.mtdp.decision_equivalence.paired_order_audit import paired_order_audit


def test_identical_arms_have_zero_delta():
    result = paired_order_audit(["a", "b", "c", "d"], ["b", "a", "c", "d"],
                                ["b", "a", "c", "d"], {"a": 5, "b": 5, "c": 1, "d": 0})
    assert all(value == 0 for value in result["candidate_minus_baseline"].values())


def test_perfect_vs_reversed_and_raw_units():
    result = paired_order_audit(["a", "b", "c", "d"], ["a", "b", "c", "d"],
                                ["d", "c", "b", "a"], {"a": 100, "b": 50, "c": 20, "d": 0})
    assert result["candidate_minus_baseline"]["first_action_regret_raw"] == -100
    assert result["candidate_minus_baseline"]["pairwise_accuracy"] == 1
    assert result["score_unit"].startswith("raw")


def test_all_ties_are_not_informative():
    result = paired_order_audit(["a", "b", "c", "d"], ["d", "c", "b", "a"],
                                ["a", "b", "c", "d"], dict.fromkeys("abcd", 7))
    assert result["candidate_minus_baseline"]["pairwise_accuracy"] is None
    assert result["candidate"]["recall_at_1"] == 1
    assert result["candidate"]["informative_at_3"] is False


def test_invalid_arm_rejected_even_when_candidate_valid():
    with pytest.raises(ValueError):
        paired_order_audit(["a", "b"], ["a", "b"], ["a", "a"], {"a": 1, "b": 0})


def test_exhaustive_pairwise_antisymmetry_without_ties():
    legal = ["a", "b", "c", "d"]
    scores = dict(zip(legal, [4, 3, 2, 1]))
    base = list(legal)
    for perm in itertools.permutations(legal):
        forward = paired_order_audit(legal, perm, base, scores)
        backward = paired_order_audit(legal, base, perm, scores)
        for key, value in forward["candidate_minus_baseline"].items():
            assert value == -backward["candidate_minus_baseline"][key]
