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

    def test_cross_game_coverage_matches_exhaustive_reference(self):
        # Fixed synthetic matrix: positions, games, signatures and legal sets.
        # No Scan/Jass scores and no independence claim.
        for n in range(1, 80):
            rows = [
                rec(str((i * 7 + n) % 5), str(i),
                    str((i * 11 + n) % 7),
                    [str((i * 13 + n) % 4)])
                for i in range(n)
            ]
            expected_collided = expected_cross = expected_discordant = 0
            for a in rows:
                peers = [b for b in rows if b is not a
                         and b["signature"] == a["signature"]]
                expected_collided += bool(peers)
                cross = [b for b in peers if b["game_id"] != a["game_id"]]
                expected_cross += bool(cross)
                expected_discordant += any(
                    set(b["legal_actions"]) != set(a["legal_actions"])
                    for b in cross
                )
            result = coverage(rows)
            self.assertEqual(result["positions_in_signature_collision"],
                             expected_collided, n)
            self.assertEqual(result["positions_in_cross_game_collision"],
                             expected_cross, n)
            self.assertEqual(result["positions_in_cross_game_different_legal_collision"],
                             expected_discordant, n)

    def test_empty_and_invalid(self):
        self.assertIsNone(coverage([])["cross_game_different_legal_coverage"])
        with self.assertRaises(ValueError):
            coverage([rec("a", "1", "S", ["1-2"]), rec("a", "1", "S", ["1-2"])])
        with self.assertRaises(ValueError):
            coverage([rec("a", "1", "S", ["1-2", "1-2"])])


if __name__ == "__main__":
    unittest.main()
