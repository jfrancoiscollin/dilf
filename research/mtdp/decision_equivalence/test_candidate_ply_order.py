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
