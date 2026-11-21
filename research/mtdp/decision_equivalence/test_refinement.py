"""Synthetic regression tests for D1 structural refinement."""
import unittest

from research.mtdp.decision_equivalence.refinement import verify_refinement


def row(game, pos, l, lcb):
    return {
        "game_id": game, "position_id": pos, "successor_fingerprint": "s",
        "signatures": {"L": l, "LCB": lcb},
    }


class RefinementTests(unittest.TestCase):
    def test_valid_split(self):
        result = verify_refinement([
            row("g", "1", "a", "x"), row("g", "2", "a", "y"),
            row("h", "3", "b", "z"),
        ], ["L", "LCB"])
        comparison = result["comparisons"][0]
        self.assertTrue(comparison["is_refinement"])
        self.assertEqual((comparison["parent_classes"], comparison["child_classes"]), (2, 3))

    def test_merge_violation(self):
        result = verify_refinement([
            row("g", "1", "a", "x"), row("h", "2", "b", "x"),
        ], ["L", "LCB"])
        comparison = result["comparisons"][0]
        self.assertFalse(comparison["is_refinement"])
        self.assertEqual(comparison["violations"][0]["parent_classes"], 2)

    def test_duplicate_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            verify_refinement([row("g", "1", "a", "x")] * 2, ["L", "LCB"])

    def test_missing_family_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing/invalid"):
            verify_refinement([row("g", "1", "a", "x")], ["L", "quiet"])

    def test_target_score_rejected(self):
        record = row("g", "1", "a", "x")
        record["scan_score"] = 42
        with self.assertRaisesRegex(ValueError, "score-blind"):
            verify_refinement([record], ["L", "LCB"])


if __name__ == "__main__":
    unittest.main()
