"""D1 decision-ranking metrics. No engine calls, no training or score imputation.

Scores are from the root player's perspective, higher is better. Every action
must be scored; absent/duplicate/non-finite actions are rejected rather than
silently dropped. Ties use deterministic lexical action IDs.
"""
import math


def compare_rankings(reference, proposed, *, top_k=3):
    """Compare complete action->score maps; proposed scores may be surrogate.

    Returns root-reference regret and action-ranking diagnostics. This is NOT
    minimax equivalence or evidence of generalization.
    """
    if not isinstance(reference, dict) or not isinstance(proposed, dict):
        raise ValueError("expected action-score dictionaries")
    if not reference or set(reference) != set(proposed):
        raise ValueError("nonempty identical action sets required")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    for scores in (reference, proposed):
        for action, value in scores.items():
            if not isinstance(action, str) or not action:
                raise ValueError("invalid action identifier")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("non-finite or non-numeric score")
    oracle = sorted(reference, key=lambda a: (-reference[a], a))
    predicted = sorted(proposed, key=lambda a: (-proposed[a], a))
    best_value = reference[oracle[0]]
    selected = predicted[0]
    regret = best_value - reference[selected]
    if regret < 0:
        raise AssertionError("negative regret")
    k = min(top_k, len(oracle))
    oracle_top = set(oracle[:k])
    predicted_top = set(predicted[:k])
    pairs = [(a, b) for i, a in enumerate(oracle) for b in oracle[i + 1:]]
    strict = [(a, b) for a, b in pairs if reference[a] != reference[b]]
    concordant = sum((reference[a] - reference[b]) * (proposed[a] - proposed[b]) > 0 for a, b in strict)
    return {
        "n_actions": len(oracle),
        "top1_match": selected == oracle[0],
        "topk_recall": len(oracle_top & predicted_top) / k,
        "regret": regret,
        "strict_reference_pairs": len(strict),
        "strict_pair_concordance": concordant / len(strict) if strict else None,
        "reference_top1_tied": sum(v == best_value for v in reference.values()) > 1,
    }
