"""Compare two Scan audits on identical MTDP inputs, pairs and legal actions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

_COHORTS = ("holdout_pairs", "pcblues_transfer_pairs")
_PROVENANCE = (
    "schema", "scan_binary_sha256", "baseline_inputs", "holdout_inputs",
    "baseline_fens", "holdout_fens", "overlapping_fens", "novel_holdout_fens",
    "novel_quiet_fens",
)
_PAIR_FIELDS = ("fen_a", "fen_b", "games_a", "games_b", "status")


def _pairs(rows):
    pairs = {(row["fen_a"], row["fen_b"]): row for row in rows}
    if len(pairs) != len(rows):
        raise ValueError("Duplicate ordered pair")
    return pairs


def _actions(report):
    return {
        fen: {json.dumps(row["action"]) for row in rows}
        for fen, rows in report["action_scores_centimen"].items()
    }


def _cost(rows, direction):
    transfers = [row[direction] for row in rows]
    ordinary = [
        transfer["ordinary_regret_centimen"] for transfer in transfers
        if transfer["ordinary_regret_centimen"] is not None
    ]
    positive = [cost for cost in ordinary if cost > 0]
    switches = Counter(
        f'{t["best_category"]} -> {t["transferred_category"]}' for t in transfers
        if t["best_category"] != t["transferred_category"]
    )
    return {
        "ordinary": len(ordinary),
        "positive_ordinary": len(positive),
        "mean_ordinary_centimen": mean(ordinary) if ordinary else None,
        "median_positive_centimen": median(positive) if positive else None,
        "max_ordinary_centimen": max(ordinary, default=None),
        "at_least_50_centimen": sum(cost >= 50 for cost in ordinary),
        "category_switches": dict(sorted(switches.items())),
    }


def compare(shallow, deep):
    for field in _PROVENANCE:
        if shallow[field] != deep[field]:
            raise ValueError(f"Different audit provenance: {field}")
    depths = [shallow["scan_successor_depth"], deep["scan_successor_depth"]]
    if depths[0] >= depths[1]:
        raise ValueError("Expected increasing search depths")
    if _actions(shallow) != _actions(deep):
        raise ValueError("Different scored positions or legal actions")

    cohorts = {}
    for name in _COHORTS:
        a, b = _pairs(shallow[name]), _pairs(deep[name])
        if a.keys() != b.keys():
            raise ValueError(f"Different pairs in {name}")
        for key, row in a.items():
            if any(row[field] != b[key][field] for field in _PAIR_FIELDS):
                raise ValueError(f"Different pair eligibility or provenance in {name}: {key}")
        keys = sorted(key for key, row in a.items() if row["status"] == "scored")
        low = [a[key] for key in keys]
        high = [b[key] for key in keys]
        no_common_low = {key for key in keys if not a[key]["optimal_sets_overlap"]}
        no_common_high = {key for key in keys if not b[key]["optimal_sets_overlap"]}
        costs = {}
        for direction in ("a_to_b", "b_to_a"):
            high_cost = [
                key for key in keys
                if (a[key][direction]["ordinary_regret_centimen"] or 0) >= 50
            ]
            costs[direction] = {
                "shallow": _cost(low, direction),
                "deep": _cost(high, direction),
                "at_least_50_at_both_depths": sum(
                    (b[key][direction]["ordinary_regret_centimen"] or 0) >= 50
                    for key in high_cost
                ),
            }
        cohorts[name] = {
            "candidate_pairs": len(a),
            "scored_pairs": len(keys),
            "same_pick_shallow": sum(row["same_pick"] for row in low),
            "same_pick_deep": sum(row["same_pick"] for row in high),
            "disjoint_optima_shallow": len(no_common_low),
            "disjoint_optima_deep": len(no_common_high),
            "disjoint_at_both_depths": len(no_common_low & no_common_high),
            "costs": costs,
        }
    return {"scan_successor_depths": depths, "cohorts": cohorts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shallow", type=Path)
    parser.add_argument("deep", type=Path)
    args = parser.parse_args()
    summary = compare(json.loads(args.shallow.read_text()), json.loads(args.deep.read_text()))
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
