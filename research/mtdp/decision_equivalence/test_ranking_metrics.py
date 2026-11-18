"""Deductive fixtures only: no FMJD cohort and no empirical performance claim."""
import unittest

from research.mtdp.decision_equivalence.ranking_metrics import evaluate_order


class RankingMetricTests(unittest.TestCase):
    def test_saturated_three_moves_does_not_enter_primary_population(self):
        r = evaluate_order(["a", "b", "c"], ["a", "b", "c"],
                           {"a": 0, "b": 2, "c": 9})
        self.assertEqual((r["recall_at_1"], r["recall_at_3"]), (0, 1))
        self.assertFalse(r["discriminating_at_3"])
        self.assertEqual(r["first_action_regret_raw"], 9)

    def test_four_moves_rank_four_fails_top_three(self):
        r = evaluate_order(["a", "b", "c", "d"], ["a", "b", "c", "d"],
                           {"a": -3, "b": 1, "c": 0, "d": 7})
        self.assertEqual((r["recall_at_3"], r["first_optimum_rank"]), (0, 4))
        self.assertTrue(r["discriminating_at_3"])

    def test_tied_optimum_at_two_and_four(self):
        r = evaluate_order(["a", "b", "c", "d"], ["a", "b", "c", "d"],
                           {"a": 2, "b": 8, "c": 1, "d": 8})
        self.assertEqual((r["recall_at_1"], r["recall_at_3"]), (0, 1))
        self.assertEqual(r["first_optimum_rank"], 2)
        self.assertEqual(r["first_action_regret_raw"], 6)
        self.assertEqual(r["top3_oracle_regret_raw"], 0)

    def test_top_three_oracle_is_not_first_action(self):
        r = evaluate_order(["a", "b", "c", "d"], ["a", "b", "c", "d"],
                           {"a": -10, "b": 0, "c": 20, "d": 5})
        self.assertEqual(r["first_action_regret_raw"], 30)
        self.assertEqual(r["top3_oracle_regret_raw"], 0)

    def test_terminal_no_decision(self):
        r = evaluate_order([], [], {})
        self.assertFalse(r["decision"])
        self.assertIsNone(r["recall_at_3"])

    def test_invalid_inputs_fail_closed(self):
        cases = [
            (["a", "a"], ["a", "a"], {"a": 1}),
            (["a", "b"], ["a", "a"], {"a": 1, "b": 2}),
            (["a", "b"], ["a", "b"], {"a": 1}),
            (["a"], ["a"], {"a": True}),
            (["a"], ["a"], {"a": 1.0}),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                evaluate_order(*args)


if __name__ == "__main__":
    unittest.main()
