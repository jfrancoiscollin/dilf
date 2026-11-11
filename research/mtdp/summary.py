"""Descriptive audit of MTDP JSONL exports (no causal or strategic inference)."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


def summarize(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize provenance, duplicates and material strata without scoring positions."""
    rows = list(records)
    counts = Counter(row["source"] for row in rows)
    hashes = Counter(row["position_hash"] for row in rows)
    balances = Counter(str(row["metrics"]["material_balance"]) for row in rows)
    missing_king_verification = sum(
        row.get("metadata", {}).get("king_detection_verified") is not True
        for row in rows
    )
    occupancy = [float(row["metrics"]["occupied_fraction"]) for row in rows]
    return {
        "schema_version": "mtdp-audit-v1",
        "observations": len(rows),
        "distinct_positions": len(hashes),
        "duplicate_observations": sum(n - 1 for n in hashes.values()),
        "sources": dict(sorted(counts.items())),
        "material_balance_histogram": dict(sorted(balances.items(), key=lambda kv: int(kv[0]))),
        "king_detection_unverified_observations": missing_king_verification,
        "mean_occupied_fraction": mean(occupancy) if occupancy else None,
        "interpretation": "descriptive corpus audit only; no strategic inference",
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit an MTDP JSONL corpus")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = summarize(load_jsonl(args.input))
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is None:
        print(output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote audit to {args.output}")


if __name__ == "__main__":
    main()
