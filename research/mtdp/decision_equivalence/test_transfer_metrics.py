import unittest

from research.mtdp.decision_equivalence.transfer_metrics import evaluate_transfer


class TransferMetricsTests(unittest.TestCase):
    def test_unique_optimum_and_regret(self):
        result = evaluate_transfer({"a": 20, "b": 10, "c": -5}, ["b", "a", "c"], top_k=2)
        self.assertFalse(result["top1_optimal_tie_accepted"])
        self.assertEqual(result["top1_regret_score_units"], 10)
        self.assertEqual(result["topk_guaranteed_reference_recall"], 1.0)
        self.assertEqual(result["topk_possible_reference_recall"], 1.0)
        self.assertFalse(result["topk_boundary_tied"])

    def test_tied_optimum_and_boundary(self):
        result = evaluate_transfer({"a": 8, "b": 8, "c": 8, "d": 0},
                                   ["b", "d", "a", "c"], top_k=2)
        self.assertTrue(result["top1_optimal_tie_accepted"])
        self.assertEqual(result["top1_regret_score_units"], 0)
        self.assertIsNone(result["topk_guaranteed_reference_recall"])
        self.assertEqual(result["topk_possible_reference_recall"], 0.5)
        self.assertTrue(result["topk_boundary_tied"])

    def test_k_clamped_and_singleton(self):
        result = evaluate_transfer({"a": -1}, ["a"], top_k=3)
        self.assertEqual(result["top_k"], 1)
        self.assertTrue(result["top1_optimal_tie_accepted"])
        self.assertFalse(result["minimax_equivalence_established"])

    def test_rejects_partial_illegal_duplicate_and_nonfinite(self):
        for order in (["a"], ["a", "a"], ["a", "c"], ["a", "b", "c"]):
            with self.assertRaises(ValueError):
                evaluate_transfer({"a": 1, "b": 0}, order)
        for score in (float("nan"), float("inf"), True, "1"):
            with self.assertRaises(ValueError):
                evaluate_transfer({"a": score}, ["a"])
        with self.assertRaises(ValueError):
            evaluate_transfer({"a": 1}, ["a"], top_k=0)


if __name__ == "__main__":
    unittest.main()
