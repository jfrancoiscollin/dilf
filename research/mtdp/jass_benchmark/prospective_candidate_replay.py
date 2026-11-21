"""Pre-score independent tournament replay and historical overlap gate.

No Scan scores, archived outcomes, or Jass winners may enter this module.
A passing report is NOT a scientific freeze until chronology and pinned
Jass catalogue checks are separately satisfied.
"""

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from research.mtdp.best_move_audit import load_positions
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.geometry_ablation import (
    enumerate_occupancy_matches, occupancy_catalogue,
)
from research.mtdp.pdn import read_games

EXPECTED_EVENT = "fFgE7oED"
EXPECTED_PDN_SHA256 = "916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2"
PROTOCOL = "research/mtdp/jass_benchmark/spatial-jass/replication/TOTAL_BUDGET_TIEBREAK_PROTOCOL.md"
PREVIOUS = "research/mtdp/jass_benchmark/spatial-jass/replication/CARZrQpl/provenance.json"
BASELINE = "data/exports/pcblues/pcblues_games.pdn"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def public_ids(path: Path) -> list[str]:
    ids = []
    for game in read_games(path):
        site = urlsplit(game.tags.get("Site", ""))
        value = site.path.lstrip("/").split("/")[0]
        if site.hostname != "lidraughts.org" or len(value) != 8 or not value.isalnum():
            raise ValueError("PDN missing a unique Lidraughts game Site ID")
        ids.append(value)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Missing or repeated public Lidraughts game IDs")
    return ids


def prior_rows(document: object) -> set[str]:
    if isinstance(document, dict):
        document = document.get("targets")
    if not isinstance(document, list):
        raise ValueError("Historical FEN manifest is not a list or targets catalogue")
    out = set()
    for row in document:
        if not isinstance(row, dict):
            raise ValueError("Invalid historical FEN row")
        fen = row.get("fen", row.get("target_fen"))
        if not isinstance(fen, str) or not fen.startswith(("B:", "W:")):
            raise ValueError("Missing historical board FEN")
        out.add(fen)
    return out


def validated_archive_fens(root: Path, previous: dict) -> tuple[set[str], dict]:
    inventory = dict(previous["prior_manifests"])
    for entry in previous["eligible_shards"]:
        path = entry["path"]
        if path in inventory and inventory[path] != entry["stored_sha256"]:
            raise ValueError("Conflicting historical shard digest")
        inventory[path] = entry["stored_sha256"]
    excluded = set()
    for name, expected in sorted(inventory.items()):
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe historical archive path")
        raw = (root / rel).read_bytes()
        if digest(raw) != expected:
            raise ValueError(f"Historical FEN archive SHA256 mismatch: {name}")
        payload = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
        excluded.update(prior_rows(payload))
    if len(inventory) < 200 or not excluded:
        raise ValueError("Incomplete previous-position freeze inventory")
    return excluded, {"archived_files": len(inventory), "excluded_fens": len(excluded)}


def checked_history(root: Path, history: Path, previous: dict,
                    candidate_ids: set[str]) -> dict:
    records = [*previous["inputs"]["exclusions"], *previous["inputs"]["event"]]
    old_ids = set()
    for record in records:
        name, expected = record["file"], record["sha256"]
        if not name.startswith("mtdp-lidraughts-") or not name.endswith(".pdn"):
            continue  # Non-Lidraughts opening inputs have no public IDs.
        rel = Path(name)
        if rel.name != name:
            raise ValueError("Unsafe prior public export name")
        file = history / rel
        raw = file.read_bytes()
        if digest(raw) != expected:
            raise ValueError(f"Earlier tournament export SHA256 mismatch: {name}")
        ids = public_ids(file)
        if len(ids) != record["games"]:
            raise ValueError("Historical public game count differs from sealed provenance")
        if old_ids.intersection(ids):
            raise ValueError("Overlapping public game IDs inside the historical corpus")
        old_ids.update(ids)
    if len(records) < 20 or len(old_ids) < 1000:
        raise ValueError("Historical game exclusion corpus incomplete")
    overlap = old_ids & candidate_ids
    if overlap:
        raise ValueError(f"Candidate repeats previously used public games: {sorted(overlap)[:5]}")
    return {"previous_tournament_exports": sum(
        r["file"].startswith("mtdp-lidraughts-") for r in records
    ), "previous_public_games": len(old_ids),
            "candidate_duplicate_public_game_ids": 0}



def select_population(source_states, first_ply, target_states, target_games, overlap, engine):
    """The registered L/LCB selection, shared without changing its ordering."""
    excluded_source = set(source_states)
    novel = sorted(set(target_states) - overlap - excluded_source)
    index = defaultdict(list)
    for fen, state in source_states.items():
        catalogue, _ = occupancy_catalogue(state, engine)
        if catalogue is None:
            continue
        legal, signature = catalogue
        game = min(first_ply[fen])
        index[(signature[0], legal)].append(
            ((game, min(first_ply[fen][game]), fen), signature)
        )
    category = Counter()
    selection = []
    for fen in novel:
        catalogue, status = occupancy_catalogue(target_states[fen], engine)
        category[status] += 1
        if catalogue is None:
            continue
        legal, signature = catalogue
        matches = enumerate_occupancy_matches(index, catalogue)
        if not matches["L"] or not matches["LCB"]:
            continue
        selection.append({
            "fen": fen,
            "games": sorted(target_games[fen]),
            "legal": [
                [list(route), list(captures), bool(is_capture)]
                for route, captures, is_capture in legal
            ],
            "source_fens": {
                arm: matches[arm][0][2] for arm in ("L", "LCB")
            },
            "source_games": {
                arm: matches[arm][0][0] for arm in ("L", "LCB")
            },
        })
    return selection, category, novel


def audit(root: Path, pdn: Path, history: Path) -> dict:
    previous = json.loads((root / PREVIOUS).read_bytes())
    if previous.get("event", {}).get("id") != "CARZrQpl":
        raise ValueError("Previous latest fixed tournament unexpectedly changed")
    payload = pdn.read_bytes()
    if digest(payload) != EXPECTED_PDN_SHA256:
        raise ValueError("Candidate PDN does not match two independent frozen downloads")
    if pdn.name != f"mtdp-lidraughts-{EXPECTED_EVENT}.pdn":
        raise ValueError("Prospective PDN filename changed")
    ids = set(public_ids(pdn))
    overlap, archival = validated_archive_fens(root, previous)
    independence = checked_history(root, history, previous, ids)
    base = root / BASELINE
    if digest(base.read_bytes()) != previous["inputs"]["baseline"][0]["sha256"]:
        raise ValueError("PC Blues baseline changed")

    engine = create_engine()
    first_ply = {}
    source_states, _, base_record = load_positions(
        [base], engine, set(), plies_by_game=first_ply,
    )
    if (base_record[0]["accepted"] != 26 or base_record[0]["rejected"]
            or base_record[0]["duplicates"]):
        raise ValueError("PC Blues FMJD baseline no longer reproduces")
    replay_audit = {}
    target_states, target_games, target_record = load_positions(
        [pdn], engine, set(), game_audit=replay_audit,
    )
    record = target_record[0]
    if record["accepted"] == 0 or record["games"] != len(ids):
        raise ValueError("Prospective game replay yielded no validated games")
    if len(replay_audit) != record["games"]:
        raise ValueError("FMJD replay did not audit every original public game")
    excluded_source = set(source_states)
    selection, category, novel = select_population(
        source_states, first_ply, target_states, target_games, overlap, engine,
    )
    return {
        "schema": "mtdp-preregistered-candidate-fmjd-replay-audit-v1",
        "scope": "before_scan_scores_no_scientific_freeze_chronology_not_proven",
        "candidate": EXPECTED_EVENT,
        "candidate_pdn_sha256": EXPECTED_PDN_SHA256,
        "protocol_sha256": digest((root / PROTOCOL).read_bytes()),
        "previous_provenance_sha256": digest((root / PREVIOUS).read_bytes()),
        "archive": archival,
        "independence": independence,
        "replay": {
            "games": record["games"],
            "accepted": record["accepted"],
            "duplicate_trajectories": record["duplicates"],
            "quarantined_games": record["rejected"],
            "distinct_replayed_positions": len(target_states),
            "novel_positions": len(novel),
            "candidate_pdn_positions_overlapping_previous": len(set(target_states) & overlap),
            "candidate_pdn_positions_overlapping_baseline": len(set(target_states) & excluded_source),
            "position_categories": dict(sorted(category.items())),
        },
        "common_L_LCB_targets": len(selection),
        "candidate_targets": selection,
        "game_audit": replay_audit,
        "next_gate": "chronological_selection_then_pinned_Jass_legal_catalogue_then_publish_scoring_freeze",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--pdn", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.pdn, args.history)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "scope", "candidate", "archive", "independence", "replay",
        "common_L_LCB_targets", "next_gate",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
