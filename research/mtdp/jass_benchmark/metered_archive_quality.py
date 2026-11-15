"""Retrospective Scan-16 quality audit of the REAL equal-node MTDP receipts.

Use ONLY archived, fully pre-existing target references AFTER each engine
decision has already been recorded. This is post-hoc mechanism diagnosis,
NEVER a new held-out preregistered result or an Elo claim.
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.depth_sensitivity import regret
from research.mtdp.jass_benchmark.metered_archive_gate import BUDGETS, JASS_COMMIT, sha256
from research.mtdp.jass_benchmark.spatial_replication import read_scan_scores
from research.mtdp.top_k_transfer import _action

EVENTS = {
    "uG0fGZzB": 25, "l45uk39x": 12, "GYEtKzUg": 55,
    "MtDQWBNR": 33, "CARZrQpl": 348,
}
SCHEMA = "mtdp-metered-archive-retrospective-quality-v1"


def game_cluster_interval(observations: list[tuple[str, str, float]]) -> dict:
    """Stratify by archived event and resample whole target-game clusters."""
    if not observations:
        return {"games": 0, "ci95": None}
    clusters: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for event, game, value in observations:
        clusters[event][game].append(value)
    strata = [
        [(sum(vals), len(vals)) for _, vals in sorted(games.items())]
        for _, games in sorted(clusters.items())
    ]
    games = sum(len(group) for group in strata)
    if games < 2:
        return {"games": games, "ci95": None}
    rng = random.Random(20261115)
    distribution = []
    for _ in range(5000):
        draws = [
            cluster for group in strata for cluster in rng.choices(group, k=len(group))
        ]
        distribution.append(sum(total for total, _ in draws) / sum(n for _, n in draws))
    distribution.sort()
    return {"games": games, "ci95": [
        distribution[int((len(distribution) - 1) * 0.025)],
        distribution[int((len(distribution) - 1) * 0.975)],
    ]}


def analyze(receipts_root: Path, replication: Path) -> dict:
    frozen = json.loads((replication / "frozen-cohort.json").read_bytes())
    entries = {row["event"]: row for row in frozen["arenas"]}
    if (set(entries) != set(EVENTS)
            or any(entries[event]["matched"] != count for event, count in EVENTS.items())):
        raise ValueError("Unexpected frozen cohort catalogue")

    scores_by_event = {}
    manifests = {}
    for event in EVENTS:
        directory = replication / event
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        provenance = json.loads((directory / "provenance.json").read_bytes())
        _, scores = read_scan_scores(directory, provenance, manifest)
        if sha256(manifest_path) != entries[event]["manifest_sha256"]:
            raise ValueError("Frozen arena manifest hash mismatch")
        manifests[event] = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
        scores_by_event[event] = scores["target"]

    budget_reports = {}
    population = None
    across_budget = {}
    for budget in BUDGETS:
        items, delta_vs_native, delta_vs_lcb, changes = [], [], [], []
        reasons = Counter()
        expected_identities = set()
        for event, count in EVENTS.items():
            path = receipts_root / str(budget) / (event + ".json")
            packet = json.loads(path.read_bytes())
            if (packet.get("schema") != "mtdp-real-equal-compute-archive-engineering-gate-v1"
                    or packet.get("scope") != "archived_cohort_technical_validation_not_independent_strength_evidence"
                    or packet.get("event") != event or packet.get("budget") != budget
                    or not packet.get("full_arena") or packet.get("examined_positions") != count
                    or not packet.get("summary", {}).get("all_paired_comparable")
                    or packet.get("fingerprints", {}).get("jass_commit") != JASS_COMMIT
                    or packet["fingerprints"]["manifest_sha256"] != entries[event]["manifest_sha256"]
                    or packet["fingerprints"]["source_sha256"] != sha256(replication / event / "source.json")
                    or len(packet["positions"]) != count):
                raise ValueError("Archived receipt identity or provenance mismatch")

            for row in packet["positions"]:
                fen = row["fen"]
                identity = (event, fen)
                if identity in expected_identities or fen not in manifests[event]:
                    raise ValueError("Duplicate or unknown archive engineering position")
                expected_identities.add(identity)
                frozen_target = manifests[event][fen]
                if (row["budget"] != budget or row["event"] != event
                        or row["games"] != frozen_target["target_games"]
                        or not row["paired_comparable"]
                        or row["verification_nodes"] + row["main_nodes"] != budget
                        or row["verification_nodes"] > budget // 10
                        or any(row[arm]["nodes"] + (
                            0 if arm != "control_main" else row["verification_nodes"]
                        ) != budget for arm in (
                            "control_main", "native_baseline", "lcb_baseline"
                        ))):
                    raise ValueError("Mismatch in real engine receipts or total budget")

                by_key = {move["jass_key"]: _action(move)
                          for move in frozen_target["legal_moves"]}
                scored = scores_by_event[event][fen]
                if len(by_key) != len(scored) or set(by_key.values()) != set(scored):
                    raise ValueError("Scan target actions differ from frozen legal keys")
                best = max(scored.values())
                arms = {}
                for label, receipt in (
                    ("control", row["control_main"]), ("native", row["native_baseline"]),
                    ("lcb", row["lcb_baseline"]),
                ):
                    move = receipt["best_move"]
                    if move not in by_key:
                        raise ValueError("Scored move not legal in frozen target")
                    score = scored[by_key[move]]
                    arms[label] = {"move": move, "scan16_score": score,
                                   **regret(best, score)}
                game = min(row["games"])
                for comparator, output in (
                    ("native", delta_vs_native), ("lcb", delta_vs_lcb),
                ):
                    a = arms["control"]["ordinary_regret_centimen"]
                    b = arms[comparator]["ordinary_regret_centimen"]
                    if a is not None and b is not None:
                        output.append((event, game, a - b))
                changed = arms["control"]["move"] != arms["native"]["move"]
                if changed:
                    changes.append({
                        "event": event, "fen": fen, "game": game,
                        "budget": budget, "decision_reason": row["decision_reason"],
                        "intervention": row["intervention"],
                        "verification_nodes": row["verification_nodes"],
                        "scan16_best": best, "control": arms["control"],
                        "native": arms["native"], "lcb": arms["lcb"],
                    })
                items.append({
                    "event": event, "fen": fen, "budget": budget,
                    "verification_nodes": row["verification_nodes"],
                    "intervention": row["intervention"],
                    "reason": row["decision_reason"], "arms": arms,
                })
                reasons[row["decision_reason"]] += 1
        if len(expected_identities) != 473:
            raise ValueError("Frozen cohort not fully reproduced")
        if population is not None and expected_identities != population:
            raise ValueError("Frozen population differs between node budgets")
        population = expected_identities
        across_budget[budget] = items
        def difference(values):
            ds = [v for _, _, v in values]
            return {
                "ordinary_pairs": len(ds),
                "mean_centimen": fmean(ds) if ds else None,
                "positive_control_worse": sum(v > 0 for v in ds),
                "negative_control_better": sum(v < 0 for v in ds),
                "equal": sum(v == 0 for v in ds),
                "whole_game_cluster_bootstrap": game_cluster_interval(values),
            }

        budget_reports[str(budget)] = {
            "positions": len(items),
            "mean_verification_nodes": fmean(r["verification_nodes"] for r in items),
            "max_verification_nodes": max(r["verification_nodes"] for r in items),
            "verification_budget_fraction": fmean(
                r["verification_nodes"] / budget for r in items),
            "verified_interventions": sum(r["intervention"] is not None for r in items),
            "decision_reasons": dict(sorted(reasons.items())),
            "agreement_with_native": sum(
                r["arms"]["control"]["move"] == r["arms"]["native"]["move"]
                for r in items),
            "agreement_lcb_with_native": sum(
                r["arms"]["lcb"]["move"] == r["arms"]["native"]["move"]
                for r in items),
            "scan16_optimum_hits": {arm: sum(
                r["arms"][arm]["covered"] for r in items
            ) for arm in ("control", "native", "lcb")},
            "ordinary_regret_control_minus_native": difference(delta_vs_native),
            "ordinary_regret_control_minus_lcb": difference(delta_vs_lcb),
            "control_native_changed_cases": changes,
        }
    return {
        "schema": SCHEMA,
        "scope": "retrospective_archived_positions_not_independent_holdout_no_strength_claim",
        "frozen_arenas": list(EVENTS),
        "positions_per_budget": 473,
        "jass_commit": JASS_COMMIT,
        "budgets": budget_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--replication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.receipts, args.replication)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    for budget, cell in report["budgets"].items():
        print(json.dumps({
            "budget": int(budget),
            "positions": cell["positions"],
            "control_vs_native": cell["agreement_with_native"],
            "lcb_vs_native": cell["agreement_lcb_with_native"],
            "control_native_changed_cases": cell["control_native_changed_cases"],
            "optimum_hits": cell["scan16_optimum_hits"],
            "control_minus_native": cell["ordinary_regret_control_minus_native"],
            "verified_interventions": cell["verified_interventions"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
