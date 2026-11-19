"""Deterministic paired bootstrap by game for D1, in raw score units.

This is an analysis utility, not evidence of independent games or score calibration.
A position may contribute only once; all rows must contain paired outcomes.
"""
from collections import defaultdict
from collections.abc import Mapping, Sequence
from random import Random
from statistics import mean

from .ranking_metrics import evaluate_order


def paired_game_bootstrap(rows: Sequence[Mapping], *, repetitions: int = 2000,
                          seed: int = 20261119) -> dict:
    """Percentile 95% CI on paired recall@3 and first-action regret.

    The primary >=4-action regret and recall share a score-blind denominator.
    Legacy delta_first_regret_raw covers all nonterminal decision positions;
    it is a separate estimand and must not be compared to aggregate primary regret.

    Primary recall@3 population is determined by n_legal >= 4 only.
    Bootstrap resamples games with replacement, preserving all within-game
    positions. Returns position-weighted estimands and a game count; use
    separate tournament-level analyses when tournament generalization matters.
    """
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("nonempty rows required")
    if type(repetitions) is not int or repetitions < 100:
        raise ValueError("at least 100 repetitions required")
    if type(seed) is not int:
        raise ValueError("integer seed required")
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("invalid row")
        pid, gid = row.get("id"), row.get("game_id")
        if not isinstance(pid, str) or not pid or not isinstance(gid, str) or not gid:
            raise ValueError("missing position/game provenance")
        if pid in seen:
            raise ValueError("duplicate position id")
        seen.add(pid)
        a = evaluate_order(row["legal"], row["proposed"], row["scores"])
        b = evaluate_order(row["legal"], row["baseline"], row["scores"])
        if a["decision"]:
            groups[gid].append((a["discriminating_at_3"],
                a["recall_at_3"] - b["recall_at_3"],
                a["first_action_regret_raw"] - b["first_action_regret_raw"]))
        else:
            groups[gid]
    games = sorted(groups)
    if not games or not any(groups.values()):
        raise ValueError("no decision positions")

    def estimate(sample):
        entries = [item for game in sample for item in groups[game]]
        recall = [delta for eligible, delta, _ in entries if eligible]
        return (mean(recall) if recall else None,
                mean(regret for eligible, _, regret in entries if eligible)
                if recall else None,
                mean(regret for _, _, regret in entries) if entries else None)

    observed = estimate(games)
    rng = Random(seed)
    draws = [estimate([games[rng.randrange(len(games))] for _ in games])
             for _ in range(repetitions)]

    def interval(index):
        values = sorted(pair[index] for pair in draws if pair[index] is not None)
        if not values:
            return None
        return [values[int(.025 * (len(values) - 1))],
                values[int(.975 * (len(values) - 1))]]

    return {"n_games": len(games), "n_decisions": sum(map(len, groups.values())),
            "n_primary_ge4": sum(eligible for values in groups.values()
                                 for eligible, _, _ in values),
            "delta_recall3": observed[0], "delta_recall3_ci95": interval(0),
            "delta_first_regret_primary_ge4_raw": observed[1],
            "delta_first_regret_primary_ge4_ci95": interval(1),
            "delta_first_regret_raw": observed[2],
            "delta_first_regret_raw_ci95": interval(2),
            "bootstrap_repetitions": repetitions, "bootstrap_seed": seed,
            "resampling_unit": "game", "estimand_weighting": "position"}
