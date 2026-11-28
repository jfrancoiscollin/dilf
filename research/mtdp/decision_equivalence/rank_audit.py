"""Score-blind-independent D1-D action-ranking audit primitives.

No Scan calibration, corpus admission, or minimax equivalence is implied.
Scores are from the side-to-move perspective; higher is better.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Hashable, Mapping, Sequence


@dataclass(frozen=True)
class RankingAudit:
    top1_exact: bool
    top3_exact: bool
    regret_top1: float
    regret_top3: float
    n_legal: int


def audit_ranking(
    legal: Sequence[Hashable],
    proposed: Sequence[Hashable],
    scores: Mapping[Hashable, float],
) -> RankingAudit:
    """Fail closed on ambiguous actions, missing scores or invalid proposals.

    'top3' means an optimum appears in the first min(3,n_legal) actions,
    not that three actions were searched or that minimax is preserved.
    """
    if not legal or len(set(legal)) != len(legal):
        raise ValueError("legal actions must be nonempty and unique")
    if len(proposed) != len(legal) or set(proposed) != set(legal):
        raise ValueError("proposal must be a permutation of all legal actions")
    if set(scores) != set(legal):
        raise ValueError("scores must cover exactly the legal actions")
    if any(not isfinite(float(v)) for v in scores.values()):
        raise ValueError("scores must be finite")
    best = max(float(scores[a]) for a in legal)
    k = min(3, len(legal))
    regrets = [max(0.0, best - float(scores[a])) for a in proposed[:k]]
    return RankingAudit(
        top1_exact=regrets[0] == 0.0,
        top3_exact=min(regrets) == 0.0,
        regret_top1=regrets[0],
        regret_top3=min(regrets),
        n_legal=len(legal),
    )
