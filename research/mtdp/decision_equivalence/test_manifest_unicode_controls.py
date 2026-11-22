"""Adversarial tests for invisible Unicode identifier aliases in D1-C."""
import unittest

from research.mtdp.decision_equivalence.manifest_leak_audit import audit


def rows(value):
    return [
        {"split": split, "fen": "W:W31:B20", "game_id": value + str(i), "trajectory_id": "t" + str(i)}
        for i, split in enumerate(("train", "validation", "test"))
    ]


class UnicodeIdentifierTests(unittest.TestCase):
    def test_zero_width_joiner_rejected(self):
        result = audit(rows("game\u200d"))
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(len(result["errors"]), 3)
        self.assertTrue(all("unicode_control_identifier" in e for e in result["errors"]))

    def test_bidirectional_override_rejected(self):
        result = audit(rows("game\u202e"))
        self.assertEqual(result["status"], "STOP")

    def test_newline_inside_identifier_rejected(self):
        result = audit(rows("game\n"))
        self.assertEqual(result["status"], "STOP")

    def test_noncontrol_unicode_not_claimed_canonical(self):
        result = audit(rows("partie-é"))
        self.assertEqual(result["status"], "STOP")  # same FEN across splits

    def test_ascii_unique_manifest_still_passes(self):
        data = rows("game")
        for i, row in enumerate(data):
            row["fen"] = f"W:W{31+i}:B20"
        self.assertEqual(audit(data)["status"], "PASS_STRUCTURAL_ONLY")


if __name__ == "__main__":
    unittest.main()
