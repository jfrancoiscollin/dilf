"""Compare frozen Scan references and reevaluate the archived Jass choices."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median, quantiles

from research.mtdp.best_move_audit import compare_scores
from research.mtdp.top_k_transfer import _action, _category, _direction

ARMS = {"native", "canonical", "transfer"}
DEPTHS = (12, 16)


def read_input(record):
    path = Path(record["path"])
    stored = path.read_bytes()
    raw = gzip.decompress(stored) if path.suffix == ".gz" else stored
    for data, key in ((stored, "stored_sha256"), (raw, "content_sha256")):
        if hashlib.sha256(data).hexdigest() != record[key]:
            raise ValueError(f"Input hash mismatch for {path}: {key}")
    if path.name.endswith((".jsonl", ".jsonl.gz")):
        return [json.loads(line) for line in raw.splitlines()]
    return json.loads(raw)


def legal_actions(targets):
    expected = {}
    for row in targets:
        moves = row["legal_moves"]
        by_key = {move["jass_key"]: _action(move) for move in moves}
        actions = set(by_key.values())
        if len(actions) != len(moves) or len(by_key) != len(moves):
            raise ValueError(f"Ambiguous frozen actions for {row['target_fen']}")
        for fen in (row["source_fen"], row["target_fen"]):
            if expected.setdefault(fen, actions) != actions:
                raise ValueError(f"Inconsistent frozen actions for {fen}")
    return expected


def validate_reference(reference, expected, provenance, cohort_hash, depth):
    fields = {
        "schema": "mtdp-jass-scan-reference-v1",
        "cohort_sha256": cohort_hash,
        "scan_binary_sha256": provenance["scan_linux"],
        "scan_eval_sha256": provenance["data/eval"],
        "scan_successor_depth": depth,
    }
    for key, value in fields.items():
        if reference.get(key) != value:
            raise ValueError(f"Invalid depth-{depth} reference field: {key}")
    rows_by_fen = reference["action_scores_centimen"]
    if rows_by_fen.keys() != expected.keys():
        raise ValueError(f"Depth-{depth} reference has different scored positions")
    scores = {}
    for fen, rows in rows_by_fen.items():
        scored = {_action(row): row["score"] for row in rows}
        if (scored.keys() != expected[fen] or len(scored) != len(rows)
                or any(type(value) is not int for value in scored.values())):
            raise ValueError(f"Depth-{depth} reference has invalid action scores for {fen}")
        scores[fen] = scored
    return scores


def regret(best, chosen):
    best_kind, chosen_kind = _category(best), _category(chosen)
    return {
        "ordinary_regret_centimen": best - chosen if best_kind == chosen_kind == "ordinary" else None,
        "best_category": best_kind,
        "candidate_category": chosen_kind,
        "covered": best == chosen,
    }


def compare_event(manifest, old, new, receipts, hashes, cohort_hash):
    if manifest["schema"] != "mtdp-jass-cohort-v1":
        raise ValueError("Unexpected cohort schema")
    targets = {row["target_fen"]: row for row in manifest["targets"]}
    if len(targets) != len(manifest["targets"]):
        raise ValueError("Duplicate frozen target")
    expected = legal_actions(targets.values())
    references = (old, new)
    scores = [validate_reference(ref, expected, hashes, cohort_hash, depth)
              for ref, depth in zip(references, DEPTHS, strict=True)]
    expected_receipts = {(fen, budget) for fen in targets
                         for budget in manifest["engine"]["jass_node_budgets"]}
    receipts_by_key = {(row["target_fen"], row["budget"]): row for row in receipts}
    if receipts_by_key.keys() != expected_receipts or len(receipts_by_key) != len(receipts):
        raise ValueError("Missing, extra or duplicate Jass receipt")

    pairs = []
    for fen, row in sorted(targets.items()):
        source = row["source_fen"]
        game = min(row["target_games"])
        snapshots = []
        for reference, score_by_fen in zip(references, scores, strict=True):
            transfer = compare_scores(score_by_fen[source], score_by_fen[fen])
            snapshots.append({
                "optimal_source": transfer["optimal_a"], "optimal_target": transfer["optimal_b"],
                "disjoint": not transfer["optimal_sets_overlap"],
                **{f"top{k}": _direction(source, fen, reference["action_scores_centimen"], k)
                   for k in (1, 3)},
            })
        pair = {"target_fen": fen, "source_fen": source, "game": game, "scan": snapshots, "jass": {}}
        by_key = {move["jass_key"]: _action(move) for move in row["legal_moves"]}
        for budget in manifest["engine"]["jass_node_budgets"]:
            receipt = receipts_by_key[fen, budget]
            if (any(receipt[key] != row[key] for key in ("target_games", "source_game", "source_fen"))
                    or receipt["arms"].keys() != ARMS):
                raise ValueError(f"Jass receipt identity changed for {fen} at {budget}")
            arms = {}
            for arm, record in receipt["arms"].items():
                if record["nodes"] != budget or record["best_move"] not in by_key:
                    raise ValueError(f"Invalid Jass move or consumed budget for {fen} at {budget}")
                action = by_key[record["best_move"]]
                values = [regret(max(scored[fen].values()), scored[fen][action]) for scored in scores]
                if (values[0]["ordinary_regret_centimen"] != record["ordinary_regret_centimen"]
                        or scores[0][fen][action] != record["scan_centimen"]):
                    raise ValueError(f"Jass receipt disagrees with the depth-12 reference for {fen}")
                arms[arm] = values
            pair["jass"][budget] = arms
        pairs.append(pair)
    return pairs


def distribution(values):
    return {
        "ordinary": len(values), "mean_centimen": fmean(values) if values else None,
        "median_centimen": median(values) if values else None,
        "max_centimen": max(values, default=None), "min_centimen": min(values, default=None),
        "at_least_50": sum(value >= 50 for value in values),
    }


def game_bootstrap(observations):
    """Weight target games equally and resample within each event."""
    games = defaultdict(lambda: defaultdict(list))
    for event, game, value in observations:
        games[event][game].append(value)
    strata = [[fmean(samples) for samples in group.values()] for group in games.values()]
    count = sum(map(len, strata))
    if count < 2:
        return {"games": count, "mean_centimen": fmean(strata[0]) if count else None, "ci95": None}
    rng = random.Random(20261112)
    samples = [fmean(value for stratum in strata for value in rng.choices(stratum, k=len(stratum)))
               for _ in range(10_000)]
    cuts = quantiles(samples, n=1000, method="inclusive")
    return {"games": count, "mean_centimen": fmean(value for stratum in strata for value in stratum),
            "ci95": [cuts[24], cuts[974]]}


def compare_costs(rows):
    """Summarize two matched depth measurements; nulls are categorical scores."""
    result = {}
    for index, depth in enumerate(DEPTHS):
        values = [(event, game, pair[index]) for event, game, pair in rows if pair[index] is not None]
        result[str(depth)] = {**distribution([value for _, _, value in values]),
                              "game_bootstrap": game_bootstrap(values)}
    matched = [(event, game, a, b) for event, game, (a, b) in rows if a is not None and b is not None]
    result["matched_ordinary"] = len(matched)
    result["sign_changes"] = sum((a > 0) - (a < 0) != (b > 0) - (b < 0) for _, _, a, b in matched)
    result["opposite_signs"] = sum(a * b < 0 for _, _, a, b in matched)
    result["at_least_50_both"] = sum(a >= 50 and b >= 50 for _, _, a, b in matched)
    result["change_16_minus_12"] = game_bootstrap(
        (event, game, b - a) for event, game, a, b in matched
    )
    return result


def summarize_regrets(rows):
    result = compare_costs([
        (event, game, [value["ordinary_regret_centimen"] for value in pair])
        for event, game, pair in rows
    ])
    for index, depth in enumerate(DEPTHS):
        values = [pair[index] for _, _, pair in rows]
        result[str(depth)].update({
            "covered": sum(value["covered"] for value in values),
            "category_switches": dict(Counter(
                f"{value['best_category']}->{value['candidate_category']}" for value in values
                if value["best_category"] != value["candidate_category"]
            )),
        })
    result["coverage_agreement"] = sum(a["covered"] == b["covered"] for _, _, (a, b) in rows)
    return result


def summarize(events):
    rows = [(event, row) for event, pairs in events.items() for row in pairs]
    scan = {
        "disjoint_12": sum(row["scan"][0]["disjoint"] for _, row in rows),
        "disjoint_16": sum(row["scan"][1]["disjoint"] for _, row in rows),
        "disjoint_both": sum(all(value["disjoint"] for value in row["scan"]) for _, row in rows),
        **{f"same_optimal_{side}_set": sum(row["scan"][0][f"optimal_{side}"]
                                          == row["scan"][1][f"optimal_{side}"] for _, row in rows)
           for side in ("source", "target")},
    }
    for k in (1, 3):
        scan[f"top{k}"] = summarize_regrets([
            (event, row["game"], [value[f"top{k}"] for value in row["scan"]]) for event, row in rows
        ])
    jass = {}
    for budget in sorted(rows[0][1]["jass"]):
        by_arm = {
            arm: [(event, row["game"], row["jass"][budget][arm]) for event, row in rows]
            for arm in sorted(ARMS)
        }
        jass[budget] = {"arms": {arm: summarize_regrets(values) for arm, values in by_arm.items()},
                        "paired_deltas": {}}
        for control in ("canonical", "native"):
            paired = []
            for (event, game, transfer), (_, _, witness) in zip(by_arm["transfer"], by_arm[control], strict=True):
                values = []
                for a, b in zip(transfer, witness, strict=True):
                    a, b = a["ordinary_regret_centimen"], b["ordinary_regret_centimen"]
                    values.append(a - b if a is not None and b is not None else None)
                paired.append((event, game, values))
            jass[budget]["paired_deltas"][f"transfer_minus_{control}"] = compare_costs(paired)
    return {"targets": len(rows), "excluded": 0, "scan": scan, "jass": jass}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("provenance", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text())
    events = {}
    seen_targets = set()
    for event, cohort in sorted(provenance["cohorts"].items()):
        inputs = cohort["inputs"]
        manifest, old, receipts, build = (read_input(inputs[key])
                                          for key in ("manifest", "reference12", "receipts", "build"))
        cohort_hash = inputs["manifest"]["content_sha256"]
        if (build["cohort_sha256"] != cohort_hash
                or build["scan_reference_sha256"] != inputs["reference12"]["content_sha256"]
                or build["settings"] != manifest["engine"] or len(manifest["targets"]) != cohort["targets"]):
            raise ValueError(f"Archived build and cohort provenance disagree for {event}")
        new = read_input(cohort["reference16"])
        events[event] = compare_event(manifest, old, new, receipts, provenance["scan_sha256"], cohort_hash)
        target_fens = {pair["target_fen"] for pair in events[event]}
        if seen_targets & target_fens:
            raise ValueError(f"Targets overlap an earlier cohort: {event}")
        seen_targets.update(target_fens)
    report = {"depths": DEPTHS, "overall": summarize(events),
              "cohorts": {event: summarize({event: pairs}) for event, pairs in events.items()},
              "pairs": events}
    args.output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
