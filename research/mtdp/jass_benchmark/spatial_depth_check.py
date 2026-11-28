"""Rescore the frozen 50,000-node LCB move disagreements with a frozen control."""

import argparse
import json
from pathlib import Path

from research.mtdp.jass_benchmark.depth_sensitivity import regret, validate_reference
from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.multi_event_freeze import REPLICATION_PROTOCOL
from research.mtdp.jass_benchmark.multi_event_replication import score_catalogue
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_replication import read_arena, validate_cohort
from research.mtdp.top_k_transfer import _action

BUDGET = 50_000
DEPTH = 18
CONTROLS = ("L", "native")


def prepare(arenas, *, control="L"):
    arms = ("LCB", control)
    packets = [read_arena(arena) for arena in arenas]
    validate_cohort([(provenance, frozen) for provenance, frozen, _, _ in packets],
                    sha256(REPLICATION_PROTOCOL))
    targets, choices, inputs = [], {}, {}
    hashes = packets[0][0]["scan_sha256"]
    for arena, (provenance, _, _, rows) in zip(arenas, packets, strict=True):
        if provenance["scan_sha256"] != hashes:
            raise ValueError(f"Scan build differs across arenas: {arena}")
        selected = [
            row for row in rows if row["budget"] == BUDGET
            and all(arm["stop"] == "nodes" for arm in row["arms"].values())
            and row["arms"]["LCB"]["best_move"] != row["arms"][control]["best_move"]
        ]
        if not selected:
            continue
        paths = ("manifest.json", "results/target.json", "results/paired-results.jsonl.gz")
        event = provenance["event"]["id"]
        inputs[event] = {path: sha256(arena / path) for path in paths}
        manifest = json.loads((arena / "manifest.json").read_bytes())
        by_fen = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
        for row in selected:
            fen = row["target_fen"]
            targets.append(by_fen[fen])
            choices[fen] = {"arena": event, "arms": {
                arm: {key: row["arms"][arm][key] for key in (
                    "best_move", "scan_centimen", "scan_optimal", "scan_best_category",
                    "scan_chosen_category", "ordinary_regret_centimen",
                )} for arm in arms
            }}
    return {
        "schema": "mtdp-jass-cohort-v1",
        "engine": {"scan_binary_sha256": hashes["scan_linux"], "scan_successor_depth": DEPTH},
        "budget": BUDGET, "scan_sha256": hashes, "targets": targets,
        **({"control": control} if control != "L" else {}),
        "choices": choices, "inputs": inputs,
    }


def compare(manifest, reference, digest):
    if reference.get("role") != "target":
        raise ValueError("Expected a target Scan reference")
    control = manifest.get("control", "L")
    arms = ("LCB", control)
    scores = validate_reference(reference, score_catalogue(manifest, "target"),
                                manifest["scan_sha256"], digest, DEPTH)
    positions = []
    for row in manifest["targets"]:
        fen = row["target_fen"]
        choice = manifest["choices"][fen]
        keys = {move["jass_key"]: _action(move) for move in row["legal_moves"]}
        scored = scores[fen]
        best = max(scored.values())
        outcomes = {}
        for arm in arms:
            prior = choice["arms"][arm]
            move = prior["best_move"]
            value = scored[keys[move]]
            outcomes[arm] = {
                "move": move,
                "depth16": {
                    "score_centimen": prior["scan_centimen"],
                    "covered": prior["scan_optimal"],
                    "best_category": prior["scan_best_category"],
                    "candidate_category": prior["scan_chosen_category"],
                    "ordinary_regret_centimen": prior["ordinary_regret_centimen"],
                },
                "depth18": {"score_centimen": value, **regret(best, value)},
            }
        deltas = {}
        for depth in ("depth16", "depth18"):
            a, b = (outcomes[arm][depth]["ordinary_regret_centimen"] for arm in arms)
            deltas[depth] = a - b if a is not None and b is not None else None
        positions.append({"arena": choice["arena"], "fen": fen, "arms": outcomes,
                          f"lcb_minus_{control.lower()}_centimen": deltas})
    return {"budget": BUDGET, "manifest_sha256": digest, "positions": positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", action="append", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--control", choices=CONTROLS, default="L")
    args = parser.parse_args()
    if (args.reference is None) != (args.output is None):
        parser.error("--reference and --output must be supplied together")
    manifest = prepare(args.arena, control=args.control)
    if args.reference is None:
        write_json(args.manifest, manifest)
        return
    if json.loads(args.manifest.read_bytes()) != manifest:
        raise ValueError("Depth check manifest differs from archived search receipts")
    reference = json.loads(args.reference.read_bytes())
    summary = compare(manifest, reference, sha256(args.manifest))
    write_json(args.output, {**summary, "reference_sha256": sha256(args.reference)})


if __name__ == "__main__":
    main()
