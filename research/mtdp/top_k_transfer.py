"""Evaluate top-k transferred move candidates from frozen Scan depth-12 reports.

Offline diagnostic only: not a Jass search-speed or playing-strength benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.local_neighborhood import typed_radius_two

COHORTS = ("holdout_pairs", "pcblues_transfer_pairs")


def _action(row):
    return (tuple(row["action"][0]), tuple(row["action"][1]), bool(row["action"][2]))


def _ranked(rows):
    return sorted(((_action(row), row["score"]) for row in rows), key=lambda x: (-x[1], x[0]))


def _category(score):
    return "win" if score > 8000 else "loss" if score < -8000 else "ordinary"


def _direction(source, destination, scores, k):
    src, dst = _ranked(scores[source]), dict(_ranked(scores[destination]))
    if not src or set(a for a, _ in src) != set(dst):
        raise ValueError("Missing or inconsistent legal action scores")
    candidates = [action for action, _ in src[:k]]
    best = max(dst.values())
    available = max(dst[action] for action in candidates)
    best_actions = {action for action, score in dst.items() if score == best}
    return {
        "covered": bool(best_actions.intersection(candidates)),
        "candidate_count": len(candidates),
        "full_legal_set": len(candidates) == len(dst),
        "ordinary_regret_centimen": best - available
        if _category(best) == _category(available) == "ordinary" else None,
        "best_category": _category(best),
        "candidate_category": _category(available),
    }


def _summarize(directions):
    ordinary = [
        row["ordinary_regret_centimen"] for row in directions
        if row["ordinary_regret_centimen"] is not None
    ]
    switches = Counter(
        f'{row["best_category"]}->{row["candidate_category"]}'
        for row in directions if row["best_category"] != row["candidate_category"]
    )
    return {
        "directional_transfers": len(directions),
        "full_legal_set_transfers": sum(row["full_legal_set"] for row in directions),
        "optimal_covered": sum(row["covered"] for row in directions),
        "ordinary_transfers": len(ordinary),
        "ordinary_regret_positive": sum(value > 0 for value in ordinary),
        "ordinary_regret_at_least_50": sum(value >= 50 for value in ordinary),
        "ordinary_regret_max": max(ordinary, default=None),
        "category_switches": dict(sorted(switches.items())),
    }


def analyze(report, k=3):
    if k < 1:
        raise ValueError("k must be positive")
    if report.get("schema") != "mtdp-best-move-v1" or report.get("scan_successor_depth") != 12:
        raise ValueError("Expected depth-12 best-move audit")
    scores = report["action_scores_centimen"]
    results, by_direction = {}, {}
    for cohort in COHORTS:
        buckets = {
            name: {"a_to_b": [], "b_to_a": []}
            for name in ("all", "retained_radius_two", "removed_radius_two")
        }
        for row in report[cohort]:
            if row["status"] != "scored":
                continue
            a, b = row["fen_a"], row["fen_b"]
            if a == b:
                raise ValueError("Distinct positions required")
            key_a, key_b = typed_radius_two(parse_fen(a)), typed_radius_two(parse_fen(b))
            if key_a is None or key_b is None or key_a[1] != key_b[1]:
                raise ValueError("Pair does not share baseline quiet signature")
            refinement_bucket = "retained_radius_two" if key_a == key_b else "removed_radius_two"
            for direction, source, destination in (("a_to_b", a, b), ("b_to_a", b, a)):
                result = _direction(source, destination, scores, k)
                buckets["all"][direction].append(result)
                buckets[refinement_bucket][direction].append(result)
        results[cohort] = {
            name: _summarize(rows["a_to_b"] + rows["b_to_a"]) for name, rows in buckets.items()
        }
        by_direction[cohort] = {
            name: {direction: _summarize(values) for direction, values in rows.items()}
            for name, rows in buckets.items()
        }
    return {
        "schema": "mtdp-top-k-transfer-v1",
        "k": k,
        "cohorts": results,
        "by_direction": by_direction,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be positive")
    result = {}
    for path in args.reports:
        if path.name in result:
            parser.error(f"duplicate report filename: {path.name}")
        payload = path.read_bytes()
        result[path.name] = analyze(json.loads(payload), args.k)
        result[path.name]["input_sha256"] = hashlib.sha256(payload).hexdigest()
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
