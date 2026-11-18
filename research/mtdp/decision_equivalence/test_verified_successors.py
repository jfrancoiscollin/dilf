"""Synthetic fail-closed completeness checks; not an FMJD oracle certification."""
import unittest
from research.mtdp.decision_equivalence.verified_successors import verified_fingerprint
from research.mtdp.decision_equivalence.canonical_successors import fingerprint


class VerifiedSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.actions = ["31-27", "32-28"]
        self.successors = {"31-27": "B:27", "32-28": "B:28"}

    def test_complete_order_independent(self):
        self.assertEqual(verified_fingerprint(self.successors, list(reversed(self.actions))),
                         fingerprint(self.successors))

    def test_missing_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            verified_fingerprint({"31-27": "B:27"}, self.actions)

    def test_extra_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            verified_fingerprint({**self.successors, "33-29": "B:29"}, self.actions)

    def test_duplicate_oracle_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verified_fingerprint(self.successors, ["31-27", "31-27"])

    def test_blank_successor_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid canonical"):
            verified_fingerprint({**self.successors, "31-27": " "}, self.actions)


if __name__ == "__main__":
    unittest.main()
