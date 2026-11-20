"""Synthetic regression tests only; these are not FMJD measurements."""
import pytest
from research.mtdp.decision_equivalence.rank_concordance import pairwise_rank_concordance as metric


def test_perfect_and_reverse():
    s = {"a": 9, "b": 4, "c": 0}
    assert metric(list(s), list(s), s)["pairwise_accuracy"] == 1
    assert metric(list(s), list(reversed(s)), s)["pairwise_accuracy"] == 0


def test_tied_actions_not_counted_as_errors():
    x = metric(["a", "b", "c"], ["b", "a", "c"], {"a": 5, "b": 5, "c": 1})
    assert (x["concordant_pairs"], x["discordant_pairs"], x["score_tied_pairs"]) == (2, 0, 1)


def test_all_tied_or_terminal_is_undefined():
    assert metric(["a", "b"], ["b", "a"], {"a": 1, "b": 1})["pairwise_accuracy"] is None
    assert metric([], [], {})["pairwise_accuracy"] is None


@pytest.mark.parametrize("legal,ordered,scores", [
    (["a"], ["a", "a"], {"a": 1}),
    (["a", "a"], ["a", "a"], {"a": 1}),
    (["a"], ["a"], {"a": True}),
    (["a"], ["a"], {}),
])
def test_reject_invalid(legal, ordered, scores):
    with pytest.raises(ValueError):
        metric(legal, ordered, scores)
