"""D1 score-only bridge from paired rankings to game-clustered uncertainty.

Rows are already admitted, frozen observations; this module neither admits
positions nor computes signatures. Never infer minimax equivalence or Elo.
"""
from collections.abc import Sequence

from .paired_order_audit import paired_order_audit
from .clustered_bootstrap import clustered_difference

METRICS = ("recall_at_1", "recall_at_3", "first_action_regret_raw",
           "top3_oracle_regret_raw", "pairwise_accuracy")


def paired_cluster_report(observations: Sequence[dict], *, metric: str,
                          cluster_key: str = "game_id", repetitions: int = 2000,
                          seed: int = 0,
                          top3_population: str = "conditional_informative") -> dict:
    """Bootstrap paired deltas by entire game/tournament, excluding undefined rows.

    Default legacy top-3 recall is SECONDARY conditional on *informative* positions:
    >=4 legal actions and sufficiently few optimal ties for recall to fail.
    Explicit fixed_n_ge_4 mode is PRIMARY: include all n>=4 positions,
    even when optimal ties guarantee recall, avoiding score-dependent selection.
    Pairwise concordance excludes all-score-tied positions. Missing metrics
    are never coerced to zero. Scores must be higher-is-better raw integers.
    """
    if top3_population not in ("conditional_informative", "fixed_n_ge_4"):
        raise ValueError("unknown top3 population")
    if metric not in METRICS:
        raise ValueError("unknown metric")
    if not isinstance(observations, (list, tuple)) or not observations:
        raise ValueError("nonempty frozen observations required")
    rows = []
    excluded = {"terminal": 0, "noninformative_top3": 0,
                "all_score_ties": 0}
    for obs in observations:
        if not isinstance(obs, dict) or not isinstance(obs.get(cluster_key), str) or not obs[cluster_key]:
            raise ValueError("missing cluster provenance")
        result = paired_order_audit(obs["legal"], obs["candidate"], obs["baseline"], obs["scores"])
        cm = result["candidate"]
        if not cm["decision"]:
            excluded["terminal"] += 1
            continue
        if metric == "recall_at_3" and not (
            cm["informative_at_3"] if top3_population == "conditional_informative"
            else cm["n_legal"] >= 4
        ):
            excluded["noninformative_top3"] += 1
            continue
        delta = result["candidate_minus_baseline"][metric]
        if delta is None:
            excluded["all_score_ties"] += 1
            continue
        rows.append({cluster_key: obs[cluster_key], "candidate": delta,
                     "baseline": 0})
    if not rows:
        raise ValueError("no informative observations")
    report = clustered_difference(rows, cluster_key=cluster_key, metric=metric,
                                  repetitions=repetitions, seed=seed)
    report["top3_population"] = top3_population if metric == "recall_at_3" else None
    report["top3_population_is_primary_fixed"] = (metric == "recall_at_3" and top3_population == "fixed_n_ge_4")
    report["excluded"] = excluded
    report["n_input_observations"] = len(observations)
    report["admission_verified_here"] = False
    report["score_unit"] = "raw; no centipawn conversion"
    return report
