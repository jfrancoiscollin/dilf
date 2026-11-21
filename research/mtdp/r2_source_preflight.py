"""Validate documented R2 source keys and optionally audit local JNNW copies.

No network, rclone, credentials or runner actions. This is a manifest preflight,
not an R2 existence check. The source manifest remains immutable evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.mtdp.jnnw_audit import inspect

EXPECTED_CELLS = tuple(f"c{i}" for i in range(5))
EXPECTED_GENERATIONS = ("g1", "g2")


def validate_manifest(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema") != "mtdp.r2_source_inventory.v1":
        raise ValueError("unsupported manifest schema")
    if raw.get("bucket") != "jass-data":
        raise ValueError("unexpected bucket")
    objects = raw.get("objects")
    if not isinstance(objects, list) or len(objects) != 10:
        raise ValueError("expected exactly ten objects")
    seen = set()
    for item in objects:
        cell, generation, key = item["cell"], item["generation"], item["key"]
        if cell not in EXPECTED_CELLS or generation not in EXPECTED_GENERATIONS:
            raise ValueError("unexpected cell/generation")
        if (cell, generation) in seen:
            raise ValueError("duplicate cell/generation")
        seen.add((cell, generation))
        if not isinstance(key, str) or not key.startswith("runs/") or (
            not key.endswith(f"/artefacts/{generation}-selfplay.jnnw.gz")
        ) or ".." in key.split("/") or key.startswith("/"):
            raise ValueError("invalid R2 source key")
        if item.get("verified_present") is not False or item.get("sha256") is not None:
            raise ValueError("documentary manifest must not claim cloud verification")
    if seen != {(c, g) for c in EXPECTED_CELLS for g in EXPECTED_GENERATIONS}:
        raise ValueError("missing source cell/generation")
    return {
        "schema": "mtdp.r2_preflight.v1",
        "bucket": raw["bucket"],
        "source_keys": [obj["key"] for obj in objects],
        "source_key_count": len(objects),
        "r2_access_performed": False,
        "r2_objects_verified": 0,
        "local_samples_audited": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--local-jnnw", type=Path, help="optional already-local decompressed JNNW")
    parser.add_argument("--max-records", type=int, default=1000)
    args = parser.parse_args()
    result = validate_manifest(args.manifest)
    if args.local_jnnw is not None:
        result["local_jnnw_audit"] = inspect(args.local_jnnw, max_records=args.max_records)
        result["local_samples_audited"] = result["local_jnnw_audit"]["records_inspected"]
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
