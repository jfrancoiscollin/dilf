"""Synthetic tests only: no FMJD positions or target scores."""
import pytest
from research.mtdp.decision_equivalence.topk_tie_bounds import topk_tie_bounds


def test_predicted_boundary_tie_can_hide_bad_action():
    r = topk_tie_bounds({"a": 10, "b": 9, "c": 0}, {"a": 5, "b": 4, "c": 4}, 2)
    assert (r["precision_lower"], r["precision_upper"]) == (0.5, 1)
    assert (r["recall_lower"], r["recall_upper"]) == (0.5, 1)


def test_reference_boundary_tie_recall_differs_from_precision():
    r = topk_tie_bounds({"a": 10, "b": 9, "c": 9, "d": 0},
                        {"a": 4, "b": 3, "c": 2, "d": 1}, 2)
    assert r["reference_relevant_count"] == 3
    assert r["precision_lower"] == r["precision_upper"] == 1
    assert r["recall_lower"] == r["recall_upper"] == pytest.approx(2 / 3)


def test_no_ties_has_point_bounds():
    r = topk_tie_bounds({"a": 3, "b": 2, "c": 1}, {"a": 1, "b": 3, "c": 2}, 1)
    assert r["precision_lower"] == r["precision_upper"] == 0


def test_all_predicted_tied_has_extreme_bounds():
    r = topk_tie_bounds({"a": 3, "b": 2, "c": 1}, {"a": 0, "b": 0, "c": 0}, 1)
    assert r["precision_lower"] == 0
    assert r["precision_upper"] == 1


@pytest.mark.parametrize("ref,pred,k", [
    ({}, {}, 1), ({"a": 1}, {"b": 1}, 1),
    ({"a": float("nan")}, {"a": 1}, 1),
    ({"a": 1}, {"a": 1}, 0),
    ({"a": 1}, {"a": 1}, True),
])
def test_invalid_inputs_fail_closed(ref, pred, k):
    with pytest.raises(ValueError):
        topk_tie_bounds(ref, pred, k)
