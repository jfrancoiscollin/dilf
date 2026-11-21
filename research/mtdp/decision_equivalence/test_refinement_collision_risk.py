"""Discoverable score-blind regression tests for progressive D1 collision accounting."""
import random
import unittest
from itertools import combinations

from research.mtdp.decision_equivalence.refinement_collision_risk import refinement_collision_risk


def row(game, position, coarse, fine, successor):
    return {
        "game_id": game, "position_id": position,
        "signatures": {"L": coarse, "LCB": fine},
        "successor_fingerprint": successor,
    }


def exhaustive(rows, family):
    pairs = [
        (a, b) for a, b in combinations(rows, 2)
        if a["signatures"][family] == b["signatures"][family]
    ]
    return (
        len(pairs),
        sum(a["successor_fingerprint"] != b["successor_fingerprint"] for a, b in pairs),
        sum(a["game_id"] != b["game_id"] for a, b in pairs),
        sum(a["game_id"] != b["game_id"] and
            a["successor_fingerprint"] != b["successor_fingerprint"] for a, b in pairs),
    )


class RefinementCollisionRiskTests(unittest.TestCase):
    def test_known_collision_counts(self):
        rows = [
            row("g1", "a", "x", "a", "s1"),
            row("g2", "b", "x", "a", "s2"),
            row("g1", "c", "x", "b", "s1"),
            row("g3", "d", "y", "c", "s3"),
        ]
        levels = refinement_collision_risk(rows, ["L", "LCB"])["levels"]
        self.assertEqual(
            [(x["collision_pairs"], x["divergent_successor_pairs"], x["cross_game_pairs"], x["cross_game_divergent_successor_pairs"]) for x in levels],
            [(3, 2, 2, 2), (1, 1, 1, 1)],
        )

    def test_randomized_against_exhaustive_reference(self):
        rng = random.Random(20261118)
        for trial in range(30):
            rows = []
            for i in range(25):
                coarse = str(rng.randrange(4))
                fine = coarse + ":" + str(rng.randrange(3))
                rows.append(row(str(rng.randrange(5)), f"{trial}:{i}", coarse, fine,
                                str(rng.randrange(6))))
            levels = refinement_collision_risk(rows, ["L", "LCB"])["levels"]
            for family, level in zip(("L", "LCB"), levels):
                self.assertEqual(
                    (level["collision_pairs"], level["divergent_successor_pairs"],
                     level["cross_game_pairs"], level["cross_game_divergent_successor_pairs"]),
                    exhaustive(rows, family),
                )

    def test_large_implicit_collision_group(self):
        rows = [row(f"g{i % 2}", str(i), "x", "x:0", f"s{i % 3}")
                for i in range(10000)]
        levels = refinement_collision_risk(rows, ["L", "LCB"])["levels"]
        self.assertEqual(levels[0]["collision_pairs"], 49995000)
        self.assertEqual(levels[1]["collision_pairs"], 49995000)
        self.assertEqual(levels[0]["cross_game_pairs"], 25000000)
        self.assertGreater(levels[0]["divergent_successor_pairs"], 0)

    def test_non_nested_refinement_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a refinement"):
            refinement_collision_risk([
                row("g1", "a", "x", "same", "s1"),
                row("g2", "b", "y", "same", "s2"),
            ], ["L", "LCB"])

    def test_duplicate_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            refinement_collision_risk([
                row("g", "p", "x", "a", "s1"),
                row("g", "p", "x", "a", "s1"),
            ], ["L", "LCB"])

    def test_target_score_rejected(self):
        r = row("g", "p", "x", "a", "s1")
        r["scan_score"] = 100
        with self.assertRaisesRegex(ValueError, "score-blind"):
            refinement_collision_risk([r], ["L", "LCB"])


if __name__ == "__main__":
    unittest.main()
