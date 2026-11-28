"""Synthetic fixtures and a local Git remote, not a real arena publication."""
import copy
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
from research.mtdp.jass_benchmark import named_freeze_bundle as gate
from research.mtdp.jass_benchmark.named_arena_inputs import REGISTRATION, PROTOCOL, check_final, registration
from research.mtdp.jass_cohort import ADAPTER_COMMIT, JASS_COMMIT, SCAN_COMMIT, SCAN_SHA256
ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 11, 18, 21, tzinfo=timezone.utc)
METHOD = 'research/mtdp/jass_benchmark/named_arena_replay.py'

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()

def fixture(tmp_path, root=ROOT, synthetic=True, method=None):
    acquired = tmp_path / 'acquired'; acquired.mkdir()
    reg = registration(root)
    (acquired / 'final-metadata.json').write_bytes(gate._bytes({**reg['event'], 'isFinished': True, 'secondsToStart': 0}))
    marker = '[Synthetic "true"]\r\n' if synthetic else ''
    raw = ('[Event "unit fixture"]\r\n[Site "https://lidraughts.org/SYNTH001"]\r\n' + marker + '[FEN "W:W31:B2"]\r\n\r\n*\r\n').encode()
    (acquired / gate.FIRST).write_bytes(raw); (acquired / 'final-repeat.pdn').write_bytes(raw)
    receipt = {'url': 'https://lidraughts.org/api/tournament/P1RUlfJc/games', 'bytes': len(raw), 'sha256': gate.digest(raw), 'retrieved_at_utc': NOW.isoformat()}
    (acquired / 'final-downloads.json').write_bytes(gate._bytes({'candidate': {'first': {**receipt, 'request_id': 'one'}, 'independent_repeat': {**receipt, 'request_id': 'two'}}}))
    source, target, owner = 'W:W31:B1', 'W:W31:B2', f'{gate.FIRST}:1'
    legal = [[[31, 26], [], False], [[31, 27], [], False]]
    moves = [{'action': a, 'jass_key': f'31-{a[0][1]}'} for a in legal]
    mapping = gate.digest(json.dumps([[a[0], a[1], a[2], m['jass_key']] for a, m in zip(legal, moves)], separators=(',', ':')).encode())
    selected = {'fen': target, 'games': [owner], 'source_fens': {'L': source, 'LCB': source}, 'source_games': {'L': 'pc:1', 'LCB': 'pc:1'}, 'legal': legal}
    bench = {'target_fen': target, 'target_games': [owner], 'source_fen': source, 'source_game': 'pc:1', 'source_fens': selected['source_fens'], 'source_games': selected['source_games'], 'legal_moves': moves}
    proposal = {'schema': 'mtdp-named-arena-freeze-proposal-v1', 'event': 'P1RUlfJc', 'scientific_freeze': False, 'synthetic_rehearsal': synthetic,
        'registry_sha256': gate.REGISTRY_SHA, 'history_index_sha256': gate.INDEX_SHA,
        'input_check': check_final(root, acquired / 'final-metadata.json', acquired / gate.FIRST, acquired / 'final-repeat.pdn', acquired / 'final-downloads.json', now=NOW),
        'implementation_commit': method or git(root, 'rev-parse', 'HEAD'), 'implementation_sha256': {METHOD: gate.digest((root / METHOD).read_bytes())},
        'engine': {'jass_commit': JASS_COMMIT, 'adapter_commit': ADAPTER_COMMIT, 'scan_binary_sha256': SCAN_SHA256, 'scan_commit': SCAN_COMMIT, 'jass_node_budgets': [10000, 50000, 200000], 'scan_successor_depth': 12, 'target_scan_successor_depth': 16},
        'selection': {'arm_order_seed': 20261113}, 'analysis': {k: reg[k] for k in ('primary_total_node_budget', 'bootstrap_resamples', 'bootstrap_seed', 'bootstrap_unit', 'verification_fraction')},
        'eligible': 1, 'candidate_targets': [selected], 'benchmark_targets': [bench], 'targets': [{'source_fen': source, 'target_fen': target, 'legal_moves': moves}],
        'target_plies': {target: {owner: [0]}}, 'game_audit': {owner: {'status': 'accepted'}}, 'game_status_counts': {'accepted': 1},
        'jass_catalogue': {'targets': 1, 'positions': [{'fen': f, 'actions': 2, 'mapping_sha256': mapping} for f in (source, target)]}}
    paths = [tmp_path / 'one.json', tmp_path / 'two.json']
    for path in paths: path.write_bytes(gate._bytes(proposal))
    reproduction = {'kind': 'subprocess_hash_seed_reproduction', 'runs': [{'hash_seed': s, 'exit_status': 0, 'proposal_sha256': gate.digest(paths[0].read_bytes())} for s in (7, 61)]}
    return acquired, paths, reproduction, proposal

def build(tmp_path, root=ROOT, synthetic=True, method=None):
    acquired, paths, reproduction, p = fixture(tmp_path, root, synthetic, method)
    out = tmp_path / 'bundle'
    gate._compose(root, acquired, *paths, reproduction, out, synthetic=synthetic, now=NOW if synthetic else None)
    return {n: (out / n).read_bytes() for n in gate.FILES | {'publication.json'}}, out, p

def test_synthetic_is_complete_but_never_authorizes_scoring(tmp_path):
    payloads, _, _ = build(tmp_path)
    gate.validate_payloads(payloads, allow_synthetic=True)
    with pytest.raises(ValueError, match='Synthetic'): gate.validate_payloads(payloads)

def test_same_file_and_different_proposals_rejected(tmp_path):
    acquired, paths, reproduction, _ = fixture(tmp_path)
    with pytest.raises(ValueError, match='distinct proposal'): gate._compose(ROOT, acquired, paths[0], paths[0], reproduction, tmp_path / 'out', synthetic=True, now=NOW)
    paths[1].write_text('{}')
    with pytest.raises(ValueError, match='reproduction differs'): gate._compose(ROOT, acquired, *paths, reproduction, tmp_path / 'out', synthetic=True, now=NOW)

def test_file_tampering_detected(tmp_path):
    payloads, _, _ = build(tmp_path); payloads['manifest.json'] += b'\n'
    with pytest.raises(ValueError, match='Published file changed'): gate.validate_payloads(payloads, allow_synthetic=True)

def test_budget_and_action_mapping_changes_rejected(tmp_path):
    _, _, _, p = fixture(tmp_path)
    changed = copy.deepcopy(p); changed['engine']['jass_node_budgets'][1] = 49999
    with pytest.raises(ValueError, match='budget changed'): gate.validate_proposal(changed, registration(ROOT))
    changed = copy.deepcopy(p); changed['benchmark_targets'][0]['legal_moves'][0]['jass_key'] = '31-25'
    with pytest.raises(ValueError, match='mapping receipt'): gate.validate_proposal(changed, registration(ROOT))

def test_preparation_cannot_claim_publication(tmp_path):
    payloads, _, _ = build(tmp_path); pub = json.loads(payloads['publication.json']); pub['scientific_freeze'] = True
    payloads['publication.json'] = gate._bytes(pub)
    with pytest.raises(ValueError, match='preparation state'): gate.validate_payloads(payloads, allow_synthetic=True)

def test_export_preserves_raw_crlf_bom_unicode():
    raw = b'\xef\xbb\xbf[Event "' + 'Épreuve'.encode() + b'"]\r\n*\r\n'
    assert json.loads(json.dumps(gate._text_entries({'first.pdn': raw}, 'cohort')))[0]['content'].encode() == raw

def test_prepare_checks_time_before_children_or_output(monkeypatch, tmp_path):
    def closed(*a, **k): raise ValueError('finish closed')
    monkeypatch.setattr(gate, '_inputs', closed)
    monkeypatch.setattr(gate.subprocess, 'run', lambda *a, **k: pytest.fail('premature subprocess'))
    with pytest.raises(ValueError, match='finish closed'): gate.prepare(ROOT, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()

def test_exact_commit_and_relative_path_required(monkeypatch, tmp_path):
    monkeypatch.setattr(gate.subprocess, 'run', lambda *a, **k: pytest.fail('unexpected fetch'))
    with pytest.raises(ValueError, match='exact published'): gate.verify_publication(tmp_path, 'cohort', 'HEAD')
    with pytest.raises(ValueError, match='repository-relative'): gate.verify_publication(tmp_path, '../cohort', 'a' * 40)

def test_real_git_remote_proof_and_worktree_independence(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, '_now', lambda: NOW)
    repo, remote = tmp_path / 'repo', tmp_path / 'remote.git'; repo.mkdir()
    git(repo, 'init', '-b', gate.BRANCH); git(repo, 'config', 'user.name', 'Synthetic test'); git(repo, 'config', 'user.email', 'synthetic@example.invalid')
    for name in (REGISTRATION, PROTOCOL, METHOD):
        p = repo / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes((ROOT / name).read_bytes())
    git(repo, 'add', '.'); git(repo, 'commit', '-m', 'synthetic method snapshot'); method = git(repo, 'rev-parse', 'HEAD')
    case = tmp_path / 'case'; case.mkdir(); payloads, _, _ = build(case, repo, False, method)
    relative = Path('research/mtdp/synthetic-unit-bundle'); target = repo / relative; target.mkdir(parents=True)
    for n, raw in payloads.items(): (target / n).write_bytes(raw)
    git(repo, 'add', '.'); git(repo, 'commit', '-m', 'synthetic publication snapshot'); published = git(repo, 'rev-parse', 'HEAD')
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    git(repo, 'remote', 'add', 'origin', str(remote)); git(repo, 'push', 'origin', f'{method}:refs/heads/{gate.BRANCH}')
    with pytest.raises(subprocess.CalledProcessError): gate.verify_publication(repo, str(relative), published)
    git(repo, 'push', 'origin', f'HEAD:refs/heads/{gate.BRANCH}')
    checked = gate.verify_publication(repo, str(relative), published)
    assert checked['scientific_freeze'] is True
    (target / 'manifest.json').write_text('uncommitted edit')
    assert gate.verify_publication(repo, str(relative), published)['manifest_sha256'] == checked['manifest_sha256']
    from research.mtdp.jass_benchmark.named_arena_execution import published_manifest
    manifest, proof = published_manifest(repo, str(relative), published)
    assert manifest == json.loads(payloads['manifest.json'])
    assert proof['manifest_sha256'] == checked['manifest_sha256']

def test_prepare_runs_both_real_hash_seed_child_commands(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, '_now', lambda: NOW)
    acquired, _, _, p = fixture(tmp_path, synthetic=False); calls = []
    def child(command, **kwargs):
        calls.append(kwargs['env']['PYTHONHASHSEED'])
        assert command[1:4] == ['-m', 'research.mtdp.jass_benchmark.named_arena_replay', 'proposal']
        Path(command[command.index('--output') + 1]).write_bytes(gate._bytes(p))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(gate.subprocess, 'run', child)
    result = gate.prepare(ROOT, acquired, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path / 'out')
    assert calls == ['7', '61'] and result['state'] == 'prepared_not_published'

def test_failed_child_cannot_emit_publication(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, '_now', lambda: NOW)
    acquired, _, _, p = fixture(tmp_path, synthetic=False)
    def child(command, **kwargs):
        if kwargs['env']['PYTHONHASHSEED'] == '61': raise subprocess.CalledProcessError(1, command)
        Path(command[command.index('--output') + 1]).write_bytes(gate._bytes(p))
    monkeypatch.setattr(gate.subprocess, 'run', child)
    out = tmp_path / 'out'
    with pytest.raises(subprocess.CalledProcessError): gate.prepare(ROOT, acquired, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, out)
    assert not (out / 'publication.json').exists()

def test_export_refuses_existing_committed_prefix(tmp_path):
    with pytest.raises(ValueError, match='already exists'): gate.tree_entries(ROOT, tmp_path, 'research/mtdp')
