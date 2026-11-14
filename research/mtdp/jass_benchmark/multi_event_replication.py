"""Track prospective 5+0 candidates and summarize the three frozen holdouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import fmean, quantiles

from research.mtdp.jass_benchmark.depth_sensitivity import read_input, validate_reference
from research.mtdp.jass_benchmark.geometry_ablation import (
    OCCUPANCY_ARMS, analyze, summarize_arm, write_json,
)
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256
from research.mtdp.top_k_transfer import _action

# UTC milliseconds for the start of the seventh holdout, pRW2Ahpz.
AFTER = 1794470400000
USED_EVENTS = {"L4F4P5R8", "eo66EN9z", "Z3s40c6H", "iPQl7g7q",
               "0gB7ETSW", "3onq5G6G", "LAYRsqON", "xmzj1bLG", "pRW2Ahpz"}
CONTRASTS = (("LCB", "L", False), ("LCB", "L", True), ("LM", "L", False), ("LMB", "LCB", False))


def snapshot(raw, retrieved_at, url):
    data = json.loads(raw)
    rows = []
    for phase in ("created", "started", "finished"):
        for row in data[phase]:
            variant = row["variant"]
            rows.append({
                "id": row["id"], "phase": phase, "starts_at": row["startsAt"],
                "finishes_at": row["finishesAt"], "system": row["system"],
                "variant": variant["key"] if isinstance(variant, dict) else variant,
                "clock": row["clock"], "status": row["status"],
            })
    return {"retrieved_at": retrieved_at, "url": url,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "events": sorted(rows, key=lambda row: (row["starts_at"], row["id"], row["phase"]))}


def candidates(snapshots):
    events = {}
    for evidence in sorted(snapshots, key=lambda row: row["retrieved_at"]):
        for row in evidence["events"]:
            if row["id"] in events and events[row["id"]]["phase"] == "finished":
                continue
            events[row["id"]] = row
    log, pending, finished = [], [], []
    for row in sorted(events.values(), key=lambda row: (row["starts_at"], row["id"])):
        if (row["system"] != "arena" or row["variant"] != "standard"
                or row["clock"] != {"limit": 300, "increment": 0}):
            continue
        event_id = row["id"]
        if event_id in USED_EVENTS:
            status = "used"
        elif row["starts_at"] <= AFTER:
            status = "before_cutoff"
        elif row["phase"] != "finished":
            pending.append(event_id)
            status = "pending_finish"
        elif row["status"] != 30:
            status = "not_completed"
        else:
            finished.append(event_id)
            status = "needs_pdn_and_replay"
        log.append({**row, "candidate_status": status})
    return {"required_events": 3, "metadata_candidates": finished,
            "pending_events": pending, "candidate_log": log}


def game_totals(observations):
    games = defaultdict(lambda: defaultdict(list))
    for event, game, value in observations:
        games[event][game].append(value)
    return {event: [(sum(values), len(values)) for _, values in sorted(group.items())]
            for event, group in sorted(games.items())}


def hierarchical_interval(observations):
    events = game_totals(observations)
    strata = list(events.values())
    count = sum(map(len, strata))
    if len(strata) < 2 or count < 2:
        return {"events": len(strata), "games": count, "ci95": None}
    rng = random.Random(20261112)
    estimates = []
    for _ in range(10_000):
        total = size = 0
        for stratum in rng.choices(strata, k=len(strata)):
            for game_sum, game_size in rng.choices(stratum, k=len(stratum)):
                total += game_sum
                size += game_size
        estimates.append(total / size)
    cuts = quantiles(estimates, n=1000, method="inclusive")
    return {"events": len(strata), "games": count, "ci95": [cuts[24], cuts[974]]}


def paired_observations(events, treatment, control, changed_only):
    for event, rows in events.items():
        for row in rows:
            if treatment not in row or control not in row:
                continue
            sources = row["selected_sources"]
            changed = sources[treatment] != sources[control]
            if changed_only and not changed:
                continue
            yield event, row["owner"], changed, row[treatment], row[control]


def contrast(events, treatment, control, changed_only, *, metric="top3"):
    pairs = list(paired_observations(events, treatment, control, changed_only))
    costs, coverage = [], []
    for event, game, _, treatment_row, control_row in pairs:
        a, b = treatment_row[metric], control_row[metric]
        coverage.append((event, game, int(a["covered"]) - int(b["covered"])))
        x, y = a["ordinary_regret_centimen"], b["ordinary_regret_centimen"]
        if x is not None and y is not None:
            costs.append((event, game, x - y))

    def mean(rows):
        return fmean(value for _, _, value in rows) if rows else None

    per_event = {}
    for event in events:
        local_pairs = [row for row in pairs if row[0] == event]
        local_costs = [row for row in costs if row[0] == event]
        changed_sources = sum(row[2] for row in local_pairs)
        per_event[event] = {
            "targets": len(local_pairs), "owning_games": len({row[1] for row in local_pairs}),
            "changed_sources": changed_sources,
            "changed_source_rate": changed_sources / len(local_pairs) if local_pairs else None,
            "ordinary_pairs": len(local_costs),
            "mean_regret_delta_centimen": mean(local_costs),
            "mean_coverage_delta": mean([row for row in coverage if row[0] == event]),
        }
    estimates = [row["mean_regret_delta_centimen"] for row in per_event.values()
                 if row["mean_regret_delta_centimen"] is not None]
    leave_one_out = {}
    for event in events:
        kept = [row for row in costs if row[0] != event]
        leave_one_out[event] = {"ordinary_pairs": len(kept), "mean_regret_delta_centimen": mean(kept)}
    changed_sources = sum(row[2] for row in pairs)
    return {
        "targets": len(pairs), "owning_games": len({(event, game) for event, game, *_ in pairs}),
        "changed_sources": changed_sources,
        "changed_source_rate": changed_sources / len(pairs) if pairs else None,
        "ordinary_pairs": len(costs),
        "mean_regret_delta_centimen": mean(costs), "mean_coverage_delta": mean(coverage),
        "regret_interval": hierarchical_interval(costs), "coverage_interval": hierarchical_interval(coverage),
        "by_event": per_event, "event_regret_range": [min(estimates), max(estimates)] if estimates else None,
        "leave_one_event_out": leave_one_out,
    }


def coverage_summary(rows, eligible, replayed):
    result = {}
    for arm in OCCUPANCY_ARMS:
        summary = summarize_arm(rows, arm)
        matched = summary["matched"]
        summary["unmatched"] = eligible - matched
        summary["owning_games"] = len({row["owner"] for row in rows if arm in row})
        summary["eligible_coverage"] = matched / eligible if eligible else None
        summary["replayed_coverage"] = matched / replayed if replayed else None
        result[arm] = summary
    baseline = result["L"]["matched"]
    for summary in result.values():
        loss = baseline - summary["matched"]
        summary["match_loss_vs_L"] = loss
        summary["relative_match_loss_vs_L"] = loss / baseline if baseline else None
        for metric in ("top1", "top3"):
            outcome = summary[metric]
            outcome["catastrophic"] = outcome["at_least_50"] + sum(outcome["category_transitions"].values())
    return {"eligible": eligible, "replayed": replayed, "arms": result}


def recovered_match_summary(rows):
    """Describe quality where relaxing exact occupancy adds an LCB match."""
    recovered = [row for row in rows if "LCB" in row and "LMB" not in row]
    return {
        "targets": len(recovered),
        "owning_games": len({row["owner"] for row in recovered}),
        "arms": {arm: summarize_arm(recovered, arm) for arm in ("L", "LCB")},
    }


def validate_freezes(freezes):
    if len(freezes) != 3:
        raise ValueError("Exactly three frozen events are required before scoring or aggregation")
    event_ids = set()
    game_ids, fen_ids, pdn_hashes = set(), set(), set()
    last_event = (AFTER, "")
    for provenance, frozen in freezes:
        metadata = provenance["event"]
        event = metadata["id"]
        if (event in USED_EVENTS or event in event_ids or provenance["arms"] != list(OCCUPANCY_ARMS)
                or not metadata["isFinished"] or metadata["variant"] != "standard"
                or metadata["clock"] != {"limit": 300, "increment": 0}):
            raise ValueError(f"Invalid or reused event: {event}")
        start = int(datetime.fromisoformat(metadata["startsAt"].replace("Z", "+00:00")).timestamp() * 1000)
        if start <= AFTER or (start, event) <= last_event:
            raise ValueError("Frozen events must follow the seventh holdout in chronological order")
        last_event = (start, event)
        ids = set(provenance["event_game_ids"])
        fens = {row["fen"] for row in frozen}
        digest = provenance["inputs"]["event"][0]["sha256"]
        if (len(ids) != len(provenance["event_game_ids"]) or game_ids & ids
                or fen_ids & fens or digest in pdn_hashes):
            raise ValueError("Frozen events overlap in game IDs, FENs or PDN digests")
        event_ids.add(event)
        game_ids.update(ids)
        fen_ids.update(fens)
        pdn_hashes.add(digest)
        counts = provenance["counts"]
        if len(frozen) != len(fens) or len(fens) != counts["eligible"]:
            raise ValueError(f"Frozen eligible denominator changed: {event}")


def score_catalogue(plan, role):
    catalogue = {}
    for row in plan["targets"]:
        fen = row[f"{role}_fen"]
        actions = {_action(move) for move in row["legal_moves"]}
        if len(actions) != len(row["legal_moves"]) or catalogue.setdefault(fen, actions) != actions:
            raise ValueError(f"Invalid or inconsistent actions in merged score plan: {fen}")
    return catalogue


def merge_score_plans(plans):
    if len(plans) != 3:
        raise ValueError("Exactly three score plans are required")
    engine = plans[0]["engine"]
    if any(plan["schema"] != "mtdp-jass-cohort-v1" or plan["engine"] != engine for plan in plans):
        raise ValueError("Frozen plans disagree on the scoring engine")
    merged = {**plans[0], "targets": [row for plan in plans for row in plan["targets"]]}
    for role in ("source", "target"):
        score_catalogue(merged, role)
    return merged


def split_reference(merged, merged_hash, reference, plans, role):
    expected = score_catalogue(merged, role)
    hashes = {"scan_linux": merged["engine"]["scan_binary_sha256"], "data/eval": SCAN_EVAL_SHA256}
    if reference.get("role") != role:
        raise ValueError(f"Wrong merged Scan reference role: {role}")
    validate_reference(reference, expected, hashes, merged_hash, 12 if role == "source" else 16)
    scores = reference["action_scores_centimen"]
    results = {}
    for event, plan, digest in plans:
        catalogue = score_catalogue(plan, role)
        if any(expected.get(fen) != actions for fen, actions in catalogue.items()):
            raise ValueError(f"Event action catalogue differs from merged plan: {event}")
        results[event] = {
            **reference, "cohort_sha256": digest,
            "action_scores_centimen": {fen: scores[fen] for fen in sorted(catalogue)},
        }
    return results


def read_freezes(entries):
    plans, freezes = [], []
    for entry in entries:
        provenance = read_input(entry["provenance"])
        frozen = [row for ref in provenance["eligible_shards"] for row in read_input(ref)]
        plan = read_input(provenance["score_plan"])
        expected = {
            (match[0][2], row["fen"]): {_action({"action": action}) for action in row["actions"]}
            for row in frozen for match in row["matches"].values() if match
        }
        actual = {(row["source_fen"], row["target_fen"]): {_action(move) for move in row["legal_moves"]}
                  for row in plan["targets"]}
        if expected != actual or len(actual) != len(plan["targets"]):
            raise ValueError("Score plan differs from frozen match selections")
        plans.append((provenance["event"]["id"], plan, provenance["score_plan"]["content_sha256"]))
        freezes.append((provenance, frozen))
    validate_freezes(freezes)
    return plans


def aggregate(packets):
    validate_freezes([(provenance, frozen) for provenance, _, frozen in packets])
    events, summaries = {}, {}
    for provenance, report, frozen in packets:
        event = provenance["event"]["id"]
        counts = provenance["counts"]
        matched_rows = report["matched_rows"]
        if report["targets"] != counts["eligible"]:
            raise ValueError(f"Frozen eligible denominator changed: {event}")
        matched = {row["fen"]: row for row in frozen if row["matches"]["L"]}
        if len(matched) != len(matched_rows) or matched.keys() != {row["fen"] for row in matched_rows}:
            raise ValueError(f"Matched report population changed: {event}")
        for row in matched_rows:
            expected = matched[row["fen"]]
            selected = {arm: expected["matches"][arm][0] for arm in OCCUPANCY_ARMS
                        if expected["matches"][arm]}
            if (selected != row["selected_sources"] or row["owner"] != expected["owner"]
                    or any((arm in row) != (arm in selected) for arm in OCCUPANCY_ARMS)):
                raise ValueError(f"Report does not use the frozen source or owning game: {event}")
        events[event] = matched_rows
        summaries[event] = coverage_summary(matched_rows, counts["eligible"], counts["held_fens"])
        summaries[event]["freeze_counts"] = counts
        summaries[event]["game_count"] = len(provenance["event_game_ids"])
    pooled_rows = [row for rows in events.values() for row in rows]
    overall = coverage_summary(pooled_rows,
                               sum(s["eligible"] for s in summaries.values()),
                               sum(s["replayed"] for s in summaries.values()))
    paired = {
        key: {
            f"{a}_vs_{b}" + ("_changed_sources" if changed else ""):
            contrast(events, a, b, changed, metric=metric)
            for a, b, changed in CONTRASTS
        }
        for key, metric in (("paired", "top3"), ("paired_top1", "top1"))
    }
    return {
        "events": summaries, "pooled": overall, **paired,
        "lcb_recovered_vs_lmb": {
            "pooled": recovered_match_summary(pooled_rows),
            "by_event": {event: recovered_match_summary(rows) for event, rows in events.items()},
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    snap = modes.add_parser("snapshot")
    snap.add_argument("--raw", type=Path, required=True)
    snap.add_argument("--retrieved-at", required=True)
    snap.add_argument("--url", required=True)
    track = modes.add_parser("candidates")
    track.add_argument("--snapshot", action="append", type=Path, required=True)
    prepare = modes.add_parser("prepare-score-plan")
    split = modes.add_parser("split-reference")
    for command in (prepare, split):
        command.add_argument("--freeze-index", type=Path, required=True)
    split.add_argument("--merged-plan", type=Path, required=True)
    split.add_argument("--reference", type=Path, required=True)
    split.add_argument("--role", choices=("source", "target"), required=True)
    split.add_argument("--output-dir", type=Path, required=True)
    combine = modes.add_parser("aggregate")
    combine.add_argument("--packet-index", type=Path, required=True)
    for command in (snap, track, prepare, combine):
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "snapshot":
        result = snapshot(args.raw.read_bytes(), args.retrieved_at, args.url)
    elif args.mode == "candidates":
        result = candidates([json.loads(path.read_text()) for path in args.snapshot])
    elif args.mode in ("prepare-score-plan", "split-reference"):
        plans = read_freezes(json.loads(args.freeze_index.read_text()))
        merged = merge_score_plans([plan for _, plan, _ in plans])
        if args.mode == "prepare-score-plan":
            write_json(args.output, merged)
        else:
            raw = args.merged_plan.read_bytes()
            if json.loads(raw) != merged:
                raise ValueError("Merged score plan does not reproduce from the three frozen events")
            reference = json.loads(args.reference.read_bytes())
            results = split_reference(merged, hashlib.sha256(raw).hexdigest(), reference, plans, args.role)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            for event, receipt in results.items():
                write_json(args.output_dir / f"{event}-{args.role}.json", receipt)
        return
    else:
        packets = []
        for entry in json.loads(args.packet_index.read_text()):
            provenance, report = (read_input(entry[key]) for key in ("provenance", "comparison"))
            references = {role: read_input(entry[role]) for role in ("source", "target")}
            digests = {role: entry[role]["content_sha256"] for role in references}
            if digests != report["reference_sha256"]:
                raise ValueError("Scan receipt digest changed")
            frozen = [row for ref in provenance["eligible_shards"] for row in read_input(ref)]
            rebuilt = analyze(frozen, references["source"], references["target"], provenance)
            rebuilt["reference_sha256"] = digests
            if json.dumps(rebuilt, sort_keys=True) != json.dumps(report, sort_keys=True):
                raise ValueError("Archived event analysis does not reproduce from frozen inputs")
            packets.append((provenance, report, frozen))
        result = aggregate(packets)
    write_json(args.output, result)


if __name__ == "__main__":
    main()
