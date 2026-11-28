"""Score all legal actions on the already frozen Jass source and target FENs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.best_move_audit import Scan, compare_scores
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.successor_audit import _action_key
from research.mtdp.top_k_transfer import _action

SCAN_EVAL_SHA256 = "0e7161c38af605f5e367f3f8fe17525d1c40db722714c68921971b386e58abba"
SCAN_INI_SHA256 = "dc201a7debaf98bb869fb3d6b641adb219df71b0ea22004b2d9b6f51cdb69538"


def score_manifest(manifest, engine, scan, *, role=None):
    if manifest["schema"] != "mtdp-jass-cohort-v1":
        raise ValueError("Expected a frozen Jass cohort")
    if role not in (None, "source", "target"):
        raise ValueError(f"Unexpected scoring role: {role}")
    fen_fields = ("source_fen", "target_fen") if role is None else (f"{role}_fen",)
    expected_actions = {}
    for row in manifest["targets"]:
        actions = tuple(_action(move) for move in row["legal_moves"])
        for field in fen_fields:
            fen = row[field]
            if expected_actions.setdefault(fen, actions) != actions:
                raise ValueError(f"Inconsistent frozen action set for {fen}")

    scores = {}
    for fen, actions in sorted(expected_actions.items()):
        state = parse_fen(fen)
        legal = engine.legal_moves(state)
        moves = {_action_key(move): move for move in legal}
        if tuple(sorted(moves)) != actions or len(moves) != len(legal):
            raise ValueError(f"Legal actions changed for {fen}")
        scores[fen] = {}
        for action in actions:
            successor = engine.apply_move(state, moves[action])
            try:
                scores[fen][action] = -scan.score(successor) if engine.legal_moves(successor) else 10000
            except RuntimeError as exc:
                raise RuntimeError(f"Scan failed for {fen}, action {action}: {exc}") from exc

    report = {
        "action_scores_centimen": {
            fen: [{"action": action, "score": score} for action, score in moves.items()]
            for fen, moves in scores.items()
        },
    }
    if role is None:
        report["transfers"] = []
        for row in manifest["targets"]:
            source, target = row["source_fen"], row["target_fen"]
            transfer = compare_scores(scores[source], scores[target])
            report["transfers"].append({"source_fen": source, "target_fen": target, **transfer})
    else:
        report["role"] = role
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--scan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--depth", type=int, help="Override depth for a sensitivity study.")
    parser.add_argument("--role", choices=("source", "target"),
                        help="Score only one side of the frozen pairs.")
    args = parser.parse_args()
    if args.depth is not None and args.depth < 1:
        parser.error("--depth must be positive")
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    settings = manifest["engine"]
    binary_sha256 = hashlib.sha256(args.scan.read_bytes()).hexdigest()
    if binary_sha256 != settings["scan_binary_sha256"]:
        parser.error("Scan binary does not match the frozen SHA-256")
    scan_dir = args.scan.resolve().parent
    eval_sha256 = hashlib.sha256((scan_dir / "data" / "eval").read_bytes()).hexdigest()
    ini_sha256 = hashlib.sha256((scan_dir / "scan.ini").read_bytes()).hexdigest()
    if eval_sha256 != SCAN_EVAL_SHA256 or ini_sha256 != SCAN_INI_SHA256:
        parser.error("Scan evaluation data or configuration differs from the pinned checkout")
    depth = settings["scan_successor_depth"] if args.depth is None else args.depth
    with Scan(args.scan, depth=depth) as scan:
        report = score_manifest(manifest, create_engine(), scan, role=args.role)
    report.update({
        "schema": "mtdp-jass-scan-reference-v1",
        "cohort_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "scan_binary_sha256": binary_sha256,
        "scan_eval_sha256": eval_sha256,
        "scan_successor_depth": depth,
    })
    args.output.write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
