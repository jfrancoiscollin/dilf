"""Equal-depth comparison semantics on invented action scores only."""
import pytest
from research.mtdp.jass_benchmark import named_source16_sensitivity as s


def test_fixed_same_depth_comparison_disjoint_optima():
    a,b=((31,26),(),False),((31,27),(),False)
    m={'benchmark_targets':[{'target_fen':'t','target_games':['g'],'source_fens':{'L':'s','LCB':'s'}}]}
    r=s.compare(m,{'s':{a:10,b:0}},{'t':{a:0,b:20}})
    assert r['LCB']['optimal_sets_intersect']==0 and r['LCB']['mean_regret']==20
    assert r['L']['source_pick_target_optimal']==0


def test_tied_source_optimum_is_distinct_from_selected_pick():
    a,b=((31,26),(),False),((31,27),(),False)
    m={'benchmark_targets':[{'target_fen':'t','target_games':['g'],'source_fens':{'L':'s','LCB':'s'}}]}
    r=s.compare(m,{'s':{a:10,b:10}},{'t':{a:0,b:20}})['LCB']
    assert r['optimal_sets_intersect']==1 and r['source_pick_target_optimal']==0


def test_empty_population_is_preserved():
    r=s.compare({'benchmark_targets':[]},{},{})
    assert r['LCB']['positions']==0 and r['LCB']['mean_regret'] is None


def test_no_engine_input_or_output_before_remote_proof(monkeypatch,tmp_path):
    def closed(*a):raise ValueError('closed publication')
    monkeypatch.setattr(s.runtime,'published_manifest',closed)
    monkeypatch.setattr(s.runtime,'scan_fingerprints',lambda *a:pytest.fail('premature binary read'))
    with pytest.raises(ValueError,match='closed publication'):
        s.audit(tmp_path,'cohort','a'*40,'b'*40,tmp_path,tmp_path,tmp_path/'out')
    assert not (tmp_path/'out').exists()
