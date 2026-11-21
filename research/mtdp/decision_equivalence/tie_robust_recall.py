"""Exact recall bounds over all admissible reference top-k tie-breakings.

Pure combinatorics: no target selection, no evaluation, no engine access.
"""
from __future__ import annotations

from math import isfinite


def tie_robust_topk_recall(reference: dict[str, float],
                           proposed_order: list[str], *, top_k: int = 3) -> dict:
    """Return minimum/maximum top-k recall over every score-consistent tie break.

    The reference top-k contains every action strictly above the kth score
    plus enough boundary-tied actions to reach k. Each bound divides by k.
    This is not a minimax-equivalence claim.
    """
    if not reference or type(top_k) is not int or top_k < 1:
        raise ValueError("invalid reference or k")
    if any(not isinstance(a, str) or not a for a in reference):
        raise ValueError("invalid action identifier")
    if any(type(v) not in (int, float) or not isfinite(v)
           for v in reference.values()):
        raise ValueError("invalid score")
    if (len(proposed_order) != len(reference)
            or any(not isinstance(a, str) for a in proposed_order)
            or len(set(proposed_order)) != len(proposed_order)
            or set(proposed_order) != set(reference)):
        raise ValueError("order must permute all legal actions exactly")
    k = min(top_k, len(reference))
    cutoff = sorted(reference.values(), reverse=True)[k - 1]
    fixed = {a for a, v in reference.items() if v > cutoff}
    boundary = {a for a, v in reference.items() if v == cutoff}
    selected = set(proposed_order[:k])
    slots = k - len(fixed)
    fixed_hits = len(fixed & selected)
    boundary_hits = len(boundary & selected)
    # Adversarial tie break fills slots from unselected boundary actions first.
    min_boundary_hits = max(0, slots - (len(boundary) - boundary_hits))
    max_boundary_hits = min(slots, boundary_hits)
    return {
        "schema": "mtdp-d1-tie-robust-recall-v1",
        "top_k": k,
        "boundary_tied": len(boundary) > slots,
        "recall_lower_bound": (fixed_hits + min_boundary_hits) / k,
        "recall_upper_bound": (fixed_hits + max_boundary_hits) / k,
        "minimax_equivalence_established": False,
    }
