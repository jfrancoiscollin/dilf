"""Exhaustive independent oracle for D1 cross-split leakage counts.

Synthetic identifiers only: no FMJD positions or new cohort.
"""
import itertools
import unittest

from research.mtdp.decision_equivalence.manifest_leak_audit import audit

SPLITS = ("train", "validation", "test")
KEYS = ("fen", "game_id", "trajectory_id")


def reference(rows):
    result = {}
    for key in KEYS:
        values = {row[key] for row in rows}
        result[{"fen": "fen", "game_id": "game", "trajectory_id": "trajectory"}[key]] = sum(
            len({row["split"] for row in rows if row[key] == value}) > 1
            for value in values
        )
    return result


class ExhaustiveLeakOracleTests(unittest.TestCase):
    def test_all_three_row_split_and_identifier_assignments(self):
        # 3^3 split assignments times 2^(3*3) identifier assignments = 13,824 cases.
        for splits in itertools.product(SPLITS, repeat=3):
            for bits in itertools.product(("a", "b"), repeat=9):
                rows = [
                    {"split": splits[i],
                     "fen": bits[3*i],
                     "game_id": bits[3*i+1],
                     "trajectory_id": bits[3*i+2]}
                    for i in range(3)
                ]
                observed = audit(rows)
                self.assertEqual(observed["cross_split_duplicate_counts"], reference(rows))
                expected_stop = bool(any(reference(rows).values()) or set(splits) != set(SPLITS))
                self.assertEqual(observed["status"] == "STOP", expected_stop)


if __name__ == "__main__":
    unittest.main()
