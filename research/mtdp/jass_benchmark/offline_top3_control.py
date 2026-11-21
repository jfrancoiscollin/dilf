"""Compare two equal-size candidate lists on the frozen Scan references."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median, quantiles

from research.mtdp.jass_benchmark.depth_sensitivity import (
    DEPTHS, legal_actions, read_input, regret, validate_reference,
)
from research.mtdp.top_k_transfer import _action


def candidate_lists(moves, source_scores):
    by_key = {move["jass_key"]: _action(move) for move in moves}
    actions = set(by_key.values())
    if len(by_key) != len(moves) or len(actions) != len(moves):
        raise ValueError("Ambiguous canonical action or Jass key")
    if not actions or source_scores.keys() != actions:
        raise ValueError("Source scores differ from frozen legal actions")
    k = min(3, len(actions))
    canonical = sorted(by_key, key=lambda key: key.encode("utf-8"))
    ranked = sorted(canonical, key=lambda key: -source_scores[by_key[key]])
    ties = Counter(source_scores.values())
    return by_key, {
        "canonical": canonical[:k],
        "transfer": ranked[:k],
        "source_tied_scores": {score: count for score, count in ties.items() if count > 1},
        "source_tie_at_cutoff": k < len(ranked)
        and source_scores[by_key[ranked[k - 1]]] == source_scores[by_key[ranked[k]]],
    }


def evaluate_target(target, source_scores, target_scores):
    by_key, lists = candidate_lists(target["legal_moves"], source_scores)
    if target_scores.keys() != set(by_key.values()):
        raise ValueError("Target scores differ from frozen legal actions")
    best = max(target_scores.values())
    return {
        "source_fen": target["source_fen"],
        "target_fen": target["target_fen"],
        "target_game": min(target["target_games"]),
        "legal_count": len(by_key),
        "overlap": len(set(lists["canonical"]) & set(lists["transfer"])),
        **lists,
        "outcomes": {
            name: regret(best, max(target_scores[by_key[key]] for key in lists[name]))
            for name in ("transfer", "canonical")
        },
    }


def clustered_interval(observations):
    """Resample complete target-game clusters within each event."""
    clusters = defaultdict(lambda: defaultdict(list))
    for event, game, value in observations:
        clusters[event][game].append(value)
    strata = [[(sum(values), len(values)) for values in games.values()] for games in clusters.values()]
    count = sum(map(len, strata))
    if count < 2:
        return {"games": count, "ci95": None}
    rng = random.Random(20261112)
    estimates = []
    for _ in range(10_000):
        sampled = [cluster for stratum in strata for cluster in rng.choices(stratum, k=len(stratum))]
        estimates.append(sum(total for total, _ in sampled) / sum(size for _, size in sampled))
    cuts = quantiles(estimates, n=1000, method="inclusive")
    return {"games": count, "ci95": [cuts[24], cuts[974]]}


def summarize(events):
    rows = [(event, row) for event, targets in events.items() for row in targets]
    coverage_table = dict.fromkeys(("both", "transfer_only", "canonical_only", "neither"), 0)
    coverage, paired_regret = [], []
    arms = {"transfer": [], "canonical": []}
    for event, row in rows:
        transfer = row["outcomes"]["transfer"]
        canonical = row["outcomes"]["canonical"]
        a, b = transfer["covered"], canonical["covered"]
        cell = {(True, True): "both", (True, False): "transfer_only",
                (False, True): "canonical_only", (False, False): "neither"}[a, b]
        coverage_table[cell] += 1
        identity = (event, row["target_game"])
        coverage.append((*identity, int(a) - int(b)))
        for arm, result in row["outcomes"].items():
            arms[arm].append(result)
        a, b = transfer["ordinary_regret_centimen"], canonical["ordinary_regret_centimen"]
        if a is not None and b is not None:
            paired_regret.append((*identity, a - b))
    arm_summaries = {}
    for arm, results in arms.items():
        ordinary = [r["ordinary_regret_centimen"] for r in results
                    if r["ordinary_regret_centimen"] is not None]
        arm_summaries[arm] = {
            "covered": sum(r["covered"] for r in results),
            "ordinary": len(ordinary),
            "mean_regret_centimen": fmean(ordinary) if ordinary else None,
            "median_regret_centimen": median(ordinary) if ordinary else None,
            "max_regret_centimen": max(ordinary, default=None),
            "at_least_50_centimen": sum(value >= 50 for value in ordinary),
            "category_changes": dict(Counter(
                f"{r['best_category']}->{r['candidate_category']}" for r in results
                if r["best_category"] != r["candidate_category"]
            )),
        }
    deltas = [value for _, _, value in paired_regret]
    return {
        "targets": len(rows),
        "arms": arm_summaries,
        "coverage_table": coverage_table,
        "coverage_delta": fmean(value for _, _, value in coverage),
        "coverage_bootstrap": clustered_interval(coverage),
        "ordinary_pairs": len(deltas),
        "regret_delta_mean_centimen": fmean(deltas) if deltas else None,
        "regret_delta_median_centimen": median(deltas) if deltas else None,
        "regret_bootstrap": clustered_interval(paired_regret),
        "legal_counts": dict(Counter(row["legal_count"] for _, row in rows)),
        "overlap_counts": dict(Counter(row["overlap"] for _, row in rows)),
        "equal_candidate_sets": sum(set(row["transfer"]) == set(row["canonical"]) for _, row in rows),
        "source_ties_at_cutoff": sum(row["source_tie_at_cutoff"] for _, row in rows),
    }


def analyze(provenance):
    by_depth = {depth: {} for depth in DEPTHS}
    seen = set()
    for event, cohort in sorted(provenance["cohorts"].items()):
        inputs = cohort["inputs"]
        manifest = read_input(inputs["manifest"])
        targets = sorted(manifest["targets"], key=lambda row: row["target_fen"])
        fens = {row["target_fen"] for row in targets}
        if (manifest["schema"] != "mtdp-jass-cohort-v1"
                or len(targets) != len(fens) or len(fens) != cohort["targets"] or fens & seen):
            raise ValueError(f"Invalid or overlapping frozen target catalogue for {event}")
        seen.update(fens)
        expected = legal_actions(targets)
        for depth, record in zip(DEPTHS, (inputs["reference12"], cohort["reference16"]), strict=True):
            scores = validate_reference(read_input(record), expected, provenance["scan_sha256"],
                                        inputs["manifest"]["content_sha256"], depth)
            by_depth[depth][event] = [
                evaluate_target(row, scores[row["source_fen"]], scores[row["target_fen"]])
                for row in targets
            ]
    return {
        "schema": "mtdp-offline-top3-control-v1",
        "depths": {
            depth: {"overall": summarize(events), "cohorts": {
                event: {"summary": summarize({event: rows}), "targets": rows}
                for event, rows in events.items()
            }}
            for depth, events in by_depth.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = analyze(json.loads(args.provenance.read_text()))
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
