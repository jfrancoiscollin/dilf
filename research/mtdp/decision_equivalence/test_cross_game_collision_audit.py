"""Synthetic invariants for cross-game collision decomposition."""
import unittest
from research.mtdp.decision_equivalence.cross_game_collision_audit import cross_game_collision_audit


class CrossGameCollisionTests(unittest.TestCase):
    def test_pair_partition(self):
        rows = [
            dict(game_id="A", position_id=0, signature="s", legal_moves=["1-6"]),
            dict(game_id="A", position_id=1, signature="s", legal_moves=["2-7"]),
            dict(game_id="B", position_id=0, signature="s", legal_moves=["1-6"]),
            dict(game_id="C", position_id=0, signature="t", legal_moves=["1-6"]),
        ]
        x = cross_game_collision_audit(rows)
        self.assertEqual((x["signature_collision_pairs"], x["within_game_pairs"], x["cross_game_pairs"]), (3, 1, 2))
        self.assertEqual((x["cross_game_same_legal_actions"], x["cross_game_different_legal_actions"]), (1, 1))
        self.assertFalse(x["independent_cohort_proven"])

    def test_reject_duplicate(self):
        row = dict(game_id="A", position_id=0, signature="s", legal_moves=["1-6"])
        with self.assertRaises(ValueError):
            cross_game_collision_audit([row, row])

    def test_empty(self):
        self.assertEqual(cross_game_collision_audit([])["cross_game_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
