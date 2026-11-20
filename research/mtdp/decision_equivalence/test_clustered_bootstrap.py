"""Synthetic tests: no Scan observations, no independent cohort."""
import unittest
from research.mtdp.decision_equivalence.clustered_bootstrap import clustered_difference


class ClusteredBootstrapContract(unittest.TestCase):
    def test_zero_difference_exact(self):
        rows = [{"game_id": "g1", "candidate": 1, "baseline": 1},
                {"game_id": "g1", "candidate": 0, "baseline": 0},
                {"game_id": "g2", "candidate": 1, "baseline": 1}]
        result = clustered_difference(rows, repetitions=100, seed=9)
        self.assertEqual(result["candidate_minus_baseline"], 0)
        self.assertEqual(result["ci95"], [0, 0])
        self.assertEqual(result["n_clusters"], 2)

    def test_determinism_and_observation_weighting(self):
        rows = [{"game_id": "a", "candidate": 1, "baseline": 0}] * 3
        rows += [{"game_id": "b", "candidate": 0, "baseline": 1}]
        x = clustered_difference(rows, repetitions=200, seed=3)
        self.assertEqual(x, clustered_difference(rows, repetitions=200, seed=3))
        self.assertEqual(x["candidate_minus_baseline"], 0.5)

    def test_reject_single_cluster(self):
        with self.assertRaises(ValueError):
            clustered_difference([{"game_id": "g", "candidate": 1, "baseline": 0}])

    def test_reject_nonfinite_or_boolean(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                clustered_difference([{"game_id": "a", "candidate": value, "baseline": 0},
                                      {"game_id": "b", "candidate": 0, "baseline": 0}])

    def test_reject_invalid_repetitions(self):
        with self.assertRaises(ValueError):
            clustered_difference([{"game_id": "a", "candidate": 1, "baseline": 0},
                                  {"game_id": "b", "candidate": 0, "baseline": 1}],
                                 repetitions=True)


if __name__ == "__main__":
    unittest.main()
