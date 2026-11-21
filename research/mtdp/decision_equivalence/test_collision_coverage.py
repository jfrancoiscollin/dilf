import unittest

from research.mtdp.decision_equivalence.collision_coverage import coverage


def rec(g, p, s, moves):
    return {"game_id": g, "position_id": p, "signature": s, "legal_actions": moves}


class CoverageTests(unittest.TestCase):
    def test_cross_game_discordance_counts_positions_not_pairs(self):
        rows = [rec("a", "1", "S", ["1-2"]), rec("a", "2", "S", ["1-2"]),
                rec("b", "1", "S", ["3-4"]), rec("c", "1", "T", ["5-6"])]
        result = coverage(rows)
        self.assertEqual(result["positions_in_signature_collision"], 3)
        self.assertEqual(result["positions_in_cross_game_collision"], 3)
        self.assertEqual(result["positions_in_cross_game_different_legal_collision"], 3)
        self.assertEqual(result["cross_game_different_legal_coverage"], 0.75)

    def test_same_legal_across_games_is_not_discordance(self):
        rows = [rec("a", "1", "S", ["1-2"]), rec("b", "1", "S", ["1-2"])]
        self.assertEqual(coverage(rows)["positions_in_cross_game_different_legal_collision"], 0)

    def test_intra_game_discordance_is_not_cross_game(self):
        rows = [rec("a", "1", "S", ["1-2"]), rec("a", "2", "S", ["3-4"])]
        self.assertEqual(coverage(rows)["positions_in_cross_game_collision"], 0)

    def test_empty_and_invalid(self):
        self.assertIsNone(coverage([])["cross_game_different_legal_coverage"])
        with self.assertRaises(ValueError):
            coverage([rec("a", "1", "S", ["1-2"]), rec("a", "1", "S", ["1-2"])])
        with self.assertRaises(ValueError):
            coverage([rec("a", "1", "S", ["1-2", "1-2"])])


if __name__ == "__main__":
    unittest.main()
