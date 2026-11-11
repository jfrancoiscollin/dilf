"""Deterministic tests for the offline top-k transfer diagnostic."""
import unittest

from research.mtdp.top_k_transfer import _direction, _ranked, _summarize, analyze


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

    def test_shortlist_can_cover_the_entire_legal_set(self):
        result = _direction("a", "b", self.scores, 5)
        self.assertEqual(result["candidate_count"], 4)
        self.assertEqual(_summarize([result])["full_legal_set_transfers"], 1)

    def test_forced_win_switch_excluded_from_ordinary_regret(self):
        self.scores["b"][-1]["score"] = 9999
        result = _direction("a", "b", self.scores, 3)
        summary = _summarize([result])
        self.assertEqual(summary["category_switches"], {"win->ordinary": 1})
        self.assertEqual(summary["ordinary_transfers"], 0)
        self.assertIsNone(summary["ordinary_regret_max"])

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
