"""Independent exhaustive oracle for top-K tie bounds (synthetic scores only).

Enumerates every predicted boundary resolution instead of reusing the
closed-form lower/upper bound equations from the implementation.
"""
from itertools import combinations, product

from research.mtdp.decision_equivalence.topk_tie_bounds import topk_tie_bounds


def test_exhaustive_topk_tie_bounds_four_actions_three_score_levels():
    actions = tuple("abcd")
    scores = tuple(product(range(3), repeat=len(actions)))
    checked = 0
    for ref_values in scores:
        reference = dict(zip(actions, ref_values))
        for pred_values in scores:
            predicted = dict(zip(actions, pred_values))
            for k in range(1, len(actions) + 1):
                result = topk_tie_bounds(reference, predicted, k)
                ref_threshold = sorted(ref_values, reverse=True)[k - 1]
                relevant = {a for a in actions if reference[a] >= ref_threshold}
                pred_threshold = sorted(pred_values, reverse=True)[k - 1]
                mandatory = {a for a in actions if predicted[a] > pred_threshold}
                tied = {a for a in actions if predicted[a] == pred_threshold}
                possible = [mandatory | set(extra) for extra in
                            combinations(sorted(tied), k - len(mandatory))]
                hits = [len(selection & relevant) for selection in possible]
                assert result["precision_lower"] == min(hits) / k
                assert result["precision_upper"] == max(hits) / k
                assert result["recall_lower"] == min(hits) / len(relevant)
                assert result["recall_upper"] == max(hits) / len(relevant)
                checked += 1
    assert checked == 26244
