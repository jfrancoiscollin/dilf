"""Independent O(n²) oracle for the two D1 combinatorial audits.

Synthetic only. This deliberately slow implementation must not be used on a
real corpus; it verifies accounting, not FMJD legality or decision equivalence.
"""
import random
import unittest
from itertools import combinations

from research.mtdp.decision_equivalence.cross_game_collision_audit import cross_game_collision_audit
from research.mtdp.decision_equivalence.legal_action_collision_audit import audit_action_sets


def brute_force(rows):
    pairs = [(a, b) for a, b in combinations(rows, 2)
             if a["signature"] == b["signature"]]
    same = lambda a, b: set(a["legal_moves"]) == set(b["legal_moves"])
    within = [(a, b) for a, b in pairs if a["game_id"] == b["game_id"]]
    cross = [(a, b) for a, b in pairs if a["game_id"] != b["game_id"]]
    return {
        "total": len(pairs),
        "same": sum(same(a, b) for a, b in pairs),
        "within": len(within),
        "cross": len(cross),
        "cross_same": sum(same(a, b) for a, b in cross),
    }


class CombinatorialOracleTests(unittest.TestCase):
    def test_randomized_small_groups_against_pairwise_oracle(self):
        rng = random.Random(20261121)
        action_sets = [["1-6"], ["2-7"], ["1-6", "2-7"], ["3x12"]]
        for size in (0, 1, 2, 3, 8, 17, 40):
            for repetition in range(20):
                rows = [
                    dict(game_id="game-" + str(rng.randrange(4)),
                         position_id=i,
                         signature="sig-" + str(rng.randrange(5)),
                         legal_moves=list(rng.choice(action_sets)))
                    for i in range(size)
                ]
                rng.shuffle(rows)
                oracle = brute_force(rows)
                global_audit = audit_action_sets(rows)
                by_game = cross_game_collision_audit(rows)
                self.assertEqual(global_audit["collision_pairs"], oracle["total"])
                self.assertEqual(global_audit["same_legal_action_set_pairs"], oracle["same"])
                self.assertEqual(global_audit["different_legal_action_set_pairs"],
                                 oracle["total"] - oracle["same"])
                self.assertEqual(by_game["signature_collision_pairs"], oracle["total"])
                self.assertEqual(by_game["within_game_pairs"], oracle["within"])
                self.assertEqual(by_game["cross_game_pairs"], oracle["cross"])
                self.assertEqual(by_game["cross_game_same_legal_actions"], oracle["cross_same"])
                self.assertEqual(by_game["cross_game_different_legal_actions"],
                                 oracle["cross"] - oracle["cross_same"])
                self.assertEqual(oracle["within"] + oracle["cross"], oracle["total"])
                self.assertFalse(by_game["independent_cohort_proven"])
                self.assertFalse(by_game["best_move_equivalence_proven"])
                self.assertFalse(by_game["minimax_equivalence_proven"])

    def test_action_order_is_not_a_distinct_legal_set(self):
        rows = [
            dict(game_id="A", position_id=1, signature="s", legal_moves=["1-6", "2-7"]),
            dict(game_id="B", position_id=1, signature="s", legal_moves=["2-7", "1-6"]),
        ]
        self.assertEqual(audit_action_sets(rows)["same_legal_action_set_pairs"], 1)
        self.assertEqual(cross_game_collision_audit(rows)["cross_game_same_legal_actions"], 1)


if __name__ == "__main__":
    unittest.main()
