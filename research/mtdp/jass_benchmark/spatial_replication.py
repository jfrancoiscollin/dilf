"""Aggregate the preregistered five-arena spatial Jass replication."""

import argparse
import gzip
import json
from collections import Counter
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
from research.mtdp.jass_benchmark.spatial_jass import (
    BUDGETS, source_diagnostic, summarize_budget, verify_equal_prefix_receipts,
)
from research.mtdp.jass_cohort import ADAPTER_COMMIT, JASS_COMMIT, SCAN_COMMIT
from research.mtdp.top_k_transfer import _action, _category


def read_freeze(directory):
    provenance_path = directory / "provenance.json"
    manifest_path = directory / "manifest.json"
    provenance = json.loads(provenance_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest["provenance_sha256"] != sha256(provenance_path)
            or manifest["event"] != provenance["event"]["id"]):
        raise ValueError(f"Manifest is not bound to the arena freeze: {directory}")
    frozen = [row for shard in provenance["eligible_shards"] for row in read_input(shard)]
    matched = {row["fen"]: row for row in frozen if row["matches"]["LCB"]}
    targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
    if (len(frozen) != manifest["eligible"] or len(frozen) != provenance["counts"]["eligible"]
            or len(targets) != len(manifest["benchmark_targets"])
            or len(matched) != provenance["counts"]["LCB"]
            or matched.keys() != targets.keys()):
        raise ValueError(f"Manifest target population differs from freeze: {directory}")
    for fen, row in matched.items():
        target = targets[fen]
        sources = {arm: row["matches"][arm][0] for arm in ("L", "LCB")}
        if (target["target_games"] != row["games"]
                or target["source_fens"] != {arm: source[2] for arm, source in sources.items()}
                or target["source_fen"] != sources["L"][2] or target["source_game"] != sources["L"][0]
                or [move["action"] for move in target["legal_moves"]] != row["actions"]):
            raise ValueError(f"Manifest target differs from frozen position: {fen}")
    expected_pairs = {
        (source, fen): row["legal_moves"]
        for fen, row in targets.items() for source in row["source_fens"].values()
    }
    actual_pairs = {
        (row["source_fen"], row["target_fen"]): row["legal_moves"] for row in manifest["targets"]
    }
    settings = {
        "jass_node_budgets": list(BUDGETS),
        "scan_successor_depth": 12,
        "target_scan_successor_depth": 16,
        "draught_master_commit": ADAPTER_COMMIT,
        "jass_commit": JASS_COMMIT,
        "scan_commit": SCAN_COMMIT,
        "scan_binary_sha256": provenance["scan_sha256"]["scan_linux"],
    }
    if (len(actual_pairs) != len(manifest["targets"]) or actual_pairs != expected_pairs
            or any(manifest["engine"].get(key) != value for key, value in settings.items())):
        raise ValueError(f"Manifest scoring plan differs from frozen targets or settings: {directory}")
    return provenance, frozen, manifest


def validate_traces(directory, rows, targets):
    """Bind each archived root trace to its frozen actions and paired receipt."""
    for budget in BUDGETS:
        expected = {(row["target_fen"], arm): row for row in rows if row["budget"] == budget
                    for arm in row["arms"]}
        path = directory / f"results/traces-{budget}.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as archive:
            for line in archive:
                trace = json.loads(line)
                fen, arm = trace["target_fen"], trace["arm"]
                row = expected.pop((fen, arm), None)
                if row is None or trace["budget"] != budget:
                    raise ValueError(f"Unexpected or duplicate root trace: {fen}, {arm}, {budget} nodes")
                legal = trace["legal"]
                keys = {move["jass_key"] for move in targets[fen]["legal_moves"]}
                prefix = row["prefixes"][arm]
                root = prefix + [move for move in legal if move not in prefix]
                attempts = trace["attempts"]
                if (len(legal) != len(keys) or set(legal) != keys or trace["root_order"] != root
                        or trace["fresh_tt_mib"] != 1 or trace["verified_schedule_applications"] != bool(prefix)
                        or not attempts or attempts[0]["depth"] != 1 or attempts[-1]["depth"] < 2
                        or not attempts[0]["completed"] or not attempts[0]["all_actions_searched"]):
                    raise ValueError(f"Invalid root trace settings: {fen}, {arm}, {budget} nodes")
                receipt = row["arms"][arm]
                adaptive, completed_nodes = list(legal), {}
                previous_depth, previous_nodes, previous_completed = 0, 0, False
                for attempt in attempts:
                    depth, nodes = attempt["depth"], attempt["nodes_after"]
                    if previous_depth and depth != previous_depth:
                        if depth != previous_depth + 1 or not previous_completed:
                            raise ValueError(f"Invalid root trace depth: {fen}, {arm}, {budget} nodes")
                        index = adaptive.index(completed_nodes[previous_depth][1])
                        adaptive[0], adaptive[index] = adaptive[index], adaptive[0]
                    order = root if depth == 1 else adaptive
                    visited = attempt["visited"]
                    if (attempt["expected"] != order or visited != order[:len(visited)]
                            or (attempt["all_actions_searched"] and visited != order)
                            or not previous_nodes <= nodes <= receipt["nodes"]
                            or attempt["best_move"] not in keys):
                        raise ValueError(f"Invalid root trace attempt: {fen}, {arm}, {budget} nodes")
                    previous_completed = attempt["completed"]
                    if previous_completed:
                        completed_nodes[depth] = (nodes, attempt["best_move"])
                    previous_depth, previous_nodes = depth, nodes
                completed_depth = receipt["completed_depth"]
                common_depth = min(result["completed_depth"] for result in row["arms"].values())
                # An interrupted aspiration retry discards the entire depth,
                # even if an earlier window at that depth completed.
                last_complete_depth = previous_depth - int(not previous_completed)
                if (previous_nodes != receipt["nodes"] or last_complete_depth != completed_depth
                        or completed_nodes[completed_depth][1] != receipt["best_move"]
                        or row["common_completed_depth"] != common_depth
                        or row["nodes_at_common_depth"][arm] != completed_nodes.get(common_depth, (None,))[0]):
                    raise ValueError(f"Root trace disagrees with paired receipt: {fen}, {arm}, {budget} nodes")
        if expected:
            fen, arm = next(iter(expected))
            raise ValueError(f"Missing root trace: {fen}, {arm}, {budget} nodes")


def read_arena(directory):
    provenance, frozen, manifest = read_freeze(directory)
    targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
    if not targets:
        return provenance, frozen, {"matched": 0, "changed_source": 0, "changed_prefix_targets": []}, []

    diagnostic = json.loads((directory / "source-diagnostic.json").read_bytes())
    source_path = directory / "source.json"
    source = json.loads(source_path.read_bytes())
    target = json.loads((directory / "results/target.json").read_bytes())
    if source.get("role") != "source" or target.get("role") != "target":
        raise ValueError(f"Unexpected Scan reference roles: {directory}")
    manifest_digest = sha256(directory / "manifest.json")
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
        if (row["target_games"] != targets[fen]["target_games"] or row["source_fens"] != targets[fen]["source_fens"]
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
        verify_equal_prefix_receipts(row)
    validate_traces(directory, rows, targets)
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
    optimum_labels = {
        (True, True): "both_optimal",
        (True, False): "lcb_only",
        (False, True): "control_only",
        (False, False): "neither_optimal",
    }
    for control in ("L", "native"):
        observations, changed_moves = [], []
        category_pairs = Counter()
        optimum_pairs = dict.fromkeys(optimum_labels.values(), 0)
        for event, row in complete:
            a, b = (row["arms"][arm] for arm in ("LCB", control))
            left, right = a["ordinary_regret_centimen"], b["ordinary_regret_centimen"]
            category_pairs[f'{b["scan_chosen_category"]}->{a["scan_chosen_category"]}'] += 1
            optimum_pairs[optimum_labels[a["scan_optimal"], b["scan_optimal"]]] += 1
            if left is not None and right is not None:
                observations.append((event, min(row["target_games"]), left - right))
            if a["best_move"] != b["best_move"]:
                changed_moves.append({"arena": event, "fen": row["target_fen"],
                                      "LCB_move": a["best_move"], "control_move": b["best_move"],
                                      "LCB_regret_centimen": left, "control_regret_centimen": right,
                                      "delta_centimen": left - right if left is not None and right is not None else None,
                                      "reference_category": a["scan_best_category"],
                                      "LCB_category": a["scan_chosen_category"],
                                      "control_category": b["scan_chosen_category"]})
        comparisons[control] = {
            "ordinary_pairs": len(observations),
            "nonordinary_pairs": len(complete) - len(observations),
            "chosen_category_pairs_control_to_lcb": dict(category_pairs),
            "optimum_pairs": optimum_pairs,
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


def validate_cohort(freezes, protocol_digest):
    if len(freezes) != REPLICATION_ARENAS:
        raise ValueError("Exactly five replication arenas are required")
    fens, games, exports, ids = set(), set(), set(), set()
    previous = (REPLICATION_CUTOFF, "")
    for provenance, frozen in freezes:
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


def aggregate(packets, protocol_digest):
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets], protocol_digest)
    cohorts = {}
    for provenance, frozen, diagnostic, _ in packets:
        event_id = provenance["event"]["id"]
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
    parser.add_argument("--check-freezes", action="store_true",
                        help="Verify the five frozen manifests before scoring")
    args = parser.parse_args()
    if len(args.arena) != REPLICATION_ARENAS:
        parser.error("Pass exactly five arena directories in chronological order")
    protocol_digest = sha256(REPLICATION_PROTOCOL)
    if args.check_freezes:
        freezes = [read_freeze(path) for path in args.arena]
        validate_cohort([(provenance, frozen) for provenance, frozen, _ in freezes], protocol_digest)
        write_json(args.output, {
            "protocol_sha256": protocol_digest,
            "arenas": [{
                "event": manifest["event"], "eligible": manifest["eligible"],
                "matched": len(manifest["benchmark_targets"]),
                "manifest_sha256": sha256(path / "manifest.json"),
            } for path, (_, _, manifest) in zip(args.arena, freezes, strict=True)],
        })
        return
    write_json(args.output, aggregate([read_arena(path) for path in args.arena], protocol_digest))


if __name__ == "__main__":
    main()
