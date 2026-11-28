"""Pairwise rank agreement for D1-D; descriptive, not minimax equivalence."""
from __future__ import annotations
from math import isfinite, sqrt
from typing import Hashable, Mapping, Sequence


def kendall_tau_b(legal: Sequence[Hashable], proposed: Sequence[Hashable], scores: Mapping[Hashable, float]) -> float | None:
    """Tau-b of proposed action order against higher-is-better target scores.

    Returns None when all target scores tie or fewer than two actions exist.
    A proposed order is a strict permutation; target ties are not broken.
    """
    if not legal or len(set(legal)) != len(legal):
        raise ValueError("legal actions must be nonempty and unique")
    if len(proposed) != len(legal) or len(set(proposed)) != len(proposed) or set(proposed) != set(legal):
        raise ValueError("proposal must permute all legal actions")
    if set(scores) != set(legal):
        raise ValueError("scores must cover exactly the legal actions")
    if any(not isfinite(float(s)) for s in scores.values()):
        raise ValueError("scores must be finite")
    concordant = discordant = target_ties = 0
    for i, a in enumerate(proposed):
        for b in proposed[i + 1:]:
            if scores[a] == scores[b]:
                target_ties += 1
            elif scores[a] > scores[b]:
                concordant += 1
            else:
                discordant += 1
    comparable = concordant + discordant
    if not comparable:
        return None
    return (concordant - discordant) / sqrt(comparable * (comparable + target_ties))
