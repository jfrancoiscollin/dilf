"""Run the prospective depth-one control with separately metered score probes."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.multi_event_replication import hierarchical_interval
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.prospective_tiebreak import choose_native_order_tie
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_depth_one import replay
from research.mtdp.jass_benchmark.spatial_jass import BUDGETS
from research.mtdp.jass_benchmark.spatial_replication import read_arena, read_scan_scores, validate_cohort
from research.mtdp.top_k_transfer import _action


def select(runner, target, prefix):
    """Use only the live native order and independently full-window scores."""
    blank = {_action(move): 0 for move in target["legal_moves"]}
    original, baseline, trace = replay(runner, target, blank, prefix, budget=BUDGETS[0])
    order = trace["legal"]
    scores, completed, exact = {}, {}, {}
    probe_nodes = 0
    auxiliary_nodes = baseline["nodes"]
    for move in order:
        log, probe_result, probe = replay(runner, target, blank, [move], budget=BUDGETS[0])
        first = log["moves"][0]
        first_attempt = probe["attempts"][0]
        auxiliary_nodes += probe_result["nodes"]
        probe_nodes += first_attempt["nodes_after"]
        scores[move] = first["score"]
        completed[move] = first_attempt["completed"]
        exact[move] = (
            first["move"] == move and first["alpha_before"] == original["moves"][0]["alpha_before"]
            and first["beta"] == original["moves"][0]["beta"]
            and first["alpha_before"] < first["score"] < first["beta"]
        )
    winner = original["winner"]
    if not all(completed.values()) or not all(exact.values()) or max(scores.values()) != original["score"]:
        return winner, "unresolved", scores, probe_nodes, auxiliary_nodes, original
    chosen = choose_native_order_tie(order, scores, completed=completed, exact=exact, lcb_winner=winner)
    kind = "verified_tie" if list(scores.values()).count(scores[winner]) > 1 else "no_tie"
    return chosen, kind, scores, probe_nodes, auxiliary_nodes, original


def arena_rows(arena, runner, packet):
    provenance, _, _, receipts = packet
    event = provenance["event"]["id"]
    manifest = json.loads((arena / "manifest.json").read_bytes())
    _, scores = read_scan_scores(arena, provenance, manifest)
    paired = {(row["target_fen"], row["budget"]): row for row in receipts}
    targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
    selections = {}
    for fen, target in targets.items():
        _, lists = candidate_lists(target["legal_moves"], scores["source"][target["source_fens"]["LCB"]])
        prefix = lists["transfer"]
        selections[fen] = (prefix, *select(runner, target, prefix))
    for budget in BUDGETS:
        path = arena / f"results/traces-{budget}.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            traces = {(row["target_fen"], row["arm"]): row for row in map(json.loads, stream)}
        for fen, target in targets.items():
            row = paired[fen, budget]
            prefix, chosen, kind, exact_scores, probe_nodes, auxiliary_nodes, baseline_log = selections[fen]
            target_scores = scores["target"][fen]
            if prefix != row["prefixes"]["LCB"]:
                raise ValueError(f"LCB prefix differs from archive: {fen}")
            original_traces = {arm: traces[fen, arm] for arm in ("LCB", "native")}
            for arm, original_trace in original_traces.items():
                _, result, trace = replay(runner, target, target_scores, row["prefixes"][arm], budget=budget)
                if (any(value != row["arms"][arm][key] for key, value in result.items() if key != "elapsed_us")
                        or any(value != original_trace[key] for key, value in trace.items())):
                    raise ValueError(f"Original {arm} did not reproduce: {fen}, {budget}")
            initial = original_traces["LCB"]["attempts"][0]["best_move"]
            forced = chosen if chosen != initial else None
            control_log, control, trace = replay(runner, target, target_scores, prefix,
                                       forced_winner=forced, budget=budget)
            expected = {**original_traces["LCB"]["attempts"][0], "best_move": chosen}
            if (control_log != baseline_log or trace["attempts"][0] != expected
                    or trace["root_order"] != original_traces["LCB"]["root_order"]):
                raise ValueError(f"Control altered the depth-one visit: {fen}, {budget}")
            native_first = original_traces["native"]["attempts"][0]["best_move"]
            yield {
                "event": event, "fen": fen, "budget": budget, "game": min(row["target_games"]),
                "tie_evidence": kind, "probe_depth_one_nodes": probe_nodes, "probe_scores": exact_scores,
                "auxiliary_nodes": auxiliary_nodes,
                "archived_depth_one_disagreement": initial != native_first,
                "depth_one_winners": {"LCB": initial, "native": native_first, "control": chosen},
                "control_matches_native_depth_two_order": (
                    trace["attempts"][1]["expected"] == original_traces["native"]["attempts"][1]["expected"]
                ),
                "depth_one_nodes": {arm: item["attempts"][0]["nodes_after"]
                                    for arm, item in original_traces.items()} | {"control": expected["nodes_after"]},
                "arms": {arm: {key: item[key] for key in (
                    "best_move", "nodes", "stop", "completed_depth", "scan_optimal",
                    "scan_chosen_category", "ordinary_regret_centimen",
                )} for arm, item in {**row["arms"], "control": control}.items()},
            }


def summarize(rows):
    capped = [row for row in rows if any(arm["stop"] != "nodes" for arm in row["arms"].values())]
    complete = [row for row in rows if all(arm["stop"] == "nodes" for arm in row["arms"].values())]
    changes, regrets = [], []
    for row in complete:
        a = row["arms"]
        native = a["native"]["best_move"]
        changes.append((row["event"], row["game"], int(a["control"]["best_move"] != native)
                        - int(a["LCB"]["best_move"] != native)))
        x, y = (a[arm]["ordinary_regret_centimen"] for arm in ("control", "LCB"))
        if x is not None and y is not None:
            regrets.append(x - y)
    return {
        "positions": len(rows), "exact_budget": len(complete),
        "depth_ceiling": [row["fen"] for row in capped],
        "tie_evidence": dict(Counter(row["tie_evidence"] for row in complete)),
        "disagreements_with_native": {arm: sum(
            row["arms"][arm]["best_move"] != row["arms"]["native"]["best_move"] for row in complete
        ) for arm in ("LCB", "control")},
        "paired_disagreement_delta": fmean(x for _, _, x in changes) if changes else None,
        "paired_interval": hierarchical_interval(changes),
        "ordinary_pairs": len(regrets),
        "control_vs_lcb_optimum_transitions": dict(Counter(
            f"{row['arms']['LCB']['scan_optimal']}->{row['arms']['control']['scan_optimal']}"
            for row in complete
        )),
        "control_vs_lcb_outcome_categories": dict(Counter(
            f"{row['arms']['LCB']['scan_chosen_category']}->{row['arms']['control']['scan_chosen_category']}"
            for row in complete
        )),
        "mean_control_minus_lcb_regret": fmean(regrets) if regrets else None,
        "scan_optima": {arm: sum(row["arms"][arm]["scan_optimal"] for row in complete)
                        for arm in ("LCB", "native", "control")},
        "control_matches_native_depth_two_order": sum(row["control_matches_native_depth_two_order"] for row in complete),
    }


def combine(paths, packets, freeze_digest):
    rows, digests = [], set()
    for path in paths:
        packet = json.loads(path.read_bytes())
        if packet["freeze_sha256"] != freeze_digest:
            raise ValueError(f"Receipt differs from the prospective freeze: {path}")
        digests.add(packet["runner_sha256"])
        rows.extend(packet["positions"])
    actual = {(row["event"], row["fen"], row["budget"]) for row in rows}
    events = [provenance["event"]["id"] for provenance, _, _, _ in packets]
    expected = {(event, row["target_fen"], row["budget"])
                for event, (_, _, _, receipts) in zip(events, packets, strict=True)
                for row in receipts}
    if actual != expected or len(actual) != len(rows) or len(digests) != 1:
        raise ValueError("Missing, duplicate or incompatible control receipts")
    summaries = {}
    for budget in BUDGETS:
        subset = [row for row in rows if row["budget"] == budget]
        summaries[budget] = {
            "all": summarize(subset),
            "by_tie_evidence": {
                kind: summarize([row for row in subset if row["tie_evidence"] == kind])
                for kind in ("verified_tie", "unresolved", "no_tie")
            },
            "by_arena": {event: summarize([row for row in subset if row["event"] == event])
                         for event in events},
            "leave_one_arena_out": {
                event: summarize([row for row in subset if row["event"] != event])
                for event in events
            },
            "diagnostic_depth_one_disagreements": summarize([
                row for row in subset if row["archived_depth_one_disagreement"]
            ]),
        }
    primary_rows = [row for row in rows if row["budget"] == 50_000]
    return {"freeze_sha256": freeze_digest, "runner_sha256": digests.pop(),
            "auxiliary_nodes_all_positions": sum(row["auxiliary_nodes"] for row in primary_rows),
            "probe_depth_one_nodes_all_positions": sum(row["probe_depth_one_nodes"] for row in primary_rows),
            "by_budget": summaries, "positions": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication", required=True, type=Path)
    parser.add_argument("--runner", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--arena")
    mode.add_argument("--receipts", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.replication
    freeze_path = root / "prospective-tiebreak-freeze.json"
    freeze = json.loads(freeze_path.read_bytes())
    catalogue = root / "frozen-cohort.json"
    if (sha256(catalogue) != freeze["cohort_sha256"]
            or sha256(root / "PROSPECTIVE_TIEBREAK_PROTOCOL.md") != freeze["protocol_sha256"]
            or tuple(freeze["budgets"]) != BUDGETS):
        raise ValueError("Prospective freeze differs from the current inputs")
    patch_dir = Path(__file__).resolve().parents[1] / "jass_preflight"
    for key, name in (("initial_only_patch_sha256", "initial-only.patch"),
                      ("intervention_patch_sha256", "depth-one-winner.patch")):
        if sha256(patch_dir / name) != freeze[key]:
            raise ValueError(f"Patch differs from the prospective freeze: {name}")
    entries = json.loads(catalogue.read_bytes())["arenas"]
    if sum(entry["matched"] for entry in entries) != freeze["positions"]:
        raise ValueError("Frozen position count differs")
    arenas = [root / entry["event"] for entry in entries]
    for arena, entry in zip(arenas, entries, strict=True):
        manifest_path = arena / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        if (sha256(manifest_path) != entry["manifest_sha256"]
                or manifest["engine"]["jass_commit"] != freeze["jass_commit"]):
            raise ValueError(f"Manifest differs from prospective freeze: {arena}")
    packets = [read_arena(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets],
                    sha256(REPLICATION_PROTOCOL))
    freeze_digest = sha256(freeze_path)
    if args.receipts:
        write_json(args.output, combine(args.receipts, packets, freeze_digest))
        return
    if args.runner is None:
        parser.error("--runner is required when replaying an arena")
    index = [entry["event"] for entry in entries].index(args.arena)
    rows = list(arena_rows(arenas[index], args.runner, packets[index]))
    if len({(row["fen"], row["budget"]) for row in rows}) != entries[index]["matched"] * len(BUDGETS):
        raise ValueError("Missing or duplicate control receipts")
    write_json(args.output, {"freeze_sha256": freeze_digest, "runner_sha256": sha256(args.runner),
                            "positions": rows})


if __name__ == "__main__":
    main()
