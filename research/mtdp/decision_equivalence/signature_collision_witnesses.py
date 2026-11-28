"""D1-B score-blind counterexample witnesses for signature collisions.

Each witness is an *identity pair*, not a minimax or best-move claim.
The input has the same strict schema as signature_collision_audit.audit.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .signature_collision_audit import audit, reject_duplicate_keys


def witnesses(records: list[dict], *, max_per_family: int = 20) -> dict:
    if type(max_per_family) is not int or max_per_family < 0:
        raise ValueError("max_per_family must be a nonnegative integer")
    audit(records)  # fail closed on score fields, duplicate IDs and mixed families
    names = sorted(records[0]["signatures"])
    output = {}
    for family in names:
        grouped = defaultdict(list)
        for row in records:
            grouped[row["signatures"][family]].append(row)
        found = []
        for signature in sorted(grouped):
            group = sorted(grouped[signature], key=lambda r: (r["game_id"], r["position_id"]))
            # Find a witness across *different games*, with divergent successors.
            for a in group:
                b = next((b for b in group if b["game_id"] != a["game_id"]
                          and b["successor_fingerprint"] != a["successor_fingerprint"]), None)
                if b is not None:
                    found.append({
                        "signature": signature,
                        "a": {"game_id": a["game_id"], "position_id": a["position_id"]},
                        "b": {"game_id": b["game_id"], "position_id": b["position_id"]},
                        "witness": "same_signature_different_successor_cross_game",
                    })
                    break
            if len(found) >= max_per_family:
                break
        output[family] = found[:max_per_family]
    return {"schema": "mtdp-d1-score-blind-witnesses-v1",
            "families": output,
            "interpretation": "counterexamples_to_successor_identity_only_not_minimax"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--max-per-family", type=int, default=20)
    args = parser.parse_args()
    with args.jsonl.open(encoding="utf-8") as handle:
        records = [json.loads(line, object_pairs_hook=reject_duplicate_keys,
                              parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                   for line in handle]
    print(json.dumps(witnesses(records, max_per_family=args.max_per_family),
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
