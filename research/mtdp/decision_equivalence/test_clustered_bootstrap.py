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

    def test_seed_independent_of_cluster_first_appearance(self):
        rows = [
            {"game_id": "z", "candidate": 1, "baseline": 0},
            {"game_id": "a", "candidate": 0, "baseline": 1},
            {"game_id": "m", "candidate": 1, "baseline": 1},
            {"game_id": "z", "candidate": 1, "baseline": 0},
        ]
        forward = clustered_difference(rows, repetitions=200, seed=7)
        reversed_clusters = [rows[1], rows[2], rows[0], rows[3]]
        self.assertEqual(forward, clustered_difference(reversed_clusters, repetitions=200, seed=7))

    def test_within_game_order_and_cancellation(self):
        # Extreme but finite values expose order-sensitive float summation.
        rows = [
            {"game_id": "a", "candidate": 1e16, "baseline": 0},
            {"game_id": "a", "candidate": 1, "baseline": 0},
            {"game_id": "a", "candidate": 0, "baseline": 1e16},
            {"game_id": "b", "candidate": 2, "baseline": 0},
        ]
        forward = clustered_difference(rows, repetitions=200, seed=11)
        reordered = [rows[2], rows[3], rows[0], rows[1]]
        self.assertEqual(forward, clustered_difference(reordered, repetitions=200, seed=11))
        self.assertEqual(forward["candidate_minus_baseline"], 0.75)

    def test_tournament_cluster_key(self):
        rows = [
            {"tournament_id": "t2", "candidate": 1, "baseline": 0},
            {"tournament_id": "t1", "candidate": 0, "baseline": 1},
        ]
        result = clustered_difference(rows, cluster_key="tournament_id", repetitions=100)
        self.assertEqual(result["n_clusters"], 2)
        self.assertEqual(result["cluster_key"], "tournament_id")

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
