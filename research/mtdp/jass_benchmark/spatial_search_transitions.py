"""Compare the transferred first choice with the final fixed-budget Jass move."""

import argparse
import json
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_candidate_quality import evaluate
from research.mtdp.jass_benchmark.spatial_jass import ARMS
from research.mtdp.jass_benchmark.spatial_replication import (
    read_arena, read_scan_scores, validate_cohort,
)

BUDGET = 50_000
TRANSITIONS = {
    (True, True): "retained",
    (False, True): "recovered",
    (True, False): "displaced",
    (False, False): "missed_both",
}


def compare(candidate, receipt):
    arms = {}
    for arm in ARMS:
        first = candidate[arm]["top1"]
        final = receipt["arms"][arm]
        initial_regret = first["ordinary_regret_centimen"]
        final_regret = final["ordinary_regret_centimen"]
        arms[arm] = {
            "first_move": candidate[arm]["prefix"][0],
            "final_move": final["best_move"],
            "first_regret_centimen": initial_regret,
            "final_regret_centimen": final_regret,
            "regret_change_centimen": (
                final_regret - initial_regret
                if initial_regret is not None and final_regret is not None else None
            ),
            "transition": TRANSITIONS[first["covered"], final["scan_optimal"]],
        }
    return arms


def summarize(rows):
    counts = {}
    for arm in ARMS:
        counter = Counter(dict.fromkeys(TRANSITIONS.values(), 0))
        counter.update(row["arms"][arm]["transition"] for row in rows)
        counts[arm] = dict(counter)
    return {
        "positions": len(rows),
        "arms": counts,
        "different_final_moves": sum(
            row["arms"]["L"]["final_move"] != row["arms"]["LCB"]["final_move"]
            for row in rows
        ),
    }


def analyze(arenas):
    packets = [read_arena(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets],
                    sha256(REPLICATION_PROTOCOL))
    by_arena, all_rows, excluded, inputs = {}, [], [], {}
    for arena, (provenance, _, diagnostic, receipts) in zip(arenas, packets, strict=True):
        event = provenance["event"]["id"]
        changed = set(diagnostic["changed_prefix_targets"])
        rows = []
        if changed:
            paths = ("manifest.json", "source.json", "results/target.json",
                     "source-diagnostic.json", "results/paired-results.jsonl.gz")
            inputs[event] = {path: sha256(arena / path) for path in paths}
            manifest = json.loads((arena / "manifest.json").read_bytes())
            _, scores = read_scan_scores(arena, provenance, manifest)
            targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
            for receipt in receipts:
                fen = receipt["target_fen"]
                if receipt["budget"] != BUDGET or fen not in changed:
                    continue
                if any(arm["stop"] != "nodes" for arm in receipt["arms"].values()):
                    excluded.append({"arena": event, "fen": fen})
                    continue
                candidate = evaluate(targets[fen], scores)
                rows.append({"arena": event, "fen": fen, "owner": candidate["owner"],
                             "arms": compare(candidate, receipt)})
        by_arena[event] = summarize(rows)
        all_rows.extend(rows)
    return {"budget": BUDGET, "source_depth": 12, "target_depth": 16,
            "inputs": inputs, "excluded_at_depth_ceiling": excluded,
            "summary": summarize(all_rows), "by_arena": by_arena, "positions": all_rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.arena))


if __name__ == "__main__":
    main()
