"""Tie-aware post hoc concordance of D1 action rankings.

Never use target scores to construct signatures or select corpus members.
Concordance does not imply minimax equivalence. Higher scores are better.
"""
from collections.abc import Mapping, Sequence


def pairwise_rank_concordance(legal: Sequence[str], ordered: Sequence[str],
                              scores: Mapping[str, int]) -> dict:
    """Count distinguishable pairs; score ties are neither correct nor incorrect."""
    if not isinstance(legal, (list, tuple)) or not isinstance(ordered, (list, tuple)):
        raise ValueError("legal and ordered must be lists or tuples")
    if any(not isinstance(x, str) or not x for x in legal) or len(set(legal)) != len(legal):
        raise ValueError("legal actions must be unique nonempty strings")
    if len(ordered) != len(legal) or len(set(ordered)) != len(ordered) or set(ordered) != set(legal):
        raise ValueError("ordered must be an exact permutation of legal")
    if not isinstance(scores, Mapping) or set(scores) != set(legal) or any(type(v) is not int for v in scores.values()):
        raise ValueError("scores must be complete raw integers")
    good = bad = ties = 0
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if scores[a] == scores[b]:
                ties += 1
            elif scores[a] > scores[b]:
                good += 1
            else:
                bad += 1
    informative = good + bad
    return {"n_legal": len(legal), "n_pairs": good + bad + ties,
            "concordant_pairs": good, "discordant_pairs": bad,
            "score_tied_pairs": ties, "informative_pairs": informative,
            "pairwise_accuracy": good / informative if informative else None,
            "kendall_tau_a_on_distinguishable_pairs": (good - bad) / informative if informative else None,
            "unit": "raw score ordering; no centipawn conversion"}
