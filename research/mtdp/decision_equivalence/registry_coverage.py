"""D1 registry coverage preflight: refuse a partial exclusion inventory.

Usage: python -m research.mtdp.decision_equivalence.registry_coverage inventory.json
The inventory is authored and frozen *before* scoring. This verifies presence and
integrity, not the scientific completeness of the sources.
"""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_GROUPS = frozenset({
    "pcblues_historical", "scan_depth8", "scan_depth12",
    "jass_benchmarks", "ffgE7oED_reserved",
})


FORBIDDEN_SCORE_TOKENS = ("score", "eval", "regret", "best_move", "rank", "wdl")


def reject_score_fields(value, group):
    """Inspect nested provenance too: scores must not enter exclusion inputs."""
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in str(key).lower() for token in FORBIDDEN_SCORE_TOKENS):
                raise ValueError(f"score-derived field in exclusion registry: {group}")
            reject_score_fields(child, group)
    elif isinstance(value, list):
        for child in value:
            reject_score_fields(child, group)


def verify(manifest_path):
    path = Path(manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"registries"}:
        raise ValueError("inventory must contain exactly registries")
    entries = data["registries"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("empty registry inventory")
    groups, paths = set(), set()
    result = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"group", "path", "sha256", "rows"}:
            raise ValueError("registry requires group/path/sha256/rows")
        group, relative, digest, rows = (entry[k] for k in ("group", "path", "sha256", "rows"))
        if not isinstance(group, str) or not group or group in groups:
            raise ValueError("duplicate or invalid group")
        if not isinstance(relative, str) or not relative:
            raise ValueError("invalid path")
        target = (path.parent / relative).resolve()
        if not target.is_relative_to(path.parent.resolve()) or target in paths:
            raise ValueError("path escapes inventory directory or is duplicated")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid sha256")
        if type(rows) is not int or rows < 1:
            raise ValueError("invalid row count")
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"registry digest mismatch: {group}")
        records = payload.splitlines()
        if len(records) != rows or any(not line.strip() for line in records):
            raise ValueError(f"registry row count mismatch: {group}")
        seen_records = set()
        for line in records:
            record = json.loads(line)
            reject_score_fields(record, group)
            # Repeated exclusion rows inflate coverage counts without adding evidence.
            # Canonical JSON detects duplicates despite key order or whitespace.
            canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            if canonical in seen_records:
                raise ValueError(f"duplicate exclusion record: {group}")
            seen_records.add(canonical)
            if not isinstance(record, dict) or not any(isinstance(record.get(k), str) and record[k].strip() for k in ("game_id", "trajectory_sha256", "fen_sha256")):
                raise ValueError(f"invalid exclusion identity: {group}")
            for key in ("trajectory_sha256", "fen_sha256"):
                if key in record:
                    value = record[key]
                    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                        raise ValueError(f"invalid {key} digest: {group}")
        groups.add(group)
        paths.add(target)
        result.append({"group": group, "rows": rows, "sha256": digest})
    missing = REQUIRED_GROUPS - groups
    if missing:
        raise ValueError("missing mandatory exclusion groups: " + ", ".join(sorted(missing)))
    return {"status": "integrity_only_not_completeness_certification", "registries": sorted(result, key=lambda x: x["group"])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory")
    args = parser.parse_args()
    print(json.dumps(verify(args.inventory), sort_keys=True))


if __name__ == "__main__":
    main()
