"""Aggregate the preregistered five-arena spatial Jass replication."""

import argparse
import gzip
import json
from datetime import datetime
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.depth_sensitivity import read_input, validate_reference
from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import (
    REPLICATION_ARENAS, REPLICATION_CUTOFF, REPLICATION_PROTOCOL,
)
from research.mtdp.jass_benchmark.multi_event_replication import hierarchical_interval, score_catalogue
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_jass import BUDGETS, source_diagnostic, summarize_budget
from research.mtdp.top_k_transfer import _action, _category


def read_arena(directory):
    provenance_path = directory / "provenance.json"
    manifest_path = directory / "manifest.json"
    provenance = json.loads(provenance_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest["provenance_sha256"] != sha256(provenance_path)
            or manifest["event"] != provenance["event"]["id"]):
        raise ValueError(f"Manifest is not bound to the arena freeze: {directory}")
    frozen = [row for shard in provenance["eligible_shards"] for row in read_input(shard)]
    matched = {row["fen"]: row["games"] for row in frozen if row["matches"]["LCB"]}
    targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
    if (len(frozen) != manifest["eligible"] or len(frozen) != provenance["counts"]["eligible"]
            or len(targets) != len(manifest["benchmark_targets"])
            or matched != {fen: row["target_games"] for fen, row in targets.items()}):
        raise ValueError(f"Manifest target population differs from freeze: {directory}")
    if not targets:
        return provenance, frozen, {"matched": 0, "changed_source": 0, "changed_prefix_targets": []}, []

    diagnostic = json.loads((directory / "source-diagnostic.json").read_bytes())
    source_path = directory / "source.json"
    source = json.loads(source_path.read_bytes())
    target = json.loads((directory / "results/target.json").read_bytes())
    if source.get("role") != "source" or target.get("role") != "target":
        raise ValueError(f"Unexpected Scan reference roles: {directory}")
    manifest_digest = sha256(manifest_path)
    scores = {
        role: validate_reference(reference, score_catalogue(manifest, role),
                                 provenance["scan_sha256"], manifest_digest, depth)
        for role, reference, depth in (("source", source, 12), ("target", target, 16))
    }
    expected_diagnostic = {
        **source_diagnostic(manifest, scores["source"]),
        "manifest_sha256": manifest_digest, "source_sha256": sha256(source_path),
    }
    if diagnostic != expected_diagnostic:
        raise ValueError(f"Source diagnostic does not match the frozen manifest: {directory}")
    path = directory / "results/paired-results.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as archive:
        rows = [json.loads(line) for line in archive]
    expected = {(fen, budget) for fen in targets for budget in BUDGETS}
    actual = {(row["target_fen"], row["budget"]) for row in rows}
    if len(actual) != len(rows) or actual != expected:
        raise ValueError(f"Missing, extra or duplicate target/budget receipts: {directory}")
    prefixes = {
        fen: {"native": [], **{
            arm: candidate_lists(target["legal_moves"], scores["source"][source])[1]["transfer"]
            for arm, source in target["source_fens"].items()
        }}
        for fen, target in targets.items()
    }
    for row in rows:
        fen = row["target_fen"]
        if (row["target_games"] != matched[fen] or row["source_fens"] != targets[fen]["source_fens"]
                or set(row["arms"]) != {"L", "LCB", "native"}
                or row["prefixes"] != prefixes[fen]):
            raise ValueError(f"Receipt differs from manifest or diagnostic: {fen}")
        action_scores = scores["target"][fen]
        by_key = {move["jass_key"]: action_scores[_action(move)] for move in targets[fen]["legal_moves"]}
        best = max(by_key.values())
        for receipt in row["arms"].values():
            receipt.setdefault("elapsed_us", 0)
            exact = receipt["stop"] == "nodes" and receipt["nodes"] == row["budget"]
            capped = (receipt["stop"] == "depth_ceiling" and receipt["completed_depth"] == 64
                      and 0 < receipt["nodes"] < row["budget"])
            if not (exact or capped):
                raise ValueError(f"Invalid node receipt: {fen}")
            chosen = by_key.get(receipt["best_move"])
            if chosen is None:
                raise ValueError(f"Receipt has an illegal move: {fen}")
            ordinary = _category(best) == _category(chosen) == "ordinary"
            if (receipt["scan_centimen"] != chosen or receipt["scan_optimal"] != (chosen == best)
                    or receipt["ordinary_regret_centimen"] != (best - chosen if ordinary else None)
                    or receipt["scan_best_category"] != _category(best)
                    or receipt["scan_chosen_category"] != _category(chosen)):
                raise ValueError(f"Receipt differs from the Scan reference: {fen}")
    return provenance, frozen, diagnostic, rows


def pool(packets, budget, *, changed_only):
    arena_rows = {}
    complete = []
    for provenance, _, diagnostic, rows in packets:
        event = provenance["event"]["id"]
        changed = set(diagnostic["changed_prefix_targets"])
        selected = [row for row in rows if row["budget"] == budget
                    and (not changed_only or row["target_fen"] in changed)]
        report = summarize_budget(selected, event)
        for arm in report["arms"].values():
            del arm["median_elapsed_us"]
        arena_rows[event] = report
        complete.extend((event, row) for row in selected
                        if all(receipt["stop"] == "nodes" for receipt in row["arms"].values()))

    comparisons = {}
    for control in ("L", "native"):
        observations, changed_moves = [], []
        for event, row in complete:
            a, b = (row["arms"][arm] for arm in ("LCB", control))
            left, right = a["ordinary_regret_centimen"], b["ordinary_regret_centimen"]
            if left is not None and right is not None:
                observations.append((event, min(row["target_games"]), left - right))
            if a["best_move"] != b["best_move"]:
                changed_moves.append({"arena": event, "fen": row["target_fen"],
                                      "LCB_move": a["best_move"], "control_move": b["best_move"],
                                      "LCB_regret_centimen": left, "control_regret_centimen": right})
        comparisons[control] = {
            "ordinary_pairs": len(observations),
            "nonordinary_pairs": len(complete) - len(observations),
            "mean_delta_centimen": fmean(row[2] for row in observations) if observations else None,
            "arena_game_bootstrap": hierarchical_interval(observations),
            "changed_moves": changed_moves,
        }
    return {
        "complete": all(row["complete"] for row in arena_rows.values()),
        "planned_targets": sum(row["planned_targets"] for row in arena_rows.values()),
        "budget_complete_targets": len(complete),
        "optimum_hits": {arm: sum(row["arms"][arm]["scan_optimal"] for _, row in complete)
                         for arm in ("LCB", "L", "native")},
        "by_arena": arena_rows,
        "comparisons": comparisons,
    }


def aggregate(packets, protocol_digest):
    if len(packets) != REPLICATION_ARENAS:
        raise ValueError("Exactly five replication arenas are required")
    fens, games, exports, ids = set(), set(), set(), set()
    previous = (REPLICATION_CUTOFF, "")
    cohorts = {}
    for provenance, frozen, diagnostic, _ in packets:
        event = provenance["event"]
        event_id = event["id"]
        start = int(datetime.fromisoformat(event["startsAt"]).timestamp() * 1000)
        local_fens = {row["fen"] for row in frozen}
        local_games = set(provenance["event_game_ids"])
        digest = provenance["inputs"]["event"][0]["sha256"]
        if (event_id in ids or (start, event_id) <= previous or not event["isFinished"]
                or event["variant"] != "standard" or event["clock"] != {"limit": 300, "increment": 0}
                or provenance["selection"].get("protocol_sha256") != protocol_digest
                or len(local_fens) != len(frozen) or len(local_games) != len(provenance["event_game_ids"])
                or local_fens & fens or local_games & games or digest in exports):
            raise ValueError(f"Invalid, overlapping or out-of-order replication arena: {event_id}")
        previous = (start, event_id)
        ids.add(event_id)
        fens.update(local_fens)
        games.update(local_games)
        exports.add(digest)
        cohorts[event_id] = {
            "eligible": len(frozen), "common": diagnostic["matched"],
            "changed_source": diagnostic["changed_source"],
            "changed_order": len(diagnostic["changed_prefix_targets"]),
        }
    return {
        "primary": {"budget": 50_000, "subset": "all", "control": "L"},
        "cohorts": cohorts,
        "by_budget": {budget: {
            "all": pool(packets, budget, changed_only=False),
            "changed_prefix": pool(packets, budget, changed_only=True),
        } for budget in BUDGETS},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.arena) != REPLICATION_ARENAS:
        parser.error("Pass exactly five arena directories in chronological order")
    write_json(args.output, aggregate([read_arena(path) for path in args.arena], sha256(REPLICATION_PROTOCOL)))


if __name__ == "__main__":
    main()
