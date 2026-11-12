"""Freeze a Jass move-ordering cohort before any Scan or Jass search."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from research.mtdp.best_move_audit import group_positions, load_positions
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_move_mapping import (
    MoveMappingError,
    map_root_moves,
    read_jass_catalogues,
)
from research.mtdp.local_neighborhood import typed_radius_two
from research.mtdp.successor_audit import _action_key

JASS_COMMIT = "cfe07fce6385b980553a898e9651d53419589ebc"
ADAPTER_COMMIT = "0e5189fbb251bf5eaf2e613d0f878bb17c740311"
SCAN_COMMIT = "7aae17e7b7bfc47744601afb1ee7655e18983ce5"
SCAN_SHA256 = "a634cbb44c9528eab277cdf6cdf8d29d506318ce5fba3f9bc69c2025b5941864"
BUDGETS = (10_000, 50_000, 200_000)


def _serialize_descriptor(descriptor):
    version, (turn, men, blockers), neighborhood = descriptor
    return {
        "version": version,
        "turn": turn,
        "men": sorted(men),
        "blockers": sorted(blockers),
        "neighborhood": neighborhood,
    }


def freeze_cohort(baseline, exclusions, holdout, engine, read_catalogues, *, record_provenance=False):
    seen = set()
    source_plies = {} if record_provenance else None
    target_plies = {} if record_provenance else None
    base, base_games, base_inputs = load_positions(
        [baseline], engine, seen, plies_by_game=source_plies
    )
    prior, _, prior_inputs = load_positions(exclusions, engine, seen)
    held, held_games, held_inputs = load_positions(
        [holdout], engine, seen, plies_by_game=target_plies
    )
    novel = {fen: state for fen, state in held.items() if fen not in base and fen not in prior}
    base_groups = group_positions(base)
    novel_groups = group_positions(novel)
    counts = Counter(dict.fromkeys((
        "quiet_candidates", "terminal", "forced_move", "no_signature_source",
        "no_exact_legal_source", "mapping_rejected", "covered",
    ), 0))
    pairs = []
    for signature, fens in novel_groups.items():
        for target in fens:
            counts["quiet_candidates"] += 1
            target_moves = engine.legal_moves(novel[target])
            if len(target_moves) < 2:
                counts["forced_move" if target_moves else "terminal"] += 1
                continue
            sources = base_groups.get(signature, ())
            if not sources:
                counts["no_signature_source"] += 1
                continue
            actions = sorted(map(_action_key, target_moves))
            matching = [
                source for source in sources
                if sorted(map(_action_key, engine.legal_moves(base[source]))) == actions
            ]
            if not matching:
                counts["no_exact_legal_source"] += 1
                continue
            # Choose once, before mapping. A rejected source is never replaced.
            source = min(matching, key=lambda fen: (min(base_games[fen]), fen))
            pairs.append((target, source))

    states = base | novel
    paired_fens = sorted({fen for pair in pairs for fen in pair})
    mappings = {}
    mapping_errors = {}
    for fen, catalogue in zip(
        paired_fens, read_catalogues(states[fen] for fen in paired_fens), strict=True
    ):
        try:
            mappings[fen] = map_root_moves(engine.legal_moves(states[fen]), catalogue)
        except MoveMappingError as error:
            mapping_errors[fen] = str(error)

    targets = []
    rejected_pairs = []
    for target, source in sorted(pairs):
        if target in mapping_errors or source in mapping_errors:
            counts["mapping_rejected"] += 1
            rejected_pairs.append({"target_fen": target, "source_fen": source})
            continue
        counts["covered"] += 1
        source_descriptor = typed_radius_two(base[source])
        target_descriptor = typed_radius_two(novel[target])
        row = {
            "target_fen": target,
            "target_games": sorted(held_games[target]),
            "source_fen": source,
            "source_games": sorted(base_games[source]),
            "source_game": min(base_games[source]),
            "same_typed_radius_two": source_descriptor == target_descriptor,
            "legal_moves": [
                {"action": action, "jass_key": key}
                for action, key in sorted(mappings[target].items())
            ],
        }
        if record_provenance:
            row.update({
                "target_plies_by_game": target_plies[target],
                "source_plies_by_game": source_plies[source],
                "target_typed_radius_two": _serialize_descriptor(target_descriptor),
                "source_typed_radius_two": _serialize_descriptor(source_descriptor),
            })
        targets.append(row)
    return {
        "schema": "mtdp-jass-cohort-v1",
        "baseline_inputs": base_inputs,
        "exclusion_inputs": prior_inputs,
        "holdout_inputs": held_inputs,
        "counts": {
            "holdout_fens": len(held),
            "overlap_baseline": len(held.keys() & base.keys()),
            "overlap_prior_only": len((held.keys() & prior.keys()) - base.keys()),
            "novel_fens": len(novel),
            "novel_non_quiet": len(novel) - counts["quiet_candidates"],
            **counts,
        },
        "selection": {
            "target_order": "lexicographic FEN; all covered targets",
            "source_order": "lexicographic minimum (PC Blues game ID, FEN)",
            "arm_order_seed": 0,
        },
        "mapping_errors": mapping_errors,
        "mapping_rejected_pairs": rejected_pairs,
        "targets": targets,
        "engine": {
            "draught_master_commit": ADAPTER_COMMIT,
            "jass_commit": JASS_COMMIT,
            "jass_evaluation": "handcrafted",
            "jass_threads": 1,
            "jass_fresh_tt_mib": 1,
            "jass_node_budgets": BUDGETS,
            "scan_commit": SCAN_COMMIT,
            "scan_binary_sha256": SCAN_SHA256,
            "scan_successor_depth": 12,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--exclude-previous", required=True, action="append", type=Path)
    parser.add_argument("--holdout", required=True, type=Path)
    parser.add_argument("--jass-catalogue", required=True, type=Path)
    parser.add_argument(
        "--record-provenance", action="store_true",
        help="Record all accepted game plies and both typed descriptors.",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = [args.baseline, *args.exclude_previous, args.holdout]
    if len({path.name for path in paths}) != len(paths):
        parser.error("PDN filenames must be distinct to identify game sources")
    manifest = freeze_cohort(
        args.baseline,
        args.exclude_previous,
        args.holdout,
        create_engine(),
        lambda states: read_jass_catalogues(args.jass_catalogue, states),
        record_provenance=args.record_provenance,
    )
    manifest["engine"]["jass_catalogue_sha256"] = hashlib.sha256(
        args.jass_catalogue.read_bytes()
    ).hexdigest()
    indent = None if args.record_provenance else 2
    args.output.write_text(json.dumps(manifest, sort_keys=True, indent=indent) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
