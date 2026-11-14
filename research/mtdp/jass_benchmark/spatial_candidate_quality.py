"""Evaluate the five-arena initial candidate lists using archived Scan scores."""

import argparse
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.depth_sensitivity import distribution, regret
from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.multi_event_replication import contrast
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_jass import ARMS
from research.mtdp.jass_benchmark.spatial_replication import (
    read_freeze, read_scan_scores, validate_cohort,
)

METRICS = ("top1", "top3")


def evaluate(target, scores):
    fen = target["target_fen"]
    target_scores = scores["target"][fen]
    best = max(target_scores.values())
    sources = target["source_fens"]
    row = {"fen": fen, "owner": min(target["target_games"]), "selected_sources": sources}
    for arm in ARMS:
        by_key, lists = candidate_lists(target["legal_moves"], scores["source"][sources[arm]])
        prefix = lists["transfer"]
        first = target_scores[by_key[prefix[0]]]
        row[arm] = {
            "prefix": prefix,
            "top1": regret(best, first),
            "top3": regret(best, max(target_scores[by_key[move]] for move in prefix)),
        }
    return row


def optimum_pairs(rows, metric):
    labels = {(True, True): "both", (True, False): "lcb_only",
              (False, True): "l_only", (False, False): "neither"}
    counts = Counter(dict.fromkeys(labels.values(), 0))
    counts.update(labels[row["LCB"][metric]["covered"], row["L"][metric]["covered"]]
                  for row in rows)
    return dict(counts)


def summarize(events):
    rows = [row for event_rows in events.values() for row in event_rows]
    return {
        metric: {
            "paired": contrast(events, "LCB", "L", False, metric=metric),
            "optimum_pairs": optimum_pairs(rows, metric),
            "arms": {arm: {
                "covered": sum(row[arm][metric]["covered"] for row in rows),
                "ordinary_regret_centimen": distribution([
                    row[arm][metric]["ordinary_regret_centimen"] for row in rows
                    if row[arm][metric]["ordinary_regret_centimen"] is not None
                ]),
            } for arm in ARMS},
        } for metric in METRICS
    }


def analyze(arenas):
    freezes = [read_freeze(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _ in freezes],
                    sha256(REPLICATION_PROTOCOL))
    events, changed_events, inputs = {}, {}, {}
    for arena, (provenance, _, manifest) in zip(arenas, freezes, strict=True):
        event = provenance["event"]["id"]
        events[event], changed_events[event] = [], []
        inputs[event] = {"manifest.json": sha256(arena / "manifest.json")}
        if not manifest["benchmark_targets"]:
            continue
        diagnostic, scores = read_scan_scores(arena, provenance, manifest)
        for name in ("source.json", "source-diagnostic.json", "results/target.json"):
            inputs[event][name] = sha256(arena / name)
        rows = [evaluate(target, scores) for target in manifest["benchmark_targets"]]
        changed = [row for row in rows if row["LCB"]["prefix"] != row["L"]["prefix"]]
        if [row["fen"] for row in changed] != diagnostic["changed_prefix_targets"]:
            raise ValueError(f"Changed initial orders differ from the published diagnostic: {event}")
        events[event], changed_events[event] = rows, changed
    return {
        "source_depth": 12, "target_depth": 16, "inputs": inputs,
        "all": summarize(events), "changed_prefix": summarize(changed_events),
        "changed_targets": changed_events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.arena))


if __name__ == "__main__":
    main()
