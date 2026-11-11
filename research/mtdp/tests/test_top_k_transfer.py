"""Deterministic tests for the offline top-k transfer diagnostic."""
import unittest

from research.mtdp.top_k_transfer import _direction, _ranked, analyze


class TopKTransferTests(unittest.TestCase):
    def setUp(self):
        self.a = "a"
        self.b = "b"
        self.moves = [
            [[11, 16], [], False],
            [[12, 17], [], False],
            [[13, 18], [], False],
            [[14, 19], [], False],
        ]
        self.scores = {
            "a": [{"action": action, "score": score} for action, score in
                  zip(self.moves, [100, 90, 80, 70])],
            "b": [{"action": action, "score": score} for action, score in
                  zip(self.moves, [20, 30, 40, 100])],
        }

    def test_ranking_deterministic_and_ties(self):
        rows = list(reversed(self.scores["a"]))
        self.assertEqual(_ranked(rows)[0][0][0], (11, 16))
        rows[0]["score"] = 100
        self.assertEqual(_ranked(rows)[0][0][0], (11, 16))

    def test_top_three_misses_fourth_best(self):
        result = _direction("a", "b", self.scores, 3)
        self.assertFalse(result["covered"])
        self.assertEqual(result["ordinary_regret_centimen"], 60)
        self.assertEqual(result["candidate_count"], 3)

    def test_full_legal_set_covers_optimum(self):
        result = _direction("a", "b", self.scores, 4)
        self.assertTrue(result["covered"])
        self.assertEqual(result["ordinary_regret_centimen"], 0)

    def test_missing_action_rejected(self):
        self.scores["b"].pop()
        with self.assertRaises(ValueError):
            _direction("a", "b", self.scores, 3)

    def test_nonpositive_k_rejected(self):
        with self.assertRaises(ValueError):
            analyze({"schema": "mtdp-best-move-v1", "scan_successor_depth": 12}, 0)

    def test_wrong_depth_rejected(self):
        with self.assertRaises(ValueError):
            analyze({"schema": "mtdp-best-move-v1", "scan_successor_depth": 8})


if __name__ == "__main__":
    unittest.main()
