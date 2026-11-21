"""Score-blind primary D1 population and paired ranking summaries.

Synthetic/unit-test utility; no corpus or Scan unit conversion is implied.
The primary denominator is fixed by legal action count, not target scores.
"""
from collections.abc import Mapping, Sequence
from statistics import mean

from .ranking_metrics import evaluate_order


def aggregate_paired(rows: Sequence[Mapping]) -> dict:
    """Summarize paired proposed/baseline orders on identical legal sets.

    Each row needs unique id, game_id, legal, proposed, baseline, scores.
    No position may be silently dropped after target scoring. All reported
    regret differences remain in the source engine's raw score units.
    """
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("nonempty rows required")
    seen = set()
    results = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("invalid row")
        if not all(isinstance(row.get(k), str) and row[k] for k in ("id", "game_id")):
            raise ValueError("missing position/game provenance")
        if row["id"] in seen:
            raise ValueError("duplicate position id")
        seen.add(row["id"])
        a = evaluate_order(row["legal"], row["proposed"], row["scores"])
        b = evaluate_order(row["legal"], row["baseline"], row["scores"])
        results.append((a, b))
    primary = [(a, b) for a, b in results if a["discriminating_at_3"]]
    secondary = [(a, b) for a, b in primary if a["informative_at_3"]]

    def summary(pairs):
        if not pairs:
            return {"n": 0, "recall3_proposed": None, "recall3_baseline": None,
                    "delta_recall3": None, "delta_first_regret_raw": None}
        return {"n": len(pairs),
                "recall3_proposed": mean(a["recall_at_3"] for a, _ in pairs),
                "recall3_baseline": mean(b["recall_at_3"] for _, b in pairs),
                "delta_recall3": mean(a["recall_at_3"] - b["recall_at_3"] for a, b in pairs),
                "delta_first_regret_raw": mean(a["first_action_regret_raw"] - b["first_action_regret_raw"] for a, b in pairs)}
    return {"n_all": len(results), "n_terminal": sum(not a["decision"] for a, _ in results),
            "primary_score_blind_n_ge_4": summary(primary),
            "secondary_score_dependent_informative_at_3": summary(secondary)}
