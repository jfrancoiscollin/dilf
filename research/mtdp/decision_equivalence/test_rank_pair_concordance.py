"""Synthetic, score-blind D1-D tests; no independent FMJD cohort."""
import unittest
from math import sqrt
from research.mtdp.decision_equivalence.rank_pair_concordance import kendall_tau_b


class TauBTests(unittest.TestCase):
    def test_perfect_and_reversed(self):
        scores = {"a": 3, "b": 2, "c": 1}
        self.assertEqual(kendall_tau_b(["a", "b", "c"], ["a", "b", "c"], scores), 1)
        self.assertEqual(kendall_tau_b(["a", "b", "c"], ["c", "b", "a"], scores), -1)

    def test_tied_targets_not_arbitrarily_ordered(self):
        scores = {"a": 2, "b": 2, "c": 1}
        self.assertAlmostEqual(kendall_tau_b(["a", "b", "c"], ["b", "a", "c"], scores), 2 / sqrt(6))
        self.assertIsNone(kendall_tau_b(["a", "b"], ["b", "a"], {"a": 1, "b": 1}))

    def test_reject_incomplete_and_nonfinite(self):
        for order, scores in [
            (["a", "a"], {"a": 1, "b": 0}),
            (["a"], {"a": 1, "b": 0}),
            (["a", "b"], {"a": float("nan"), "b": 0}),
        ]:
            with self.assertRaises(ValueError):
                kendall_tau_b(["a", "b"], order, scores)

    def test_one_action_undefined(self):
        self.assertIsNone(kendall_tau_b(["a"], ["a"], {"a": 0}))


if __name__ == "__main__":
    unittest.main()
