"""Synthetic paired-cluster tests; no real Scan scores or independent cohort."""
import pytest

from research.mtdp.decision_equivalence.paired_cluster_report import paired_cluster_report


def obs(game, scores, candidate=None, baseline=None):
    legal = list(scores)
    return {"game_id": game, "legal": legal, "scores": scores,
            "candidate": candidate if candidate is not None else legal,
            "baseline": baseline if baseline is not None else list(reversed(legal))}


def test_top3_excludes_saturated_and_tied_positions():
    rows = [
        obs("g1", {"a": 4, "b": 3, "c": 2, "d": 1}),
        obs("g2", {"a": 4, "b": 3, "c": 2, "d": 1}),
        obs("g3", {"a": 5, "b": 5, "c": 5, "d": 5}),
        obs("g4", {"a": 2, "b": 1, "c": 0}),
    ]
    r = paired_cluster_report(rows, metric="recall_at_3", repetitions=100, seed=7)
    assert r["n_observations"] == 2
    assert r["n_clusters"] == 2
    assert r["excluded"]["noninformative_top3"] == 2
    assert r["candidate_minus_baseline"] == 1


def test_all_ties_and_terminal_are_not_zero_imputed():
    rows = [obs("g1", {"a": 2, "b": 1}), obs("g2", {"a": 2, "b": 1}),
            obs("g3", {"a": 1, "b": 1}), obs("g4", {})]
    r = paired_cluster_report(rows, metric="pairwise_accuracy", repetitions=100)
    assert r["n_observations"] == 2
    assert r["excluded"]["all_score_ties"] == 1
    assert r["excluded"]["terminal"] == 1


def test_reordering_games_preserves_bootstrap():
    rows = [obs("g1", {"a": 9, "b": 4, "c": 2, "d": 0}),
            obs("g2", {"a": 3, "b": 1, "c": 0, "d": -2}),
            obs("g1", {"a": 2, "b": 0, "c": -1, "d": -4})]
    a = paired_cluster_report(rows, metric="first_action_regret_raw", repetitions=150, seed=17)
    b = paired_cluster_report(list(reversed(rows)), metric="first_action_regret_raw", repetitions=150, seed=17)
    assert a == b
    assert a["candidate_minus_baseline"] < 0


def test_fails_closed_on_missing_clusters_or_bad_rank():
    with pytest.raises(ValueError):
        paired_cluster_report([obs("g1", {"a": 1, "b": 0})],
                              metric="recall_at_1", repetitions=100)
    with pytest.raises(ValueError):
        paired_cluster_report([obs("g1", {"a": 1, "b": 0})],
                              metric="unsupported")
    with pytest.raises(ValueError):
        paired_cluster_report([obs("g1", {"a": 1, "b": 0}, ["a", "a"])],
                              metric="recall_at_1", repetitions=100)


def test_primary_fixed_population_keeps_score_tied_positions():
    rows = [
        obs("g1", {"a": 4, "b": 3, "c": 2, "d": 1}),
        obs("g2", {"a": 4, "b": 3, "c": 2, "d": 1}),
        obs("g3", {"a": 5, "b": 5, "c": 5, "d": 5}),
        obs("g4", {"a": 2, "b": 1, "c": 0}),
    ]
    primary = paired_cluster_report(rows, metric="recall_at_3", repetitions=100,
                                    seed=7, top3_population="fixed_n_ge_4")
    secondary = paired_cluster_report(rows, metric="recall_at_3", repetitions=100,
                                      seed=7, top3_population="conditional_informative")
    assert primary["n_observations"] == 3
    assert primary["n_clusters"] == 3
    assert primary["excluded"]["noninformative_top3"] == 1
    assert primary["candidate_minus_baseline"] == pytest.approx(2 / 3)
    assert primary["top3_population_is_primary_fixed"] is True
    assert secondary["n_observations"] == 2
    assert secondary["candidate_minus_baseline"] == 1
    assert secondary["top3_population_is_primary_fixed"] is False


def test_unknown_top3_population_fails_closed():
    with pytest.raises(ValueError, match="population"):
        paired_cluster_report([obs("g1", {"a": 1, "b": 0})],
                              metric="recall_at_3", top3_population="auto")
