"""Trace depth-one ties through the fixed-budget Jass comparison."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_native_convergence import ARMS, compare
from research.mtdp.jass_benchmark.spatial_replication import read_arena, validate_cohort

BUDGET = 50_000


def analyze(replication, arenas):
    audit = replication / "depth-one-ties.json.gz"
    with gzip.open(audit, "rt", encoding="utf-8") as stream:
        ties = {(row["arena"], row["fen"]): row for row in json.load(stream)["positions"]}
    packets = [read_arena(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets],
                    sha256(REPLICATION_PROTOCOL))
    groups = {"same_final_move": [], "different_final_move": []}
    for arena, (provenance, _, _, receipts) in zip(arenas, packets, strict=True):
        event = provenance["event"]["id"]
        if not receipts:
            continue
        with gzip.open(arena / f"results/traces-{BUDGET}.jsonl.gz", "rt", encoding="utf-8") as stream:
            traces = {(row["target_fen"], row["arm"]): row for row in map(json.loads, stream)
                      if row["arm"] in ARMS}
        for receipt in receipts:
            if receipt["budget"] != BUDGET:
                continue
            fen = receipt["target_fen"]
            trace = compare(receipt, {arm: traces[fen, arm] for arm in ARMS})
            if trace["depth_one_moves"]["LCB"] == trace["depth_one_moves"]["native"]:
                continue
            tie = ties.pop((event, fen))
            if (not tie["both_probes_match_original"] or len(set(tie["forced_first_scores"].values())) != 1
                    or {arm: tie["original"][arm]["winner"] for arm in ARMS} != trace["depth_one_moves"]
                    or any(arm["stop"] != "nodes" for arm in receipt["arms"].values())):
                raise ValueError(f"Tie audit differs from the full-budget trace: {fen}")
            disagreements = set(trace["common_depths_with_different_best_move"])
            agreement = [depth for depth in range(1, trace["common_completed_depth"] + 1)
                         if depth not in disagreements]
            final = {arm: {key: receipt["arms"][arm][key] for key in (
                "best_move", "scan_optimal", "scan_chosen_category", "ordinary_regret_centimen",
            )} for arm in ARMS}
            a, b = (final[arm]["ordinary_regret_centimen"] for arm in ARMS)
            different = final["LCB"]["best_move"] != final["native"]["best_move"]
            if different != tie["different_final_move"]:
                raise ValueError(f"Final move differs from the tie audit: {fen}")
            groups["different_final_move" if different else "same_final_move"].append({
                "arena": event, "fen": fen, "first_common_agreement": agreement[0] if agreement else None,
                "later_common_divergence": [depth for depth in sorted(disagreements)
                                            if agreement and depth > agreement[0]],
                "agreed_common_depths": agreement,
                "common_completed_depth": trace["common_completed_depth"], "final": final,
                "lcb_minus_native_centimen": a - b if a is not None and b is not None else None,
            })
    if ties:
        raise ValueError("Tie audit contains positions absent from the search traces")
    return {"budget": BUDGET, "tie_audit_sha256": sha256(audit), "groups": {
        name: {"summary": summarize(rows), "positions": rows} for name, rows in groups.items()
    }}


def summarize(rows):
    deltas = [row["lcb_minus_native_centimen"] for row in rows
              if row["lcb_minus_native_centimen"] is not None]
    return {
        "positions": len(rows), "ordinary_pairs": len(deltas),
        "mean_delta_centimen": fmean(deltas) if deltas else None,
        "lower_equal_higher_lcb_regret": [sum(x < 0 for x in deltas), deltas.count(0),
                                         sum(x > 0 for x in deltas)],
        "scan_optima": {arm: sum(row["final"][arm]["scan_optimal"] for row in rows) for arm in ARMS},
        "first_common_agreement": dict(Counter(
            str(row["first_common_agreement"] or "none") for row in rows
        )),
        "diverged_after_agreement": sum(bool(row["later_common_divergence"]) for row in rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication", type=Path, required=True)
    parser.add_argument("--arena", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.replication, args.arena))


if __name__ == "__main__":
    main()
