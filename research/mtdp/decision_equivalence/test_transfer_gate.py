"""Synthetic-only tests for conservative D1 transfer eligibility."""
import unittest
from research.mtdp.decision_equivalence.transfer_gate import eligible_cross_game_pairs


def row(game, pos, fen, moves, sig="s"):
    return dict(game_id=game, position_id=pos, fen=fen, legal_moves=moves, signature=sig)


class TransferGateTests(unittest.TestCase):
    def test_rejections_and_eligible_pairs(self):
        rows = [row("A", 1, "fen1", ["1-6", "2-7"]),
                row("A", 2, "fen2", ["1-6", "2-7"]),
                row("B", 1, "fen1", ["2-7", "1-6"]),
                row("C", 1, "fen3", ["3-8"]),
                row("D", 1, "fen4", ["2-7", "1-6"])]
        out = eligible_cross_game_pairs(rows)
        self.assertEqual(out["eligible_count"], 4)
        self.assertEqual(out["rejected"], {"same_game": 1, "different_legal_actions": 4, "identical_fen": 1})
        self.assertFalse(out["best_move_equivalence_proven"])
        self.assertFalse(out["independent_cohort_proven"])

    def test_signature_and_action_order(self):
        self.assertEqual(eligible_cross_game_pairs([row("A",1,"x",["1-6"]),row("B",1,"y",["1-6"],"t")])["eligible_count"],0)
        self.assertEqual(eligible_cross_game_pairs([row("A",1,"x",["1-6","2-7"]),row("B",1,"y",["2-7","1-6"])])["eligible_count"],1)

    def test_fail_closed(self):
        for rows in ([row("A",1,"x",["1-6"]),row("A",1,"y",["1-6"])],
                     [row("A",True,"x",["1-6"])],
                     [row("A",1,"x",["1-6","1-6"])],
                     [row("A",1,"",["1-6"])]):
            with self.assertRaises(ValueError):
                eligible_cross_game_pairs(rows)


if __name__ == "__main__":
    unittest.main()
