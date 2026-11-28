"""Deductive tied-optimum and stratified whole-game estimand checks."""
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark import two_arena_analysis as a

E0,E1 = a.runtime.study.EVENTS
A = ((1,6),(),False)
B = ((2,7),(),False)


def population():
    return [{'event':e,'owner':g,'fen':f} for e,g,f in (
        (E0,'g1','p1'),(E0,'g2','p2'),(E1,'g3','p3'),(E1,'g3','p4'),(E1,'g4','p5'))]


def test_bootstrap_position_weighted_ratio_and_fixed_arena_strata():
    pop = population();rows = [{**r,'x':100 if r['owner'] == 'g2' else 0} for r in pop]
    result = a.bootstrap(rows,pop,'x')
    assert result['mean'] == 20  # five positions; not mean of four game means (25)
    assert result['owner_games'] == 4 and result['sampling_owner_games'] == {E0:2,E1:2}
    assert result['ci95'] == [0,50]  # cannot resample all positions from g2 across arenas
    assert result['undefined_draws'] == 0 and result['percentile_indices'] == [249,9749]


def test_paired_fields_use_identical_owner_sampling_frame():
    pop = population();rows = [{**r,'x':100 if r['owner'] == 'g2' else 0} for r in pop]
    for r in rows:r['y'] = r['x']+7
    x,y = a.bootstrap(rows,pop,'x'),a.bootstrap(rows,pop,'y')
    assert y['mean']-x['mean'] == 7
    assert [b-c for b,c in zip(y['ci95'],x['ci95'])] == [7,7]


def test_empty_subgroup_draws_are_reported_not_retried_or_silently_dropped():
    pop = population();r = {**pop[0],'x':5}
    result = a.bootstrap([r],pop,'x')
    assert result['mean'] == 5 and result['sampling_owner_games'] == {E0:2,E1:2}
    assert 2000 < result['undefined_draws'] < 3000 and result['ci95'] is None
    empty = a.bootstrap([],pop,'x')
    assert empty['positions'] == 0 and empty['undefined_draws'] == 10000 and empty['mean'] is None


def test_owner_or_position_duplication_is_not_an_independent_sample():
    pop = population()
    with pytest.raises(ValueError,match='ownership changed'):
        a.bootstrap([{**pop[0],'owner':'unknown','x':0}],pop,'x')
    with pytest.raises(ValueError,match='Duplicate position'):
        a.bootstrap([{**pop[0],'x':0},{**pop[0],'x':1}],pop,'x')


def test_geometry_separates_disjoint_sets_source_tie_and_common_frozen_LCB_mask():
    def target(fen,owner,equal):
        return {'target_fen':fen,'bootstrap_owner':owner,'target_games':[owner],
                'source_fens':{'L':'sL','LCB':'sTie' if equal else 'sA'},
                'same_full_quiet_signature':{'L':False,'LCB':equal}}
    joint = {'events':{E0:{'benchmark_targets':[target('tB','g1',True),target('tA','g2',False)]},
                       E1:{'benchmark_targets':[]}}}
    sources = {'sL':{A:1,B:0},'sTie':{A:0,B:0},'sA':{A:1,B:0}}
    targets = {'tB':{A:0,B:10},'tA':{A:0,B:5}}
    result = a.geometry(joint,sources,targets)
    primary = result['LCB']['estimates']['all']['LCB_full_equal']
    assert primary['positions'] == 1 and primary['optimal_sets_disjoint'] == 0
    assert primary['source_pick_target_optimal'] == 0 and primary['ordinary_mean_regret'] == 10
    assert primary['suboptimal_pick_despite_optimum_intersection'] == 1
    assert result['LCB']['estimates']['all']['LCB_full_different']['optimal_sets_disjoint'] == 1
    # L stays on the same LCB-defined mask even though its own full signature differs.
    assert result['L']['estimates']['all']['LCB_full_equal']['positions'] == 1
    assert result['LCB']['estimates'][E1]['all']['positions'] == 0


def test_geometry_retains_categorical_cost_instead_of_fabricating_ordinary_regret():
    row = {'event':E0,'owner':'g','fen':'p','a_to_b':{'best_category':'win','transferred_category':'ordinary'},
           'disjoint':1,'pick_optimal':0,'ordinary_regret':None,'positive_regret':None}
    result = a._summary_geometry([row],[row])
    assert result['ordinary_positions'] == 0 and result['ordinary_mean_regret'] is None
    assert result['optimal_sets_disjoint'] == 1 and result['category_transitions'] == {'win/ordinary':1}


def test_analysis_code_must_have_preceded_target_opening(monkeypatch,tmp_path):
    root = Path(__file__).resolve().parents[3]
    monkeypatch.setattr(a.runtime,'published',lambda *args:({},{}))
    monkeypatch.setattr(a.runtime,'method',lambda *args:{})
    monkeypatch.setattr(a.runtime,'_blob',lambda *args:b'changed pre-target implementation')
    with pytest.raises(ValueError,match='pre-target decisions commit'):
        a.analyze(root,'p','f'*40,'d'*40,'decisions',tmp_path/'missing-source',tmp_path/'missing-target')
