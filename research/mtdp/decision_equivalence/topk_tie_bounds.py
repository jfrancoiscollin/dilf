"""Tie-invariant bounds on top-k precision under arbitrary predicted tie breaks.

Reference relevance includes all actions tied at reference rank k.
Prediction selects exactly k actions; ties at predicted rank k may be
resolved arbitrarily. Bounds quantify uncertainty, not minimax equivalence.
"""
from math import isfinite


def topk_tie_bounds(reference: dict[str, float], proposed: dict[str, float], k: int = 3) -> dict:
    if not reference or reference.keys() != proposed.keys():
        raise ValueError("nonempty identical action sets required")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v)
           for v in list(reference.values()) + list(proposed.values())):
        raise ValueError("scores must be finite numeric values")
    k = min(k, len(reference))
    ref_cut = sorted(reference.values(), reverse=True)[k - 1]
    relevant = {a for a, v in reference.items() if v >= ref_cut}
    pred_cut = sorted(proposed.values(), reverse=True)[k - 1]
    fixed = {a for a, v in proposed.items() if v > pred_cut}
    boundary = {a for a, v in proposed.items() if v == pred_cut}
    slots = k - len(fixed)
    hits_fixed = len(fixed & relevant)
    hits_boundary = len(boundary & relevant)
    minimum_hits = hits_fixed + max(0, slots - (len(boundary) - hits_boundary))
    maximum_hits = hits_fixed + min(slots, hits_boundary)
    return {
        "k": k,
        "reference_relevant_count": len(relevant),
        "predicted_boundary_size": len(boundary),
        "predicted_boundary_slots": slots,
        "precision_lower": minimum_hits / k,
        "precision_upper": maximum_hits / k,
        "recall_lower": minimum_hits / len(relevant),
        "recall_upper": maximum_hits / len(relevant),
    }
