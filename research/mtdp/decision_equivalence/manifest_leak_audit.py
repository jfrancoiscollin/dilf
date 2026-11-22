"""Score-blind cross-split leakage audit for a preregistered D1 manifest.

Input: JSONL objects with split, game_id, fen, trajectory_id.
Exact-string comparisons only; no FMJD FEN canonicalization or provenance authentication.
"""
import argparse
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

SPLITS = {"train", "validation", "test"}
KEYS = ("fen", "game_id", "trajectory_id")


def audit(rows):
    seen = {key: defaultdict(set) for key in KEYS}
    errors = []
    counts = {split: 0 for split in sorted(SPLITS)}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"row_{index}:not_object")
            continue
        split = row.get("split")
        if not isinstance(split, str) or split not in SPLITS:
            errors.append(f"row_{index}:invalid_split")
            continue
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in KEYS):
            errors.append(f"row_{index}:missing_identifier")
            continue
        if any(row[key] != row[key].strip() for key in KEYS):
            errors.append(f"row_{index}:noncanonical_identifier_whitespace")
            continue
        if any(any(unicodedata.category(ch).startswith("C") for ch in row[key]) for key in KEYS):
            errors.append(f"row_{index}:unicode_control_identifier")
            continue
        counts[split] += 1
        for key in KEYS:
            seen[key][row[key]].add(split)
    collisions = {
        key: sum(len(splits) > 1 for splits in seen[key].values())
        for key in KEYS
    }
    return {
        "status": "STOP" if errors or any(collisions.values()) or not all(counts.values()) else "PASS_STRUCTURAL_ONLY",
        "row_counts": counts,
        "cross_split_duplicate_counts": {
            "fen": collisions["fen"],
            "game": collisions["game_id"],
            "trajectory": collisions["trajectory_id"],
        },
        "errors": errors,
        "limitations": "Exact identifiers only; surrounding whitespace and Unicode controls rejected, but source authenticity, other aliases, chronological order and FMJD FEN normalization unverified.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        with args.manifest.open(encoding="utf-8") as stream:
            result = audit(json.loads(line) for line in stream if line.strip())
    except (OSError, UnicodeError, ValueError) as exc:
        result = {"status": "STOP", "errors": [f"unreadable_manifest:{type(exc).__name__}"]}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_STRUCTURAL_ONLY" else 1)


if __name__ == "__main__":
    main()
