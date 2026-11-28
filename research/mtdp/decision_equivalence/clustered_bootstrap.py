"""D1 clustered uncertainty for *already admitted* decision observations.

This module only aggregates precomputed, score-unit-agnostic ranking metrics.
Never treat positions from one game as independent bootstrap samples.
"""
from collections import defaultdict
import math
import random


def clustered_difference(rows, *, cluster_key="game_id", metric="recall_at_1",
                         repetitions=2000, seed=0):
    """Paired bootstrap of candidate minus baseline, resampling entire clusters.

    Each row has cluster_key, candidate, baseline; all values must be finite
    numbers (not bool). Equal weight per observation, not per cluster.
    Return the observed difference and percentile 95% interval. The same
    resampled clusters contribute to both arms, preserving pairing.
    """
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 100:
        raise ValueError("repetitions must be integer >= 100")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be integer")
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("nonempty rows required")
    clusters = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(cluster_key), str) or not row[cluster_key]:
            raise ValueError("missing cluster identifier")
        a, b = row.get("candidate"), row.get("baseline")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in (a, b)):
            raise ValueError("paired metrics must be finite numbers")
        try:
            finite_inputs = all(math.isfinite(x) for x in (a, b))
        except OverflowError as exc:
            raise ValueError('paired difference not representable as finite float') from exc
        if not finite_inputs:
            raise ValueError("paired metrics must be finite numbers")
        # Finite inputs can still overflow during conversion or subtraction.
        try:
            delta = float(a) - float(b)
        except (OverflowError, ValueError) as exc:
            raise ValueError('paired difference not representable as finite float') from exc
        if not math.isfinite(delta):
            raise ValueError('paired difference not representable as finite float')
        clusters[row[cluster_key]].append(delta)
    if len(clusters) < 2:
        raise ValueError("at least two independent clusters required")
    # Stable RNG mapping across manifest/row order; do not depend on dict insertion order.
    groups = [sorted(clusters[key]) for key in sorted(clusters)]
    try:
        observed = math.fsum(math.fsum(g) for g in groups) / sum(map(len, groups))
    except (OverflowError, ValueError) as exc:
        raise ValueError("clustered aggregate not representable as finite float") from exc
    rng = random.Random(seed)
    samples = []
    for _ in range(repetitions):
        chosen = rng.choices(groups, k=len(groups))
        try:
            samples.append(math.fsum(math.fsum(g) for g in chosen) / sum(map(len, chosen)))
        except (OverflowError, ValueError) as exc:
            raise ValueError("bootstrap aggregate not representable as finite float") from exc
    samples.sort()
    lo = samples[int(0.025 * (repetitions - 1))]
    hi = samples[int(0.975 * (repetitions - 1))]
    return {"metric": metric, "cluster_key": cluster_key,
            "n_clusters": len(groups), "n_observations": len(rows),
            "candidate_minus_baseline": observed, "ci95": [lo, hi],
            "repetitions": repetitions, "seed": seed,
            "unit": "raw input metric; no centipawn conversion"}
