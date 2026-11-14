"""Freeze and evaluate legal-only versus legal-plus-geometry PC Blues matches."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean
from urllib.parse import urlsplit

from research.mtdp.best_move_audit import load_positions
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.depth_sensitivity import distribution, read_input, regret, validate_reference
from research.mtdp.jass_benchmark.offline_top3_control import clustered_interval
from research.mtdp.jass_cohort import ADAPTER_COMMIT, SCAN_COMMIT, SCAN_SHA256
from research.mtdp.pdn import read_games
from research.mtdp.successor_audit import _action_key, _quiet_signature
from research.mtdp.top_k_transfer import _action

ARMS = ("L", "LG")
OCCUPANCY_ARMS = ("L", "LM", "LCB", "LMB")
OCCUPANCY_CONTRASTS = (("LM", "L"), ("LCB", "L"), ("LMB", "L"), ("LMB", "LCB"))


def quiet_catalogue(state, engine):
    signature = _quiet_signature(state)
    if signature is None:
        return None, "non_quiet"
    actions = tuple(sorted(map(_action_key, engine.legal_moves(state))))
    if len(set(actions)) != len(actions) or any(action[1] for action in actions):
        raise ValueError("Ambiguous or capturing action in quiet catalogue")
    if len(actions) < 2:
        return None, "terminal" if not actions else "forced"
    return (actions, signature), "eligible"


def enumerate_matches(index, catalogue):
    actions, signature = catalogue
    rows = sorted(index.get(actions, []))
    return {
        "L": [identity for identity, _ in rows],
        "LG": [identity for identity, key in rows if key == signature],
    }


def occupancy_catalogue(state, engine):
    if state.kings_of(state.turn):
        return None, "mover_king"
    actions = tuple(sorted(map(_action_key, engine.legal_moves(state))))
    if len(set(actions)) != len(actions):
        raise ValueError("Duplicate canonical action")
    signature = _quiet_signature(state)
    capturing = any(action[1] for action in actions)
    if capturing != (signature is None):
        raise ValueError("FMJD capture status disagrees with quiet geometry")
    if capturing:
        return None, "capture"
    if len(actions) < 2:
        return None, "terminal" if not actions else "forced"
    return (actions, signature), "eligible"


def enumerate_occupancy_matches(index, catalogue):
    actions, (turn, men, blockers) = catalogue
    rows = sorted(index.get((turn, actions), []))
    return {
        "L": [identity for identity, _ in rows],
        "LM": [identity for identity, key in rows if key[1] == men],
        "LCB": [identity for identity, key in rows if len(key[1]) == len(men) and key[2] == blockers],
        "LMB": [identity for identity, key in rows if key == (turn, men, blockers)],
    }


def check_event_game_ids(holdout, previous):
    def public_ids(path):
        ids = []
        for game in read_games(path):
            url = urlsplit(game.tags.get("Site", ""))
            first = url.path.lstrip("/").split("/")[0]
            if url.hostname == "lidraughts.org" and len(first) == 8 and first.isalnum():
                ids.append(first)
        return ids

    ids = public_ids(holdout)
    if len(ids) != len(read_games(holdout)) or len(ids) != len(set(ids)):
        raise ValueError("Holdout must have a unique public game ID for every PDN game")
    prior = {game_id for path in previous for game_id in public_ids(path)}
    if overlap := set(ids) & prior:
        raise ValueError(f"Holdout overlaps earlier game IDs: {sorted(overlap)}")
    return ids


def novel_targets(held, base, prior, frozen):
    return sorted(held.keys() - base.keys() - prior.keys() - frozen)


def freeze(baseline, exclusions, holdout, prior_fens, engine, *, mover_occupancy=False):
    arms = OCCUPANCY_ARMS if mover_occupancy else ARMS
    classify = occupancy_catalogue if mover_occupancy else quiet_catalogue
    matcher = enumerate_occupancy_matches if mover_occupancy else enumerate_matches
    public_game_ids = check_event_game_ids(holdout, [baseline, *exclusions]) if mover_occupancy else None
    seen = set()
    source_plies, game_audit = {}, {}
    base, _, base_inputs = load_positions([baseline], engine, seen, plies_by_game=source_plies)
    if base_inputs[0]["accepted"] != 26 or base_inputs[0]["rejected"] or base_inputs[0]["duplicates"]:
        raise ValueError("PC Blues must replay as 26 validated distinct games")
    prior, _, prior_inputs = load_positions(exclusions, engine, seen)
    held, held_games, held_inputs = load_positions([holdout], engine, seen, game_audit=game_audit)
    index = defaultdict(list)
    for fen, state in base.items():
        catalogue, _ = classify(state, engine)
        if catalogue is None:
            continue
        actions, signature = catalogue
        game = min(source_plies[fen])
        lookup = (signature[0], actions) if mover_occupancy else actions
        index[lookup].append(((game, min(source_plies[fen][game]), fen), signature))

    rows, score_pairs = [], []
    counts = Counter(dict.fromkeys(("eligible", "terminal", "forced", "non_quiet"), 0))
    if mover_occupancy:
        del counts["non_quiet"]
        counts.update({"mover_king": 0, "capture": 0})
    for fen in novel_targets(held, base, prior, prior_fens):
        catalogue, status = classify(held[fen], engine)
        counts[status] += 1
        if catalogue is None:
            continue
        actions, signature = catalogue
        matches = matcher(index, catalogue)
        game_ids = sorted(held_games[fen])
        side, men, blockers = signature
        rows.append({
            "fen": fen, "games": game_ids, "owner": game_ids[0],
            "actions": actions, "geometry": [side, sorted(men), sorted(blockers)],
            "matches": matches,
        })
        selected = {matches[arm][0][2] for arm in arms if matches[arm]}
        for source_fen in sorted(selected):
            score_pairs.append({"source_fen": source_fen, "target_fen": fen,
                                "legal_moves": [{"action": action} for action in actions]})

    summary = {
        "schema": "mtdp-geometry-ablation-freeze-v1",
        "inputs": {"baseline": base_inputs, "exclusions": prior_inputs, "event": held_inputs},
        "counts": {
            "held_fens": len(held), "overlap_pcblues": len(held.keys() & base.keys()),
            "overlap_prior_only": len((held.keys() & (prior.keys() | prior_fens)) - base.keys()),
            "overlap_prior_manifest": len(held.keys() & prior_fens),
            "eligible_source_fens": sum(map(len, index.values())),
            **counts,
            **{arm: sum(bool(row["matches"][arm]) for row in rows) for arm in arms},
        },
    }
    if mover_occupancy:
        summary["arms"] = arms
        summary["event_game_ids"] = public_game_ids
        summary["counts"]["novel_replayed_fens"] = sum(
            counts[key] for key in ("eligible", "terminal", "forced", "mover_king", "capture")
        )
    plan = {
        "schema": "mtdp-jass-cohort-v1",
        "engine": {"scan_binary_sha256": SCAN_SHA256, "scan_commit": SCAN_COMMIT,
                   "scan_successor_depth": 12, "draught_master_commit": ADAPTER_COMMIT},
        "targets": score_pairs,
    }
    return summary, rows, plan, game_audit


def outcomes(source, target, k):
    if source.keys() != target.keys() or not source:
        raise ValueError("Source and target legal catalogues differ")
    ranked = sorted(source, key=lambda action: (-source[action], action))
    target_best = max(target.values())
    source_best = source[ranked[0]]
    return {
        "top1": regret(target_best, target[ranked[0]]),
        "top3": regret(target_best, max(target[action] for action in ranked[:k])),
        "disjoint_optima": not any(source[action] == source_best and target[action] == target_best
                                   for action in ranked),
        "prefix": ranked[:k],
    }


def summarize_arm(records, arm):
    matched = [row[arm] for row in records if arm in row]
    source_counts = [row["match_counts"][arm] for row in records if arm in row]
    return {
        "matched": len(matched), "unmatched": len(records) - len(matched),
        "mean_sources_per_match": fmean(source_counts) if source_counts else None,
        "source_count_histogram": dict(Counter(source_counts)),
        "disjoint_optima": sum(row["disjoint_optima"] for row in matched),
        **{metric: {
            **distribution([row[metric]["ordinary_regret_centimen"] for row in matched
                            if row[metric]["ordinary_regret_centimen"] is not None]),
            "covered": sum(row[metric]["covered"] for row in matched),
            "category_transitions": dict(Counter(
                f"{row[metric]['best_category']}->{row[metric]['candidate_category']}" for row in matched
                if row[metric]["best_category"] != row[metric]["candidate_category"]
            )),
        } for metric in ("top1", "top3")},
    }


def paired_summary(records, stricter="LG", control="L"):
    pairs = [row for row in records if stricter in row and control in row]
    metrics = {}
    for name in ("top1", "top3"):
        coverage, costs = [], []
        for row in pairs:
            a, b = row[stricter][name], row[control][name]
            identity = ("holdout", row["owner"])
            coverage.append((*identity, int(a["covered"]) - int(b["covered"])))
            x, y = a["ordinary_regret_centimen"], b["ordinary_regret_centimen"]
            if x is not None and y is not None:
                costs.append((*identity, x - y))
        metrics[name] = {
            "coverage_delta": fmean(value for _, _, value in coverage) if coverage else None,
            "coverage_ci": clustered_interval(coverage),
            "regret_delta_centimen": distribution([value for _, _, value in costs]),
            "regret_ci": clustered_interval(costs),
        }
    changed = sum(
        row["selected_sources"][stricter] != row["selected_sources"][control]
        if "selected_sources" in row else row["source_differs"]
        for row in pairs
    )
    return {"paired": len(pairs), "different_source": changed, **metrics}


def analyze(rows, source, target, provenance):
    arms = tuple(provenance.get("arms", ARMS))
    if arms not in (ARMS, OCCUPANCY_ARMS):
        raise ValueError("Unexpected frozen matching arms")
    mover_occupancy = arms == OCCUPANCY_ARMS
    constraints = (("LM", "L"), ("LCB", "L"), ("LMB", "LM"), ("LMB", "LCB")) if mover_occupancy else (("LG", "L"),)
    expected = {"source": {}, "target": {}}
    for row in rows:
        actions = {_action({"action": value}) for value in row["actions"]}
        if len(actions) != len(row["actions"]):
            raise ValueError("Duplicate frozen action")
        sets = {arm: {tuple(match) for match in row["matches"][arm]} for arm in arms}
        if any(not sets[a] <= sets[b] for a, b in constraints):
            raise ValueError("Geometry matches must be legal matches and obey arm nesting")
        if sets["L"]:
            expected["target"][row["fen"]] = actions
        for arm in arms:
            matches = row["matches"][arm]
            if matches:
                fen = matches[0][2]
                if expected["source"].setdefault(fen, actions) != actions:
                    raise ValueError(f"Inconsistent frozen action set for {fen}")
    scores = {}
    for role, depth, reference in (("source", 12, source), ("target", 16, target)):
        if reference.get("role") != role:
            raise ValueError(f"Wrong reference role: {role}")
        scores[role] = validate_reference(reference, expected[role], provenance["scan_sha256"],
                                          provenance["score_plan"]["content_sha256"], depth)
        if mover_occupancy and any(abs(value) > 10_000 for moves in scores[role].values() for value in moves.values()):
            raise ValueError(f"Invalid {role} Scan score category")
    records = []
    for row in rows:
        matches = row["matches"]
        record = {"fen": row["fen"], "games": row["games"], "owner": row["owner"],
                  "match_counts": {arm: len(matches[arm]) for arm in arms}}
        if mover_occupancy:
            record["selected_sources"] = {arm: matches[arm][0] for arm in arms if matches[arm]}
        else:
            record["source_differs"] = bool(matches["LG"] and matches["L"][0] != matches["LG"][0])
        for arm in arms:
            if matches[arm]:
                fen = matches[arm][0][2]
                scored = scores["target"][row["fen"]]
                record[arm] = outcomes(scores["source"][fen], scored, min(3, len(scored)))
        records.append(record)
    single = [row for row in records if len(row["games"]) == 1]
    report = {
        "targets": len(rows), "arms": {arm: summarize_arm(records, arm) for arm in arms},
        "matched_rows": [row for row in records if "L" in row],
    }
    if mover_occupancy:
        report["paired"] = {f"{a}_vs_{b}": paired_summary(records, a, b) for a, b in OCCUPANCY_CONTRASTS}
        report["single_game_sensitivity"] = {
            f"{a}_vs_{b}": paired_summary(single, a, b) for a, b in OCCUPANCY_CONTRASTS
        }
        for arm, summary in report["arms"].items():
            for metric in ("top1", "top3"):
                outcome = summary[metric]
                outcome["catastrophic"] = outcome["at_least_50"] + sum(outcome["category_transitions"].values())
    else:
        report["paired"] = paired_summary(records)
        report["single_game_sensitivity"] = paired_summary(single)
    return report


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def prior_fens(paths):
    result = set()
    for path in paths:
        raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        result.update(row["target_fen"] for row in json.loads(raw)["targets"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_subparsers(dest="mode", required=True)
    freezing = mode.add_parser("freeze")
    for name in ("baseline", "holdout", "output-dir"):
        freezing.add_argument(f"--{name}", required=True, type=Path)
    for name in ("exclude-previous", "prior-manifest"):
        freezing.add_argument(f"--{name}", required=True, action="append", type=Path)
    freezing.add_argument("--mover-occupancy", action="store_true")
    freezing.add_argument("--prior-eligible-shard", action="append", default=[], type=Path)
    analysis = mode.add_parser("analyze")
    for name in ("provenance", "source", "target", "output"):
        analysis.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        excluded = prior_fens(args.prior_manifest)
        for shard in args.prior_eligible_shard:
            excluded.update(row["fen"] for row in json.loads(gzip.decompress(shard.read_bytes())))
        summary, rows, plan, audit = freeze(
            args.baseline, args.exclude_previous, args.holdout, excluded, create_engine(),
            mover_occupancy=args.mover_occupancy,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, value in (("freeze-summary", summary), ("eligible", rows), ("score-plan", plan), ("game-audit", audit)):
            write_json(args.output_dir / f"{name}.json", value)
    else:
        provenance = json.loads(args.provenance.read_text())
        rows = [row for record in provenance["eligible_shards"] for row in read_input(record)]
        if len(rows) != provenance["counts"]["eligible"] or len(rows) != len({row["fen"] for row in rows}):
            raise ValueError("Frozen target population disagrees with provenance")
        refs = {role: getattr(args, role).read_bytes() for role in ("source", "target")}
        report = analyze(rows, json.loads(refs["source"]), json.loads(refs["target"]), provenance)
        report["reference_sha256"] = {role: hashlib.sha256(data).hexdigest() for role, data in refs.items()}
        write_json(args.output, report)


if __name__ == "__main__":
    main()
