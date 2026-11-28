"""D1 synthetic invariants for paired game-cluster uncertainty.

No FMJD cohort, Scan scoring, or Jass benchmark is run by these tests.
"""
import pytest

from research.mtdp.decision_equivalence.clustered_bootstrap import clustered_difference


def test_row_permutation_does_not_change_seeded_paired_interval():
    rows = [
        {"game_id": "b", "candidate": 4, "baseline": 1},
        {"game_id": "a", "candidate": 2, "baseline": 5},
        {"game_id": "b", "candidate": 7, "baseline": 3},
        {"game_id": "c", "candidate": -2, "baseline": 1},
        {"game_id": "a", "candidate": 6, "baseline": 6},
    ]
    first = clustered_difference(rows, repetitions=400, seed=17)
    reverse = clustered_difference(list(reversed(rows)), repetitions=400, seed=17)
    assert first == reverse


def test_paired_difference_invariant_to_common_score_offset():
    rows = [
        {"game_id": "a", "candidate": 3, "baseline": 1},
        {"game_id": "a", "candidate": 5, "baseline": 2},
        {"game_id": "b", "candidate": 0, "baseline": 4},
        {"game_id": "c", "candidate": 9, "baseline": 8},
    ]
    shifted = [
        {**row, "candidate": row["candidate"] + 10000,
         "baseline": row["baseline"] + 10000}
        for row in rows
    ]
    assert clustered_difference(rows, repetitions=400, seed=19) == clustered_difference(
        shifted, repetitions=400, seed=19
    )


def test_invalid_boolean_metric_fails_closed():
    rows = [
        {"game_id": "a", "candidate": True, "baseline": 0},
        {"game_id": "b", "candidate": 1, "baseline": 0},
    ]
    with pytest.raises(ValueError, match="finite numbers"):
        clustered_difference(rows, repetitions=100)
