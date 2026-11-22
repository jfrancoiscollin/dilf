"""Fail-closed D1-C receipt validation; structural checks are not proof of historical independence."""
import argparse
import json
import re
from pathlib import Path

RESERVED = {"fFgE7oED", "P1RUlfJc", "s7ahYqL4", "D9PF2OSW"}
SPLITS = {"train", "validation", "test"}


def check(receipt):
    if not isinstance(receipt, dict):
        return ["receipt_not_object"]
    errors = []
    for key in ("source_sha256", "manifest_sha256", "exclusion_registry_sha256"):
        if not isinstance(receipt.get(key), str) or not re.fullmatch("[0-9a-f]{64}", receipt[key]):
            errors.append("invalid_" + key)
    if not isinstance(receipt.get("parser_commit"), str) or not re.fullmatch("[0-9a-f]{40}", receipt["parser_commit"]):
        errors.append("invalid_parser_commit")
    sources = receipt.get("exclusion_registry_sources")
    if not isinstance(sources, list) or not sources or any(not isinstance(s, str) or not s.strip() for s in sources):
        errors.append("missing_registry_sources")
    coverage = receipt.get("reserved_event_coverage")
    if not isinstance(coverage, dict) or set(coverage) != RESERVED or any(v is not True for v in coverage.values()):
        errors.append("reserved_events_not_fully_covered")
    history = receipt.get("historical_cohort_coverage")
    if not isinstance(history, dict) or history.get("authenticated") is not True or not isinstance(history.get("registry_ref"), str) or not history["registry_ref"].strip():
        errors.append("historical_registry_not_authenticated")
    splits = receipt.get("game_counts_by_split")
    if not isinstance(splits, dict) or set(splits) != SPLITS or any(type(v) is not int or v <= 0 for v in splits.values()):
        errors.append("invalid_split_counts")
    quarantine = receipt.get("quarantine_counts_by_reason")
    if not isinstance(quarantine, dict) or any(not isinstance(k, str) or not k or type(v) is not int or v < 0 for k, v in quarantine.items()):
        errors.append("invalid_quarantine_counts")
    duplicates = receipt.get("cross_split_duplicate_counts")
    if not isinstance(duplicates, dict) or not duplicates or any(type(v) is not int or v != 0 for v in duplicates.values()):
        errors.append("cross_split_duplicates_unresolved")
    if receipt.get("audit_result") != "PASS":
        errors.append("structural_audit_not_passed")
    if not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"].strip():
        errors.append("missing_reviewer")
    if receipt.get("decision") != "PASS":
        errors.append("decision_not_pass")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        errors = check(json.loads(args.receipt.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as exc:
        errors = ["unreadable_receipt:" + type(exc).__name__]
    print(json.dumps({"structural_receipt_pass": not errors, "errors": errors}, sort_keys=True))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
