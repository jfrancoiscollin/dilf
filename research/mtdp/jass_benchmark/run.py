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
from research.mtdp.top_k_transfer import _action, _category, _ranked


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_run(raw, target, budget, prefix, scores):
    (
        fen, actual_budget, nodes, depth, stop, best, score, elapsed, pv, legal, order, *attempts
    ) = raw.split("\t")
    by_key = {move["jass_key"]: _action(move) for move in target["legal_moves"]}
    legal_keys = legal.split(",")
    expected_order = prefix + [key for key in legal_keys if key not in prefix]
    if (
        parse_fen(fen) != parse_fen(target["target_fen"])
        or int(actual_budget) != budget
        or int(nodes) != budget
        or len(legal_keys) != len(by_key)
        or set(legal_keys) != by_key.keys()
        or order.split(",") != expected_order
        or best not in by_key
    ):
        raise ValueError(f"Unexpected Jass receipt for {fen}")
    trace = []
    for attempt in attempts:
        level, index, completed, all_visited, spent, visited = attempt.split(":")
        trace.append({
            "depth": int(level), "attempt": int(index), "completed": completed == "1",
            "all_actions_searched": all_visited == "1", "nodes_after": int(spent),
            "visited": visited.split(",") if visited else [],
        })
    best_scan = max(scores.values())
    chosen_scan = scores[by_key[best]]
    ordinary = _category(best_scan) == _category(chosen_scan) == "ordinary"
    return {
        "nodes": int(nodes), "completed_depth": int(depth), "stop": stop,
        "best_move": best, "jass_score": int(score), "elapsed_us": int(elapsed),
        "pv": pv.split(",") if pv else [], "scan_centimen": chosen_scan,
        "scan_optimal": best_scan == chosen_scan,
        "scan_best_category": _category(best_scan), "scan_chosen_category": _category(chosen_scan),
        "ordinary_regret_centimen": best_scan - chosen_scan if ordinary else None,
    }, {"legal": legal_keys, "root_order": expected_order, "attempts": trace}


def run_benchmark(manifest, reference, runner):
    rng = random.Random(manifest["selection"]["arm_order_seed"])
    score_rows = reference["action_scores_centimen"]
    requests, jobs = [], []
    for target in manifest["targets"]:
        canonical = [_action(move) for move in target["legal_moves"]]
        keys = {move: row["jass_key"] for move, row in zip(canonical, target["legal_moves"], strict=True)}
        scores = dict(_ranked(score_rows[target["target_fen"]]))
        source = _ranked(score_rows[target["source_fen"]])
        if set(canonical) != scores.keys() or set(canonical) != {move for move, _ in source}:
            raise ValueError("Scan action scores do not match the frozen manifest")
        prefixes = {
            "native": [],
            "transfer": [keys[move] for move, _ in source[:3]],
            "canonical": [keys[move] for move in canonical[:3]],
        }
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
    result = subprocess.run(
        [str(runner.resolve())], input="\n".join(requests) + "\n",
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
        parsed = {}
        for arm in arms:
            receipt, trace = read_run(next(receipts), target, budget, prefixes[arm], scores)
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


def summarize(rows):
    comparisons = {}
    for control in ("canonical", "native"):
        deltas, node_deltas = [], []
        changed = 0
        for row in rows:
            transfer, baseline = row["arms"]["transfer"], row["arms"][control]
            changed += transfer["best_move"] != baseline["best_move"]
            a, b = transfer["ordinary_regret_centimen"], baseline["ordinary_regret_centimen"]
            if a is not None and b is not None:
                deltas.append(a - b)
            nodes = row["nodes_at_common_depth"]
            if nodes["transfer"] is not None and nodes[control] is not None:
                node_deltas.append(nodes["transfer"] - nodes[control])
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
            for arm in ("native", "transfer", "canonical")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "scan-reference", "runner", "output-dir"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    reference = json.loads(args.scan_reference.read_text())
    if (
        reference["schema"] != "mtdp-jass-scan-reference-v1"
        or reference["cohort_sha256"] != sha256(args.manifest)
        or reference["scan_binary_sha256"] != manifest["engine"]["scan_binary_sha256"]
        or reference["scan_successor_depth"] != manifest["engine"]["scan_successor_depth"]
    ):
        parser.error("Scan reference does not match the frozen manifest")
    paired, traces = run_benchmark(manifest, reference, args.runner)
    by_budget, by_source_game = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for row in paired:
        by_budget[row["budget"]].append(row)
        by_source_game[row["source_game"]][row["budget"]].append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "paired-results.jsonl", paired)
    write_jsonl(args.output_dir / "root-order-traces.jsonl", traces)
    write_json(args.output_dir / "jass-build-manifest.json", {
        "jass_commit": manifest["engine"]["jass_commit"],
        "runner_sha256": sha256(args.runner), "cohort_sha256": sha256(args.manifest),
        "scan_reference_sha256": sha256(args.scan_reference), "settings": manifest["engine"],
    })
    write_json(args.output_dir / "summary.json", {
        "searches": len(traces),
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
