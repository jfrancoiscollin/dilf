"""Paired game-cluster bootstrap for D1; no engine calls or score fitting.

Each game is one resampling unit, regardless of its number of positions.
The estimand is the equally game-weighted mean of within-game paired deltas.
Use only on a frozen, game-disjoint evaluation split.
"""
import math
import random
from collections import defaultdict


def paired_game_bootstrap(rows, *, replicates=2000, seed=0, confidence=0.95):
    """rows: iterable of (game_id, position_id, baseline, candidate)."""
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 2:
        raise ValueError("replicates must be an integer >= 2")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one")
    grouped = defaultdict(list)
    seen = set()
    for game, position, baseline, candidate in rows:
        if not isinstance(game, str) or not game or not isinstance(position, str) or not position:
            raise ValueError("game and position IDs must be nonempty strings")
        if position in seen:
            raise ValueError("duplicate position ID across or within games")
        seen.add(position)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (baseline, candidate)):
            raise ValueError("non-finite or non-numeric metric")
        delta = candidate - baseline
        if not math.isfinite(delta):
            raise ValueError("non-finite paired difference (numeric overflow)")
        grouped[game].append(delta)
    if len(grouped) < 2:
        raise ValueError("at least two independent game clusters required")
    means = [sum(v) / len(v) for _, v in sorted(grouped.items())]
    n = len(means)
    rng = random.Random(seed)
    draws = sorted(sum(means[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(replicates))
    alpha = (1 - confidence) / 2
    def quantile(p):
        index = p * (replicates - 1)
        lo = math.floor(index)
        hi = math.ceil(index)
        return draws[lo] * (hi - index) + draws[hi] * (index - lo) if lo != hi else draws[lo]
    return {"n_games": n, "n_positions": len(seen), "estimate": sum(means) / n,
            "ci_lower": quantile(alpha), "ci_upper": quantile(1 - alpha),
            "confidence": confidence, "replicates": replicates, "seed": seed,
            "estimand": "equal_game_weight_paired_difference"}
