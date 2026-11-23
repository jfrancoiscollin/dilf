"""Synthetic D1-D checks; not an independent FMJD cohort."""
import unittest

from research.mtdp.decision_equivalence.rank_audit import audit_ranking


class TestRankAudit(unittest.TestCase):
    def test_top_three_recovers_missed_top_one(self):
        x = audit_ranking(["a", "b", "c", "d"], ["b", "c", "a", "d"],
                          {"a": 10, "b": 7, "c": 8, "d": 0})
        self.assertFalse(x.top1_exact)
        self.assertTrue(x.top3_exact)
        self.assertEqual((x.regret_top1, x.regret_top3), (3, 0))

    def test_tied_optima(self):
        x = audit_ranking(["a", "b"], ["b", "a"], {"a": 1, "b": 1})
        self.assertTrue(x.top1_exact)
        self.assertEqual(x.regret_top3, 0)

    def test_single_legal_action(self):
        self.assertTrue(audit_ranking(["a"], ["a"], {"a": -3}).top3_exact)

    def test_rejects_ambiguous_or_partial_mapping(self):
        for legal, order, scores in [
            (["a", "a"], ["a", "a"], {"a": 1}),
            (["a", "b"], ["a"], {"a": 1, "b": 0}),
            (["a", "b"], ["a", "a"], {"a": 1, "b": 0}),
            (["a", "b"], ["a", "b"], {"a": 1}),
            (["a"], ["a"], {"a": float("nan")}),
        ]:
            with self.subTest(legal=legal, order=order, scores=scores):
                with self.assertRaises(ValueError):
                    audit_ranking(legal, order, scores)


if __name__ == "__main__":
    unittest.main()
