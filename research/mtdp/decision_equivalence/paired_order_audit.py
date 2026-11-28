"""D1 score-only paired audit. Never feed these outcomes into signatures or cohort selection.

All arms must rank the identical full legal action set; raw scores are not
centipawns unless an external, preregistered conversion is supplied.
"""
from collections.abc import Mapping, Sequence

from .ranking_metrics import evaluate_order
from .rank_concordance import pairwise_rank_concordance


def paired_order_audit(legal: Sequence[str], candidate: Sequence[str],
                       baseline: Sequence[str], scores: Mapping[str, int]) -> dict:
    """Evaluate candidate and control on exactly the same position and scores.

    No inference of independent observations, minimax equivalence, or Elo.
    """
    candidate_metrics = evaluate_order(legal, candidate, scores)
    baseline_metrics = evaluate_order(legal, baseline, scores)
    candidate_rank = pairwise_rank_concordance(legal, candidate, scores)
    baseline_rank = pairwise_rank_concordance(legal, baseline, scores)
    fields = ("recall_at_1", "recall_at_3", "first_action_regret_raw",
              "top3_oracle_regret_raw")
    deltas = {
        key: (candidate_metrics[key] - baseline_metrics[key]
              if candidate_metrics[key] is not None else None)
        for key in fields
    }
    ca, ba = candidate_rank["pairwise_accuracy"], baseline_rank["pairwise_accuracy"]
    deltas["pairwise_accuracy"] = ca - ba if ca is not None and ba is not None else None
    return {
        "candidate": candidate_metrics, "baseline": baseline_metrics,
        "candidate_concordance": candidate_rank,
        "baseline_concordance": baseline_rank,
        "candidate_minus_baseline": deltas,
        "score_unit": "raw; no centipawn conversion",
        "independent_cohort_claim": False,
    }
