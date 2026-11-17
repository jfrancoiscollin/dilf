"""Synthetic regression tests: never interpret signature collisions as minimax."""
import unittest
from research.mtdp.decision_equivalence.signature_collision_audit import audit


def row(game, pos, sig, successor):
    return {"game_id": game, "position_id": pos,
            "signatures": {"L": sig}, "successor_fingerprint": successor}


class CollisionAuditTests(unittest.TestCase):
    def test_collision_not_successor_equivalence(self):
        report = audit([row("a", "1", "x", "next1"),
                        row("b", "2", "x", "next2"),
                        row("b", "3", "y", "next3")])
        metric = report["families"]["L"]
        self.assertEqual(metric["unique_signatures"], 2)
        self.assertEqual(metric["cross_game_collision_groups"], 1)
        self.assertEqual(metric["successor_divergent_collision_groups"], 1)
        self.assertEqual(metric["compression_ratio"], 1.5)

    def test_identical_successors_not_minimax(self):
        metric = audit([row("a", "1", "x", "same"),
                        row("b", "2", "x", "same")])["families"]["L"]
        self.assertEqual(metric["successor_divergent_collision_groups"], 0)

    def test_reject_duplicate_identity(self):
        with self.assertRaises(ValueError):
            audit([row("a", "1", "x", "a"), row("a", "1", "y", "b")])

    def test_reject_score_field(self):
        record = row("a", "1", "x", "next")
        record["score"] = 10
        with self.assertRaises(ValueError):
            audit([record])

    def test_reject_inconsistent_families(self):
        record = row("b", "2", "x", "b")
        record["signatures"] = {"LCB": "x"}
        with self.assertRaises(ValueError):
            audit([row("a", "1", "x", "a"), record])

    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            audit([])


if __name__ == "__main__":
    unittest.main()
