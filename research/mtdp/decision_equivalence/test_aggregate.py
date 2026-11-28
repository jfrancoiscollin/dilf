"""Synthetic cases only, never interpreted as independent FMJD evidence."""
import unittest
from research.mtdp.decision_equivalence.aggregate import aggregate_paired


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"id": "p1", "game_id": "g1", "legal": ["a", "b", "c", "d"],
             "proposed": ["a", "b", "c", "d"], "baseline": ["d", "a", "b", "c"],
             "scores": {"a": 0, "b": 0, "c": 0, "d": 9}},
            {"id": "p2", "game_id": "g2", "legal": ["a", "b", "c", "d"],
             "proposed": ["a", "b", "c", "d"], "baseline": ["d", "a", "b", "c"],
             "scores": {"a": 0, "b": 0, "c": 9, "d": 9}},
            {"id": "p3", "game_id": "g3", "legal": ["a", "b", "c"],
             "proposed": ["a", "b", "c"], "baseline": ["c", "a", "b"],
             "scores": {"a": 0, "b": 0, "c": 9}},
        ]

    def test_primary_denominator_independent_of_optimal_ties(self):
        result = aggregate_paired(self.rows)
        self.assertEqual(result["n_all"], 3)
        self.assertEqual(result["primary_score_blind_n_ge_4"]["n"], 2)
        self.assertEqual(result["secondary_score_dependent_informative_at_3"]["n"], 1)
        self.assertEqual(result["primary_score_blind_n_ge_4"]["delta_recall3"], -0.5)
        self.assertEqual(result["primary_score_blind_n_ge_4"]["delta_first_regret_raw"], 9)

    def test_tie_changes_secondary_not_primary_denominator(self):
        rows = [dict(r) for r in self.rows]
        rows[0]["scores"] = {"a": 0, "b": 0, "c": 9, "d": 9}
        result = aggregate_paired(rows)
        self.assertEqual(result["primary_score_blind_n_ge_4"]["n"], 2)
        self.assertEqual(result["secondary_score_dependent_informative_at_3"]["n"], 0)

    def test_no_eligible_rows_return_null_metrics(self):
        result = aggregate_paired([self.rows[2]])["primary_score_blind_n_ge_4"]
        self.assertEqual(result["n"], 0)
        self.assertIsNone(result["delta_recall3"])

    def test_reject_duplicate_or_invalid_pair(self):
        with self.assertRaises(ValueError):
            aggregate_paired([self.rows[0], self.rows[0]])
        broken = dict(self.rows[0], baseline=["a", "a", "c", "d"])
        with self.assertRaises(ValueError):
            aggregate_paired([broken])
