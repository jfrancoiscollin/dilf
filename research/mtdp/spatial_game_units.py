"""Game-level descriptive audit of MTDP spatial dynamics reports.

Games, not individual plies, are the observational units. No significance
test or claim of independent game sampling is made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, median


def summarize(report: dict) -> dict:
    if report.get("schema_version") != "mtdp-spatial-dynamics-v1":
        raise ValueError("unsupported spatial dynamics schema")
    rows = report.get("per_game")
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty per_game required")
    ids = set()
    rates = []
    repeats = []
    transition_total = 0
    unchanged_total = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid game record")
        gid = row.get("game_id")
        n, t = row.get("positions"), row.get("transitions")
        u, r = row.get("unchanged_descriptors_transitions"), row.get("revisited_exact_positions")
        if not isinstance(gid, str) or not gid or gid in ids:
            raise ValueError("invalid or duplicate game ID")
        ids.add(gid)
        if any(type(x) is not int or x < 0 for x in (n, t, u, r)):
            raise ValueError("invalid game counts")
        if n < 1 or t != n - 1 or u > t or r >= n:
            raise ValueError("inconsistent game counts")
        if t:
            rates.append(u / t)
            transition_total += t
            unchanged_total += u
        repeats.append(r)
    if report.get("games") != len(rows) or report.get("positions") != sum(
        row["positions"] for row in rows
    ) or report.get("transitions") != sum(row["transitions"] for row in rows):
        raise ValueError("aggregate counts inconsistent with per_game")
    if report.get("unchanged_descriptors_transitions") != sum(
        row["unchanged_descriptors_transitions"] for row in rows
    ) or report.get("revisited_exact_positions_within_games") != sum(repeats):
        raise ValueError("aggregate descriptor counts inconsistent with per_game")
    return {
        "schema": "mtdp.spatial_game_unit_summary.v1",
        "games": len(rows),
        "games_with_transitions": len(rates),
        "mean_game_unchanged_transition_fraction": mean(rates) if rates else None,
        "median_game_unchanged_transition_fraction": median(rates) if rates else None,
        "min_game_unchanged_transition_fraction": min(rates) if rates else None,
        "max_game_unchanged_transition_fraction": max(rates) if rates else None,
        "pooled_transition_unchanged_fraction_descriptive_only": (
            unchanged_total / transition_total if transition_total else None
        ),
        "games_with_revisited_positions": sum(r > 0 for r in repeats),
        "total_revisited_positions": sum(repeats),
        "independent_games_verified": False,
        "statistical_significance_claimed": False,
        "interpretation": (
            "Primary estimate weights games equally; pooled transition rate is a "
            "diagnostic, not an independent-sample estimate. No IID or strategic claim."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("spatial_report", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = summarize(json.loads(a.spatial_report.read_text(encoding="utf-8")))
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if a.output:
        a.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
