"""Synthetic tie diagnostics; not an independent FMJD cohort."""
import pytest
from research.mtdp.decision_equivalence.tie_aware_metrics import tie_aware_diagnostics


def test_reference_tie_not_false_top1_error():
    out = tie_aware_diagnostics({"a": 10, "b": 10, "c": 0},
                                {"a": 0, "b": 2, "c": 1})
    assert out["top1_match"] is False
    assert out["top1_optimal_set_match"] is True
    assert out["regret"] == 0
    assert out["reference_optimal_set_size"] == 2


def test_k_boundary_ties_are_included():
    out = tie_aware_diagnostics({"a": 10, "b": 8, "c": 8, "d": 0},
                                {"a": 4, "b": 1, "c": 3, "d": 2}, top_k=2)
    assert out["reference_topk_boundary_set_size"] == 3
    assert out["topk_boundary_recall"] == pytest.approx(2 / 3)
    assert out["topk_boundary_precision"] == 1
    assert out["topk_recall"] == 0.5


def test_proposal_ties_reduce_coverage_not_concordance():
    out = tie_aware_diagnostics({"a": 3, "b": 2, "c": 1},
                                {"a": 4, "b": 4, "c": 0})
    assert out["untied_pair_count"] == 2
    assert out["untied_pair_concordance"] == 1
    assert out["untied_pair_coverage"] == pytest.approx(2 / 3)


def test_all_ties_no_claim_of_rank_agreement():
    out = tie_aware_diagnostics({"a": 1, "b": 1}, {"a": 0, "b": 0})
    assert out["untied_pair_count"] == 0
    assert out["untied_pair_concordance"] is None
    assert out["untied_pair_coverage"] == 0


def test_boundary_recall_and_precision_diverge_with_ties():
    out = tie_aware_diagnostics({"a": 5, "b": 4, "c": 4, "d": 4, "e": 0},
                                {"a": 10, "b": 9, "c": 8, "d": 7, "e": 6}, top_k=2)
    assert out["reference_topk_boundary_set_size"] == 4
    assert out["topk_boundary_precision"] == 1
    assert out["topk_boundary_recall"] == pytest.approx(0.5)


def test_no_boundary_tie_precision_equals_recall():
    out = tie_aware_diagnostics({"a": 3, "b": 2, "c": 1},
                                {"a": 3, "b": 1, "c": 2}, top_k=2)
    assert out["topk_boundary_precision"] == out["topk_boundary_recall"] == 0.5


def test_predicted_top1_tie_exposes_optimistic_vs_pessimistic_regret():
    out = tie_aware_diagnostics({"a": 10, "b": 4, "c": 0},
                                {"a": 2, "b": 2, "c": 1})
    assert out["top1_optimal_set_match"] is True  # lexical tie break
    assert out["predicted_top1_set_size"] == 2
    assert out["predicted_top1_any_reference_optimal"] is True
    assert out["predicted_top1_all_reference_optimal"] is False
    assert out["predicted_top1_worst_reference_regret"] == 6
    assert out["regret"] == 0  # deterministic selection only


def test_predicted_top1_tie_all_optimal_has_zero_worst_regret():
    out = tie_aware_diagnostics({"a": 10, "b": 10, "c": 0},
                                {"a": 2, "b": 2, "c": 1})
    assert out["predicted_top1_all_reference_optimal"] is True
    assert out["predicted_top1_worst_reference_regret"] == 0


def test_predicted_top1_tie_no_optimal_action():
    out = tie_aware_diagnostics({"a": 10, "b": 4, "c": 1},
                                {"a": 0, "b": 2, "c": 2})
    assert out["predicted_top1_any_reference_optimal"] is False
    assert out["predicted_top1_worst_reference_regret"] == 9
