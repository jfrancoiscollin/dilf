"""Compare archived LCB and native root traces on changed-prefix positions."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_jass import BUDGETS
from research.mtdp.jass_benchmark.spatial_replication import read_arena, validate_cohort

ARMS = ("LCB", "native")


def compare(receipt, traces):
    outcomes = {arm: receipt["arms"][arm] for arm in ARMS}
    moves = {
        arm: {attempt["depth"]: attempt["best_move"] for attempt in traces[arm]["attempts"]
              if attempt["completed"] and attempt["depth"] <= outcomes[arm]["completed_depth"]}
        for arm in ARMS
    }
    depths = sorted(moves["LCB"].keys() & moves["native"].keys())
    disagreement = [depth for depth in depths if moves["LCB"][depth] != moves["native"][depth]]
    common_depth = min(outcome["completed_depth"] for outcome in outcomes.values())
    if depths != list(range(1, common_depth + 1)):
        raise ValueError(f"Missing common completed depth for {receipt['target_fen']}")
    return {
        "same_initial_order": traces["LCB"]["root_order"] == traces["native"]["root_order"],
        "depth_one_moves": {arm: moves[arm][1] for arm in ARMS},
        "final_moves": {arm: outcomes[arm]["best_move"] for arm in ARMS},
        "common_completed_depth": common_depth,
        "common_depths_with_different_best_move": disagreement,
        "agreement_after_last_disagreement": (
            disagreement[-1] + 1 if disagreement and disagreement[-1] < common_depth else None
        ),
    }


def summarize(rows):
    phases = Counter()
    for row in rows:
        initial = "same_order" if row["same_initial_order"] else "different_order"
        first = "same_depth_one_move" if len(set(row["depth_one_moves"].values())) == 1 else "different_depth_one_move"
        final = "same_final_move" if len(set(row["final_moves"].values())) == 1 else "different_final_move"
        phases[f"{initial}/{first}/{final}"] += 1
    return {
        "positions": len(rows), "initial_and_final_agreement": dict(phases),
        "positions_with_common_depth_disagreement": sum(
            bool(row["common_depths_with_different_best_move"]) for row in rows
        ),
        "positions_with_later_common_depth_agreement": sum(
            row["agreement_after_last_disagreement"] is not None for row in rows
        ),
    }


def analyze(arenas):
    packets = [read_arena(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets],
                    sha256(REPLICATION_PROTOCOL))
    report = {}
    for budget in BUDGETS:
        positions, inputs, excluded = [], {}, []
        for arena, (provenance, _, diagnostic, receipts) in zip(arenas, packets, strict=True):
            event = provenance["event"]["id"]
            changed = set(diagnostic["changed_prefix_targets"])
            if not changed:
                continue
            path = arena / f"results/traces-{budget}.jsonl.gz"
            inputs[event] = {
                path.name: sha256(path),
                "paired-results.jsonl.gz": sha256(arena / "results/paired-results.jsonl.gz"),
            }
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                traces = {(row["target_fen"], row["arm"]): row for row in map(json.loads, stream)
                          if row["target_fen"] in changed and row["arm"] in ARMS}
            for receipt in receipts:
                fen = receipt["target_fen"]
                if receipt["budget"] != budget or fen not in changed:
                    continue
                if any(arm["stop"] != "nodes" for arm in receipt["arms"].values()):
                    excluded.append({"arena": event, "fen": fen})
                    continue
                positions.append({"arena": event, "fen": fen, **compare(
                    receipt, {arm: traces[fen, arm] for arm in ARMS},
                )})
        report[budget] = {"summary": summarize(positions), "positions": positions,
                          "inputs": inputs, "excluded_at_depth_ceiling": excluded}
    return {"by_budget": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.arena))


if __name__ == "__main__":
    main()
