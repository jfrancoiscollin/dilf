"""D1-C composition: internal receipt and historical overlap are separate gates.

A PASS here means only that *supplied* inventories are consistent; it never
certifies external provenance or scientific independence. No target scores.
"""
from .candidate_receipt_gate import receipt_gate
from .corpus_admission_guard import audit_candidate


def preflight(records, *, expected_sha256, authenticated_sources,
              authenticated_game_events, historical_fens, reserved_fens,
              excluded_games, excluded_events):
    """Fail closed on absent exclusions, ambiguous game IDs and either gate."""
    inventories = (historical_fens, reserved_fens, excluded_games, excluded_events)
    if any(x is None for x in inventories):
        raise ValueError("all four exclusion inventories must be supplied")
    # The overlap guard uses bare game IDs. Never silently conflate two
    # unrelated games from distinct sources under that identifier.
    game_sources = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("invalid candidate row")
        game, source = row.get("game_id"), row.get("source_id")
        if game in game_sources and game_sources[game] != source:
            raise ValueError("game_id reused across sources; namespace before audit")
        game_sources[game] = source
    receipt = receipt_gate(
        records, expected_sha256=expected_sha256,
        authenticated_sources=authenticated_sources,
        authenticated_game_events=authenticated_game_events)
    overlap = audit_candidate(
        records, historical_fens=historical_fens,
        reserved_fens=reserved_fens, excluded_games=excluded_games,
        excluded_events=excluded_events)
    return {
        "internal_preflight_pass": receipt["integrity_pass"] and overlap["eligible"],
        "receipt": receipt, "overlap": overlap,
        "external_authenticity_proven": False,
        "independent_cohort_admitted": False,
    }


if __name__ == "__main__":
    import hashlib
    import unittest
    from .candidate_receipt_gate import canonical_bytes

    class PreflightTests(unittest.TestCase):
        def setUp(self):
            self.rows = [{"source_id": "s", "game_id": "g",
                          "event_id": "e", "fen": "F"}]
            self.kw = dict(
                expected_sha256=hashlib.sha256(canonical_bytes(self.rows)).hexdigest(),
                authenticated_sources={"s"},
                authenticated_game_events={("s", "g"): "e"},
                historical_fens={"H"}, reserved_fens={"R"},
                excluded_games={"old"}, excluded_events={"protected"})

        def test_clean_still_not_admitted(self):
            r = preflight(self.rows, **self.kw)
            self.assertTrue(r["internal_preflight_pass"])
            self.assertFalse(r["independent_cohort_admitted"])

        def test_historical_overlap_blocks(self):
            self.assertFalse(preflight(self.rows, **dict(self.kw, historical_fens={"F"}))
                             ["internal_preflight_pass"])

        def test_reserved_event_blocks(self):
            self.assertFalse(preflight(self.rows, **dict(self.kw, excluded_events={"e"}))
                             ["internal_preflight_pass"])

        def test_missing_inventory_rejected(self):
            with self.assertRaises(ValueError):
                preflight(self.rows, **dict(self.kw, reserved_fens=None))

        def test_cross_source_game_id_collision_rejected(self):
            rows = self.rows + [{"source_id": "t", "game_id": "g",
                                 "event_id": "e", "fen": "F2"}]
            with self.assertRaisesRegex(ValueError, "reused across sources"):
                preflight(rows, **self.kw)

        def test_wrong_digest_blocks(self):
            self.assertFalse(preflight(self.rows, **dict(self.kw, expected_sha256="0"*64))
                             ["internal_preflight_pass"])

    unittest.main()
