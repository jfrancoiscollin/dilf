"""Fail-closed, score-blind admission checks for a proposed D1 corpus.

This is a structural preflight, NOT proof of historical exclusion: callers must
supply an independently authenticated registry of forbidden aliases.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

RESERVED = frozenset({"fFgE7oED", "P1RUlfJc", "s7ahYqL4", "D9PF2OSW"})
SPLITS = frozenset({"train", "validation", "test"})


def audit(rows: list[dict], forbidden: dict) -> dict:
    """Return deterministic diagnostics; admission requires zero errors.

    Each row: tournament_id, game_id, ply, fen, split, raw_sha256,
    trajectory_sha256, canonical_sha256, event_id. Hashes must be
    independently computed upstream, not accepted as historical proof.
    """
    errors: set[str] = set()
    required = ("tournament_id", "game_id", "ply", "fen", "split",
                "raw_sha256", "trajectory_sha256", "canonical_sha256", "event_id")
    if not rows:
        errors.add("empty_corpus")
    if not isinstance(forbidden, dict) or any(
        key not in forbidden or not isinstance(forbidden[key], list)
        for key in ("game_ids", "raw_sha256", "trajectory_sha256", "canonical_sha256")
    ):
        errors.add("missing_authenticated_exclusion_registry")
        forbidden = {}
    # Malformed registry entries must never silently bypass exclusion or crash.
    for key in ("game_ids", "raw_sha256", "trajectory_sha256", "canonical_sha256"):
        entries = forbidden.get(key, [])
        if not isinstance(entries, list) or any(
            not isinstance(value, str) or not value or
            (key != "game_ids" and (len(value) != 64 or
             any(ch not in "0123456789abcdef" for ch in value)))
            for value in entries
        ):
            errors.add("invalid_exclusion_registry:" + key)
    blocked = {key: set(value for value in forbidden.get(key, [])
                        if isinstance(value, str))
               if isinstance(forbidden.get(key, []), list) else set()
               for key in ("game_ids", "raw_sha256", "trajectory_sha256", "canonical_sha256")}
    games: dict[str, set[str]] = {}
    tournaments: dict[str, set[str]] = {}
    positions: dict[str, set[str]] = {}
    raw_sources: dict[str, set[str]] = {}
    trajectories: dict[str, set[str]] = {}
    seen_ply: set[tuple[str, int]] = set()
    last_ply: dict[str, int] = {}
    game_provenance: dict[str, tuple[str, str, str, str]] = {}
    counts: Counter[str] = Counter()
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(
            key not in row or row[key] is None or row[key] == "" for key in required
        ):
            errors.add(f"row_{i}:missing_provenance")
            continue
        split, game, tournament = row["split"], row["game_id"], row["tournament_id"]
        if (not isinstance(split, str) or split not in SPLITS or
                not isinstance(game, str) or not game.strip() or
                not isinstance(tournament, str) or not tournament.strip()):
            errors.add(f"row_{i}:invalid_partition")
            continue
        if not isinstance(row["fen"], str) or not row["fen"].strip() or\
           not isinstance(row["event_id"], str) or not row["event_id"].strip():
            errors.add(f"row_{i}:invalid_provenance")
            continue
        if type(row["ply"]) is not int or row["ply"] < 0:
            errors.add(f"row_{i}:invalid_ply")
            continue
        if any(not isinstance(row[key], str) or len(row[key]) != 64 or
               any(c not in "0123456789abcdef" for c in row[key])
               for key in ("raw_sha256", "trajectory_sha256", "canonical_sha256")):
            errors.add(f"row_{i}:invalid_hash")
            continue
        if (row["event_id"] in RESERVED or tournament in RESERVED or
                game in blocked["game_ids"] or any(
            row[key] in blocked[key] for key in
            ("raw_sha256", "trajectory_sha256", "canonical_sha256")
        ):
            errors.add(f"row_{i}:reserved_or_historical_overlap")
        if (game, row["ply"]) in seen_ply:
            errors.add(f"row_{i}:duplicate_game_ply")
        seen_ply.add((game, row["ply"]))
        # Preserve source chronology before any target engine scores are attached.
        if game in last_ply and row["ply"] <= last_ply[game]:
            errors.add(f"row_{i}:non_chronological_game_ply")
        last_ply[game] = row["ply"]
        # A game identity must name one immutable source and trajectory,
        # even when every observation stays in the same partition.
        provenance = (tournament, row["event_id"], row["raw_sha256"],
                      row["trajectory_sha256"])
        previous = game_provenance.setdefault(game, provenance)
        if previous != provenance:
            errors.add(f"row_{i}:inconsistent_game_provenance")
        games.setdefault(game, set()).add(split)
        tournaments.setdefault(tournament, set()).add(split)
        positions.setdefault(row["canonical_sha256"], set()).add(split)
        raw_sources.setdefault(row["raw_sha256"], set()).add(split)
        trajectories.setdefault(row["trajectory_sha256"], set()).add(split)
        counts[split] += 1
    if any(len(s) > 1 for s in games.values()):
        errors.add("cross_split_game_leakage")
    if any(len(s) > 1 for s in positions.values()):
        errors.add("cross_split_position_leakage")
    if any(len(s) > 1 for s in raw_sources.values()):
        errors.add("cross_split_raw_source_leakage")
    if any(len(s) > 1 for s in trajectories.values()):
        errors.add("cross_split_trajectory_leakage")
    if any(len(s) > 1 for s in tournaments.values()):
        errors.add("cross_split_tournament_overlap")
    # This structural check cannot authenticate registry completeness.
    return {"admissible_structurally": not errors, "errors": sorted(errors),
            "rows_by_split": dict(sorted(counts.items())),
            "games": len(games), "tournaments": len(tournaments),
            "distinct_position_hashes": len(positions),
            "historical_exclusion_proven": False}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("exclusions", type=Path)
    args = parser.parse_args()
    raw = args.manifest.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    result = audit(rows, json.loads(args.exclusions.read_text()))
    result["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))
    if not result["admissible_structurally"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
