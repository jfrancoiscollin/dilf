"""D1 score-unit-agnostic ranking metrics; no Scan scores used to build signatures.

All scores must be complete and oriented so larger is better. A ranked proposal
must be an exact permutation of the legal actions. This module does not infer
minimax equivalence or convert raw Scan integers to material-pawn units.
"""
from collections.abc import Mapping, Sequence


def evaluate_order(legal: Sequence[str], ordered: Sequence[str],
                   scores: Mapping[str, int]) -> dict:
    """Return decision metrics, separating recall@3 from first-action regret.

    Empty legal sets are terminal/no-decision observations. Reject missing
    scores, duplicate actions, malformed ordering and boolean scores.
    """
    if not isinstance(legal, (list, tuple)) or not isinstance(ordered, (list, tuple)):
        raise ValueError("legal and ordered must be sequences")
    if any(not isinstance(a, str) or not a for a in legal):
        raise ValueError("invalid action")
    if len(set(legal)) != len(legal):
        raise ValueError("duplicate legal action")
    if any(not isinstance(a, str) or not a for a in ordered):
        raise ValueError("invalid ordered action")
    if len(ordered) != len(legal) or set(ordered) != set(legal) or len(set(ordered)) != len(ordered):
        raise ValueError("ordered must be an exact permutation of legal")
    if not isinstance(scores, Mapping) or set(scores) != set(legal):
        raise ValueError("scores must cover exactly all legal actions")
    if any(type(v) is not int for v in scores.values()):
        raise ValueError("raw scores must be integers, not bool/float")
    n = len(legal)
    if not n:
        return {"n_legal": 0, "decision": False, "recall_at_1": None,
                "recall_at_3": None, "discriminating_at_3": False, "informative_at_3": False,\n                "n_optimal": 0,
                "first_optimum_rank": None, "first_action_regret_raw": None,
                "top3_oracle_regret_raw": None}
    best = max(scores.values())
    optimal = {a for a in legal if scores[a] == best}
    rank = next(i for i, a in enumerate(ordered, 1) if a in optimal)\n    # With k=3, recall is guaranteed if more than n-k actions tie for best.\n    # This is distinct from the purely legal-count gate (n >= 4).\n    informative_at_3 = n >= 4 and len(optimal) <= n - 3
    return {"n_legal": n, "decision": True, "recall_at_1": int(rank == 1),
            "recall_at_3": int(rank <= 3), "discriminating_at_3": n >= 4,\n            "informative_at_3": informative_at_3, "n_optimal": len(optimal),
            "first_optimum_rank": rank,
            "first_action_regret_raw": best - scores[ordered[0]],
            "top3_oracle_regret_raw": best - max(scores[a] for a in ordered[:3])}
