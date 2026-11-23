"""Synthetic regressions for combined D1-C chronological admission gate."""
import hashlib
import unittest

from research.mtdp.decision_equivalence.candidate_chronological_preflight import chronological_preflight
from research.mtdp.decision_equivalence.candidate_receipt_gate import canonical_bytes
from research.mtdp.decision_equivalence.candidate_ply_order import audit_ply_order


class ChronologicalPreflightTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"source_id": "s", "game_id": "g", "event_id": "e", "fen": "F1", "ply": 1},
            {"source_id": "s", "game_id": "g", "event_id": "e", "fen": "F2", "ply": 2},
        ]
        self.kw = dict(authenticated_sources={"s"},
                       authenticated_game_events={("s", "g"): "e"},
                       historical_fens={"H"}, reserved_fens={"R"},
                       excluded_games={"old"}, excluded_events={"protected"})

    def check(self, rows):
        digest = hashlib.sha256(canonical_bytes(rows)).hexdigest()
        return chronological_preflight(rows, expected_sha256=digest, **self.kw)

    def test_monotonic_internal_pass_is_not_authentication(self):
        result = self.check(self.rows)
        self.assertTrue(result["internal_preflight_pass"])
        self.assertFalse(result["external_authenticity_proven"])
        self.assertFalse(result["independent_cohort_admitted"])

    def test_reversed_ply_rejected_even_with_matching_digest(self):
        result = self.check(list(reversed(self.rows)))
        self.assertFalse(result["internal_preflight_pass"])
        self.assertFalse(result["chronology"]["chronological_metadata_pass"])

    def test_invalid_ply_rejected_even_with_matching_digest(self):
        rows = [dict(self.rows[0], ply=True), self.rows[1]]
        self.assertFalse(self.check(rows)["internal_preflight_pass"])

    def test_excluded_event_rejected_despite_valid_chronology(self):
        self.kw["excluded_events"] = {"e"}
        result = self.check(self.rows)
        self.assertTrue(result["chronology"]["chronological_metadata_pass"])
        self.assertFalse(result["internal_preflight_pass"])


    def test_interleaved_games_preserve_individual_ply_order(self):
        rows = [
            self.rows[0],
            {"source_id": "s", "game_id": "g2", "event_id": "e2", "fen": "F3", "ply": 0},
            self.rows[1],
            {"source_id": "s", "game_id": "g2", "event_id": "e2", "fen": "F4", "ply": 1},
        ]
        self.kw["authenticated_game_events"][("s", "g2")] = "e2"
        result = self.check(rows)
        self.assertTrue(result["internal_preflight_pass"])
        self.assertFalse(result["independent_cohort_admitted"])

    def test_invalid_ply_does_not_hide_event_identity_change(self):
        rows = [self.rows[0], dict(self.rows[1], event_id="other", ply=None)]
        # The baseline rejects ambiguous game/event identity by exception.
        # Check that contract and the chronology diagnostics independently.
        with self.assertRaisesRegex(ValueError, "game_id assigned to multiple events"):
            self.check(rows)
        chronology = audit_ply_order(rows)
        self.assertFalse(chronology["chronological_metadata_pass"])
        reasons = {problem["reason"] for problem in chronology["problems"]}
        self.assertIn("game_event_changed", reasons)
        self.assertIn("missing_or_invalid_ply", reasons)

    def test_cross_source_game_id_collision_is_rejected(self):
        rows = [self.rows[0], dict(self.rows[1], source_id="other", event_id="e2")]
        self.kw["authenticated_sources"].add("other")
        self.kw["authenticated_game_events"][("other", "g")] = "e2"
        with self.assertRaisesRegex(ValueError, "reused across sources"):
            self.check(rows)


if __name__ == "__main__":
    unittest.main()
