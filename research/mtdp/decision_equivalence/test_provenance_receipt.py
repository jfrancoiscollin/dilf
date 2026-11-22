"""Synthetic-only tests of the D1-C receipt gate (no engine scores)."""
import copy
import unittest
from research.mtdp.decision_equivalence.provenance_receipt import check


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "source_sha256": "a" * 64,
            "manifest_sha256": "b" * 64,
            "exclusion_registry_sha256": "c" * 64,
            "parser_commit": "d" * 40,
            "exclusion_registry_sources": ["verified-artifact:example"],
            "reserved_event_coverage": {k: True for k in ("fFgE7oED", "P1RUlfJc", "s7ahYqL4", "D9PF2OSW")},
            "historical_cohort_coverage": {"authenticated": True, "registry_ref": "verified-artifact:example"},
            "game_counts_by_split": {"train": 10, "validation": 3, "test": 3},
            "quarantine_counts_by_reason": {},
            "cross_split_duplicate_counts": {"fen": 0, "game": 0},
            "audit_result": "PASS",
            "reviewer": "independent-reviewer",
            "decision": "PASS",
        }

    def test_complete_synthetic_receipt(self):
        self.assertEqual(check(self.valid), [])

    def test_historical_registry_must_be_authenticated(self):
        for value in (None, {}, {"authenticated": True}, {"authenticated": False, "registry_ref": "x"}):
            r = copy.deepcopy(self.valid)
            r["historical_cohort_coverage"] = value
            self.assertIn("historical_registry_not_authenticated", check(r))

    def test_all_reserved_events_required(self):
        for change in (lambda d: d.pop("fFgE7oED"), lambda d: d.update({"fFgE7oED": False}), lambda d: d.update({"unknown": True})):
            r = copy.deepcopy(self.valid)
            change(r["reserved_event_coverage"])
            self.assertIn("reserved_events_not_fully_covered", check(r))

    def test_leak_and_counts_rejected(self):
        for key, value, error in (
            ("cross_split_duplicate_counts", {"fen": 1}, "cross_split_duplicates_unresolved"),
            ("game_counts_by_split", {"train": 0, "validation": 2, "test": 1}, "invalid_split_counts"),
            ("quarantine_counts_by_reason", {"x": -1}, "invalid_quarantine_counts"),
        ):
            r = copy.deepcopy(self.valid)
            r[key] = value
            self.assertIn(error, check(r))

    def test_all_fields_required(self):
        for key in self.valid:
            r = copy.deepcopy(self.valid)
            del r[key]
            self.assertTrue(check(r), key)
        self.assertEqual(check(None), ["receipt_not_object"])


if __name__ == "__main__":
    unittest.main()
