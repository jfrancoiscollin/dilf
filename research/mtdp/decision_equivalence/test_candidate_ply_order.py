"""D1-C chronology guard regression tests, synthetic data only."""
import unittest
from research.mtdp.decision_equivalence.candidate_ply_order import audit_ply_order

class PlyOrderTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(source_id="s", game_id="g", event_id="e", ply=i) for i in (4, 6, 9)]
    def test_ordered_sparse_plies_pass_without_provenance_claim(self):
        result = audit_ply_order(self.rows)
        self.assertTrue(result["chronological_metadata_pass"])
        self.assertFalse(result["external_ply_provenance_authenticated"])
    def test_reordering_rejected_even_with_new_hash(self):
        self.assertFalse(audit_ply_order([self.rows[1], self.rows[0]])["chronological_metadata_pass"])
    def test_duplicate_ply_rejected(self):
        self.assertFalse(audit_ply_order([self.rows[0], self.rows[0]])["chronological_metadata_pass"])
    def test_missing_ply_rejected(self):
        self.assertFalse(audit_ply_order([dict(self.rows[0], ply=None)])["chronological_metadata_pass"])
    def test_bool_ply_rejected(self):
        self.assertFalse(audit_ply_order([dict(self.rows[0], ply=True)])["chronological_metadata_pass"])
    def test_interleaved_games_allowed(self):
        other = dict(self.rows[0], game_id="h", ply=2)
        self.assertTrue(audit_ply_order([self.rows[0], other, self.rows[1]])["chronological_metadata_pass"])
    def test_changed_event_rejected(self):
        self.assertFalse(audit_ply_order([self.rows[0], dict(self.rows[1], event_id="other")])["chronological_metadata_pass"])

    def test_event_change_not_hidden_by_invalid_ply(self):
        rows = [self.rows[0], dict(self.rows[1], event_id="other", ply=None)]
        reasons = [p["reason"] for p in audit_ply_order(rows)["problems"]]
        self.assertIn("game_event_changed", reasons)
        self.assertIn("missing_or_invalid_ply", reasons)

    def test_invalid_ply_still_registers_game_event(self):
        rows = [dict(self.rows[0], ply=None), dict(self.rows[1], event_id="other")]
        reasons = [p["reason"] for p in audit_ply_order(rows)["problems"]]
        self.assertIn("game_event_changed", reasons)
