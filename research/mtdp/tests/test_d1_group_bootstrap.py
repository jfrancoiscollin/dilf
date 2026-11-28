"""Synthetic checks for game-cluster inference; not empirical FMJD evidence."""
import pytest

from research.mtdp.decision_equivalence.group_bootstrap import paired_game_bootstrap


def test_deterministic_and_game_weighted():
    rows = [("a", "p1", 0, 1), ("a", "p2", 0, 1), ("a", "p3", 0, 1),
            ("b", "p4", 1, 0)]
    x = paired_game_bootstrap(rows, seed=9, replicates=300)
    assert x == paired_game_bootstrap(reversed(rows), seed=9, replicates=300)
    assert x["estimate"] == 0
    assert x["n_games"] == 2 and x["n_positions"] == 4
    assert x["ci_lower"] <= 0 <= x["ci_upper"]


def test_constant_deltas_have_degenerate_interval():
    x = paired_game_bootstrap([("a", "p1", 2, 3), ("b", "p2", 4, 5)])
    assert x["estimate"] == x["ci_lower"] == x["ci_upper"] == 1


@pytest.mark.parametrize("rows", [[], [("a", "p", 0, 1)],
    [("a", "p", 0, 1), ("b", "p", 0, 1)],
    [("a", "p", float("nan"), 1), ("b", "q", 0, 1)],
    [("a", "p", True, 1), ("b", "q", 0, 1)]])
def test_invalid_rows_rejected(rows):
    with pytest.raises(ValueError):
        paired_game_bootstrap(rows)


def test_invalid_settings():
    rows = [("a", "p", 0, 1), ("b", "q", 0, 1)]
    for kwargs in ({"replicates": 1}, {"seed": True}, {"confidence": 1}):
        with pytest.raises(ValueError):
            paired_game_bootstrap(rows, **kwargs)


def test_finite_large_scores_do_not_overflow_group_or_bootstrap_means():
    # Ordinary sum([1e308, 1e308]) overflows, but their mean is finite.
    rows = [("a", "p1", 0.0, 1e308), ("a", "p2", 0.0, 1e308),
            ("b", "p3", 0.0, 1e308), ("b", "p4", 0.0, 1e308)]
    result = paired_game_bootstrap(rows, seed=7, replicates=100)
    assert result["estimate"] == 1e308
    assert result["ci_lower"] == result["ci_upper"] == 1e308


def test_finite_large_scores_mixed_sign_remain_finite():
    rows = [("a", "p1", 0.0, 1e308), ("a", "p2", 0.0, -1e308),
            ("b", "p3", 0.0, 1e308), ("b", "p4", 0.0, -1e308)]
    result = paired_game_bootstrap(rows, seed=11, replicates=100)
    assert result["estimate"] == 0.0
    assert result["ci_lower"] == result["ci_upper"] == 0.0
