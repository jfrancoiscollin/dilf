"""Synthetic contract checks for D1 action-ranking metrics; no engine cohort."""
import unittest

from research.mtdp.decision_equivalence.ranking_metrics import evaluate_order


class RankingMetricsContract(unittest.TestCase):
    def test_tied_best_is_not_arbitrary_single_label(self):
        result = evaluate_order(["a", "b", "c", "d"], ["b", "d", "a", "c"],
                                {"a": 10, "b": 10, "c": 0, "d": 1})
        self.assertEqual(result["n_optimal"], 2)
        self.assertEqual(result["recall_at_1"], 1)
        self.assertEqual(result["first_action_regret_raw"], 0)
        self.assertEqual(result["top3_oracle_regret_raw"], 0)

    def test_top3_is_not_first_action_quality(self):
        result = evaluate_order(["a", "b", "c", "d"], ["d", "c", "a", "b"],
                                {"a": 20, "b": 0, "c": 1, "d": -5})
        self.assertEqual(result["recall_at_1"], 0)
        self.assertEqual(result["recall_at_3"], 1)
        self.assertEqual(result["first_action_regret_raw"], 25)
        self.assertEqual(result["top3_oracle_regret_raw"], 0)

    def test_all_tied_is_not_discriminating(self):
        result = evaluate_order(["a", "b", "c", "d"], ["d", "c", "b", "a"],
                                dict.fromkeys(["a", "b", "c", "d"], 0))
        self.assertFalse(result["informative_at_3"])
        self.assertEqual(result["n_optimal"], 4)

    def test_fail_closed_on_missing_scores_and_non_permutation(self):
        with self.assertRaises(ValueError):
            evaluate_order(["a", "b"], ["a", "b"], {"a": 1})
        with self.assertRaises(ValueError):
            evaluate_order(["a", "b"], ["a", "a"], {"a": 1, "b": 0})
        with self.assertRaises(ValueError):
            evaluate_order(["a"], ["a"], {"a": True})


if __name__ == "__main__":
    unittest.main()
