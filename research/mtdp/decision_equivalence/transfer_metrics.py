"""Decision-transfer metrics for *already authorized* per-action evaluations.

This module never fetches scores or selects a cohort. Scores are from the
side-to-move perspective; larger is better. Units are caller-defined.
"""
from __future__ import annotations

from math import isfinite


def evaluate_transfer(reference: dict[str, float], proposed_order: list[str],
                      *, top_k: int = 3) -> dict:
    """Compare an ordering to a reference action-score table.

    Ties at the reference optimum are accepted. A missing/duplicate/illegal
    action fails closed; no silent intersection or score imputation.
    """
    if not reference or top_k < 1 or isinstance(top_k, bool):
        raise ValueError("empty reference or invalid top_k")
    if any(not isinstance(a, str) or not a for a in reference):
        raise ValueError("invalid action")
    if any(isinstance(s, bool) or not isinstance(s, (int, float))
           or not isfinite(s) for s in reference.values()):
        raise ValueError("nonfinite/non-numeric score")
    if (len(proposed_order) != len(reference)
            or len(set(proposed_order)) != len(proposed_order)
            or set(proposed_order) != set(reference)):
        raise ValueError("ordering must be an exact permutation of legal actions")
    best = max(reference.values())
    optimal = {a for a, score in reference.items() if score == best}
    first = proposed_order[0]
    k = min(top_k, len(proposed_order))
    # Strict top-k membership is ill-defined at score ties. Report
    # guaranteed and possible membership separately at the kth boundary.
    # Recall denominators are the entire corresponding membership pools;
    # possible recall is not the maximum recall of a tie-broken k-action set.
    scores = sorted(reference.values(), reverse=True)
    cutoff = scores[k - 1]
    guaranteed = {a for a, score in reference.items() if score > cutoff}
    possible = {a for a, score in reference.items() if score >= cutoff}
    proposed = set(proposed_order[:k])
    return {
        "schema": "mtdp-d1-transfer-metrics-v1",
        "legal_actions": len(reference),
        "top_k": k,
        "top1_optimal_tie_accepted": first in optimal,
        "top1_regret_score_units": best - reference[first],
        "topk_guaranteed_reference_recall": (
            len(proposed & guaranteed) / len(guaranteed) if guaranteed else None
        ),
        "topk_possible_reference_recall": len(proposed & possible) / len(possible),
        "topk_boundary_tied": len(possible) > k,
        "decision_equivalence_established": False,
        "minimax_equivalence_established": False,
    }
