"""Prepare exact named-arena inputs; only a verified remote commit is a freeze."""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from research.mtdp.jass_benchmark.named_arena_inputs import EVENT, PROTOCOL, PROTOCOL_SHA, REGISTRATION, REGISTRATION_SHA, check_final, registration
from research.mtdp.jass_benchmark.named_arena_replay import INDEX_SHA, REGISTRY_SHA
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest
from research.mtdp.jass_cohort import ADAPTER_COMMIT, JASS_COMMIT, SCAN_COMMIT, SCAN_SHA256
from research.mtdp.pdn import read_games

FIRST = f'mtdp-lidraughts-{EVENT}.pdn'
FILES = {'proposal.json', 'reproduction.json', 'provenance.json', 'manifest.json', 'final-metadata.json',
         FIRST, 'final-repeat.pdn', 'final-downloads.json', 'registration.json', 'protocol.md'}
BRANCH = 'research/mtdp-foundation'


def _bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def _now():
    return datetime.now(timezone.utc)


def _inputs(root, directory, *, now=None):
    return check_final(root, directory / 'final-metadata.json', directory / FIRST, directory / 'final-repeat.pdn',
                       directory / 'final-downloads.json', now=now or _now())


def _synthetic_game(directory):
    return any(g.tags.get('Synthetic', '').lower() == 'true' for g in read_games(directory / FIRST))


def validate_proposal(p, reg):
    if (p.get('schema') != 'mtdp-named-arena-freeze-proposal-v1' or p.get('event') != EVENT
            or p.get('scientific_freeze') is not False or p.get('registry_sha256') != REGISTRY_SHA
            or p.get('history_index_sha256') != INDEX_SHA):
        raise ValueError('Proposal identity or historical provenance changed')
    if (not re.fullmatch('[0-9a-f]{40}', p.get('implementation_commit', '')) or not p.get('implementation_sha256')
            or any(not re.fullmatch('[0-9a-f]{64}', v) for v in p['implementation_sha256'].values())):
        raise ValueError('Implementation provenance is incomplete')
    e = p['engine']
    if (e['jass_commit'] != JASS_COMMIT or e['adapter_commit'] != ADAPTER_COMMIT or e['scan_commit'] != SCAN_COMMIT
            or e['scan_binary_sha256'] != SCAN_SHA256 or e['jass_node_budgets'] != reg['total_node_budgets']
            or e['scan_successor_depth'] != 12 or e['target_scan_successor_depth'] != 16):
        raise ValueError('Registered engine, reference or budget changed')
    if p['analysis'] != {k: reg[k] for k in ('primary_total_node_budget', 'bootstrap_resamples', 'bootstrap_seed', 'bootstrap_unit', 'verification_fraction')}:
        raise ValueError('Registered analysis changed')
    targets = p['benchmark_targets']
    selected = {r['fen']: r for r in p['candidate_targets']}
    if len(selected) != len(p['candidate_targets']) or len(selected) != len(targets) or len({r['target_fen'] for r in targets}) != len(targets):
        raise ValueError('Incomplete or duplicated selected population')
    positions = {r['fen']: r for r in p['jass_catalogue']['positions']}
    expected = {r['target_fen'] for r in targets} | {f for r in targets for f in r['source_fens'].values()}
    if p['jass_catalogue']['targets'] != len(targets) or set(positions) != expected or len(positions) != len(p['jass_catalogue']['positions']):
        raise ValueError('Incomplete Jass catalogue receipt')
    for r in targets:
        chosen = selected[r['target_fen']]
        if r['source_fens'] != chosen['source_fens'] or r['target_games'] != chosen['games'] or set(r['source_fens']) != {'L', 'LCB'}:
            raise ValueError('Selected source or ownership changed')
        actions = [(tuple(m['action'][0]), tuple(m['action'][1]), m['action'][2]) for m in r['legal_moves']]
        keys = [m['jass_key'] for m in r['legal_moves']]
        if len(actions) < 2 or len(set(actions)) != len(actions) or len(set(keys)) != len(keys):
            raise ValueError('Incomplete or ambiguous legal action mapping')
        if set(actions) != {(tuple(a[0]), tuple(a[1]), a[2]) for a in chosen['legal']}:
            raise ValueError('Replay and benchmark action lists differ')
        serialized = [[list(a[0]), list(a[1]), a[2], key] for a, key in sorted(zip(actions, keys))]
        fingerprint = digest(json.dumps(serialized, separators=(',', ':')).encode())
        for fen in {r['target_fen'], *r['source_fens'].values()}:
            if positions[fen]['mapping_sha256'] != fingerprint or positions[fen]['actions'] != len(actions):
                raise ValueError('Jass mapping receipt disagrees with benchmark actions')
        if not r['target_games'] or len(set(r['target_games'])) != len(r['target_games']) or any(p['game_audit'][g]['status'] != 'accepted' for g in r['target_games']):
            raise ValueError('A target is owned by an excluded or missing game')
    pairs = [{'source_fen': source, 'target_fen': r['target_fen'], 'legal_moves': r['legal_moves']}
             for r in targets for source in sorted(set(r['source_fens'].values()))]
    if p['targets'] != pairs:
        raise ValueError('Source-target pairs do not cover the selected population')


def _reproduction(reproduction, proposal_bytes):
    runs = reproduction.get('runs', [])
    if (reproduction.get('kind') != 'subprocess_hash_seed_reproduction' or [r.get('hash_seed') for r in runs] != [7, 61]
            or any(r.get('exit_status') != 0 or r.get('proposal_sha256') != digest(proposal_bytes) for r in runs)):
        raise ValueError('Two successful hash-seed executions are required')


def _compose(root, acquired, first_proposal, repeat_proposal, reproduction, output, *, synthetic=False, now=None):
    if now is not None and not synthetic:
        raise ValueError('Only an explicitly synthetic rehearsal may supply a test clock')
    if first_proposal.resolve() == repeat_proposal.resolve() or first_proposal.samefile(repeat_proposal):
        raise ValueError('Two distinct proposal files are required')
    raw = first_proposal.read_bytes()
    if raw != repeat_proposal.read_bytes():
        raise ValueError('Proposal reproduction differs')
    p = json.loads(raw)
    if (bool(p.get('synthetic_rehearsal')) or _synthetic_game(acquired)) != synthetic:
        raise ValueError('Synthetic input cannot enter production freeze preparation')
    checked = _inputs(root, acquired, now=now)
    if checked != p['input_check']:
        raise ValueError('Proposal is not bound to these final acquisition inputs')
    reg = registration(root)
    validate_proposal(p, reg)
    if not synthetic:
        _reproduction(reproduction, raw)
    provenance = {'schema': 'mtdp-named-freeze-provenance-v1', 'event': reg['event'], 'proposal_sha256': digest(raw),
                  'input_check': checked, 'registry_sha256': REGISTRY_SHA, 'history_index_sha256': INDEX_SHA,
                  'registration_sha256': REGISTRATION_SHA, 'protocol_sha256': PROTOCOL_SHA,
                  'implementation_commit': p['implementation_commit'], 'implementation_sha256': p['implementation_sha256'],
                  'game_status_counts': p['game_status_counts'], 'synthetic_rehearsal': synthetic}
    manifest = {k: p[k] for k in ('event', 'engine', 'selection', 'analysis', 'eligible', 'targets', 'benchmark_targets', 'target_plies')}
    manifest.update(schema='mtdp-jass-cohort-v1', provenance_sha256=digest(_bytes(provenance)), mapping_errors=[], mapping_rejected_pairs=0,
                    scientific_freeze=False, publication_required=True, synthetic_rehearsal=synthetic)
    payloads = {'proposal.json': raw, 'reproduction.json': _bytes(reproduction), 'provenance.json': _bytes(provenance),
                'manifest.json': _bytes(manifest), 'registration.json': (root / REGISTRATION).read_bytes(), 'protocol.md': (root / PROTOCOL).read_bytes()}
    for name in ('final-metadata.json', FIRST, 'final-repeat.pdn', 'final-downloads.json'):
        payloads[name] = (acquired / name).read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).exists() for name in [*payloads, 'publication.json']):
        raise ValueError('Refusing to overwrite an existing freeze bundle')
    for name, data in payloads.items():
        (output / name).write_bytes(data)
    publication = {'schema': 'mtdp-named-freeze-publication-v1', 'event': EVENT,
                   'state': 'synthetic_rehearsal_only' if synthetic else 'prepared_not_published',
                   'synthetic_rehearsal': synthetic, 'scientific_freeze': False,
                   'files': {n: {'bytes': len(v), 'sha256': digest(v)} for n, v in sorted(payloads.items())}}
    (output / 'publication.json').write_bytes(_bytes(publication))
    return publication


def prepare(root, acquired, registry, index, adapter, jass, executable, output):
    _inputs(root, acquired)
    if _synthetic_game(acquired):
        raise ValueError('Synthetic input cannot enter production freeze preparation')
    output.mkdir(parents=True, exist_ok=False)
    paths, runs = [], []
    for seed in (7, 61):
        path = output / f'proposal-{seed}.json'
        command = [sys.executable, '-m', 'research.mtdp.jass_benchmark.named_arena_replay', 'proposal',
                   '--root', str(root), '--registry', str(registry), '--index', str(index),
                   '--metadata', str(acquired / 'final-metadata.json'), '--first', str(acquired / FIRST),
                   '--repeat', str(acquired / 'final-repeat.pdn'), '--download-log', str(acquired / 'final-downloads.json'),
                   '--adapter', str(adapter), '--jass', str(jass), '--executable', str(executable), '--output', str(path)]
        subprocess.run(command, check=True, env={**os.environ, 'PYTHONHASHSEED': str(seed)}, capture_output=True, text=True)
        paths.append(path)
        runs.append({'hash_seed': seed, 'exit_status': 0, 'proposal_sha256': digest(path.read_bytes())})
    return _compose(root, acquired, *paths, {'kind': 'subprocess_hash_seed_reproduction', 'runs': runs}, output)


def validate_payloads(payloads, *, allow_synthetic=False):
    pub = json.loads(payloads['publication.json'])
    if pub.get('schema') != 'mtdp-named-freeze-publication-v1' or pub.get('event') != EVENT:
        raise ValueError('Unknown publication bundle')
    if pub.get('scientific_freeze') is not False or pub.get('state') != ('synthetic_rehearsal_only' if pub.get('synthetic_rehearsal') else 'prepared_not_published'):
        raise ValueError('Publication preparation state changed')
    if pub.get('synthetic_rehearsal') and not allow_synthetic:
        raise ValueError('Synthetic rehearsal can never authorize scoring')
    if set(pub['files']) != FILES:
        raise ValueError('Publication file inventory is incomplete')
    for name, record in pub['files'].items():
        data = payloads[name]
        if digest(data) != record['sha256'] or len(data) != record['bytes']:
            raise ValueError(f'Published file changed: {name}')
    if digest(payloads['registration.json']) != REGISTRATION_SHA or digest(payloads['protocol.md']) != PROTOCOL_SHA:
        raise ValueError('Published scientific protocol changed')
    p, m = json.loads(payloads['proposal.json']), json.loads(payloads['manifest.json'])
    validate_proposal(p, json.loads(payloads['registration.json']))
    if (p.get('synthetic_rehearsal') or m.get('synthetic_rehearsal')) and not allow_synthetic:
        raise ValueError('Synthetic rehearsal can never authorize scoring')
    if m.get('schema') != 'mtdp-jass-cohort-v1' or m.get('scientific_freeze') is not False or m.get('publication_required') is not True or m.get('mapping_errors') != [] or m.get('mapping_rejected_pairs') != 0:
        raise ValueError('Prepared manifest cannot assert its own publication')
    if not pub.get('synthetic_rehearsal'):
        _reproduction(json.loads(payloads['reproduction.json']), payloads['proposal.json'])
    if m['provenance_sha256'] != digest(payloads['provenance.json']) or json.loads(payloads['provenance.json'])['proposal_sha256'] != digest(payloads['proposal.json']):
        raise ValueError('Manifest, provenance or proposal binding changed')
    for key in ('event', 'engine', 'selection', 'analysis', 'eligible', 'targets', 'benchmark_targets', 'target_plies'):
        if m[key] != p[key]:
            raise ValueError('Published manifest differs from verified proposal')
    return pub, p


def verify_publication(root, relative_directory, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('An exact published commit SHA is required')
    relative = Path(relative_directory)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Bundle path must be repository-relative')
    ref = f'refs/remotes/origin/{BRANCH}'
    subprocess.run(['git', '-C', str(root), 'fetch', '--no-tags', 'origin', f'refs/heads/{BRANCH}:{ref}'], check=True, capture_output=True)
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', ref], text=True).strip()
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', commit, head], check=True)
    payloads = {n: subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{relative.as_posix()}/{n}']) for n in FILES | {'publication.json'}}
    _, p = validate_payloads(payloads)
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', p['implementation_commit'], commit], check=True)
    for name, expected in p['implementation_sha256'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe implementation file path')
        data = subprocess.check_output(['git', '-C', str(root), 'show', f'{p["implementation_commit"]}:{name}'])
        if digest(data) != expected:
            raise ValueError('Published implementation fingerprint changed')
    with tempfile.TemporaryDirectory() as directory:
        acquired = Path(directory)
        for name in ('final-metadata.json', FIRST, 'final-repeat.pdn', 'final-downloads.json'):
            (acquired / name).write_bytes(payloads[name])
        if _synthetic_game(acquired) or _inputs(root, acquired) != p['input_check']:
            raise ValueError('Published final inputs do not match the proposal')
    return {'schema': 'mtdp-named-publication-verification-v1', 'event': EVENT, 'published_commit': commit,
            'observed_branch_head': head, 'manifest_sha256': digest(payloads['manifest.json']),
            'scientific_freeze': True, 'verified_at_utc': _now().isoformat()}


def _text_entries(payloads, prefix):
    return [{'path': f'{prefix}/{name}', 'mode': '100644', 'type': 'blob', 'content': data.decode('utf-8')} for name, data in sorted(payloads.items())]


def tree_entries(root, directory, prefix):
    relative = Path(prefix)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Publication prefix must be repository-relative')
    if subprocess.check_output(['git', '-C', str(root), 'ls-tree', '--name-only', 'HEAD', '--', relative.as_posix()], text=True).strip():
        raise ValueError('Publication prefix already exists in the checked-out commit')
    payloads = {n: (directory / n).read_bytes() for n in FILES | {'publication.json'}}
    _, p = validate_payloads(payloads)
    if _synthetic_game(directory) or _inputs(root, directory) != p['input_check']:
        raise ValueError('Exported bundle is not a final production acquisition')
    return _text_entries(payloads, relative.as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'verify', 'export-tree'))
    parser.add_argument('--root', type=Path, required=True)
    for key in ('acquired', 'registry', 'index', 'adapter', 'jass', 'executable', 'output'):
        parser.add_argument(f'--{key}', type=Path)
    for key in ('directory', 'commit', 'prefix'):
        parser.add_argument(f'--{key}')
    a = parser.parse_args()
    required = ('acquired', 'registry', 'index', 'adapter', 'jass', 'executable', 'output') if a.mode == 'prepare' else ('directory', 'commit') if a.mode == 'verify' else ('directory', 'prefix')
    if any(getattr(a, k) is None for k in required):
        parser.error(f'Mode {a.mode} requires {required}')
    result = (prepare(a.root, a.acquired, a.registry, a.index, a.adapter, a.jass, a.executable, a.output) if a.mode == 'prepare'
              else verify_publication(a.root, a.directory, a.commit) if a.mode == 'verify' else tree_entries(a.root, Path(a.directory), a.prefix))
    if a.mode == 'verify' and a.output is not None:
        a.output.write_bytes(_bytes(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
