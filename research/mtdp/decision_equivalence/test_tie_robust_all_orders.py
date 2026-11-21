"""Exhaustive independent oracle for D1 tie bounds across all proposed orders.

Synthetic only: does not constitute an independent FMJD cohort.
"""
import itertools
import unittest

from research.mtdp.decision_equivalence.tie_robust_recall import tie_robust_topk_recall


class AllOrdersTieOracle(unittest.TestCase):
    def test_every_order_small_tables(self):
        checked = 0
        for n in range(1, 5):
            actions = tuple("abcd"[:n])
            for values in itertools.product((0, 1, 2), repeat=n):
                scores = dict(zip(actions, values))
                for k in range(1, n + 1):
                    cutoff = sorted(values, reverse=True)[k - 1]
                    fixed = {a for a in actions if scores[a] > cutoff}
                    boundary = [a for a in actions if scores[a] == cutoff]
                    valid = [fixed | set(extra) for extra in
                             itertools.combinations(boundary, k - len(fixed))]
                    for order in itertools.permutations(actions):
                        proposed = set(order[:k])
                        exact = [len(proposed & candidate) / k for candidate in valid]
                        result = tie_robust_topk_recall(scores, list(order), top_k=k)
                        self.assertEqual(result["recall_lower_bound"], min(exact))
                        self.assertEqual(result["recall_upper_bound"], max(exact))
                        checked += 1
        self.assertEqual(checked, 8301)


if __name__ == "__main__":
    unittest.main()
