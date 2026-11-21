"""Engineering fixtures only; no target data or reference engine is executed."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import named_arena_execution as run

ROOT = Path(__file__).resolve().parents[3]
COMMIT = 'a' * 40


@pytest.fixture
def context(monkeypatch, tmp_path):
    action = [[31, 26], [], False]
    manifest = {'schema': 'mtdp-jass-cohort-v1', 'engine': {
        'scan_binary_sha256': hashlib.sha256(b'binary').hexdigest(),
        'scan_successor_depth': 12, 'target_scan_successor_depth': 16},
        'targets': [{'source_fen': 'W:W31:B1', 'target_fen': 'W:W31:B2',
                     'legal_moves': [{'action': action, 'jass_key': '31-26'}]}]}
    raw = json.dumps(manifest).encode()
    proof = {'scientific_freeze': True, 'published_commit': COMMIT,
             'manifest_sha256': run.digest(raw)}
    calls = []
    monkeypatch.setattr(run, 'verify_publication', lambda *a: (calls.append('proof') or proof))
    monkeypatch.setattr(run, '_blob', lambda *a: raw)
    monkeypatch.setattr(run, 'execution_fingerprints', lambda *a: {'unit-fixture': 'b' * 64})
    monkeypatch.setattr(run, 'SCAN_EVAL_SHA256', run.digest(b'eval'))
    monkeypatch.setattr(run, 'SCAN_INI_SHA256', run.digest(b'ini'))
    binary = tmp_path / 'scan'; binary.write_bytes(b'binary')
    (tmp_path / 'data').mkdir(); (tmp_path / 'data/eval').write_bytes(b'eval')
    (tmp_path / 'scan.ini').write_bytes(b'ini')
    monkeypatch.setattr(run, 'checked_engine', lambda p: (calls.append('adapter') or object()))

    class FakeScan:
        def __init__(self, path, depth): calls.append(('scan', depth))
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(run, 'Scan', FakeScan)
    def score(m, engine, scan, *, role):
        calls.append(('score', role))
        return {'role': role, 'action_scores_centimen': {
            r[f'{role}_fen']: [{'action': action, 'score': 17}] for r in m['targets']}}
    monkeypatch.setattr(run, 'score_manifest', score)
    def invoke(role='source'):
        return run.score_reference(ROOT, 'cohort', COMMIT, tmp_path, binary, role, tmp_path / 'result.json')
    return SimpleNamespace(manifest=manifest, raw=raw, proof=proof, calls=calls, binary=binary,
                           invoke=invoke, output=tmp_path / 'result.json')


@pytest.mark.parametrize('role,depth', [('source', 12), ('target', 16)])
def test_committed_manifest_role_depth_and_proof_are_bound(context, role, depth):
    report = context.invoke(role)
    assert context.calls == ['proof', 'adapter', ('scan', depth), ('score', role)]
    assert report['cohort_sha256'] == context.proof['manifest_sha256']
    assert report['publication_verification']['published_commit'] == COMMIT
    assert report['scan_successor_depth'] == depth
    assert set(report['action_scores_centimen']) == {context.manifest['targets'][0][f'{role}_fen']}
    assert json.loads(context.output.read_bytes()) == report


def test_failed_publication_precedes_all_engine_input_and_output(monkeypatch, context):
    def closed(*args): raise ValueError('Unpublished or synthetic')
    monkeypatch.setattr(run, 'verify_publication', closed)
    monkeypatch.setattr(run, 'scan_fingerprints', lambda *a: pytest.fail('premature engine input'))
    monkeypatch.setattr(run, '_blob', lambda *a: pytest.fail('premature manifest read'))
    with pytest.raises(ValueError, match='Unpublished'): context.invoke()
    assert context.calls == [] and not context.output.exists()


@pytest.mark.parametrize('key,value', [('manifest_sha256', '0' * 64), ('published_commit', 'b' * 40), ('scientific_freeze', False)])
def test_wrong_publication_receipt_stops_before_engine(context, key, value):
    context.proof[key] = value
    with pytest.raises(ValueError, match='snapshot'): context.invoke()
    assert context.calls == ['proof'] and not context.output.exists()


@pytest.mark.parametrize('file', ['scan', 'data/eval', 'scan.ini'])
def test_changed_binary_eval_or_config_cannot_start_engine(context, file):
    (context.binary.parent / file).write_bytes(b'changed')
    with pytest.raises(ValueError, match='Scan binary'): context.invoke()
    assert context.calls == ['proof'] and not context.output.exists()


@pytest.mark.parametrize('role,field', [('source', 'scan_successor_depth'), ('target', 'target_scan_successor_depth')])
def test_depth_cannot_be_overridden(context, monkeypatch, role, field):
    changed = copy.deepcopy(context.manifest); changed['engine'][field] = 8
    monkeypatch.setattr(run, 'published_manifest', lambda *a: (changed, context.proof))
    with pytest.raises(ValueError, match='depth changed'): context.invoke(role)
    assert context.calls == [] and not context.output.exists()


def test_output_never_overwrites_prior_reference(context):
    context.output.write_bytes(b'prior')
    with pytest.raises(ValueError, match='overwrite'): context.invoke()
    assert context.output.read_bytes() == b'prior' and context.calls == ['proof']


@pytest.mark.parametrize('failure', ['missing-action', 'duplicate-action', 'wrong-role'])
def test_bad_reference_is_not_written(context, monkeypatch, failure):
    row = {'action': [[31, 26], [], False], 'score': 17}
    rows = [] if failure == 'missing-action' else [row, row] if failure == 'duplicate-action' else [row]
    monkeypatch.setattr(run, 'score_manifest', lambda *a, **k: {
        'role': 'target' if failure == 'wrong-role' else 'source',
        'action_scores_centimen': {'W:W31:B1': rows}})
    with pytest.raises(ValueError): context.invoke()
    assert not context.output.exists()


def test_failed_scan_keeps_output_absent(context, monkeypatch):
    def failed(*args, **kwargs): raise RuntimeError('technical failure')
    monkeypatch.setattr(run, 'score_manifest', failed)
    with pytest.raises(RuntimeError, match='technical'): context.invoke()
    assert not context.output.exists()


def test_empty_frozen_population_is_retained_without_engine(context, monkeypatch):
    changed = copy.deepcopy(context.manifest); changed['targets'] = []
    monkeypatch.setattr(run, 'published_manifest', lambda *a: (changed, context.proof))
    report = context.invoke()
    assert report['action_scores_centimen'] == {} and context.calls == []


def test_conflicting_source_catalogues_rejected():
    action = {'action': [[31, 26], [], False]}
    rows = [{'source_fen': 'one', 'legal_moves': [action]},
            {'source_fen': 'one', 'legal_moves': [{'action': [[31, 27], [], False]}]}]
    with pytest.raises(ValueError, match='Conflicting'): run.expected_actions({'targets': rows}, 'source')


def test_execution_method_must_match_freeze_commit(monkeypatch):
    monkeypatch.setattr(run, '_blob', lambda root, commit, name: (root / name).read_bytes())
    result = run.execution_fingerprints(ROOT, COMMIT)
    assert set(result) == set(run.METHOD_FILES)
    monkeypatch.setattr(run, '_blob', lambda *a: b'old method')
    with pytest.raises(ValueError, match='changed after freeze'): run.execution_fingerprints(ROOT, COMMIT)


def test_another_checkout_cannot_substitute_execution_method(tmp_path):
    with pytest.raises(ValueError, match='another checkout'): run.execution_fingerprints(tmp_path, COMMIT)
