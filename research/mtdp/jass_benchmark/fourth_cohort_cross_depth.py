"""Evaluate frozen source-depth-12 shortlists against target depth 16."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.depth_sensitivity import (
    distribution, legal_actions, read_input, regret, validate_reference,
)
from research.mtdp.jass_benchmark.offline_top3_control import evaluate_target, summarize
from research.mtdp.top_k_transfer import _action


def analyze(manifest, source, target, provenance):
    event = provenance["event"]["id"]
    rows = sorted(manifest["targets"], key=lambda row: row["target_fen"])
    expected = legal_actions(rows)
    if (manifest["schema"] != "mtdp-jass-cohort-v1"
            or len(rows) != len({row["target_fen"] for row in rows})
            or len(rows) != manifest["counts"]["covered"] or not rows
            or manifest["engine"] != provenance["engines"]
            or manifest["mapping_errors"] or manifest["mapping_rejected_pairs"]):
        raise ValueError("Invalid frozen cohort or ambiguous move mapping")
    scores = {}
    for role, depth, reference in (("source", 12, source), ("target", 16, target)):
        if reference.get("role") != role or provenance["depths"][role] != depth:
            raise ValueError(f"Expected {role} reference at depth {depth}")
        fens = {row[f"{role}_fen"] for row in rows}
        scores[role] = validate_reference(
            reference, {fen: expected[fen] for fen in fens},
            provenance["scan_sha256"], provenance["manifest"]["content_sha256"], depth,
        )
    evaluated = []
    for row in rows:
        source_scores = scores["source"][row["source_fen"]]
        target_scores = scores["target"][row["target_fen"]]
        result = evaluate_target(row, source_scores, target_scores)
        source_best, target_best = max(source_scores.values()), max(target_scores.values())
        source_optima = {action for action, score in source_scores.items() if score == source_best}
        target_optima = {action for action, score in target_scores.items() if score == target_best}
        first_key = result["transfer"][0]
        first_action = next(_action(move) for move in row["legal_moves"] if move["jass_key"] == first_key)
        result.update({
            "target_games": row["target_games"],
            "disjoint_optima": source_optima.isdisjoint(target_optima),
            "first_transfer": regret(target_best, target_scores[first_action]),
        })
        evaluated.append(result)
    deltas = Counter()
    for row in evaluated:
        arms = row["outcomes"]
        a, b = (arms[arm]["ordinary_regret_centimen"] for arm in ("transfer", "canonical"))
        if a is not None and b is not None:
            deltas[a - b] += 1
    exclusive = [row for row in evaluated if len(row["target_games"]) == 1]
    first_costs = [row["first_transfer"]["ordinary_regret_centimen"] for row in evaluated]
    first_summary = distribution([value for value in first_costs if value is not None])
    first_summary["covered"] = sum(row["first_transfer"]["covered"] for row in evaluated)
    return {
        "schema": "mtdp-fourth-cohort-cross-depth-v1",
        "event": event,
        "depths": provenance["depths"],
        "summary": summarize({event: evaluated}),
        "disjoint_optima": sum(row["disjoint_optima"] for row in evaluated),
        "first_transfer": first_summary,
        "paired_regret_delta_counts_centimen": dict(deltas),
        "multi_game_targets": len(evaluated) - len(exclusive),
        "single_game_sensitivity": summarize({event: exclusive}) if exclusive else None,
        "targets": evaluated,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("provenance", "source", "target", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text())
    raw = {role: getattr(args, role).read_bytes() for role in ("source", "target")}
    report = analyze(read_input(provenance["manifest"]),
                     json.loads(raw["source"]), json.loads(raw["target"]), provenance)
    report["reference_sha256"] = {role: hashlib.sha256(data).hexdigest() for role, data in raw.items()}
    args.output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
