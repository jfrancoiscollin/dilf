"""Regression checks for linear-count D1 score-blind collision audit."""
import unittest

from research.mtdp.decision_equivalence.score_blind_collisions import audit


def row(game, pos, sig, actions):
    return {"game_id": game, "position_id": pos,
            "signature": sig, "legal_actions": actions}


class ScoreBlindCollisionScaleTests(unittest.TestCase):
    def test_combinatorial_counts(self):
        data = [row("a", "1", "S", ["a", "b"]),
                row("a", "2", "S", ["b", "a"]),
                row("b", "3", "S", ["a"]),
                row("c", "4", "T", ["z"])]
        r = audit(data)
        self.assertEqual(r["collision_pairs"], 3)
        self.assertEqual(r["same_legal_action_pairs"], 1)
        self.assertEqual(r["different_legal_action_pairs"], 2)
        self.assertEqual(r["within_game_collision_pairs"], 1)
        self.assertEqual(r["compression_ratio"], 2.0)
        self.assertFalse(r["decision_equivalence_established"])

    def test_large_single_signature(self):
        n = 2000
        r = audit(row("game-" + str(i // 2), str(i), "S",
                      ["x"] if i % 2 else ["x", "y"]) for i in range(n))
        self.assertEqual(r["collision_pairs"], n * (n - 1) // 2)
        self.assertEqual(r["same_legal_action_pairs"], 2 * (1000 * 999 // 2))
        self.assertEqual(r["within_game_collision_pairs"], n // 2)

    def test_invalid_or_duplicate(self):
        with self.assertRaises(ValueError):
            audit([row("a", "1", "S", ["x"]), row("a", "1", "T", ["x"])])
        with self.assertRaises(ValueError):
            audit([row("a", "1", "S", ["x", "x"])])


if __name__ == "__main__":
    unittest.main()
