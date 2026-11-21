"""Synthetic dispatch/binding tests; no cohort search or target reference."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import named_metered_campaign as gate
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256


@pytest.fixture
def setup(monkeypatch, tmp_path):
    moves = [{'action': [[31, 26], [], False], 'jass_key': '31-26'},
             {'action': [[31, 27], [], False], 'jass_key': '31-27'}]
    target = {'target_fen': 'target', 'source_fens': {'L': 'source', 'LCB': 'source'},
              'target_games': ['game:1'], 'legal_moves': moves}
    manifest = {'event': 'P1RUlfJc', 'engine': {'jass_node_budgets': [10000, 50000, 200000], 'scan_binary_sha256': 'binary'},
                'targets': [{'source_fen': 'source', 'target_fen': 'target', 'legal_moves': moves}],
                'benchmark_targets': [target]}
    proof = {'published_commit': 'a' * 40, 'manifest_sha256': 'manifest', 'scientific_freeze': True}
    reference = {'schema': 'mtdp-jass-scan-reference-v1', 'role': 'source', 'cohort_sha256': 'manifest',
                 'scan_binary_sha256': 'binary', 'scan_eval_sha256': SCAN_EVAL_SHA256, 'scan_ini_sha256': SCAN_INI_SHA256,
                 'scan_successor_depth': 12, 'publication_verification': proof, 'execution_sha256': {},
                 'action_scores_centimen': {'source': [{'action': m['action'], 'score': i} for i,m in enumerate(moves)]}}
    source = tmp_path / 'source.json'; source.write_bytes(gate._bytes(reference))
    calls = []
    monkeypatch.setattr(gate, 'published_manifest', lambda *a: (manifest, proof))
    monkeypatch.setattr(gate, 'execution_fingerprints', lambda *a: {})
    monkeypatch.setattr(gate, 'METHOD_FILES', ())
    monkeypatch.setattr(gate, 'checked_build', lambda *a: {'unit': True})
    def smoke(*a, **k):
        calls.append(k)
        assert k['expected_legal_keys'] == ['31-26', '31-27']
        assert k['prefix'] == ['31-27', '31-26']
        return {'paired_comparable': True, 'verification_nodes': 0, 'main_nodes': k['total_nodes']}
    monkeypatch.setattr(gate, 'technical_smoke', smoke)
    def invoke(): return gate.campaign(tmp_path, 'cohort', 'a' * 40, source, tmp_path, tmp_path, tmp_path/'out')
    return SimpleNamespace(manifest=manifest, proof=proof, reference=reference, source=source, calls=calls,
                           invoke=invoke, out=tmp_path/'out')


def test_full_fixed_population_and_three_budgets(setup):
    report = setup.invoke()
    assert report['complete'] and [r['total_nodes'] for r in setup.calls] == [10000,50000,200000]
    assert all(r['planned']==r['recorded']==r['paired_comparable']==1 for r in report['counts'].values())


def test_no_source_or_build_access_before_remote_proof(setup, monkeypatch):
    def stop(*a): raise ValueError('publication missing')
    monkeypatch.setattr(gate, 'published_manifest', stop)
    monkeypatch.setattr(gate, 'checked_build', lambda *a: pytest.fail('premature build input'))
    setup.source.unlink()
    with pytest.raises(ValueError, match='publication'): setup.invoke()
    assert not setup.out.exists() and not setup.calls


@pytest.mark.parametrize('field,value', [('role','target'),('scan_successor_depth',16),('cohort_sha256','changed')])
def test_target_or_unbound_reference_cannot_drive_ordering(setup, field, value):
    setup.reference[field]=value;setup.source.write_bytes(gate._bytes(setup.reference))
    with pytest.raises(ValueError): setup.invoke()
    assert not setup.out.exists() and not setup.calls


def test_foreign_source_publication_is_rejected(setup):
    setup.reference['publication_verification']={**setup.proof,'published_commit':'b'*40}
    setup.source.write_bytes(gate._bytes(setup.reference))
    with pytest.raises(ValueError): setup.invoke()
    assert not setup.out.exists()


def test_empty_population_is_recorded_without_search(setup):
    setup.manifest['targets']=[];setup.manifest['benchmark_targets']=[]
    setup.reference['action_scores_centimen']={};setup.source.write_bytes(gate._bytes(setup.reference))
    result=setup.invoke()
    assert result['complete'] and not setup.calls
    assert all(r['planned']==r['recorded']==0 for r in result['counts'].values())


def test_failure_retains_identity_and_no_completion(setup, monkeypatch):
    def fail(*a,**k): raise RuntimeError('engine crash')
    monkeypatch.setattr(gate,'technical_smoke',fail)
    with pytest.raises(RuntimeError,match='engine crash'):setup.invoke()
    assert (setup.out/'10000/00000-FAILED.json').exists()
    assert not (setup.out/'complete.json').exists()


def test_depth_ceiling_receipt_is_kept_and_excluded(setup, monkeypatch):
    monkeypatch.setattr(gate,'technical_smoke',lambda *a,**k:{'paired_comparable':False})
    result=setup.invoke()
    assert all(r['recorded']==r['depth_ceiling_excluded']==1 and r['paired_comparable']==0 for r in result['counts'].values())


def test_previous_campaign_is_not_overwritten(setup):
    setup.out.mkdir();(setup.out/'prior').write_text('preserved')
    with pytest.raises(FileExistsError): setup.invoke()
    assert (setup.out/'prior').read_text()=='preserved' and not setup.calls


def test_build_receipt_pins_actual_binary_and_input_set(monkeypatch,tmp_path):
    inputs={n:gate.digest(n.encode()) for n in gate.BUILD_INPUTS}
    lock={'schema':'mtdp-named-jass-runner-builds-v1','jass_commit':gate.JASS_COMMIT,
          'configuration':{'build_type':'Release','simd':False,'native':False,'main_initial_only':True},
          'build_inputs':inputs,'binaries':{r:{'sha256':gate.digest(r.encode())} for r in ('probe','main')}}
    for r in ('probe','main'):(tmp_path/r).write_bytes(r.encode())
    monkeypatch.setattr(gate,'_blob',lambda root,commit,name:gate._bytes(lock) if name==gate.BUILD_RECEIPT else name.encode())
    gate.checked_build(tmp_path,'a'*40,tmp_path/'probe',tmp_path/'main')
    (tmp_path/'probe').write_bytes(b'altered')
    with pytest.raises(ValueError,match='executable'):gate.checked_build(tmp_path,'a'*40,tmp_path/'probe',tmp_path/'main')
