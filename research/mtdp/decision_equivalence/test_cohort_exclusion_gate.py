"""Synthetic tests only; do not treat as cohort evidence."""
import unittest
from research.mtdp.decision_equivalence.cohort_exclusion_gate import validate

A = "a" * 64
B = "b" * 64
C = "c" * 64


def candidate(**kw):
    return dict(game_id="g1", trajectory_sha256=A, fen_sha256=B,
                source="s", tournament="t", ply=0, **kw)


class ExclusionGateTests(unittest.TestCase):
    def test_accept_distinct(self):
        self.assertEqual(len(validate([candidate()], [[{"game_id": "reserved"}]])), 1)

    def test_forbidden_game(self):
        with self.assertRaises(ValueError):
            validate([candidate()], [[{"game_id": "g1"}]])

    def test_forbidden_trajectory(self):
        with self.assertRaises(ValueError):
            validate([candidate()], [[{"trajectory_sha256": A}]])

    def test_forbidden_fen(self):
        with self.assertRaises(ValueError):
            validate([candidate()], [[{"fen_sha256": B}]])

    def test_missing_registry(self):
        with self.assertRaises(ValueError):
            validate([candidate()], [])

    def test_score_leak(self):
        with self.assertRaises(ValueError):
            validate([{**candidate(), "scan_score": 10}], [[{"game_id": "other"}]])

    def test_duplicate_fen(self):
        with self.assertRaises(ValueError):
            validate([candidate(), {**candidate(), "ply": 1}], [[{"game_id": "other"}]])

    def test_chronology(self):
        with self.assertRaises(ValueError):
            validate([{**candidate(), "ply": 2}, {**candidate(), "ply": 1, "fen_sha256": C}],
                     [[{"game_id": "other"}]])

    def test_duplicate_trajectory_other_game(self):
        with self.assertRaises(ValueError):
            validate([candidate(), {**candidate(), "game_id": "g2", "fen_sha256": C}],
                     [[{"game_id": "other"}]])


if __name__ == "__main__":
    unittest.main()
