"""Tie-aware D1 diagnostics; deterministic, score-unit agnostic, no engine calls.

An exact score tie is an equivalence class of actions under the *reference
measurement*, not proof of minimax equivalence. All scores are root-oriented.
"""
from .decision_metrics import compare_rankings


def tie_aware_diagnostics(reference, proposed, *, top_k=3):
    """Return metrics robust to exact reference ties.

    Reference top-k includes *all* actions tied at the kth score; this
    deliberately differs from deterministic lexical top-k. Prediction top-k
    is lexical only for reproducibility. Pair coverage excludes ties in
    either ranking; no tied pair is counted as a disagreement.
    """
    base = compare_rankings(reference, proposed, top_k=top_k)
    n = len(reference)
    k = min(top_k, n)
    ranked_ref = sorted(reference, key=lambda a: (-reference[a], a))
    ranked_pred = sorted(proposed, key=lambda a: (-proposed[a], a))
    cutoff = reference[ranked_ref[k - 1]]
    acceptable = {a for a in reference if reference[a] >= cutoff}
    optimum = reference[ranked_ref[0]]
    best_actions = {a for a in reference if reference[a] == optimum}
    selected = ranked_pred[0]
    comparable = 0
    concordant = 0
    for i, a in enumerate(ranked_ref):
        for b in ranked_ref[i + 1:]:
            dr = reference[a] - reference[b]
            dp = proposed[a] - proposed[b]
            if dr == 0 or dp == 0:
                continue
            comparable += 1
            concordant += (dr * dp > 0)
    return {
        **base,
        "top1_optimal_set_match": selected in best_actions,
        "reference_optimal_set_size": len(best_actions),
        "reference_topk_boundary_set_size": len(acceptable),
        "topk_boundary_recall": len(acceptable.intersection(ranked_pred[:k])) / k,
        "untied_pair_count": comparable,
        "untied_pair_concordance": concordant / comparable if comparable else None,
        "untied_pair_coverage": comparable / (n * (n - 1) / 2) if n > 1 else None,
    }
