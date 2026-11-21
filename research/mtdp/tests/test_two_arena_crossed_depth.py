"""Changes of source choice and target horizon need crossed, matched pairs."""
import pytest
from research.mtdp.jass_benchmark import two_arena_crossed_depth as c

A, B = ((1, 6), (), False), ((2, 7), (), False)


def fixture(s16, s20, t16, t20):
    selected = [{'event': c.depth.runtime.study.EVENTS[0], 'target_fen': 't',
                 'source_fens': {'LCB': 's'}, 'bootstrap_owner': 'g', 'target_games': ['g']}]
    return c.crossed_rows(selected, {16: {'s': s16}, 20: {'s': s20}},
                          {16: {'t': t16}, 20: {'t': t20}})[0]


def test_both_paths_and_interaction_expose_confounded_matched_delta():
    r = fixture({A: 2, B: 0}, {A: 0, B: 2}, {A: 1, B: 11}, {A: 9, B: 5})
    assert [r['cells'][k]['ordinary_regret'] for k in c.CELLS] == [10, 0, 0, 4]
    assert r['source_pick_changed']
    assert r['matched_total'] == -6
    assert (r['target_at_source16'], r['source_at_target20']) == (-10, 4)
    assert (r['source_at_target16'], r['target_at_source20']) == (-10, 4)
    assert r['interaction'] == 14


def test_source_tie_retains_full_optimum_set_but_freezes_canonical_pick():
    r = fixture({B: 1, A: 1}, {B: 1, A: 1}, {A: 0, B: 5}, {A: 1, B: 3})
    assert not r['source_pick_changed']
    assert r['cells']['S16_T16']['disjoint'] == 0
    assert r['cells']['S16_T16']['pick_optimal'] == 0
    assert r['target_at_source16'] == -3
    assert r['source_at_target20'] == r['source_at_target16'] == r['interaction'] == 0


def test_one_categorical_cell_suppresses_all_effects_without_dropping_pair():
    r = fixture({A: 1, B: 0}, {A: 0, B: 1}, {A: 1, B: 5}, {A: 9000, B: 1})
    assert not r['all_four_ordinary'] and set(r['cells']) == set(c.CELLS)
    assert all(r[k] is None for k in c.EFFECTS)
    assert r['cells']['S16_T20']['a_to_b']['best_category'] == 'win'


def test_missing_action_never_becomes_a_different_offdiagonal_denominator():
    with pytest.raises(KeyError):
        fixture({A: 2, B: 0}, {A: 0, B: 2}, {A: 1, B: 11}, {B: 5})


def test_offline_archive_fails_if_worktree_bytes_differ_from_published_blob(monkeypatch, tmp_path):
    base = tmp_path / c.BASE
    base.mkdir(parents=True)
    (base / 'a.json').write_bytes(b'{}')
    monkeypatch.setattr(c.depth.runtime, '_blob', lambda *a: b'{"changed":true}')
    with pytest.raises(ValueError, match='Archived input changed'):
        c.archived(tmp_path, 'commit', 'a.json')
