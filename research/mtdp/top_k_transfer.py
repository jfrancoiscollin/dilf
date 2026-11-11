"""Evaluate top-k transferred move candidates from frozen Scan depth-12 reports.

Offline diagnostic only: not a Jass search-speed or playing-strength benchmark.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

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
        "ordinary_regret_centimen": best - available
        if _category(best) == _category(available) == "ordinary" else None,
        "best_category": _category(best),
        "candidate_category": _category(available),
    }


def analyze(report, k=3):
    if k < 1:
        raise ValueError("k must be positive")
    if report.get("schema") != "mtdp-best-move-v1" or report.get("scan_successor_depth") != 12:
        raise ValueError("Expected depth-12 best-move audit")
    scores = report["action_scores_centimen"]
    results = {}
    for cohort in COHORTS:
        buckets = {"all": [], "retained_radius_two": [], "removed_radius_two": []}
        for row in report[cohort]:
            if row["status"] != "scored":
                continue
            a, b = row["fen_a"], row["fen_b"]
            if a == b:
                raise ValueError("Distinct positions required")
            from pedagogy.game import parse_fen
            key_a, key_b = typed_radius_two(parse_fen(a)), typed_radius_two(parse_fen(b))
            if key_a is None or key_b is None or key_a[1] != key_b[1]:
                raise ValueError("Pair does not share baseline quiet signature")
            direction_results = [_direction(a, b, scores, k), _direction(b, a, scores, k)]
            buckets["all"].extend(direction_results)
            buckets["retained_radius_two" if key_a == key_b else "removed_radius_two"].extend(direction_results)
        results[cohort] = {}
        for name, directions in buckets.items():
            ordinary = [r["ordinary_regret_centimen"] for r in directions if r["ordinary_regret_centimen"] is not None]
            results[cohort][name] = {
                "directional_transfers": len(directions),
                "optimal_covered": sum(r["covered"] for r in directions),
                "ordinary_transfers": len(ordinary),
                "ordinary_regret_positive": sum(x > 0 for x in ordinary),
                "ordinary_regret_at_least_50": sum(x >= 50 for x in ordinary),
                "ordinary_regret_max": max(ordinary, default=None),
                "category_switches": dict(sorted(Counter(
                    f'{r["best_category"]}->{r["candidate_category"]}'
                    for r in directions if r["best_category"] != r["candidate_category"]
                ).items())),
            }
    return {"schema": "mtdp-top-k-transfer-v1", "k": k, "cohorts": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be positive")
    result = {path.name: analyze(json.loads(path.read_text()), args.k) for path in args.reports}
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
