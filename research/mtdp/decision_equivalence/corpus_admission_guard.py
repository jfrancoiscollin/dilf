"""D1-C score-blind admission guard. This is not proof of source authenticity.

All inputs must be independently authenticated before calling this function.
It checks canonical FEN overlap and whole-game/event quarantine, not minimax
equivalence or action rankings. Never pass Scan scores to this module.
"""
from collections import Counter


def audit_candidate(candidate, *, historical_fens, reserved_fens, excluded_games,
                    excluded_events):
    """Return an admission report; reject malformed records and any leakage.

    candidate: iterable of mappings with game_id, event_id, fen.
    The caller must first authenticate game/event IDs, FEN normalization,
    source receipts, historical inventories and reserved-target inventory.
    """
    historical_fens = set(historical_fens)
    reserved_fens = set(reserved_fens)
    excluded_games = set(excluded_games)
    excluded_events = set(excluded_events)
    records = list(candidate)
    for item in records:
        if not isinstance(item, dict) or any(
            not isinstance(item.get(k), str) or not item[k].strip()
            for k in ("game_id", "event_id", "fen")
        ):
            raise ValueError("candidate requires nonempty game_id, event_id, fen")
    games = {}
    for item in records:
        game, event = item["game_id"], item["event_id"]
        if game in games and games[game] != event:
            raise ValueError("game_id assigned to multiple events")
        games[game] = event
    fens = [r["fen"] for r in records]
    counts = Counter(fens)
    failures = {
        "historical_overlap": sorted(set(fens) & historical_fens),
        "reserved_overlap": sorted(set(fens) & reserved_fens),
        "excluded_games": sorted(set(games) & excluded_games),
        "excluded_events": sorted(set(games.values()) & excluded_events),
        "duplicate_candidate_fens": sorted(f for f, n in counts.items() if n > 1),
    }
    return {
        "eligible": bool(records) and not any(failures.values()),
        "positions": len(records), "games": len(games),
        "failures": failures,
        "provenance_authenticated": False,
        "note": "A clean set-overlap audit alone cannot certify independent provenance.",
    }


if __name__ == "__main__":
    import unittest

    class AdmissionTests(unittest.TestCase):
        def setUp(self):
            self.rows = [
                {"game_id": "g1", "event_id": "e1", "fen": "F1"},
                {"game_id": "g2", "event_id": "e2", "fen": "F2"},
            ]
            self.kw = dict(historical_fens={"H"}, reserved_fens={"R"},
                           excluded_games={"old"}, excluded_events={"protected"})

        def test_clean_is_not_provenance_proof(self):
            r = audit_candidate(self.rows, **self.kw)
            self.assertTrue(r["eligible"])
            self.assertFalse(r["provenance_authenticated"])

        def test_every_exclusion(self):
            rows = [
                {"game_id": "old", "event_id": "e1", "fen": "H"},
                {"game_id": "g2", "event_id": "protected", "fen": "R"},
                {"game_id": "g3", "event_id": "e3", "fen": "R"},
            ]
            r = audit_candidate(rows, **self.kw)
            self.assertFalse(r["eligible"])
            self.assertTrue(all(r["failures"].values()))

        def test_duplicate_across_games(self):
            rows = [dict(x, fen="F1") for x in self.rows]
            self.assertFalse(audit_candidate(rows, **self.kw)["eligible"])

        def test_game_event_conflict(self):
            rows = self.rows + [{"game_id": "g1", "event_id": "other", "fen": "F3"}]
            with self.assertRaises(ValueError):
                audit_candidate(rows, **self.kw)

        def test_malformed_and_empty(self):
            self.assertFalse(audit_candidate([], **self.kw)["eligible"])
            with self.assertRaises(ValueError):
                audit_candidate([{"game_id": "g", "event_id": "e"}], **self.kw)

    unittest.main()
