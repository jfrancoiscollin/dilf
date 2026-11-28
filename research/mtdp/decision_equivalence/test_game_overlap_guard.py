"""Synthetic regression tests; no independent FMJD cohort is claimed."""
import unittest

from research.mtdp.decision_equivalence.game_overlap_guard import find_cross_split_windows


class TestGameOverlap(unittest.TestCase):
    def rows(self, game, split, fens):
        return [dict(game_id=game, split=split, ply=i, fen=fen)
                for i, fen in enumerate(fens)]

    def test_reidentified_game(self):
        rows = self.rows("A", "train", ["a", "b", "c", "d"])
        rows += self.rows("B", "test", ["x", "b", "c", "d"])
        self.assertEqual(len(find_cross_split_windows(rows)), 1)

    def test_order_matters(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows += self.rows("B", "test", ["c", "b", "a"])
        self.assertEqual(find_cross_split_windows(rows), [])

    def test_score_leak_rejected(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows[0]["metadata"] = {"score": 3}
        with self.assertRaises(ValueError):
            find_cross_split_windows(rows)

    def test_nonchronological_rejected(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows[1]["ply"] = 0
        with self.assertRaises(ValueError):
            find_cross_split_windows(rows)

    def test_whitespace_alias(self):
        rows = self.rows("A", "train", ["a b", "c", "d"])
        rows += self.rows("B", "test", ["ab", "c", "d"])
        self.assertEqual(len(find_cross_split_windows(rows)), 1)


    def test_same_split_is_not_cross_split_evidence(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows += self.rows("B", "train", ["a", "b", "c"])
        self.assertEqual(find_cross_split_windows(rows), [])

    def test_multiple_test_aliases_reported_once_and_sorted(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows += self.rows("Z", "test", ["a", "b", "c"])
        rows += self.rows("B", "test", ["a", "b", "c"])
        matches = find_cross_split_windows(rows)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["train_games"], ["A"])
        self.assertEqual(matches[0]["test_games"], ["B", "Z"])

    def test_invalid_window_rejected(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        for window in (0, 1, -1, 2.0, True):
            with self.subTest(window=window):
                with self.assertRaises(ValueError):
                    find_cross_split_windows(rows, window=window)

    def test_gapped_plies_do_not_form_false_game_alias(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows[1]["ply"], rows[2]["ply"] = 2, 4
        rows += self.rows("B", "test", ["a", "b", "c"])
        self.assertEqual(find_cross_split_windows(rows, window=3), [])

    def test_only_consecutive_subwindow_is_eligible(self):
        rows = self.rows("A", "train", ["x", "a", "b", "c"])
        rows[1]["ply"], rows[2]["ply"], rows[3]["ply"] = 2, 3, 4
        rows += self.rows("B", "test", ["a", "b", "c"])
        matches = find_cross_split_windows(rows, window=3)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fen_window"], ["a", "b", "c"])

    def test_same_game_id_cannot_cross_splits(self):
        rows = self.rows("A", "train", ["a", "b", "c"])
        rows += self.rows("A", "test", ["d", "e", "f"])
        with self.assertRaises(ValueError):
            find_cross_split_windows(rows)

    def test_offset_windows_are_detected(self):
        rows = self.rows("A", "train", ["x", "a", "b", "c"])
        rows += self.rows("B", "test", ["a", "b", "c", "y"])
        matches = find_cross_split_windows(rows, window=3)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fen_window"], ["a", "b", "c"])

    def test_two_ply_window_is_supported(self):
        rows = self.rows("A", "train", ["a", "b"])
        rows += self.rows("B", "test", ["a", "b"])
        self.assertEqual(len(find_cross_split_windows(rows, window=2)), 1)
        self.assertEqual(find_cross_split_windows(rows, window=3), [])

if __name__ == "__main__":
    unittest.main()
