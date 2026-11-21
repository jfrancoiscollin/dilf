"""Exploratory depth20 controls never change the previously frozen population."""
from pathlib import Path

import pytest
from pedagogy.game import initial_state
from research.mtdp.jass_benchmark import two_arena_depth20 as d

A = ((1,6),(),False)
B = ((2,7),(),False)


def test_subset_uses_all_frozen_equal_pairs_and_original_LCB_source_only():
    t = {'target_fen':'t','source_fens':{'L':'other','LCB':'fixed'},'legal_moves':[],
         'same_full_quiet_signature':{'LCB':True},'bootstrap_owner':'g','target_games':['g'],'known_cost':0}
    joint = {'events':{d.runtime.study.EVENTS[0]:{'benchmark_targets':[t]},
                       d.runtime.study.EVENTS[1]:{'benchmark_targets':[{**t,'target_fen':'excluded',
                                                    'same_full_quiet_signature':{'LCB':False},'known_cost':260}]}}}
    selected,flat,identity = d.subset(joint)
    assert len(selected) == 1 and flat['targets'][0]['source_fen'] == 'fixed'
    assert identity[0]['owner'] == 'g'
    t['known_cost'] = 999
    assert d.subset(joint)[1:] == (flat,identity)  # neither zero nor large costs select a new pair


def test_unpublished_plan_precedes_any_engine_or_output(monkeypatch,tmp_path):
    def blocked(*args):raise ValueError('plan is not published')
    monkeypatch.setattr(d,'published_plan',blocked)
    monkeypatch.setattr(d.runtime,'scan_fingerprints',lambda *a:pytest.fail('engine reached before plan'))
    with pytest.raises(ValueError,match='not published'):
        d.score(tmp_path,'p',tmp_path,tmp_path,'source',tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_depth20_transport_allowance_keeps_new_game_and_exact_depth():
    s = d.Depth20Scan(Path('.'),depth=20);commands=[];timeouts=[]
    s.send = lambda *args:commands.extend(args)
    lines = iter(['info depth=20 score=0.10','done move=1-6'])
    class Queue:
        def get(self,timeout):timeouts.append(timeout);return next(lines)
    s.lines = Queue()
    assert s.score(initial_state()) == 10
    assert 'new-game' in commands and 'level depth=20' in commands and 'go analyze' in commands
    assert timeouts == [120,120]


@pytest.fixture
def packet():
    p = {'scope':'exploratory','mask_sha256':'c'*64,'parent_manifest_sha256':'b'*64,
         'engines':{'scan_sha256':'d'*64},'method_files_sha256':{'fixture':'a'*64}}
    r = {'schema':'mtdp-jass-scan-reference-v1','role':'source','reference_kind':'source20_exploratory',
         'primary_source_usable':False,'sensitivity_plan_commit':'e'*40,'sensitivity_plan_sha256':'f'*64,
         'execution_sha256':p['method_files_sha256'],'parent_manifest_sha256':p['parent_manifest_sha256'],
         'scope':p['scope'],'scan_ini_sha256':d.SCAN_INI_SHA256,'cohort_sha256':p['mask_sha256'],
         'scan_binary_sha256':'d'*64,'scan_eval_sha256':d.SCAN_EVAL_SHA256,'scan_successor_depth':20,
         'action_scores_centimen':{},'publication_verification':{'published_commit':d.FREEZE,'scientific_freeze':True}}
    return p,r


def test_empty_reference_is_still_bound_to_depth_mask_plan_and_role(packet):
    p,r = packet
    assert d.validate_packet(r,'source',p,'f'*64,'e'*40,{'targets':[]}) == {}


@pytest.mark.parametrize('field,value',[('primary_source_usable',True),('scan_successor_depth',16),
    ('cohort_sha256','0'*64),('reference_kind','source12'),('sensitivity_plan_commit','0'*40)])
def test_wrong_packet_cannot_enter_sensitivity(packet,field,value):
    p,r = packet;r[field] = value
    with pytest.raises(ValueError):d.validate_packet(r,'source',p,'f'*64,'e'*40,{'targets':[]})


def test_tie_pick_failure_is_distinct_from_disjoint_optimum_sets():
    selected = [{'event':d.runtime.study.EVENTS[0],'target_fen':'t','source_fens':{'LCB':'s'},
                 'bootstrap_owner':'g','target_games':['g']}]
    a, = d.compared_rows(selected,{'s':{A:1,B:0}},{'t':{A:0,B:5}})
    b, = d.compared_rows(selected,{'s':{A:1,B:1}},{'t':{A:0,B:5}})
    assert a['disjoint'] == 1 and b['disjoint'] == 0
    assert a['pick_optimal'] == b['pick_optimal'] == 0
    assert a['ordinary_regret'] == b['ordinary_regret'] == 5
