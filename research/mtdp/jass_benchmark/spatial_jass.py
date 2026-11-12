"""Prepare and run paired LCB, L and native Jass on a prospectively frozen arena."""

import argparse
import json
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.depth_sensitivity import read_input, validate_reference
from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_replication import score_catalogue
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists, clustered_interval
from research.mtdp.jass_benchmark.run import run_benchmark, sha256, summarize, write_jsonl
from research.mtdp.jass_cohort import JASS_COMMIT
from research.mtdp.jass_move_mapping import map_root_moves, read_jass_catalogues
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256
from research.mtdp.top_k_transfer import _action

BUDGETS = (10_000, 50_000, 200_000)
ARMS = ("L", "LCB")


def prepare(provenance, catalogue):
    plan = read_input(provenance["score_plan"])
    rows = [row for shard in provenance["eligible_shards"] for row in read_input(shard)]
    eligible = [row for row in rows if row["matches"]["LCB"]]
    expected = score_catalogue(plan, "source") | score_catalogue(plan, "target")
    targets = []
    engine = create_engine()
    states = [parse_fen(row["fen"]) for row in eligible]
    legal = read_jass_catalogues(catalogue, states)
    for row, state, jass_moves in zip(eligible, states, legal, strict=True):
        mapping = map_root_moves(engine.legal_moves(state), jass_moves)
        sources = {arm: row["matches"][arm][0] for arm in ARMS}
        if mapping.keys() != {_action({"action": action}) for action in row["actions"]}:
            raise ValueError(f"Frozen target actions differ for {row['fen']}")
        if any(mapping.keys() != expected[source[2]] for source in sources.values()):
            raise ValueError(f"Frozen source actions differ for {row['fen']}")
        targets.append({
            "target_fen": row["fen"], "target_games": row["games"],
            "source_fen": sources["L"][2], "source_game": sources["L"][0],
            "source_fens": {arm: source[2] for arm, source in sources.items()},
            "legal_moves": [{"action": action, "jass_key": mapping[action]} for action in sorted(mapping)],
        })
    pairs = [{"source_fen": source, "target_fen": row["target_fen"], "legal_moves": row["legal_moves"]}
             for row in targets for source in sorted(set(row["source_fens"].values()))]
    return {
        "schema": plan["schema"], "engine": {
            **plan["engine"], "jass_commit": JASS_COMMIT, "jass_catalogue_sha256": sha256(catalogue),
            "jass_node_budgets": BUDGETS, "target_scan_successor_depth": 16,
        },
        "selection": {"arm_order_seed": 20261113}, "event": provenance["event"]["id"],
        "eligible": len(rows), "targets": pairs, "benchmark_targets": targets,
    }


def source_diagnostic(manifest, scores):
    changed = []
    for row in manifest["benchmark_targets"]:
        sources = row["source_fens"]
        prefixes = [candidate_lists(row["legal_moves"], scores[sources[arm]])[1]["transfer"]
                    for arm in ARMS]
        if prefixes[0] != prefixes[1]:
            changed.append(row["target_fen"])
    targets = manifest["benchmark_targets"]
    return {
        "eligible": manifest["eligible"], "matched": len(targets),
        "changed_source": sum(row["source_fens"]["L"] != row["source_fens"]["LCB"] for row in targets),
        "changed_prefix_targets": changed,
    }


def summarize_budget(rows, event):
    result = summarize(rows, treatment="LCB", controls=("L", "native"))
    result["owning_games"] = len({min(row["target_games"]) for row in rows})
    for control, comparison in result["comparisons"].items():
        observations = []
        for row in rows:
            a, b = (row["arms"][arm]["ordinary_regret_centimen"] for arm in ("LCB", control))
            if a is not None and b is not None:
                observations.append((event, min(row["target_games"]), a - b))
        comparison["whole_game_bootstrap"] = clustered_interval(observations)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    freeze = modes.add_parser("prepare")
    for name in ("provenance", "catalogue", "manifest"):
        freeze.add_argument(f"--{name}", required=True, type=Path)
    for mode in ("diagnose", "run"):
        command = modes.add_parser(mode)
        for name in ("manifest", "source", "output"):
            command.add_argument(f"--{name}", required=True, type=Path)
        if mode == "run":
            for name in ("target", "runner", "diagnostic"):
                command.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        manifest = prepare(json.loads(args.provenance.read_bytes()), args.catalogue)
        manifest["provenance_sha256"] = sha256(args.provenance)
        write_json(args.manifest, manifest)
        return
    manifest = json.loads(args.manifest.read_bytes())
    hashes = {
        "scan_linux": manifest["engine"]["scan_binary_sha256"], "data/eval": SCAN_EVAL_SHA256,
    }
    source = json.loads(args.source.read_bytes())
    if source.get("role") != "source":
        raise ValueError("Expected a source Scan reference")
    source_scores = validate_reference(source, score_catalogue(manifest, "source"), hashes,
                                       sha256(args.manifest), 12)
    diagnostic = {
        **source_diagnostic(manifest, source_scores),
        "manifest_sha256": sha256(args.manifest), "source_sha256": sha256(args.source),
    }
    if args.mode == "diagnose":
        write_json(args.output, diagnostic)
        return
    if json.loads(args.diagnostic.read_bytes()) != diagnostic:
        raise ValueError("Published source diagnostic differs from frozen scores")
    target = json.loads(args.target.read_bytes())
    if target.get("role") != "target":
        raise ValueError("Expected a target Scan reference")
    validate_reference(target, score_catalogue(manifest, "target"), hashes, sha256(args.manifest), 16)
    if not diagnostic["changed_prefix_targets"]:
        raise ValueError("No changed prefixes: there is no LCB-versus-L search contrast")
    benchmark = {**manifest, "targets": manifest["benchmark_targets"]}
    pairs, traces = run_benchmark(benchmark, target, args.runner, initial_only=True,
                                  source_reference=source, compare_spatial_sources=True)
    changed = set(diagnostic["changed_prefix_targets"])
    args.output.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output / "paired-results.jsonl", pairs)
    write_jsonl(args.output / "root-order-traces.jsonl", traces)
    write_json(args.output / "summary.json", {
        "searches": len(traces), "settings": manifest["engine"],
        "runner_sha256": sha256(args.runner), "target_sha256": sha256(args.target),
        "diagnostic": diagnostic,
        "by_budget": {
            budget: {
                label: summarize_budget([row for row in pairs if row["budget"] == budget
                                         and (label == "all" or row["target_fen"] in changed)], manifest["event"])
                for label in ("all", "changed_prefix")
            }
            for budget in BUDGETS
        },
    })


if __name__ == "__main__":
    main()
