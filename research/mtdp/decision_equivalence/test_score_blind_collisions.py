import unittest

from research.mtdp.decision_equivalence.score_blind_collisions import audit


class ScoreBlindCollisionTests(unittest.TestCase):
    def test_distinguishes_signature_and_legal_actions(self):
        rows = [
            dict(game_id="a", position_id="1", signature="s", legal_actions=["31-27", "32-28"]),
            dict(game_id="b", position_id="1", signature="s", legal_actions=["32-28", "31-27"]),
            dict(game_id="a", position_id="2", signature="s", legal_actions=["31-27"]),
            dict(game_id="b", position_id="2", signature="t", legal_actions=["31-27"]),
        ]
        r = audit(rows)
        self.assertEqual((r["positions"], r["distinct_signatures"]), (4, 2))
        self.assertEqual((r["collision_pairs"], r["same_legal_action_pairs"],
                          r["different_legal_action_pairs"], r["within_game_collision_pairs"]),
                         (3, 1, 2, 1))
        self.assertEqual((r["cross_game_collision_pairs"], r["same_legal_cross_game_collision_pairs"],\n                          r["different_legal_cross_game_collision_pairs"]), (2, 1, 1))\n        self.assertFalse(r["decision_equivalence_established"])

    def test_cross_game_combinatorics_against_bruteforce(self):
        import itertools
        for n in range(1, 12):
            rows = [dict(game_id=str(i % 3), position_id=str(i),
                         signature=str(i % 2), legal_actions=["a"] if i % 4 else ["b"])
                    for i in range(n)]
            pairs = [(a, b) for a, b in itertools.combinations(rows, 2)
                     if a["signature"] == b["signature"] and a["game_id"] != b["game_id"]]
            expected_same = sum(set(a["legal_actions"]) == set(b["legal_actions"])
                                for a, b in pairs)
            result = audit(rows)
            self.assertEqual(result["cross_game_collision_pairs"], len(pairs))
            self.assertEqual(result["same_legal_cross_game_collision_pairs"], expected_same)
            self.assertEqual(result["different_legal_cross_game_collision_pairs"],
                             len(pairs) - expected_same)

    def test_rejects_duplicates(self):
        r = dict(game_id="a", position_id="1", signature="s", legal_actions=["31-27"])
        with self.assertRaises(ValueError):
            audit([r, r])
        with self.assertRaises(ValueError):
            audit([dict(r, legal_actions=["31-27", "31-27"])])

    def test_empty(self):
        self.assertIsNone(audit([])["compression_ratio"])


if __name__ == "__main__":
    unittest.main()
