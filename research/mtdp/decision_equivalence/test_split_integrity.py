"""Synthetic D1 split-integrity regression tests; no FMJD claim."""
import unittest
from hashlib import sha256
from research.mtdp.decision_equivalence.split_integrity import audit_split_integrity


def row(game, pos, split, fen):
    return dict(game_id=game, position_id=pos, split=split, fen=fen)


class SplitIntegrityTests(unittest.TestCase):
    def test_clean_partition(self):
        out = audit_split_integrity([row("A", 1, "train", "F1"),
                                     row("B", 1, "test", "F2")])
        self.assertTrue(out["admissible"])
        self.assertEqual(out["counts"], {"test": 1, "train": 1})
        self.assertFalse(out["statistical_independence_proven"])

    def test_game_leak_even_when_fens_differ(self):
        out = audit_split_integrity([row("A", 1, "train", "F1"),
                                     row("A", 2, "test", "F2")])
        self.assertFalse(out["admissible"])
        self.assertEqual(out["cross_split_games"], ["A"])

    def test_fen_leak_even_when_games_differ(self):
        out = audit_split_integrity([row("A", 1, "train", "F"),
                                     row("B", 1, "test", "F")])
        self.assertFalse(out["admissible"])
        self.assertEqual(out["cross_split_fen_sha256"],
                         [sha256(b"F").hexdigest()])

    def test_reserved_digest(self):
        digest = sha256(b"F").hexdigest()
        out = audit_split_integrity([row("A", 1, "train", "F")], [digest])
        self.assertFalse(out["admissible"])
        self.assertEqual(out["reserved_hits"], [("A", "1")])

    def test_fail_closed(self):
        bad = [
            [row("A", 1, "train", "F"), row("A", "1", "train", "G")],
            [row("A", True, "train", "F")],
            [row("A", 1, "holdout", "F")],
            [row("A", 1, "train", "")],
        ]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                audit_split_integrity(rows)
        with self.assertRaises(ValueError):
            audit_split_integrity([], ["not-a-digest"])


if __name__ == "__main__":
    unittest.main()
