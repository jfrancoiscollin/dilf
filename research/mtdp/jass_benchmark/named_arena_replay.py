"""Score-blind historical trajectory index and named-arena freeze proposal."""

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.best_move_audit import load_positions
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import compare, pinned_checkout
from research.mtdp.jass_benchmark.named_arena_inputs import (
    EVENT, PROTOCOL, REGISTRATION_SHA, check_final, registration,
)
from research.mtdp.jass_benchmark.prospective_candidate_replay import (
    BASELINE, digest, public_ids, select_population,
)
from research.mtdp.jass_cohort import ADAPTER_COMMIT, BUDGETS, JASS_COMMIT, SCAN_COMMIT, SCAN_SHA256
from research.mtdp.jass_move_mapping import map_root_moves, read_jass_catalogues
from research.mtdp.pdn import PdnReplayError, read_games, replay_game, validated_trajectory

REGISTRY_SHA = "25b3ca1a6f0a096c264c8f136135a37fd7d5bb23c04af76a39b4915a611d192e"
INDEX_SHA = "eafd1e7b1c447b69f96d307b38a1c7c0fbd8fa9dd9b68f8afe555e3faa02d1b6"
HISTORY_SUMMARY = "research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc-trajectory-index-summary.json"


def checked_registry(root, path):
    registration(root)
    raw = path.read_bytes()
    if digest(raw) != REGISTRY_SHA:
        raise ValueError("Historical registry differs from the verified input rehearsal")
    return json.loads(raw)


def checked_engine(adapter):
    pinned_checkout(adapter, ADAPTER_COMMIT)
    engine = create_engine()
    if Path(engine._rules.__file__).resolve() != (adapter / "backend/game_engine.py").resolve():
        raise ValueError("Imported FMJD engine differs from pinned checkout")
    return engine


def source_paths(root, history, reserved, adapter, registry):
    paths = []
    for row in registry["sources"]:
        name = row["file"]
        if Path(name).name != name:
            raise ValueError("Unsafe historical source name")
        path = (root / BASELINE if name == "pcblues_games.pdn" else
                reserved if name == "mtdp-lidraughts-fFgE7oED.pdn" else
                history / name if name.startswith("mtdp-lidraughts-") else
                adapter / "docs/parties" / name)
        if path.name != name or digest(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"Historical trajectory input changed: {name}")
        paths.append((path, row["games"]))
    return paths


def trajectory_fingerprint(trajectory):
    return digest("\n".join(state_to_fen(state) for _, _, state in trajectory).encode())


def token_fingerprint(game):
    start = state_to_fen(parse_fen(game.tags["FEN"])) if "FEN" in game.tags else state_to_fen(initial_state())
    return digest(json.dumps([start, [token.lower() for token in game.moves]], separators=(",", ":")).encode())


def index_games(paths, engine):
    fingerprints, confirmed_fens, audit = set(), set(), {}
    for path, expected_games in paths:
        games = read_games(path)
        if len(games) != expected_games:
            raise ValueError("Historical trajectory input game count changed")
        for game in games:
            identity = f"{path.name}:{game.index}"
            if identity in audit:
                raise ValueError("Repeated historical game identity")
            trajectory = []
            try:
                for entry in replay_game(game, engine):
                    trajectory.append(entry)
                    confirmed_fens.add(state_to_fen(entry[2]))
            except PdnReplayError as error:
                audit[identity] = {"status": "quarantined", "error": str(error),
                                   "confirmed_prefix_positions": len(trajectory)}
                continue
            fingerprint = trajectory_fingerprint(trajectory)
            audit[identity] = {"status": "duplicate" if fingerprint in fingerprints else "indexed",
                               "trajectory_sha256": fingerprint, "validated_plies": len(trajectory) - 1}
            fingerprints.add(fingerprint)
    return {"fingerprints": sorted(fingerprints), "confirmed_fens": sorted(confirmed_fens), "game_audit": audit,
            "status_counts": dict(sorted(Counter(row["status"] for row in audit.values()).items()))}


def history_index(root, registry_path, history, reserved, adapter):
    registry = checked_registry(root, registry_path)
    engine = checked_engine(adapter)
    indexed = index_games(source_paths(root, history, reserved, adapter, registry), engine)
    return {"schema": "mtdp-named-canonical-history-v1", "registry_sha256": REGISTRY_SHA,
            "adapter_commit": ADAPTER_COMMIT, "sources": registry["sources"], **indexed,
            "scope": "complete_legal_board_trajectories_only_no_ambiguous_continuations",
            "fen_scope": "all_legally_verified_prefixes_including_quarantined_games",
            "scientific_freeze": False}


def replay_candidates(pdn, engine, registry, historical_fingerprints):
    """Quarantine/exclude whole games before emitting any candidate positions."""
    games = read_games(pdn)
    ids = public_ids(pdn) if games else []
    old_ids = set(registry["public_game_ids"])
    old_tokens = set(registry["normalized_token_sequence_sha256"])
    seen, states, owners, plies, audit = set(), {}, defaultdict(set), {}, {}
    for game, public_id in zip(games, ids, strict=True):
        identity = f"{pdn.name}:{game.index}"
        row = {"public_game_id": public_id}
        audit[identity] = row
        if public_id in old_ids:
            row["status"] = "excluded_public_id"
            continue
        if token_fingerprint(game) in old_tokens:
            row["status"] = "excluded_token_sequence"
            continue
        try:
            trajectory = validated_trajectory(game, engine)
        except PdnReplayError as error:
            row.update(status="quarantined", error=str(error))
            continue
        fingerprint = trajectory_fingerprint(trajectory)
        row.update(trajectory_sha256=fingerprint, validated_plies=len(trajectory) - 1)
        if fingerprint in historical_fingerprints:
            row["status"] = "excluded_canonical_trajectory"
            continue
        if fingerprint in seen:
            row["status"] = "duplicate_within_event"
            continue
        seen.add(fingerprint)
        row["status"] = "accepted"
        for ply, _, state in trajectory:
            fen = state_to_fen(state)
            states[fen] = state
            owners[fen].add(identity)
            plies.setdefault(fen, {}).setdefault(identity, []).append(ply)
    return states, owners, plies, audit


def checked_history_index(root, path, registry):
    raw = path.read_bytes()
    expected = json.loads((root / HISTORY_SUMMARY).read_bytes())["index_sha256"]
    if digest(raw) != INDEX_SHA or expected != INDEX_SHA:
        raise ValueError("Canonical historical trajectory index changed")
    indexed = json.loads(raw)
    if (indexed["registry_sha256"] != REGISTRY_SHA or indexed["adapter_commit"] != ADAPTER_COMMIT
            or indexed["sources"] != registry["sources"]):
        raise ValueError("Canonical history index has different provenance")
    return indexed


def benchmark_manifest(rows, engine, executable):
    fens = sorted({row["fen"] for row in rows} | {
        fen for row in rows for fen in row["source_fens"].values()
    })
    catalogues = read_jass_catalogues(executable, map(parse_fen, fens))
    receipt = compare(rows, engine, catalogues)
    mappings = {fen: map_root_moves(engine.legal_moves(parse_fen(fen)), catalogue)
                for fen, catalogue in zip(fens, catalogues, strict=True)}
    targets = []
    for row in rows:
        targets.append({
            "target_fen": row["fen"], "target_games": row["games"],
            "source_fen": row["source_fens"]["L"], "source_game": row["source_games"]["L"],
            "source_fens": row["source_fens"], "source_games": row["source_games"],
            "legal_moves": [{"action": [list(a[0]), list(a[1]), a[2]], "jass_key": key}
                            for a, key in sorted(mappings[row["fen"]].items())],
        })
    return targets, receipt


def proposal(root, metadata, first, repeat, download_log, registry_path, index_path,
             adapter, jass, executable):
    # This production entry point has no clock override. It runs before any target replay.
    inputs = check_final(root, metadata, first, repeat, download_log)
    if first.name != f"mtdp-lidraughts-{EVENT}.pdn":
        raise ValueError("Named event PDN filename changed")
    implementation_commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    pinned_checkout(root, implementation_commit)
    registered = registration(root)
    registry = checked_registry(root, registry_path)
    indexed = checked_history_index(root, index_path, registry)
    engine = checked_engine(adapter)
    pinned_checkout(jass, JASS_COMMIT)
    base = root / BASELINE
    expected_base = next(row for row in registry["sources"] if row["file"] == base.name)
    if digest(base.read_bytes()) != expected_base["sha256"]:
        raise ValueError("PC Blues baseline changed")
    source_plies = {}
    source_states, _, source_records = load_positions([base], engine, set(), plies_by_game=source_plies)
    record, = source_records
    if record["accepted"] != 26 or record["rejected"] or record["duplicates"]:
        raise ValueError("PC Blues baseline no longer reproduces")
    states, owners, plies, game_audit = replay_candidates(first, engine, registry, set(indexed["fingerprints"]))
    rows, categories, novel = select_population(
        source_states, source_plies, states, owners, set(registry["confirmed_fens"]) | set(indexed["confirmed_fens"]), engine,
    )
    targets, catalogue = benchmark_manifest(rows, engine, executable)
    pairs = [{"source_fen": source, "target_fen": row["target_fen"], "legal_moves": row["legal_moves"]}
             for row in targets for source in sorted(set(row["source_fens"].values()))]
    implementation = {str(path.relative_to(root)): digest(path.read_bytes()) for path in (
        root / "research/mtdp/jass_benchmark/named_arena_replay.py",
        root / "research/mtdp/jass_benchmark/named_arena_inputs.py",
        root / "research/mtdp/jass_benchmark/prospective_candidate_replay.py",
        root / "research/mtdp/jass_benchmark/geometry_ablation.py",
        root / "research/mtdp/jass_benchmark/candidate_jass_catalogue.py",
        root / "research/mtdp/jass_move_mapping.py",
        root / "research/mtdp/draught_master_adapter.py",
        root / "research/mtdp/pdn.py",
        root / "research/mtdp/jass_preflight/legal_catalogue.cpp",
        root / "research/mtdp/jass_preflight/move_key.hpp",
    )}
    return {"schema": "mtdp-named-arena-freeze-proposal-v1", "event": EVENT,
            "scope": "pre_score_proposal_publish_immutable_manifest_before_scoring",
            "scientific_freeze": False, "input_check": inputs,
            "registry_sha256": REGISTRY_SHA, "history_index_sha256": digest(index_path.read_bytes()),
            "implementation_sha256": implementation, "implementation_commit": implementation_commit,
            "engine": {"jass_commit": JASS_COMMIT, "adapter_commit": ADAPTER_COMMIT,
                       "draught_master_commit": ADAPTER_COMMIT,
                       "jass_catalogue_sha256": digest(executable.read_bytes()),
                       "jass_node_budgets": list(BUDGETS), "scan_commit": SCAN_COMMIT,
                       "scan_sha256": SCAN_SHA256, "scan_binary_sha256": SCAN_SHA256,
                       "scan_successor_depth": 12, "target_scan_successor_depth": 16,
                       "source_scan_successor_depth": 12},
            "selection": {"arm_order_seed": 20261113},
            "analysis": {key: registered[key] for key in (
                "primary_total_node_budget", "bootstrap_resamples", "bootstrap_seed",
                "bootstrap_unit", "verification_fraction")},
            "game_status_counts": dict(sorted(Counter(row["status"] for row in game_audit.values()).items())),
            "game_audit": game_audit, "novel_positions": len(novel),
            "position_categories": dict(sorted(categories.items())),
            "candidate_targets": rows, "benchmark_targets": targets, "targets": pairs,
            "eligible": categories.get("eligible", 0), "jass_catalogue": catalogue,
            "target_plies": {row["fen"]: plies[row["fen"]] for row in rows},
            "next_gate": "two_hash_seed_runs_then_publish_freeze_commit_before_any_scores",
            "limitations": indexed["scope"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("history", "proposal"))
    for name in ("root", "registry", "adapter", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("history", "reserved", "metadata", "first", "repeat", "download-log", "index", "jass", "executable"):
        parser.add_argument(f"--{name}", type=Path)
    args = parser.parse_args()
    required = ("history", "reserved") if args.mode == "history" else (
        "metadata", "first", "repeat", "download_log", "index", "jass", "executable")
    if any(getattr(args, name) is None for name in required):
        parser.error(f"Mode {args.mode} requires {required}")
    result = (history_index(args.root, args.registry, args.history, args.reserved, args.adapter)
              if args.mode == "history" else proposal(
                  args.root, args.metadata, args.first, args.repeat, args.download_log,
                  args.registry, args.index, args.adapter, args.jass, args.executable))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("schema", "scientific_freeze")}
                     | ({"status_counts": result["status_counts"], "unique_trajectories": len(result["fingerprints"])}
                        if args.mode == "history" else {"game_status_counts": result["game_status_counts"],
                                                       "targets": len(result["benchmark_targets"])}), sort_keys=True))


if __name__ == "__main__":
    main()
