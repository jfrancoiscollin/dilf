"""Freeze and compare the depth-18 target sensitivity sample."""

import argparse
import hashlib
import json
from pathlib import Path

from research.mtdp.jass_benchmark.depth_sensitivity import read_input, validate_reference
from research.mtdp.jass_benchmark.geometry_ablation import (
    analyze, outcomes, summarize_arm, write_json,
)
from research.mtdp.jass_benchmark.multi_event_replication import (
    merge_score_plans, score_catalogue,
)
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256
from research.mtdp.top_k_transfer import _action


def load_study(index):
    plans, selected = [], {}
    for packet in json.loads(index.read_bytes()):
        provenance = read_input(packet["provenance"])
        frozen = [row for shard in provenance["eligible_shards"] for row in read_input(shard)]
        source, target = (read_input(packet[role]) for role in ("source", "target"))
        report = analyze(frozen, source, target, provenance)
        report["reference_sha256"] = {
            role: packet[role]["content_sha256"] for role in ("source", "target")
        }
        if json.dumps(report, sort_keys=True) != json.dumps(read_input(packet["comparison"]), sort_keys=True):
            raise ValueError("Archived comparison differs from frozen inputs")
        plans.append(read_input(provenance["score_plan"]))
        for row in report["matched_rows"]:
            if "LCB" not in row:
                continue
            groups = []
            if "LMB" not in row:
                groups.append("recovered")
            if row["selected_sources"]["L"] != row["selected_sources"]["LCB"]:
                groups.append("changed_source")
            if not groups:
                continue
            fen = row["fen"]
            if fen in selected:
                raise ValueError(f"Repeated target across tournaments: {fen}")
            selected[fen] = (row, groups, provenance["event"]["id"], source, target)
    merged = merge_score_plans(plans)
    manifest = {
        **merged,
        "targets": [row for row in merged["targets"] if row["target_fen"] in selected],
        "packet_index_sha256": hashlib.sha256(index.read_bytes()).hexdigest(),
        "target_successor_depth": 18,
        "selection": {
            fen: {"event": event, "owner": row["owner"], "groups": groups,
                  "sources": {arm: row["selected_sources"][arm][2] for arm in ("L", "LCB")}}
            for fen, (row, groups, event, _, _) in selected.items()
        },
    }
    if score_catalogue(manifest, "target").keys() != selected.keys():
        raise ValueError("Frozen target catalogue differs from selection")
    return manifest, selected


def action_scores(reference, fen):
    return {_action(row): row["score"] for row in reference["action_scores_centimen"][fen]}


def compare(manifest, selected, raw_manifest, reference):
    if reference.get("role") != "target":
        raise ValueError("Expected a target receipt")
    hashes = {
        "scan_linux": manifest["engine"]["scan_binary_sha256"],
        "data/eval": SCAN_EVAL_SHA256,
    }
    target18 = validate_reference(
        reference, score_catalogue(manifest, "target"), hashes,
        hashlib.sha256(raw_manifest).hexdigest(), manifest["target_successor_depth"],
    )
    if any(abs(score) > 10_000 for moves in target18.values() for score in moves.values()):
        raise ValueError("Invalid depth-18 Scan score category")
    records = []
    for fen, (row, groups, event, source, target) in sorted(selected.items()):
        by_depth = {}
        optima = {}
        for depth, scores in ((16, action_scores(target, fen)), (18, target18[fen])):
            optima[depth] = sorted(action for action, score in scores.items() if score == max(scores.values()))
            by_depth[depth] = {
                arm: outcomes(action_scores(source, manifest["selection"][fen]["sources"][arm]), scores,
                              min(3, len(scores)))
                for arm in ("L", "LCB")
            }
        for arm in ("L", "LCB"):
            if json.dumps(by_depth[16][arm], sort_keys=True) != json.dumps(row[arm], sort_keys=True):
                raise ValueError(f"Depth-16 outcomes changed for {fen}")
        records.append({
            "fen": fen, "event": event, "owner": row["owner"], "groups": groups,
            "optima": optima, "same_optima": optima[16] == optima[18],
            "disjoint_optima": not set(optima[16]) & set(optima[18]),
            "match_counts": row["match_counts"], "by_depth": by_depth,
        })

    summaries = {}
    for group in ("all", "recovered", "changed_source"):
        rows = [row for row in records if group == "all" or group in row["groups"]]
        summaries[group] = {
            "targets": len(rows), "owning_games": len({row["owner"] for row in rows}),
            "same_optima": sum(row["same_optima"] for row in rows),
            "disjoint_optima": sum(row["disjoint_optima"] for row in rows),
            "depths": {
                depth: {
                    arm: summarize_arm(
                        [{**row["by_depth"][depth], "match_counts": row["match_counts"]} for row in rows],
                        arm,
                    )
                    for arm in ("L", "LCB")
                }
                for depth in (16, 18)
            },
        }
    return {"groups": summaries, "rows": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.reference is None) != (args.output is None):
        parser.error("--reference and --output must be supplied together")
    manifest, selected = load_study(args.index)
    if args.reference is None:
        write_json(args.manifest, manifest)
        return
    raw_manifest = args.manifest.read_bytes()
    if json.loads(raw_manifest) != manifest:
        raise ValueError("Frozen selection does not reproduce from the archived study")
    raw_reference = args.reference.read_bytes()
    report = compare(manifest, selected, raw_manifest, json.loads(raw_reference))
    report["manifest_sha256"] = hashlib.sha256(raw_manifest).hexdigest()
    report["reference_sha256"] = hashlib.sha256(raw_reference).hexdigest()
    write_json(args.output, report)


if __name__ == "__main__":
    main()
