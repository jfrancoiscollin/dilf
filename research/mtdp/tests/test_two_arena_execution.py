"""New-study reference/decision separation, with empty synthetic contracts only."""
import copy
import json
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark import two_arena_execution as run
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def state():
    reg = run.study.load(ROOT)
    joint = {'schema':'mtdp-two-arena-joint-manifest-v1','event_order':list(run.study.EVENTS),
             'study_id':reg['study_id'],'engines':reg['engines'],'analysis':reg['analysis'],
             'events':{e:{'benchmark_targets':[]} for e in run.study.EVENTS}}
    proof = {'scientific_freeze':True,'published_commit':'f'*40,'observed_branch_head':'f'*40,'manifest_sha256':'c'*64}
    methods = {'fixture':'a'*64}
    source = {'schema':'mtdp-jass-scan-reference-v1','role':'source','reference_kind':'source12',
              'primary_source_usable':True,'cohort_sha256':proof['manifest_sha256'],
              'publication_verification':proof,'execution_sha256':methods,
              'scan_binary_sha256':reg['engines']['scan_sha256'],'scan_eval_sha256':SCAN_EVAL_SHA256,
              'scan_ini_sha256':SCAN_INI_SHA256,'scan_successor_depth':12,'action_scores_centimen':{}}
    return joint,proof,methods,source


def test_remote_proof_precedes_engine_and_output(monkeypatch,tmp_path):
    def blocked(*a):raise ValueError('no published freeze')
    monkeypatch.setattr(run,'published',blocked)
    monkeypatch.setattr(run,'method',lambda *a:pytest.fail('method reached before proof'))
    with pytest.raises(ValueError,match='published freeze'):
        run.reference(tmp_path,'prefix','f'*40,tmp_path,tmp_path,'source12',tmp_path/'out')
    with pytest.raises(ValueError,match='published freeze'):
        run.campaign(tmp_path,'prefix','f'*40,tmp_path,tmp_path,tmp_path,tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_flat_manifest_keeps_both_fixed_sources_and_deduplicates_equal_source(state):
    joint,*_ = state
    t = {'target_fen':'target','source_fens':{'L':'source1','LCB':'source2'},'legal_moves':[]}
    joint['events'][run.study.EVENTS[0]]['benchmark_targets'] = [t]
    flat = run.flat_manifest(joint)
    assert [r['source_fen'] for r in flat['targets']] == ['source1','source2']
    t['source_fens']['LCB'] = 'source1'
    assert len(run.flat_manifest(joint)['targets']) == 1


def test_cross_arena_target_alias_refused(state):
    joint,*_ = state
    for event in run.study.EVENTS:
        joint['events'][event]['benchmark_targets'] = [{'target_fen':'same','source_fens':{'L':'s','LCB':'s'},'legal_moves':[]}]
    with pytest.raises(ValueError,match='Duplicate cross-arena'):run.flat_manifest(joint)


@pytest.mark.parametrize('kind',['source16','target16',None])
def test_wrong_packet_kind_cannot_rank_jass(state,kind):
    joint,proof,methods,source = state;source['reference_kind'] = kind
    with pytest.raises(ValueError,match='Only the separate source12'):
        run._source12(joint,proof,source,methods)


def test_relabelling_source16_still_fails_fixed_depth(state):
    joint,proof,methods,source = state;source['scan_successor_depth'] = 16
    with pytest.raises(ValueError,match='depth-12'):
        run._source12(joint,proof,source,methods)


def test_target16_requires_published_complete_decisions_before_engine(state,monkeypatch,tmp_path):
    joint,proof,methods,_ = state
    monkeypatch.setattr(run,'published',lambda *a:(joint,proof))
    monkeypatch.setattr(run,'method',lambda *a:methods)
    monkeypatch.setattr(run,'scan_fingerprints',lambda *a:pytest.fail('target engine reached before decision proof'))
    with pytest.raises(ValueError,match='requires published complete'):
        run.reference(ROOT,'p','f'*40,tmp_path,tmp_path,'target16',tmp_path/'out')
    def blocked(*a):raise ValueError('incomplete published decisions')
    monkeypatch.setattr(run,'published_decisions',blocked)
    with pytest.raises(ValueError,match='incomplete published decisions'):
        run.reference(ROOT,'p','f'*40,tmp_path,tmp_path,'target16',tmp_path/'out','d'*40,'decisions')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('kind,depth,usable',[('source12',12,True),('source16',16,False)])
def test_empty_reference_explicit_fixed_kind_without_engine(state,monkeypatch,tmp_path,kind,depth,usable):
    joint,proof,methods,_ = state
    monkeypatch.setattr(run,'published',lambda *a:(joint,proof));monkeypatch.setattr(run,'method',lambda *a:methods)
    monkeypatch.setattr(run,'scan_fingerprints',lambda *a:{'scan_linux':joint['engines']['scan_sha256'],
        'data/eval':SCAN_EVAL_SHA256,'scan.ini':SCAN_INI_SHA256})
    monkeypatch.setattr(run,'checked_engine',lambda *a:pytest.fail('empty reference called engine'))
    out = tmp_path/'reference.json'
    report = run.reference(ROOT,'p','f'*40,tmp_path,tmp_path,kind,out)
    assert report['scan_successor_depth'] == depth and report['primary_source_usable'] is usable
    assert report['reference_kind'] == kind and report['action_scores_centimen'] == {}
    with pytest.raises(ValueError,match='already exists'):
        run.reference(ROOT,'p','f'*40,tmp_path,tmp_path,kind,out)


def test_empty_campaign_preserves_both_arenas_all_budgets_and_complete_inventory(state,monkeypatch,tmp_path):
    joint,proof,methods,source = state
    monkeypatch.setattr(run,'published',lambda *a:(joint,proof));monkeypatch.setattr(run,'method',lambda *a:methods)
    monkeypatch.setattr(run,'checked_build',lambda *a:{'fixture':True})
    monkeypatch.setattr(run,'technical_smoke',lambda *a,**k:pytest.fail('empty campaign called search'))
    src = tmp_path/'source12.json';src.write_bytes(run._bytes(source));out = tmp_path/'decisions'
    result = run.campaign(ROOT,'p','f'*40,src,tmp_path,tmp_path,out)
    assert result['complete'] is True and set(result['files']) == {'source12.json','plan.json'}
    assert set(result['counts']) == set(run.study.EVENTS)
    assert all(c['planned'] == c['recorded'] == c['paired_comparable'] == 0
               for e in result['counts'].values() for c in e.values())


def test_changed_budgets_refused_before_creating_campaign_output(state,monkeypatch,tmp_path):
    joint,proof,methods,source = state;joint['analysis']['total_node_budgets'] = [10000]
    monkeypatch.setattr(run,'published',lambda *a:(joint,proof));monkeypatch.setattr(run,'method',lambda *a:methods)
    monkeypatch.setattr(run,'checked_build',lambda *a:{})
    src = tmp_path/'source.json';src.write_bytes(run._bytes(source))
    with pytest.raises(ValueError,match='budgets changed'):
        run.campaign(ROOT,'p','f'*40,src,tmp_path,tmp_path,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_missing_decision_inventory_is_rejected(state,monkeypatch,tmp_path):
    joint,proof,methods,_ = state
    complete = {'schema':'mtdp-two-arena-decisions-v1','complete':True,'freeze_commit':proof['published_commit'],
                'manifest_sha256':proof['manifest_sha256'],'execution_sha256':methods,'files':{'source12.json':'a'*64}}
    monkeypatch.setattr(run.subprocess,'run',lambda *a,**k:None)
    monkeypatch.setattr(run,'_blob',lambda *a:run._bytes(complete))
    with pytest.raises(ValueError,match='inventory incomplete'):
        run.published_decisions(ROOT,joint,proof,'d'*40,'decisions',methods)
