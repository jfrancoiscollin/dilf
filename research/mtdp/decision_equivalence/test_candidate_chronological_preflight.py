"""Synthetic regressions for combined D1-C chronological admission gate."""
import hashlib
import unittest

from research.mtdp.decision_equivalence.candidate_chronological_preflight import chronological_preflight
from research.mtdp.decision_equivalence.candidate_receipt_gate import canonical_bytes


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


if __name__ == "__main__":
    unittest.main()
