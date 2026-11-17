"""Synthetic tests only; no claim of minimax or best-move equivalence."""
import unittest
from research.mtdp.decision_equivalence.canonical_successors import fingerprint


class CanonicalSuccessorsTests(unittest.TestCase):
    def test_order_independent(self):
        self.assertEqual(fingerprint({"a": "s1", "b": "s2"}),
                         fingerprint({"b": "s2", "a": "s1"}))

    def test_same_actions_different_successors(self):
        self.assertNotEqual(fingerprint({"a": "s1", "b": "s2"}),
                            fingerprint({"a": "s3", "b": "s2"}))

    def test_different_actions(self):
        self.assertNotEqual(fingerprint({"a": "s1"}), fingerprint({"b": "s1"}))

    def test_reject_ambiguous_input(self):
        for bad in ({}, [], {"": "s"}, {"a": ""}, {"a": None},
                    {" a": "s"}, {"a": " s"}, {1: "s"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fingerprint(bad)


if __name__ == "__main__":
    unittest.main()
