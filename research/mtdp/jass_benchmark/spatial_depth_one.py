"""Audit depth-one score ties with the original and forced-first root orders."""

import argparse
import gzip
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.run import read_run, sha256
from research.mtdp.jass_benchmark.spatial_replication import read_arena, read_scan_scores

BUDGET = 50_000
ARMS = ("LCB", "native")


def replay(runner, target, scores, prefix, *, forced_winner=None):
    fen = target["target_fen"]
    env = {key: value for key, value in os.environ.items()
           if key not in ("JASS_EGDB_PATH", "JASS_EGDB_MTC_PATH", "MTDP_DEPTH_ONE_WINNER")}
    env["JASS_TRACE_ROOT"] = "1"
    if forced_winner is not None:
        env["MTDP_DEPTH_ONE_WINNER"] = forced_winner
    result = subprocess.run(
        [str(runner.resolve()), "--initial-only", "--record-depth-ceiling"],
        input=" ".join([fen, str(BUDGET), *prefix]) + "\n",
        check=True, capture_output=True, text=True, env=env,
    )
    moves, ends, receipts = [], [], []
    for line in result.stdout.splitlines():
        if not line.startswith("info roottrace "):
            receipts.append(line)
            continue
        fields = dict(field.split("=", 1) for field in line.split()[2:])
        if fields["depth"] != "1":
            continue
        if fields["event"] == "move":
            moves.append({key: int(fields[key]) for key in ("score", "alpha_before", "beta")}
                         | {"move": fields["move"]})
        if fields["event"] == "end":
            ends.append(fields)
    raw, = receipts
    receipt, trace = read_run(raw, target, BUDGET, prefix, scores,
                              initial_only=True, record_depth_ceiling=True)
    end, = ends
    attempt = trace["attempts"][0]
    if (end["complete"] != "1" or (forced_winner or end["bestmove"]) != attempt["best_move"]
            or int(end["nodes"]) != attempt["nodes_after"]
            or [move["move"] for move in moves] != attempt["visited"]):
        raise ValueError(f"Depth-one score log differs from structured trace: {fen}")
    return {"winner": end["bestmove"], "score": int(end["score"]), "moves": moves}, receipt, trace


def analyze(replication, runner):
    runner_digest = sha256(runner)
    prior = replication / "native-early-search.json.gz"
    with gzip.open(prior, "rt", encoding="utf-8") as stream:
        cohort = json.load(stream)["by_budget"][str(BUDGET)]
    selected = {}
    for row in cohort["positions"]:
        if row["depth_one_moves"]["LCB"] != row["depth_one_moves"]["native"]:
            selected.setdefault(row["arena"], []).append(row)
    positions = []
    for event, rows in selected.items():
        arena = replication / event
        settings = json.loads((arena / "results/jass-summary.json").read_bytes())
        if settings["runner_sha256"] != runner_digest:
            raise ValueError(f"Runner differs from the archived search build: {event}")
        provenance, _, _, receipts = read_arena(arena)
        manifest = json.loads((arena / "manifest.json").read_bytes())
        _, scores = read_scan_scores(arena, provenance, manifest)
        targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
        paired = {row["target_fen"]: row for row in receipts if row["budget"] == BUDGET}
        trace_path = arena / f"results/traces-{BUDGET}.jsonl.gz"
        with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
            archived = {(row["target_fen"], row["arm"]): row for row in map(json.loads, stream)}
        for row in rows:
            fen = row["fen"]
            target, receipt = targets[fen], paired[fen]
            original, forced = {}, {}
            for arm in ARMS:
                log, actual, trace = replay(runner, target, scores["target"][fen], receipt["prefixes"][arm])
                expected = receipt["arms"][arm]
                expected_trace = archived[fen, arm]
                if (any(actual[key] != expected[key] for key in actual if key != "elapsed_us")
                        or any(value != expected_trace[key] for key, value in trace.items())
                        or log["winner"] != row["depth_one_moves"][arm]):
                    raise ValueError(f"Archived search did not reproduce: {fen}, {arm}")
                original[arm] = log
                probe, _, _ = replay(runner, target, scores["target"][fen], [log["winner"]])
                first = probe["moves"][0]
                if first["move"] != log["winner"] or not first["alpha_before"] < first["score"] < first["beta"]:
                    raise ValueError(f"Forced-first score did not return inside its window: {fen}, {arm}")
                forced[arm] = first["score"]
            positions.append({
                "arena": event, "fen": fen, "original": original, "forced_first_scores": forced,
                "original_scores_equal": original["LCB"]["score"] == original["native"]["score"],
                "forced_first_scores_equal": forced["LCB"] == forced["native"],
                "both_probes_match_original": all(forced[arm] == original[arm]["score"] for arm in ARMS),
                "different_final_move": row["final_moves"]["LCB"] != row["final_moves"]["native"],
            })
    return {"budget": BUDGET, "runner_sha256": runner_digest, "cohort_sha256": sha256(prior),
            "positions": positions, "summary": dict(Counter(
                f"original_equal={row['original_scores_equal']}/probe_equal={row['forced_first_scores_equal']}"
                for row in positions
            ))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("replication", "runner", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.replication, args.runner))


if __name__ == "__main__":
    main()
