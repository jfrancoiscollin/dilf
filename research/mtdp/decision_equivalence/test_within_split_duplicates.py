"""Synthetic diagnostics only; no independent FMJD cohort."""
import unittest
from hashlib import sha256
from research.mtdp.decision_equivalence.within_split_duplicates import audit_within_split_duplicates


def r(game, pos, split, fen):
    return dict(game_id=game, position_id=pos, split=split, fen=fen)


class WithinSplitDuplicateTests(unittest.TestCase):
    def test_cross_game_repeated_fen_in_same_split(self):
        result = audit_within_split_duplicates([
            r("A", 1, "train", "F"), r("B", 2, "train", "F"),
            r("C", 3, "test", "F")])
        self.assertEqual(result["duplicate_positions_beyond_first"], 1)
        self.assertEqual(result["cross_game_duplicate_clusters"], 1)
        self.assertEqual(result["duplicate_clusters"][0]["fen_sha256"],
                         sha256(b"F").hexdigest())
        self.assertEqual(result["duplicate_clusters"][0]["positions"],
                         [("A", "1"), ("B", "2")])
        self.assertFalse(result["independent_observations_proven"])

    def test_same_game_repeats_not_independent(self):
        result = audit_within_split_duplicates([
            r("A", 1, "train", "F"), r("A", 2, "train", "F")])
        self.assertEqual(result["duplicate_positions_beyond_first"], 1)
        self.assertEqual(result["cross_game_duplicate_clusters"], 0)

    def test_distinct_fens_and_splits(self):
        result = audit_within_split_duplicates([
            r("A", 1, "train", "F"), r("B", 1, "test", "F"),
            r("C", 1, "train", "G")])
        self.assertEqual(result["duplicate_clusters"], [])

    def test_reject_ambiguous_ids(self):
        with self.assertRaises(ValueError):
            audit_within_split_duplicates([
                r("A", 1, "train", "F"), r("A", "1", "train", "G")])
        for row in [r("A", True, "train", "F"), r("", 1, "train", "F"),
                    r("A", 1, "holdout", "F"), r("A", 1, "train", "")]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                audit_within_split_duplicates([row])


if __name__ == "__main__":
    unittest.main()
