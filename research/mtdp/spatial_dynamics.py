"""Reproducible within-game spatial dynamics, not a strategic-value estimator.

Only adjacent plies of the same validated game are compared. No cross-game
transitions, result labels, or causal claims are permitted.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from research.mtdp.summary import load_jsonl

_FIELDS = (
    "center_core_white", "center_core_black",
    "center_extended_white", "center_extended_black",
    "adjacency_edges_white", "adjacency_edges_black",
    "occupied_squares", "material_balance",
)


def analyze_dynamics(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Audit repeated positions and measured changes along game trajectories."""
    games: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if row.get("source") != "pcblues_game_pdn":
            raise ValueError("Only validated pcblues_game_pdn trajectory rows are accepted")
        metadata = row["metadata"]
        if metadata.get("king_detection_verified") is not True:
            raise ValueError("Unverified king status in trajectory")
        games[row["source_id"]].append(row)

    total_transitions = 0
    repeats = 0
    unchanged = 0
    field_changes: Counter[str] = Counter()
    delta_abs: dict[str, list[float]] = {field: [] for field in _FIELDS}
    game_reports: list[dict[str, Any]] = []
    for game_id, rows in sorted(games.items()):
        rows.sort(key=lambda row: row["metadata"]["ply"])
        plies = [row["metadata"]["ply"] for row in rows]
        if plies != list(range(len(plies))):
            raise ValueError(f"{game_id}: non-contiguous or duplicated plies")
        seen: set[str] = set()
        game_repeats = 0
        game_unchanged = 0
        for index, row in enumerate(rows):
            fingerprint = row["position_hash"]
            if fingerprint in seen:
                game_repeats += 1
            seen.add(fingerprint)
            if index == 0:
                continue
            before = rows[index - 1]["metrics"]
            after = row["metrics"]
            changes = [field for field in _FIELDS if before[field] != after[field]]
            if not changes:
                game_unchanged += 1
            for field in _FIELDS:
                delta_abs[field].append(abs(float(after[field]) - float(before[field])))
                if field in changes:
                    field_changes[field] += 1
        transitions = max(0, len(rows) - 1)
        total_transitions += transitions
        repeats += game_repeats
        unchanged += game_unchanged
        game_reports.append({
            "game_id": game_id,
            "positions": len(rows),
            "transitions": transitions,
            "revisited_exact_positions": game_repeats,
            "unchanged_descriptors_transitions": game_unchanged,
        })

    return {
        "schema_version": "mtdp-spatial-dynamics-v1",
        "games": len(games),
        "positions": sum(len(rows) for rows in games.values()),
        "transitions": total_transitions,
        "revisited_exact_positions_within_games": repeats,
        "unchanged_descriptors_transitions": unchanged,
        "descriptor_change_counts": dict(sorted(field_changes.items())),
        "mean_absolute_ply_change": {
            field: mean(values) if values else None
            for field, values in delta_abs.items()
        },
        "per_game": game_reports,
        "interpretation": (
            "Descriptive adjacent-ply statistics only. Descriptor equality does "
            "not imply strategic equivalence; within-game repeats are not "
            "independent observations. No performance or causal claims."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze validated MTDP spatial trajectories")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze_dynamics(load_jsonl(args.input))
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
