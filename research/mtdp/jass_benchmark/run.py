"""Run the three paired Jass arms against a frozen cohort and Scan reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from pedagogy.game import parse_fen
from research.mtdp.jass_benchmark.depth_sensitivity import legal_actions, validate_reference
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists, clustered_interval
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256
from research.mtdp.top_k_transfer import _action, _category, _ranked


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_run(raw, target, budget, prefix, scores, *, initial_only=False, record_depth_ceiling=False):
    (
        fen, actual_budget, nodes, depth, stop, best, score, elapsed, pv, legal, order, *attempts
    ) = raw.split("\t")
    by_key = {move["jass_key"]: _action(move) for move in target["legal_moves"]}
    legal_keys = legal.split(",")
    expected_order = prefix + [key for key in legal_keys if key not in prefix]
    depth_ceiling = (
        record_depth_ceiling and stop == "depth_ceiling" and int(depth) == 64
        and 0 < int(nodes) < budget
    )
    exact_budget = int(nodes) == budget and (
        stop == "nodes" if record_depth_ceiling else stop != "depth_ceiling"
    )
    if (
        parse_fen(fen) != parse_fen(target["target_fen"])
        or int(actual_budget) != budget
        or not (exact_budget or depth_ceiling)
        or len(legal_keys) != len(by_key)
        or set(legal_keys) != by_key.keys()
        or order.split(",") != expected_order
        or best not in by_key
    ):
        raise ValueError(
            f"Unexpected Jass receipt for {fen} at {budget} nodes: "
            f"reported {nodes} nodes, stop={stop}, depth={depth}"
        )
    trace = []
    for attempt in attempts:
        level, index, completed, all_visited, spent, visited, *ordering = attempt.split(":")
        if len(ordering) != (2 if initial_only else 0):
            raise ValueError(f"Jass trace mode differs from request for {fen}")
        row = {
            "depth": int(level), "attempt": int(index), "completed": completed == "1",
            "all_actions_searched": all_visited == "1", "nodes_after": int(spent),
            "visited": visited.split(",") if visited else [],
        }
        if initial_only:
            best_at_attempt, expected = ordering
            row["best_move"] = best_at_attempt
            row["expected"] = expected.split(",")
        trace.append(row)
    best_scan = max(scores.values())
    chosen_scan = scores[by_key[best]]
    ordinary = _category(best_scan) == _category(chosen_scan) == "ordinary"
    ordering_trace = {"legal": legal_keys, "root_order": expected_order, "attempts": trace}
    if initial_only:
        ordering_trace["verified_schedule_applications"] = int(bool(prefix))
        ordering_trace["fresh_tt_mib"] = 1
    return {
        "nodes": int(nodes), "completed_depth": int(depth), "stop": stop,
        "best_move": best, "jass_score": int(score), "elapsed_us": int(elapsed),
        "pv": pv.split(",") if pv else [], "scan_centimen": chosen_scan,
        "scan_optimal": best_scan == chosen_scan,
        "scan_best_category": _category(best_scan), "scan_chosen_category": _category(chosen_scan),
        "ordinary_regret_centimen": best_scan - chosen_scan if ordinary else None,
    }, ordering_trace


def run_benchmark(manifest, reference, runner, *, initial_only=False, source_reference=None,
                  compare_spatial_sources=False):
    if compare_spatial_sources and (not initial_only or source_reference is None):
        raise ValueError("Spatial source comparison needs initial-only ordering and source scores")
    rng = random.Random(manifest["selection"]["arm_order_seed"])
    score_rows = reference["action_scores_centimen"]
    source_rows = score_rows if source_reference is None else source_reference["action_scores_centimen"]
    requests, jobs = [], []
    for target in manifest["targets"]:
        canonical = [_action(move) for move in target["legal_moves"]]
        keys = {move: row["jass_key"] for move, row in zip(canonical, target["legal_moves"], strict=True)}
        scores = dict(_ranked(score_rows[target["target_fen"]]))
        source = _ranked(source_rows[target["source_fen"]])
        if set(canonical) != scores.keys() or set(canonical) != {move for move, _ in source}:
            raise ValueError("Scan action scores do not match the frozen manifest")
        prefixes = {
            "native": [],
            "transfer": [keys[move] for move, _ in source[:3]],
            "canonical": [keys[move] for move in canonical[:3]],
        }
        if source_reference is not None:
            _, lists = candidate_lists(target["legal_moves"], dict(source))
            prefixes.update({arm: lists[arm] for arm in ("transfer", "canonical")})
        if compare_spatial_sources:
            if target["source_fens"]["L"] != target["source_fen"]:
                raise ValueError("L source differs from the frozen baseline")
            spatial_scores = dict(_ranked(source_rows[target["source_fens"]["LCB"]]))
            _, spatial_lists = candidate_lists(target["legal_moves"], spatial_scores)
            prefixes = {"native": [], "L": lists["transfer"], "LCB": spatial_lists["transfer"]}
        for budget in manifest["engine"]["jass_node_budgets"]:
            arms = list(prefixes)
            rng.shuffle(arms)
            jobs.append((target, budget, arms, prefixes, scores))
            requests.extend(
                " ".join([target["target_fen"], str(budget), *prefixes[arm]]) for arm in arms
            )

    environment = dict(os.environ)
    environment.pop("JASS_EGDB_PATH", None)
    environment.pop("JASS_EGDB_MTC_PATH", None)
    environment["JASS_TRACE_ROOT"] = "0"
    command = [str(runner.resolve())]
    if initial_only:
        command.append("--initial-only")
    if compare_spatial_sources:
        command.append("--record-depth-ceiling")
    result = subprocess.run(
        command, input="\n".join(requests) + "\n",
        text=True, capture_output=True, env=environment,
    )
    if result.returncode:
        raise RuntimeError(f"Jass runner failed ({result.returncode}): {result.stderr.strip()}")
    output = result.stdout.splitlines()
    if len(output) != len(requests):
        raise ValueError(f"Expected {len(requests)} Jass receipts, got {len(output)}")
    receipts = iter(output)
    paired, traces = [], []
    for target, budget, arms, prefixes, scores in jobs:
        identity = {
            key: target[key] for key in ("target_fen", "target_games", "source_fen", "source_game")
        }
        pair = {**identity, "budget": budget, "arm_order": arms, "arms": {}}
        if compare_spatial_sources:
            pair["source_fens"] = target["source_fens"]
            pair["prefixes"] = prefixes
        parsed = {}
        for arm in arms:
            receipt, trace = read_run(
                next(receipts), target, budget, prefixes[arm], scores, initial_only=initial_only,
                record_depth_ceiling=compare_spatial_sources,
            )
            pair["arms"][arm] = receipt
            parsed[arm] = trace["attempts"]
            traces.append({"target_fen": target["target_fen"], "budget": budget, "arm": arm, **trace})
        common_depth = min(receipt["completed_depth"] for receipt in pair["arms"].values())
        pair["common_completed_depth"] = common_depth
        pair["nodes_at_common_depth"] = {
            arm: max(
                (row["nodes_after"] for row in attempts
                 if row["depth"] == common_depth and row["completed"]), default=None,
            )
            for arm, attempts in parsed.items()
        }
        paired.append(pair)
    return paired, traces


def summarize(rows, *, treatment="transfer", controls=("canonical", "native")):
    comparisons = {}
    for control in controls:
        deltas, node_deltas = [], []
        changed = 0
        for row in rows:
            transfer, baseline = row["arms"][treatment], row["arms"][control]
            changed += transfer["best_move"] != baseline["best_move"]
            a, b = transfer["ordinary_regret_centimen"], baseline["ordinary_regret_centimen"]
            if a is not None and b is not None:
                deltas.append(a - b)
            nodes = row["nodes_at_common_depth"]
            if nodes[treatment] is not None and nodes[control] is not None:
                node_deltas.append(nodes[treatment] - nodes[control])
        comparisons[control] = {
            "ordinary_pairs": len(deltas), "changed_moves": changed,
            "transfer_better": sum(value < 0 for value in deltas),
            "transfer_worse": sum(value > 0 for value in deltas),
            "mean_delta_centimen": mean(deltas) if deltas else None,
            "median_delta_centimen": median(deltas) if deltas else None,
            "common_depth_pairs": len(node_deltas),
            "median_node_delta_at_common_depth": median(node_deltas) if node_deltas else None,
        }
    return {
        "targets": len(rows),
        "comparisons": comparisons,
        "arms": {
            arm: {
                "scan_optima": sum(row["arms"][arm]["scan_optimal"] for row in rows),
                "mean_completed_depth": mean(row["arms"][arm]["completed_depth"] for row in rows),
                "median_elapsed_us": median(row["arms"][arm]["elapsed_us"] for row in rows),
                "stop_reasons": dict(Counter(row["arms"][arm]["stop"] for row in rows)),
                "category_switches": dict(Counter(
                    f'{receipt["scan_best_category"]}->{receipt["scan_chosen_category"]}'
                    for receipt in (row["arms"][arm] for row in rows)
                    if receipt["scan_best_category"] != receipt["scan_chosen_category"]
                )),
            }
            for arm in (treatment, *controls)
        },
    }


def summarize_target_games(rows):
    """Assign each distinct FEN to one target game, then weight games equally."""
    games = defaultdict(list)
    for row in rows:
        games[min(row["target_games"])].append(row)
    by_game = {game: summarize(group) for game, group in sorted(games.items())}
    comparisons = {}
    for control in ("canonical", "native"):
        means = [
            summary["comparisons"][control]["mean_delta_centimen"]
            for summary in by_game.values()
            if summary["comparisons"][control]["ordinary_pairs"]
        ]
        comparisons[control] = {
            "ordinary_games": len(means),
            "transfer_better_games": sum(value < 0 for value in means),
            "transfer_worse_games": sum(value > 0 for value in means),
            "mean_game_delta_centimen": mean(means) if means else None,
            "median_game_delta_centimen": median(means) if means else None,
        }
    return {
        "games": len(games),
        "targets_in_multiple_games": sum(len(row["target_games"]) > 1 for row in rows),
        "comparisons": comparisons,
        "by_game": by_game,
    }


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")



def validate_cross_depth(manifest, source, target, cohort_hash):
    if (manifest["schema"] != "mtdp-jass-cohort-v1"
            or not manifest["targets"] or manifest["mapping_errors"] or manifest["mapping_rejected_pairs"]
            or manifest["engine"]["scan_successor_depth"] != 12):
        raise ValueError("Invalid frozen cross-depth cohort")
    expected = legal_actions(manifest["targets"])
    hashes = {"scan_linux": manifest["engine"]["scan_binary_sha256"], "data/eval": SCAN_EVAL_SHA256}
    for role, reference, depth in (("source", source, 12), ("target", target, 16)):
        if reference.get("role") != role:
            raise ValueError(f"Expected the {role} Scan reference")
        fens = {row[f"{role}_fen"] for row in manifest["targets"]}
        validate_reference(reference, {fen: expected[fen] for fen in fens}, hashes, cohort_hash, depth)


def cross_depth_intervals(rows):
    comparisons = {}
    for control in ("canonical", "native"):
        observations = []
        single_game = []
        for row in rows:
            transfer = row["arms"]["transfer"]["ordinary_regret_centimen"]
            baseline = row["arms"][control]["ordinary_regret_centimen"]
            if transfer is None or baseline is None:
                continue
            value = ("holdout", min(row["target_games"]), transfer - baseline)
            observations.append(value)
            if len(row["target_games"]) == 1:
                single_game.append(value)
        comparisons[control] = {
            "whole_game_bootstrap": clustered_interval(observations),
            "single_game_sensitivity": {
                "ordinary_pairs": len(single_game),
                "mean_delta_centimen": mean(value for _, _, value in single_game) if single_game else None,
                **clustered_interval(single_game),
            },
        }
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "scan-reference", "runner", "output-dir"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--initial-only", action="store_true")
    parser.add_argument("--source-scan-reference", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    reference = json.loads(args.scan_reference.read_text())
    source_reference = None
    if args.source_scan_reference:
        if not args.initial_only:
            parser.error("--source-scan-reference requires --initial-only")
        source_reference = json.loads(args.source_scan_reference.read_text())
        validate_cross_depth(manifest, source_reference, reference, sha256(args.manifest))
    elif (
        reference["schema"] != "mtdp-jass-scan-reference-v1"
        or reference["cohort_sha256"] != sha256(args.manifest)
        or reference["scan_binary_sha256"] != manifest["engine"]["scan_binary_sha256"]
        or reference["scan_successor_depth"] != manifest["engine"]["scan_successor_depth"]
    ):
        parser.error("Scan reference does not match the frozen manifest")
    paired, traces = run_benchmark(
        manifest, reference, args.runner, initial_only=args.initial_only, source_reference=source_reference,
    )
    by_budget, by_source_game = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for row in paired:
        by_budget[row["budget"]].append(row)
        by_source_game[row["source_game"]][row["budget"]].append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "paired-results.jsonl", paired)
    write_jsonl(args.output_dir / "root-order-traces.jsonl", traces)
    write_json(args.output_dir / "jass-build-manifest.json", {
        "root_order_mode": "initial-only" if args.initial_only else "persistent",
        "jass_commit": manifest["engine"]["jass_commit"],
        "runner_sha256": sha256(args.runner), "cohort_sha256": sha256(args.manifest),
        "scan_reference_sha256": sha256(args.scan_reference), "settings": manifest["engine"],
        **({"source_scan_reference_sha256": sha256(args.source_scan_reference),
            "source_scan_depth": 12, "target_scan_depth": 16} if source_reference is not None else {}),
    })
    write_json(args.output_dir / "summary.json", {
        "searches": len(traces),
        **({"cross_depth_intervals_centimen": {
            budget: cross_depth_intervals(rows) for budget, rows in by_budget.items()
        }} if source_reference is not None else {}),
        "by_budget": {budget: summarize(rows) for budget, rows in by_budget.items()},
        "by_target_game": {
            budget: summarize_target_games(rows) for budget, rows in by_budget.items()
        },
        "by_source_game": {
            game: {budget: summarize(rows) for budget, rows in budgets.items()}
            for game, budgets in by_source_game.items()
        },
    })


if __name__ == "__main__":
    main()
