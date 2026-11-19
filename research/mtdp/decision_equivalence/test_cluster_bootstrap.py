"""Synthetic checks only; no FMJD outcome claims."""
import pytest
from research.mtdp.decision_equivalence.cluster_bootstrap import paired_game_bootstrap


def row(pid, game, scores, proposed, baseline):
    legal = list(scores)
    return dict(id=pid, game_id=game, legal=legal, scores=scores,
                proposed=proposed, baseline=baseline)


def test_reproducible_and_game_clustered():
    scores = dict(zip('abcd', [4, 3, 2, 1]))
    rows = [row('p1', 'g1', scores, list('abcd'), list('dcba')),
            row('p2', 'g1', scores, list('abcd'), list('dcba')),
            row('p3', 'g2', scores, list('dcba'), list('abcd'))]
    result = paired_game_bootstrap(rows, repetitions=200, seed=7)
    assert result == paired_game_bootstrap(rows, repetitions=200, seed=7)
    assert result['n_games'] == 2 and result['n_primary_ge4'] == 3
    assert result['delta_recall3'] == pytest.approx(1/3)
    assert result['delta_first_regret_raw'] == pytest.approx(-1)
    assert result['delta_recall3_ci95'][0] <= result['delta_recall3'] <= result['delta_recall3_ci95'][1]


def test_primary_denominator_ignores_score_ties():
    tied = dict(zip('abcd', [1, 1, 1, 1]))
    result = paired_game_bootstrap([row('x', 'g', tied, list('abcd'), list('dcba'))], repetitions=100)
    assert result['n_primary_ge4'] == 1
    assert result['delta_recall3'] == 0


def test_duplicate_rejected():
    scores = {'a': 1}
    r = row('x', 'g', scores, ['a'], ['a'])
    with pytest.raises(ValueError, match='duplicate'):
        paired_game_bootstrap([r, r], repetitions=100)


def test_no_primary_is_explicit():
    r = row('x', 'g', {'a': 2, 'b': 1}, ['a', 'b'], ['b', 'a'])
    result = paired_game_bootstrap([r], repetitions=100)
    assert result['delta_recall3'] is None
    assert result['delta_recall3_ci95'] is None
    assert result['delta_first_regret_raw'] == -1


def test_primary_regret_excludes_small_branching_positions():
    four = row('wide', 'game1', dict(zip('abcd', [4, 3, 2, 1])),
               list('abcd'), list('dcba'))
    two = row('narrow', 'game2', {'a': 100, 'b': 0}, ['b', 'a'], ['a', 'b'])
    result = paired_game_bootstrap([four, two], repetitions=200, seed=17)
    assert result['n_primary_ge4'] == 1
    assert result['delta_first_regret_primary_ge4_raw'] == -3
    assert result['delta_first_regret_raw'] == pytest.approx(48.5)
    assert result['delta_first_regret_primary_ge4_ci95'] is None
    assert result['delta_first_regret_primary_ge4_ci95_exploratory'] == [-3, -3]
    assert result['primary_ci_status'] == 'insufficient_cluster_coverage'


def test_no_primary_regret_explicitly_undefined():
    two = row('narrow', 'game', {'a': 2, 'b': 1}, ['a', 'b'], ['b', 'a'])
    result = paired_game_bootstrap([two], repetitions=100)
    assert result['delta_first_regret_primary_ge4_raw'] is None
    assert result['delta_first_regret_primary_ge4_ci95'] is None
    assert result['delta_first_regret_raw'] == -1


def test_sparse_primary_games_coverage_gate():
    rows = [row(f'p{i}', f'g{i}', {'a': 4, 'b': 3, 'c': 2, 'd': 1}
                if i == 0 else {'a': 2, 'b': 1},
                list('abcd') if i == 0 else ['a', 'b'],
                list('dcba') if i == 0 else ['b', 'a']) for i in range(10)]
    result = paired_game_bootstrap(rows, repetitions=1000, seed=19)
    assert result['n_primary_games'] == 1
    assert result['primary_ci_status'] == 'insufficient_cluster_coverage'
    assert result['delta_recall3_ci95'] is None
    assert result['n_bootstrap_undefined_primary'] > 0
    assert result['n_bootstrap_defined_primary'] + result['n_bootstrap_undefined_primary'] == 1000
    assert result['bootstrap_primary_defined_ratio'] < .95


def test_all_games_primary_full_coverage():
    scores = dict(zip('abcd', [4, 3, 2, 1]))
    rows = [row(f'p{i}', f'g{i}', scores, list('abcd'), list('dcba')) for i in range(5)]
    result = paired_game_bootstrap(rows, repetitions=200, seed=4)
    assert result['n_primary_games'] == 5
    assert result['n_bootstrap_defined_primary'] == 200
    assert result['n_bootstrap_undefined_primary'] == 0
    assert result['bootstrap_primary_defined_ratio'] == 1
    assert result['primary_ci_status'] == 'ok'
    assert result['delta_recall3_ci95'] == [1, 1]


def test_coverage_counts_reproducible():
    rows = [row('p1', 'g1', dict(zip('abcd', [4, 3, 2, 1])), list('abcd'), list('dcba')),
            row('p2', 'g2', {'a': 2, 'b': 1}, ['a', 'b'], ['b', 'a'])]
    a = paired_game_bootstrap(rows, repetitions=200, seed=101)
    b = paired_game_bootstrap(rows, repetitions=200, seed=101)
    assert a == b
    assert a['n_bootstrap_defined_primary'] + a['n_bootstrap_undefined_primary'] == 200
