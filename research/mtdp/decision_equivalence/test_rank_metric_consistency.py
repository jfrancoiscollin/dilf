"""Cross-metric invariants on synthetic positions; no FMJD evidence."""
from itertools import permutations

from research.mtdp.decision_equivalence.rank_audit import audit_ranking
from research.mtdp.decision_equivalence.rank_concordance import pairwise_rank_concordance


def test_two_action_top_one_matches_pairwise_direction():
    for left, right in [(3, 1), (1, 3)]:
        scores = {"a": left, "b": right}
        for order in permutations(("a", "b")):
            rank = audit_ranking(["a", "b"], order, scores)
            pair = pairwise_rank_concordance(["a", "b"], list(order), scores)
            assert rank.top1_exact == (pair["pairwise_accuracy"] == 1.0)
            assert rank.top3_exact
            assert rank.regret_top3 == 0


def test_all_tied_is_not_evidence_of_rank_discrimination():
    scores = {"a": 0, "b": 0, "c": 0}
    for order in permutations(scores):
        rank = audit_ranking(list(scores), order, scores)
        pair = pairwise_rank_concordance(list(scores), list(order), scores)
        assert rank.top1_exact and rank.top3_exact
        assert rank.regret_top1 == rank.regret_top3 == 0
        assert pair["informative_pairs"] == 0
        assert pair["pairwise_accuracy"] is None


def test_top_one_success_does_not_imply_full_rank_concordance():
    scores = {"a": 9, "b": 5, "c": 1}
    rank = audit_ranking(list(scores), ["a", "c", "b"], scores)
    pair = pairwise_rank_concordance(list(scores), ["a", "c", "b"], scores)
    assert rank.top1_exact and rank.top3_exact
    assert pair["discordant_pairs"] == 1
    assert pair["pairwise_accuracy"] == 2 / 3
