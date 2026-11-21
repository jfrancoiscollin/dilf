import itertools
import unittest

from research.mtdp.decision_equivalence.tie_robust_recall import (
    tie_robust_topk_recall,
)


class TieRobustRecallTests(unittest.TestCase):
    def test_adversarial_and_favorable_tie_break(self):
        result = tie_robust_topk_recall(
            {"a": 8, "b": 8, "c": 8, "d": 0},
            ["b", "d", "a", "c"], top_k=2)
        self.assertEqual(result["recall_lower_bound"], 0.5)
        self.assertEqual(result["recall_upper_bound"], 1.0)
        self.assertTrue(result["boundary_tied"])

    def test_unique_cutoff_and_clamp(self):
        result = tie_robust_topk_recall(
            {"a": 3, "b": 2, "c": 1}, ["b", "a", "c"], top_k=2)
        self.assertEqual(result["recall_lower_bound"], 1)
        self.assertEqual(result["recall_upper_bound"], 1)
        self.assertFalse(result["boundary_tied"])
        self.assertEqual(tie_robust_topk_recall(
            {"a": 1}, ["a"], top_k=9)["top_k"], 1)

    def test_exhaustive_small_score_tables(self):
        # Independent oracle enumerates every score-consistent reference top-k.
        for n in range(1, 6):
            actions = tuple("abcde"[:n])
            for values in itertools.product((0, 1, 2), repeat=n):
                ref = dict(zip(actions, values))
                for k in range(1, n + 1):
                    cutoff = sorted(values, reverse=True)[k - 1]
                    fixed = {a for a in actions if ref[a] > cutoff}
                    tied = [a for a in actions if ref[a] == cutoff]
                    possibilities = [
                        fixed | set(choice) for choice in
                        itertools.combinations(tied, k - len(fixed))
                    ]
                    # Reversed legal order catches nontrivial intersection.
                    order = list(reversed(actions))
                    proposed = set(order[:k])
                    recalls = [len(proposed & p) / k for p in possibilities]
                    result = tie_robust_topk_recall(ref, order, top_k=k)
                    self.assertEqual(result["recall_lower_bound"], min(recalls))
                    self.assertEqual(result["recall_upper_bound"], max(recalls))

    def test_fail_closed(self):
        for ref, order, k in [
            ({}, [], 1), ({"a": float("nan")}, ["a"], 1),
            ({"a": True}, ["a"], 1), ({"a": 1}, ["a"], True),
            ({"a": 1, "b": 2}, ["a", "a"], 1),
            ({"a": 1, "b": 2}, ["a"], 1),
        ]:
            with self.assertRaises(ValueError):
                tie_robust_topk_recall(ref, order, top_k=k)


if __name__ == "__main__":
    unittest.main()
