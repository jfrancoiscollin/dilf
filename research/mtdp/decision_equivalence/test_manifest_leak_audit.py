"""Deterministic adversarial tests for score-blind split leakage audit."""
import unittest
from research.mtdp.decision_equivalence.manifest_leak_audit import audit


def row(split, game, fen, trajectory):
    return {"split": split, "game_id": game, "fen": fen, "trajectory_id": trajectory}


class LeakAuditTests(unittest.TestCase):
    def test_disjoint(self):
        result = audit([row("train", "g1", "f1", "t1"), row("validation", "g2", "f2", "t2"), row("test", "g3", "f3", "t3")])
        self.assertEqual(result["status"], "PASS_STRUCTURAL_ONLY")
        self.assertEqual(result["cross_split_duplicate_counts"], {"fen": 0, "game": 0, "trajectory": 0})

    def test_each_leak_dimension(self):
        result = audit([row("train", "g1", "f1", "t1"), row("validation", "g1", "f2", "t2"), row("test", "g3", "f1", "t1")])
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(result["cross_split_duplicate_counts"], {"fen": 1, "game": 1, "trajectory": 1})

    def test_same_split_repeats_not_cross_split(self):
        result = audit([row("train", "g1", "f1", "t1"), row("train", "g1", "f1", "t1"), row("validation", "g2", "f2", "t2"), row("test", "g3", "f3", "t3")])
        self.assertEqual(result["cross_split_duplicate_counts"], {"fen": 0, "game": 0, "trajectory": 0})

    def test_whitespace_alias_rejected(self):
        rows = [row("train", "g1 ", "f1", "t1"), row("validation", "g2", "f2", "t2"), row("test", "g3", "f3", "t3")]
        result = audit(rows)
        self.assertEqual(result["status"], "STOP")
        self.assertIn("row_1:noncanonical_identifier_whitespace", result["errors"])
        for key in ("game_id", "fen", "trajectory_id"):
            rows = [row("train", "g1", "f1", "t1"), row("validation", "g2", "f2", "t2"), row("test", "g3", "f3", "t3")]
            rows[0][key] = " " + rows[0][key]
            self.assertEqual(audit(rows)["status"], "STOP")

    def test_non_nfc_aliases_rejected_for_each_identifier(self):
        # Canonically equivalent composed/decomposed strings must not evade
        # cross-partition leakage checks; reject rather than silently normalize.
        for key in ("game_id", "fen", "trajectory_id"):
            with self.subTest(key=key):
                rows = [row("train", "g1", "f1", "t1"),
                        row("validation", "g2", "f2", "t2"),
                        row("test", "g3", "f3", "t3")]
                rows[0][key] = "e\u0301"
                result = audit(rows)
                self.assertEqual(result["status"], "STOP")
                self.assertIn("row_1:noncanonical_unicode_normalization", result["errors"])

    def test_nfc_identifier_is_not_rejected_by_normalization_gate(self):
        rows = [row("train", "\u00e9", "f1", "t1"),
                row("validation", "g2", "f2", "t2"),
                row("test", "g3", "f3", "t3")]
        self.assertEqual(audit(rows)["status"], "PASS_STRUCTURAL_ONLY")

    def test_missing_split_and_bad_row_fail_closed(self):
        self.assertEqual(audit([row("train", "g1", "f1", "t1")])["status"], "STOP")
        self.assertEqual(audit([None])["status"], "STOP")
        self.assertEqual(audit([row("train", "g1", "f1", "t1"), {"split": "test", "game_id": True, "fen": "f", "trajectory_id": "t"}])["status"], "STOP")


if __name__ == "__main__":
    unittest.main()
