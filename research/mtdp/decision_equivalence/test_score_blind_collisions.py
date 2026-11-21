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
        self.assertFalse(r["decision_equivalence_established"])

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
