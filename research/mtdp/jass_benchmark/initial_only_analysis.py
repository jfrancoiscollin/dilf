"""Summarize the preregistered initial-only comparison and Scan transfers."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, quantiles

from research.mtdp.top_k_transfer import _direction, _summarize


def game_means(observations):
    games = defaultdict(list)
    for game, _, delta in observations:
        games[game].append(delta)
    return {game: mean(values) for game, values in sorted(games.items())}


def primary_comparison(paired):
    observations = []
    missing = 0
    for row in paired:
        if row["budget"] != 200_000:
            continue
        transfer = row["arms"]["transfer"]["ordinary_regret_centimen"]
        canonical = row["arms"]["canonical"]["ordinary_regret_centimen"]
        if transfer is None or canonical is None:
            missing += 1
            continue
        observations.append((min(row["target_games"]), row["source_game"], transfer - canonical))
    deltas = [delta for _, _, delta in observations]
    by_game = game_means(observations)
    clusters = list(by_game.values())
    rng = random.Random(20261112)
    interval = None
    if len(clusters) > 1:
        sample_means = [mean(rng.choices(clusters, k=len(clusters))) for _ in range(10_000)]
        percentiles = quantiles(sample_means, n=1000, method="inclusive")
        interval = [percentiles[24], percentiles[974]]
    leave_source_out = {}
    for source in sorted({source for _, source, _ in observations}):
        remaining = game_means(row for row in observations if row[1] != source)
        leave_source_out[source] = mean(remaining.values()) if remaining else None
    return {
        "ordinary_positions": len(deltas),
        "missing_ordinary_positions": missing,
        "mean_delta_centimen": mean(deltas) if deltas else None,
        "median_delta_centimen": median(deltas) if deltas else None,
        "target_game_means_centimen": by_game,
        "mean_target_game_delta_centimen": mean(clusters) if clusters else None,
        "median_target_game_delta_centimen": median(clusters) if clusters else None,
        "target_game_bootstrap_95_ci_centimen": interval,
        "leave_selected_source_game_out_mean_centimen": leave_source_out,
    }


def scan_transfer(reference):
    transfers = reference["transfers"]
    scores = reference["action_scores_centimen"]
    result = {
        "pairs": len(transfers),
        "disjoint_optima": sum(not row["optimal_sets_overlap"] for row in transfers),
    }
    for k in (1, 3):
        rows = [_direction(row["source_fen"], row["target_fen"], scores, k) for row in transfers]
        ordinary = [row["ordinary_regret_centimen"] for row in rows
                    if row["ordinary_regret_centimen"] is not None]
        result[f"top_{k}"] = {
            **_summarize(rows),
            "ordinary_regret_mean_centimen": mean(ordinary) if ordinary else None,
            "ordinary_regret_median_centimen": median(ordinary) if ordinary else None,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("paired-results", "scan-reference", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    paired = [json.loads(line) for line in args.paired_results.read_text().splitlines()]
    reference = json.loads(args.scan_reference.read_text())
    report = {"primary": primary_comparison(paired), "scan_transfer": scan_transfer(reference)}
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
