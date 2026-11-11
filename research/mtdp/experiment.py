"""Pre-registered, leakage-aware experiment planning for spatial hypotheses.

This module prepares independent matched strata; it does not calculate
significance or use engine evaluations. Sampling must happen by game/source
group, not individual position, to avoid train/test leakage.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Stratum:
    material_balance: int
    total_pieces_bin: str
    kings_present: bool
    turn: str


def position_stratum(row: dict[str, Any]) -> Stratum:
    metrics = row["metrics"]
    total = int(metrics["occupied_squares"])
    phase = "0-10" if total <= 10 else "11-20" if total <= 20 else "21-30" if total <= 30 else "31-40" if total <= 40 else "41+"
    return Stratum(
        material_balance=int(metrics["material_balance"]),
        total_pieces_bin=phase,
        kings_present=bool(row.get("metadata", {}).get("kings_present", False)),
        turn=str(metrics["turn"]),
    )


def audit_strata(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Count observable strata; do not infer unverified king status."""
    groups: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        s = position_stratum(row)
        groups[(s.material_balance, s.total_pieces_bin, s.turn)].append(row)
    return {
        "strata": [
            {"material_balance": k[0], "total_pieces_bin": k[1],
             "turn": k[2], "observations": len(v),
             "unique_positions": len({r["position_hash"] for r in v}),
             "source_counts": dict(sorted(Counter(r["source"] for r in v).items()))}
            for k, v in sorted(groups.items())
        ],
        "note": "King-status stratification deferred until piece-type labels are audited.",
    }
