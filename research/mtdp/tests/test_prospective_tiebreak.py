"""Contract tests for the prospective outcome-blind tie selector."""
import pytest

from research.mtdp.jass_benchmark.prospective_tiebreak import choose_native_order_tie


def select(order, scores, winner="b", completed=None, exact=None):
    completed = completed if completed is not None else dict.fromkeys(order, True)
    exact = exact if exact is not None else dict.fromkeys(order, True)
    return choose_native_order_tie(order, scores, completed=completed, exact=exact, lcb_winner=winner)


def test_equal_scores_use_native_order_not_archived_winner():
    assert select(["a", "b", "c"], {"a": 7, "b": 7, "c": 3}) == "a"


def test_unequal_scores_preserve_unique_winner():
    assert select(["a", "b"], {"a": 1, "b": 2}) == "b"


def test_inexact_bound_falls_back_to_lcb():
    assert select(["a", "b"], {"a": 2, "b": 2}, exact={"a": False, "b": True}) == "b"


def test_incomplete_search_falls_back_to_lcb():
    assert select(["a", "b"], {"a": 2, "b": 2}, completed={"a": False, "b": True}) == "b"


def test_missing_receipt_falls_back_to_lcb():
    assert select(["a", "b"], {"b": 2}) == "b"


@pytest.mark.parametrize("order,winner", [(["a", "a"], "a"), ([], "a"), (["a"], "b")])
def test_illegal_or_duplicate_moves_rejected(order, winner):
    with pytest.raises(ValueError):
        select(order, dict.fromkeys(order, 1), winner=winner)


def test_inconsistent_winner_rejected():
    with pytest.raises(ValueError):
        select(["a", "b"], {"a": 3, "b": 2})


def test_boolean_score_rejected():
    with pytest.raises(ValueError):
        select(["a", "b"], {"a": True, "b": 1})


@pytest.mark.parametrize("order", [["", "b"], [1, "b"], [None, "b"]])
def test_invalid_move_keys_rejected(order):
    with pytest.raises(ValueError):
        select(order, dict.fromkeys(order, 2))


@pytest.mark.parametrize("field", ["completed", "exact"])
def test_truthy_nonboolean_evidence_rejected(field):
    evidence = {"a": "yes", "b": True}
    kwargs = {field: evidence}
    with pytest.raises(ValueError):
        select(["a", "b"], {"a": 2, "b": 2}, **kwargs)


def test_native_order_changes_tie_choice_but_not_score():
    scores = {"a": 4, "b": 4, "c": 1}
    assert select(["a", "b", "c"], scores) == "a"
    assert select(["b", "a", "c"], scores) == "b"
