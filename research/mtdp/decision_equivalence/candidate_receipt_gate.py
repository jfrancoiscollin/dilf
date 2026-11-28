"""D1-C: fail-closed receipt gate for score-blind candidate provenance.

This validates internal integrity only; a matching digest cannot establish that
an external game/event identity is genuine or that all historical data is known.
"""
import hashlib
import json


def canonical_bytes(records):
    """Stable, ordered JSONL bytes; chronology is part of the commitment."""
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty ordered list required")
    for row in records:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) or not row[k].strip()
            for k in ("game_id", "event_id", "fen", "source_id")
        ):
            raise ValueError("missing candidate identity or source")
        if "score" in row or "scan_score" in row or "best_move" in row:
            raise ValueError("target-derived labels forbidden before freeze")
    return b"".join(
        (json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        for r in records
    )


def receipt_gate(records, *, expected_sha256, authenticated_sources,
                 authenticated_game_events):
    """Verify a frozen ordered candidate against separately authenticated IDs.

    authenticated_game_events maps (source_id, game_id) to event_id. Caller must
    obtain this map independently from source receipts, not candidate rows.
    """
    payload = canonical_bytes(records)
    digest = hashlib.sha256(payload).hexdigest()
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ValueError("expected SHA-256 required")
    if not isinstance(authenticated_sources, (set, frozenset)) or not authenticated_sources:
        raise ValueError("authenticated source inventory required")
    if not isinstance(authenticated_game_events, dict) or not authenticated_game_events:
        raise ValueError("authenticated game/event inventory required")
    problems = []
    seen = set()
    for index, row in enumerate(records):
        key = (row["source_id"], row["game_id"])
        if key not in authenticated_game_events or authenticated_game_events[key] != row["event_id"]:
            problems.append({"index": index, "reason": "unverified_game_event"})
        if row["source_id"] not in authenticated_sources:
            problems.append({"index": index, "reason": "unverified_source"})
        if (key, row["fen"]) in seen:
            problems.append({"index": index, "reason": "duplicate_game_fen"})
        seen.add((key, row["fen"]))
    return {
        "integrity_pass": digest == expected_sha256 and not problems,
        "sha256": digest,
        "expected_sha256_match": digest == expected_sha256,
        "problems": problems,
        "external_authenticity_proven": False,
        "independent_cohort_admitted": False,
    }


if __name__ == "__main__":
    import unittest

    class ReceiptGateTests(unittest.TestCase):
        def setUp(self):
            self.rows = [{"source_id": "s", "game_id": "g", "event_id": "e", "fen": "F"}]
            self.sha = hashlib.sha256(canonical_bytes(self.rows)).hexdigest()
            self.kw = dict(expected_sha256=self.sha, authenticated_sources={"s"},
                           authenticated_game_events={("s", "g"): "e"})

        def test_matching_receipt_is_not_independence(self):
            r = receipt_gate(self.rows, **self.kw)
            self.assertTrue(r["integrity_pass"])
            self.assertFalse(r["independent_cohort_admitted"])

        def test_changed_order_or_fen_breaks_digest(self):
            rows = self.rows + [dict(self.rows[0], fen="F2")]
            self.assertFalse(receipt_gate(rows, **self.kw)["integrity_pass"])
            self.assertFalse(receipt_gate([dict(self.rows[0], fen="X")], **self.kw)["integrity_pass"])

        def test_chronological_reordering_breaks_frozen_receipt(self):
            rows = self.rows + [dict(self.rows[0], fen="F2")]
            digest = hashlib.sha256(canonical_bytes(rows)).hexdigest()
            original = receipt_gate(rows, **dict(self.kw, expected_sha256=digest))
            reordered = receipt_gate(list(reversed(rows)),
                                     **dict(self.kw, expected_sha256=digest))
            self.assertTrue(original["integrity_pass"])
            self.assertFalse(reordered["integrity_pass"])
            self.assertFalse(reordered["expected_sha256_match"])

        def test_unknown_identity_rejected(self):
            r = receipt_gate([dict(self.rows[0], event_id="other")],
                             **dict(self.kw, expected_sha256=hashlib.sha256(
                                 canonical_bytes([dict(self.rows[0], event_id="other")])).hexdigest()))
            self.assertFalse(r["integrity_pass"])

        def test_no_score_leak(self):
            with self.assertRaises(ValueError):
                canonical_bytes([dict(self.rows[0], scan_score=0)])

        def test_empty_inventory_fails_closed(self):
            with self.assertRaises(ValueError):
                receipt_gate(self.rows, **dict(self.kw, authenticated_sources=set()))

    unittest.main()
