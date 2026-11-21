"""Score-blind summary of an existing rclone lsjson --recursive --files-only inventory.

No network, credentials, object download, or R2 mutation. Never treats object
counts as independent positions or a valid cohort.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path


def summarize(objects: Iterable[dict]) -> dict:
    """Validate and summarize metadata only; input is never a position corpus."""
    paths: set[str] = set()
    prefix_counts: Counter[str] = Counter()
    suffix_counts: Counter[str] = Counter()
    total = 0
    for obj in objects:
        if not isinstance(obj, dict):
            raise ValueError("inventory entry must be an object")
        path, size = obj.get("Path"), obj.get("Size")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("invalid relative object path")
        if path in paths:
            raise ValueError("duplicate object path")
        if type(size) is not int or size < 0:
            raise ValueError("invalid object size")
        paths.add(path)
        total += size
        prefix_counts[path.split("/")[0]] += 1
        suffix_counts[Path(path).suffix.lower() or "(none)"] += 1
    return {
        "schema": "mtdp-d1-r2-object-inventory-v1",
        "objects": len(paths),
        "total_bytes": total,
        "top_level_prefix_counts": dict(sorted(prefix_counts.items())),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "position_count": None,
        "independent_game_count": None,
        "corpus_admissible": False,
        "score_blind": True,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory", type=Path, help="existing rclone lsjson inventory, no credentials")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raw = args.inventory.read_bytes()
    decoded = json.loads(raw)
    if not isinstance(decoded, list):
        raise ValueError("inventory must be a JSON array")
    report = summarize(decoded)
    report["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
