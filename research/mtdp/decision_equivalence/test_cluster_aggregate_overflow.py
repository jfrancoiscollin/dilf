"""Regression: finite paired deltas can overflow during cluster aggregation."""
import pytest

from research.mtdp.decision_equivalence.clustered_bootstrap import clustered_difference


def test_observed_cluster_sum_overflow_fails_closed():
    rows = [
        {"game_id": "g1", "candidate": 1e308, "baseline": 0},
        {"game_id": "g1", "candidate": 1e308, "baseline": 0},
        {"game_id": "g2", "candidate": 0, "baseline": 0},
    ]
    with pytest.raises(ValueError, match="clustered aggregate not representable"):
        clustered_difference(rows, repetitions=100)


def test_large_finite_values_without_overflow_still_work():
    rows = [
        {"game_id": "g1", "candidate": 1e307, "baseline": 0},
        {"game_id": "g2", "candidate": -1e307, "baseline": 0},
    ]
    result = clustered_difference(rows, repetitions=100, seed=11)
    assert result["candidate_minus_baseline"] == 0
    assert all(float("-inf") < x < float("inf") for x in result["ci95"])


def test_bootstrap_draw_overflow_fails_closed_even_if_observed_is_finite():
    # Observed 8e307 + 8e307 - 8e307 is finite; a resample with
    # only positive clusters can overflow. Seed 3 produces such a draw.
    rows = [
        {"game_id": "g1", "candidate": 8e307, "baseline": 0},
        {"game_id": "g2", "candidate": 8e307, "baseline": 0},
        {"game_id": "g3", "candidate": -8e307, "baseline": 0},
    ]
    with pytest.raises(ValueError, match="bootstrap aggregate not representable"):
        clustered_difference(rows, repetitions=100, seed=3)
