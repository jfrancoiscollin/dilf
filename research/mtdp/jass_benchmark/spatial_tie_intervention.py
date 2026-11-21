"""Replay the LCB order while committing the independently verified native tie winner."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_depth_one import BUDGET, replay
from research.mtdp.jass_benchmark.spatial_replication import read_arena, read_scan_scores

ARMS = ("LCB", "native")


def analyze(replication, runner):
    audit = replication / "depth-one-ties.json.gz"
    with gzip.open(audit, "rt", encoding="utf-8") as stream:
        cases = json.load(stream)["positions"]
    rows = []
    for event in dict.fromkeys(row["arena"] for row in cases):
        arena = replication / event
        provenance, _, _, receipts = read_arena(arena)
        manifest = json.loads((arena / "manifest.json").read_bytes())
        _, scores = read_scan_scores(arena, provenance, manifest)
        targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
        paired = {row["target_fen"]: row for row in receipts if row["budget"] == BUDGET}
        with gzip.open(arena / f"results/traces-{BUDGET}.jsonl.gz", "rt", encoding="utf-8") as stream:
            traces = {(row["target_fen"], row["arm"]): row for row in map(json.loads, stream)}
        for case in (row for row in cases if row["arena"] == event):
            fen = case["fen"]
            target, receipt = targets[fen], paired[fen]
            if (len(set(case["forced_first_scores"].values())) != 1
                    or not case["both_probes_match_original"]):
                raise ValueError(f"Missing independent proof of a depth-one tie: {fen}")
            for arm in ARMS:
                log, result, trace = replay(runner, target, scores["target"][fen], receipt["prefixes"][arm])
                if (log != case["original"][arm]
                        or any(value != receipt["arms"][arm][key]
                               for key, value in result.items() if key != "elapsed_us")
                        or any(value != traces[fen, arm][key] for key, value in trace.items())):
                    raise ValueError(f"Unmodified search differs from the archive: {fen} {arm}")
            forced = case["original"]["native"]["winner"]
            log, result, trace = replay(runner, target, scores["target"][fen],
                                        receipt["prefixes"]["LCB"], forced_winner=forced)
            first = {**traces[fen, "LCB"]["attempts"][0], "best_move": forced}
            if (log != case["original"]["LCB"] or trace["attempts"][0] != first
                    or trace["root_order"] != traces[fen, "LCB"]["root_order"]
                    or result["stop"] != "nodes"):
                raise ValueError(f"Intervention altered the depth-one search or node budget: {fen}")
            outputs = {arm: receipt["arms"][arm] for arm in ARMS} | {"forced": result}
            rows.append({
                "arena": event, "fen": fen,
                "first_winner": forced,
                "depth_one_nodes": first["nodes_after"],
                "native_depth_two_order_reproduced": (
                    trace["attempts"][1]["expected"] == traces[fen, "native"]["attempts"][1]["expected"]
                ),
                "final": {arm: {key: item[key] for key in (
                    "best_move", "completed_depth", "scan_optimal", "ordinary_regret_centimen",
                )} for arm, item in outputs.items()},
            })
    return {"budget": BUDGET, "runner_sha256": sha256(runner), "tie_audit_sha256": sha256(audit),
            "all": summarize(rows), "original_disagreements": summarize([
                row for row in rows if row["final"]["LCB"]["best_move"] != row["final"]["native"]["best_move"]
            ]), "positions": rows}


def summarize(rows):
    agreement = Counter()
    for row in rows:
        moves = {arm: result["best_move"] for arm, result in row["final"].items()}
        agreement[f"LCB={moves['forced'] == moves['LCB']}/native={moves['forced'] == moves['native']}"] += 1
    return {
        "positions": len(rows),
        "native_depth_two_order_reproduced": sum(row["native_depth_two_order_reproduced"] for row in rows),
        "forced_final_move_agreement": dict(agreement),
        "scan_optima": {arm: sum(row["final"][arm]["scan_optimal"] for row in rows)
                        for arm in (*ARMS, "forced")},
        "mean_scan_regret_centimen": {arm: fmean(values) if (values := [
            row["final"][arm]["ordinary_regret_centimen"] for row in rows
            if row["final"][arm]["ordinary_regret_centimen"] is not None
        ]) else None for arm in (*ARMS, "forced")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("replication", "runner", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.replication, args.runner))


if __name__ == "__main__":
    main()
