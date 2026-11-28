"""D1 regression: bootstrap resamples games, never individual positions.

Synthetic data only; does not validate a new FMJD cohort or any Jass gain.
"""
import pytest

from research.mtdp.decision_equivalence.clustered_bootstrap import clustered_difference


def test_exact_paired_null_remains_zero_with_unequal_game_lengths():
    rows = [
        {"game_id": "g1", "candidate": 1, "baseline": 1},
        {"game_id": "g1", "candidate": 2, "baseline": 2},
        {"game_id": "g1", "candidate": 3, "baseline": 3},
        {"game_id": "g2", "candidate": -7, "baseline": -7},
    ]
    report = clustered_difference(rows, repetitions=200, seed=13)
    assert report["n_clusters"] == 2
    assert report["n_observations"] == 4
    assert report["candidate_minus_baseline"] == 0
    assert report["ci95"] == [0, 0]


def test_whole_game_resampling_with_unequal_cluster_sizes():
    # With only two games, every replicate is a weighted mean of entire
    # groups: one three-position game (+1 each), one one-position game (-1).
    rows = [
        *({"game_id": "g1", "candidate": 1, "baseline": 0} for _ in range(3)),
        {"game_id": "g2", "candidate": -1, "baseline": 0},
    ]
    report = clustered_difference(rows, repetitions=400, seed=13)
    assert report["candidate_minus_baseline"] == 0.5
    # Resampling two whole games yields only {-1, 0.5, 1}.
    # An individual-position bootstrap could yield additional values.
    assert report["ci95"] == [-1, 1]


def test_reject_single_game_even_with_many_positions():
    rows = [{"game_id": "same-game", "candidate": 1, "baseline": 0}
            for _ in range(100)]
    with pytest.raises(ValueError, match="two independent clusters"):
        clustered_difference(rows, repetitions=100, seed=13)
