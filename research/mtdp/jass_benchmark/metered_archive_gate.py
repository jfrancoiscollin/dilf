"""Archive-only engineering gate for the live equal-node MTDP Jass control.

Reuses the five *already frozen* 2026-11-13 arenas strictly for technical
reproduction. The selector uses Scan-12 SOURCE scores for LCB prefixes only.
It never opens Scan-16 TARGET scores and never treats archived positions
as the new preregistered independent holdout.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark.depth_sensitivity import validate_reference
from research.mtdp.jass_benchmark.metered_engine_smoke import technical_smoke
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.top_k_transfer import _action

BUDGETS = (10_000, 50_000, 200_000)
JASS_COMMIT = "cfe07fce6385b980553a898e9651d53419589ebc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_frozen_arena(replication: Path, event: str) -> tuple[dict, list[dict], dict]:
    """Validate the pinned arena and its Scan-12 source ranking, never target scores."""
    cohort = json.loads((replication / "frozen-cohort.json").read_bytes())
    entries = cohort["arenas"]
    if len(entries) != 5 or sum(entry["matched"] for entry in entries) != 473:
        raise ValueError("Unexpected five-arena frozen engineering cohort")
    matches = [entry for entry in entries if entry["event"] == event]
    if len(matches) != 1:
        raise ValueError("Requested arena not present exactly once in frozen cohort")
    entry = matches[0]
    directory = replication / event
    manifest_path, provenance_path = directory / "manifest.json", directory / "provenance.json"
    source_path, diagnostic_path = directory / "source.json", directory / "source-diagnostic.json"
    if sha256(manifest_path) != entry["manifest_sha256"]:
        raise ValueError("Frozen manifest digest mismatch")
    manifest = json.loads(manifest_path.read_bytes())
    provenance = json.loads(provenance_path.read_bytes())
    diagnostic = json.loads(diagnostic_path.read_bytes())
    targets = manifest["benchmark_targets"]
    if (manifest["event"] != event or provenance["event"]["id"] != event
            or manifest["provenance_sha256"] != sha256(provenance_path)
            or manifest["engine"]["jass_commit"] != JASS_COMMIT
            or tuple(manifest["engine"]["jass_node_budgets"]) != BUDGETS
            or len(targets) != entry["matched"]
            or len({row["target_fen"] for row in targets}) != len(targets)):
        raise ValueError("Frozen arena identity, engine or target population changed")
    if (diagnostic["manifest_sha256"] != sha256(manifest_path)
            or diagnostic["source_sha256"] != sha256(source_path)
            or diagnostic["matched"] != entry["matched"]):
        raise ValueError("Frozen Scan-12 source diagnostic mismatch")
    # A source FEN must have a single unambiguous canonical action catalogue.
    expected = {}
    for row in manifest["targets"]:
        moves = row["legal_moves"]
        keys = [move["jass_key"] for move in moves]
        actions = [_action(move) for move in moves]
        if (not actions or len(set(actions)) != len(actions)
                or len(set(keys)) != len(keys)):
            raise ValueError("Ambiguous frozen source action catalogue")
        source = row["source_fen"]
        catalog = set(actions)
        if source in expected and expected[source] != catalog:
            raise ValueError("Conflicting frozen source action lists")
        expected[source] = catalog
    reference = json.loads(source_path.read_bytes())
    if reference.get("role") != "source":
        raise ValueError("Engineering gate requires Scan source, not target")
    scores = validate_reference(
        reference, expected, provenance["scan_sha256"], sha256(manifest_path), 12,
    )
    selection = []
    for row in sorted(targets, key=lambda value: value["target_fen"]):
        source = row["source_fens"]["LCB"]
        if source not in scores:
            raise ValueError("Missing frozen LCB source ranking")
        _, prefixes = candidate_lists(row["legal_moves"], scores[source])
        selection.append({
            "target_fen": row["target_fen"],
            "target_games": row["target_games"],
            "prefix": prefixes["transfer"],
            "legal_count": len(row["legal_moves"]),
        })
    return entry, selection, {
        "manifest_sha256": sha256(manifest_path),
        "source_sha256": sha256(source_path),
        "provenance_sha256": sha256(provenance_path),
    }


def run(replication: Path, event: str, budget: int,
        probe_binary: Path, main_binary: Path, *, diagnostic_limit: int | None = None) -> dict:
    if budget not in BUDGETS:
        raise ValueError("Budget must be one of the three frozen experimental budgets")
    entry, selection, fingerprints = read_frozen_arena(replication, event)
    if diagnostic_limit is not None:
        if type(diagnostic_limit) is not int or diagnostic_limit <= 0:
            raise ValueError("Invalid diagnostic position limit")
        selection = selection[:diagnostic_limit]
    receipts = []
    for item in selection:
        try:
            outcome = technical_smoke(
                probe_binary, main_binary, item["target_fen"],
                total_nodes=budget, prefix=item["prefix"],
            )
        except Exception as error:
            raise RuntimeError(
                f"Archived engineering gate halted: event={event} "
                f"budget={budget} target_fen={item['target_fen']}"
            ) from error
        if (outcome["native_legal_actions"] != item["legal_count"]
                or not outcome["paired_comparable"]
                or outcome["verification_nodes"] > budget // 10
                or outcome["verification_nodes"] + outcome["main_nodes"] != budget):
            raise ValueError("Real Jass root catalogue or total budget mismatch")
        receipts.append({
            "event": event, "fen": item["target_fen"], "games": item["target_games"],
            "budget": budget, "LCB_prefix": item["prefix"], **outcome,
        })
    reasons = Counter(row["decision_reason"] for row in receipts)
    return {
        "schema": "mtdp-real-equal-compute-archive-engineering-gate-v1",
        "scope": "archived_cohort_technical_validation_not_independent_strength_evidence",
        "event": event, "budget": budget, "positions": receipts,
        "planned_positions": entry["matched"],
        "examined_positions": len(receipts),
        "full_arena": diagnostic_limit is None,
        "fingerprints": {**fingerprints, "jass_commit": JASS_COMMIT},
        "summary": {
            "all_paired_comparable": all(row["paired_comparable"] for row in receipts),
            "total_verification_nodes": sum(row["verification_nodes"] for row in receipts),
            "mean_verification_nodes": fmean(row["verification_nodes"] for row in receipts),
            "maximum_verification_nodes": max(row["verification_nodes"] for row in receipts),
            "fraction_of_budget_spent_verifying": fmean(
                row["verification_nodes"] / budget for row in receipts
            ),
            "decision_reasons": dict(sorted(reasons.items())),
            "interventions": sum(row["intervention"] is not None for row in receipts),
            "native_matches_lcb": sum(
                row["native_baseline"]["best_move"] == row["lcb_baseline"]["best_move"]
                for row in receipts
            ),
            "control_matches_native": sum(
                row["control_main"]["best_move"] == row["native_baseline"]["best_move"]
                for row in receipts
            ),
            "control_matches_lcb": sum(
                row["control_main"]["best_move"] == row["lcb_baseline"]["best_move"]
                for row in receipts
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication", type=Path, required=True)
    parser.add_argument("--arena", required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--probe-runner", type=Path, required=True)
    parser.add_argument("--main-runner", type=Path, required=True)
    parser.add_argument("--diagnostic-limit", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.replication, args.arena, args.budget,
                 args.probe_runner, args.main_runner,
                 diagnostic_limit=args.diagnostic_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "event", "budget", "planned_positions", "examined_positions", "full_arena",
        "summary")}, sort_keys=True))


if __name__ == "__main__":
    main()
