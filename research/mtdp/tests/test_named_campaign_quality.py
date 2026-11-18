"""Pre-target analysis regressions on invented scores and receipts only."""
import copy
import json

import pytest

from research.mtdp.jass_benchmark import named_campaign_quality as q


def test_bootstrap_whole_games_and_known_negative_difference():
    values = [('one', -20), ('one', -20), ('two', -20)]
    result = q.bootstrap(values)
    assert result['positions'] == 3 and result['games'] == 2
    assert result['mean'] == -20 and result['ci95'] == [-20, -20]
    assert result == q.bootstrap(values)


def test_empty_and_one_game_have_no_artificial_interval():
    assert q.bootstrap([])['mean'] is None and q.bootstrap([])['ci95'] is None
    assert q.bootstrap([('one', 4), ('one', 6)])['ci95'] is None


def sample():
    target={'target_fen':'f','target_games':['g:1'],'legal_moves':[{'jass_key':'a'},{'jass_key':'b'}]}
    r={'fen':'f','games':['g:1'],'budget':10000,'LCB_prefix':['b','a'],'native_legal_actions':2,
       'verification_receipts':[{'issued_limit':1000,'nodes':100}], 'verification_nodes':100,
       'main_limit':9900,'main_nodes':9900,'complete_budget':True,'paired_comparable':True,
       'native_baseline':{'best_move':'a','nodes':10000,'depth_ceiling':False},
       'lcb_baseline':{'best_move':'b','nodes':10000,'depth_ceiling':False},
       'control_main':{'best_move':'b','nodes':9900,'depth_ceiling':False}}
    return target,r


def test_valid_total_accounting_and_explicit_ceiling():
    t,r=sample(); assert q.check_receipt(r,t,10000,['b','a'])
    r['native_baseline'].update(nodes=9999,depth_ceiling=True);r['paired_comparable']=False
    assert not q.check_receipt(r,t,10000,['b','a'])


@pytest.mark.parametrize('error', ['verification','main','flag','legal','prefix','budget','ceiling'])
def test_wrong_decision_receipts_cannot_enter_estimate(error):
    t,r=sample()
    if error=='verification':r['verification_nodes']=99
    elif error=='main':r['control_main']['nodes']=9901
    elif error=='flag':r['paired_comparable']=False
    elif error=='legal':r['native_baseline']['best_move']='illegal'
    elif error=='prefix':r['LCB_prefix']=['a','b']
    elif error=='budget':r['budget']=50000
    else:r['control_main']['depth_ceiling']=True
    with pytest.raises(ValueError):q.check_receipt(r,t,10000,['b','a'])


def test_complete_analysis_on_known_invented_scores(monkeypatch,tmp_path):
    moves=[{'action':[[31,26],[],False],'jass_key':'a'},{'action':[[31,27],[],False],'jass_key':'b'}]
    targets=[{'target_fen':f'f{i}','target_games':[f'g:{i}'],'source_fens':{'L':'s','LCB':'s'},'legal_moves':moves} for i in (1,2)]
    manifest={'event':'unit','engine':{'scan_binary_sha256':'binary'},'benchmark_targets':targets,
              'targets':[{'source_fen':'s','target_fen':t['target_fen'],'legal_moves':moves} for t in targets]}
    proof={'published_commit':'a'*40,'manifest_sha256':'manifest','scientific_freeze':True}
    def reference(role):
        fens=['s'] if role=='source' else ['f1','f2']
        return {'schema':'mtdp-jass-scan-reference-v1','role':role,'cohort_sha256':'manifest',
                'scan_binary_sha256':'binary','scan_eval_sha256':q.SCAN_EVAL_SHA256,'scan_ini_sha256':q.SCAN_INI_SHA256,
                'scan_successor_depth':12 if role=='source' else 16,'publication_verification':proof,'execution_sha256':{},
                'action_scores_centimen':{f:[{'action':m['action'],'score':i*20} for i,m in enumerate(moves)] for f in fens}}
    source=tmp_path/'source';source.write_bytes(q._bytes(reference('source')))
    target=tmp_path/'target';target.write_bytes(q._bytes(reference('target')))
    receipts=tmp_path/'receipts';receipts.mkdir()
    complete={'complete':True,'publication_verification':proof,'source_sha256':q.digest(source.read_bytes()),
              'planned_targets':2,'budgets':[10000,50000,200000]}
    (receipts/'complete.json').write_bytes(q._bytes(complete))
    for budget in complete['budgets']:
        d=receipts/str(budget);d.mkdir()
        for i,t in enumerate(targets):
            _,r=sample();r.update(fen=t['target_fen'],games=t['target_games'],budget=budget,main_limit=budget-100,main_nodes=budget-100)
            r['verification_receipts'][0]['issued_limit']=budget//10
            for field in q.ARMS.values():r[field]['nodes']=budget-100 if field=='control_main' else budget
            r.update(intervention='b',decision_reason='unit_verified_tie')
            (d/f'{i:05d}.json').write_bytes(q._bytes(r))
    monkeypatch.setattr(q,'published_manifest',lambda *a:(manifest,proof))
    monkeypatch.setattr(q,'execution_fingerprints',lambda *a:{})
    result=q.analyze(tmp_path,'unit','a'*40,source,target,receipts)
    primary=result['budgets']['50000']
    assert primary['paired']==2 and primary['optimum_hits_paired']=={'native':0,'lcb':2,'control':2}
    assert primary['control_minus_native']['mean']==-20
    assert primary['control_minus_native']['ci95']==[-20,-20]
    assert primary['control_minus_lcb']['mean']==0
    assert len(primary['changed_choice_cases'])==2
