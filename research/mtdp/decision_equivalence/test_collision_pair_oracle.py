"""Exhaustive small-case oracle for score-blind signature collision counts.

This test never reads engine scores or reserved FMJD positions.
"""
import itertools
import unittest

from research.mtdp.decision_equivalence.signature_collision_metrics import measure


class CollisionPairOracleTest(unittest.TestCase):
    def test_all_five_position_assignments(self):
        # 2^5 signature assignments x 3^5 game assignments = 7776 cases.
        for sigs in itertools.product("XY", repeat=5):
            for games in itertools.product("abc", repeat=5):
                rows = [
                    {"position_id": str(i), "game_id": games[i], "signature": sigs[i]}
                    for i in range(5)
                ]
                result = measure(rows)
                colliding = [
                    (i, j) for i in range(5) for j in range(i + 1, 5)
                    if sigs[i] == sigs[j]
                ]
                cross = sum(games[i] != games[j] for i, j in colliding)
                self.assertEqual(result["collision_pairs"], len(colliding))
                self.assertEqual(result["cross_game_collision_pairs"], cross)
                self.assertEqual(result["same_game_collision_pairs"], len(colliding) - cross)
                self.assertEqual(result["collision_pair_fraction"], len(colliding) / 10)
                self.assertEqual(result["cross_game_pair_fraction_all_positions"], cross / 10)
                self.assertEqual(
                    result["cross_game_collision_pair_fraction"],
                    cross / len(colliding) if colliding else None,
                )
                self.assertFalse(result["decision_equivalence_established"])
                self.assertFalse(result["minimax_equivalence_established"])


if __name__ == "__main__":
    unittest.main()
