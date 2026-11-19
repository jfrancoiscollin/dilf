"""Joint publication bundle: preparation alone never authorizes a search."""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark import two_arena_acquisition as acquisition
from research.mtdp.jass_benchmark import two_arena_replay as replay
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes, _reproduction
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest
from research.mtdp.pdn import read_games

MODULE = 'research/mtdp/jass_benchmark/two_arena_freeze.py'
PRESTART = study.PREFIX + 'two-named-arenas-20261118-publication-proof.json'
PRESTART_SHA = '29cdfb7f9a684b363e874377bd294568fcc7722fa76c758718dcc871c2bb9ae8'
INPUT_NAMES = ('metadata.json', 'downloads.json', 'first.pdn', 'repeat.pdn')
FILES = {'proposal.json', 'manifest.json', 'reproduction.json', 'registration.json',
         'protocol.md', 'prestart-publication.json', 'acquisition-audit.json'} | {
             f'{event}/{name}' for event in study.EVENTS for name in INPUT_NAMES}


def _git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def _safe_path(value):
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts or path == Path('.'):
        raise ValueError('A nonempty repository-relative path is required')
    return path.as_posix()


def _sha(value, size=64):
    return isinstance(value, str) and re.fullmatch(f'[0-9a-f]{{{size}}}', value) is not None


def _prestart(raw):
    if digest(raw) != PRESTART_SHA:
        raise ValueError('Live pre-start publication receipt changed')
    p = json.loads(raw)
    if (p['events'] != list(study.EVENTS) or not p['publication_seen_before_all_starts']
            or p['registration_sha256'] != study.REGISTRATION_SHA or p['protocol_sha256'] != study.PROTOCOL_SHA
            or not _sha(p['published_commit'], 40)
            or study.utc(p['verified_at_utc']) >= study.utc(study.STARTS[0])):
        raise ValueError('Missing prospective publication evidence')
    return p


def _synthetic(directory):
    return any(any(k.lower() == 'synthetic' for k in game.tags)
               for event in study.EVENTS for game in read_games(directory/event/'first.pdn'))


def _audit_acquisition(directory):
    files = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():raise ValueError('Acquisition audit cannot contain symlinks')
        if not path.is_file():continue
        name = path.relative_to(directory).as_posix();raw = path.read_bytes()
        files[name] = {'sha256':digest(raw),'bytes':len(raw),'content_base64':base64.b64encode(raw).decode()}
    return {'schema':'mtdp-two-arena-raw-acquisition-audit-v1','files':files,'scientific_freeze':False}


def _validate_audit(payloads,p,allow_synthetic):
    audit = json.loads(payloads['acquisition-audit.json'])
    if audit.get('schema') != 'mtdp-two-arena-raw-acquisition-audit-v1' or audit.get('scientific_freeze') is not False:
        raise ValueError('Invalid raw acquisition audit')
    minimum = {'acquisition.json'} | {f'{e}/{n}' for e in study.EVENTS for n in (*INPUT_NAMES,'metadata-download.json')}
    if not minimum.issubset(audit['files']):raise ValueError('Raw metadata or acquisition receipts missing')
    raw_files = {}
    for name,entry in audit['files'].items():
        _safe_path(name)
        if name not in minimum and not re.fullmatch(
                r'(?:s7ahYqL4|D9PF2OSW)/attempt-0[1-4]/(?:first\.pdn|repeat\.pdn|first-download\.json|repeat-download\.json|downloads\.json)',name):
            raise ValueError('Unexpected file in raw acquisition audit')
        raw = base64.b64decode(entry['content_base64'],validate=True)
        if digest(raw) != entry['sha256'] or len(raw) != entry['bytes']:
            raise ValueError('Raw acquisition audit bytes changed')
        if name in payloads and raw != payloads[name]:raise ValueError('Raw acquisition audit differs from final inputs')
        if name.endswith('.pdn') and re.search(br'\[synthetic\s+',raw,re.I) and not allow_synthetic:
            raise ValueError('Synthetic acquisition attempt cannot authorize scoring')
        raw_files[name] = raw
    if json.loads(raw_files['acquisition.json']) != p['input_check']:
        raise ValueError('Acquisition audit is not bound to the input check')
    game_ids = {r['request_id'] for event in study.EVENTS
                for k,r in json.loads(payloads[f'{event}/downloads.json']).items() if k in ('first','independent_repeat')}
    for event in study.EVENTS:
        r = json.loads(raw_files[f'{event}/metadata-download.json'])
        if (r['url'] != f'https://lidraughts.org/api/tournament/{event}' or not _sha(r['sha256'])
                or r['bytes'] <= 0 or not r['request_id'] or r['request_id'] in game_ids
                or not study.FINAL_GATE <= study.utc(r['requested_at_utc']) <= study.utc(r['retrieved_at_utc']) <= study._now()):
            raise ValueError('Final metadata transport receipt is inconsistent')
        game_ids.add(r['request_id'])


def validate_proposal(root, p):
    registered = study.load(root)
    if (p.get('schema') != 'mtdp-two-arena-joint-proposal-v1'
            or p.get('study_id') != registered['study_id'] or p.get('event_order') != list(study.EVENTS)
            or set(p.get('events', {})) != set(study.EVENTS) or p.get('scientific_freeze') is not False
            or type(p.get('synthetic_rehearsal')) is not bool
            or p.get('registration_sha256') != study.REGISTRATION_SHA or p.get('protocol_sha256') != study.PROTOCOL_SHA
            or p.get('exclusions_sha256') != replay.EXCLUSIONS_SHA):
        raise ValueError('Joint proposal identity or exclusions changed')
    if (p['analysis'] != registered['analysis'] or p['engines'] != {
            **registered['engines'], 'jass_catalogue_sha256': replay.CATALOGUE_SHA}):
        raise ValueError('Registered references, engines or budgets changed')
    if (not _sha(p.get('implementation_commit'), 40)
            or set(p.get('implementation_sha256', {})) != set(replay.DEPENDENCIES)
            or any(not _sha(v) for v in p['implementation_sha256'].values())):
        raise ValueError('Joint implementation inventory incomplete')
    earlier_fens = set()
    for event in study.EVENTS:
        e = p['events'][event]
        if e['game_status_counts'] != dict(Counter(r['status'] for r in e['game_audit'].values())):
            raise ValueError('Whole-game status counts changed')
        selected = {r['fen']:r for r in e['candidate_targets']}
        targets = e['benchmark_targets']
        if (len(selected) != len(e['candidate_targets']) or len(selected) != len(targets)
                or len({r['target_fen'] for r in targets}) != len(targets)):
            raise ValueError('Incomplete or duplicate joint population')
        if earlier_fens & set(selected):
            raise ValueError('Later target overlaps an earlier confirmed prefix')
        catalogue = e['jass_catalogue']; positions = {r['fen']:r for r in catalogue['positions']}
        expected = set(selected) | {f for r in targets for f in r['source_fens'].values()}
        if (set(positions) != expected or len(positions) != len(catalogue['positions'])
                or catalogue['targets'] != len(targets)
                or catalogue['distinct_positions'] != len(expected)
                or catalogue['distinct_sources'] != len({f for r in targets for f in r['source_fens'].values()})
                or catalogue['target_action_occurrences'] != sum(len(r['legal_moves']) for r in targets)):
            raise ValueError('Incomplete joint action catalogue')
        if targets != replay.full_signature_labels(targets):
            raise ValueError('Frozen full-signature mask or bootstrap owner changed')
        if e['full_signature_strata'] != {arm:{
                'equal':sum(r['same_full_quiet_signature'][arm] for r in targets),
                'different':sum(not r['same_full_quiet_signature'][arm] for r in targets),
        } for arm in ('L','LCB')}:
            raise ValueError('Signature-stratum denominators changed')
        if set(e['target_plies']) != set(selected):
            raise ValueError('Missing target ply provenance')
        for r in targets:
            chosen = selected[r['target_fen']]
            if (r['source_fens'] != chosen['source_fens'] or r['source_games'] != chosen['source_games']
                    or r['target_games'] != chosen['games'] or set(r['source_fens']) != {'L','LCB'}):
                raise ValueError('Preselected source or game ownership changed')
            if (not r['target_games'] or sorted(set(r['target_games'])) != r['target_games']
                    or set(e['target_plies'][r['target_fen']]) != set(r['target_games'])
                    or any(e['game_audit'][g]['status'] != 'accepted' for g in r['target_games'])):
                raise ValueError('Target owned by missing or excluded game')
            actions = [(tuple(m['action'][0]),tuple(m['action'][1]),m['action'][2]) for m in r['legal_moves']]
            keys = [m['jass_key'] for m in r['legal_moves']]
            if (len(actions) < 2 or len(set(actions)) != len(actions) or len(set(keys)) != len(keys)
                    or set(actions) != {(tuple(a[0]),tuple(a[1]),a[2]) for a in chosen['legal']}):
                raise ValueError('Incomplete or non-bijective target actions')
            serial = [[list(a[0]),list(a[1]),a[2],key] for a,key in sorted(zip(actions,keys))]
            fingerprint = digest(json.dumps(serial,separators=(',',':')).encode())
            for fen in {r['target_fen'],*r['source_fens'].values()}:
                if positions[fen]['mapping_sha256'] != fingerprint or positions[fen]['actions'] != len(actions):
                    raise ValueError('Source-target action receipt changed')
        indexed = e['whole_event_index']
        if any(r['status'] == 'quarantined' and 'trajectory_sha256' in r for r in indexed['game_audit'].values()):
            raise ValueError('Quarantine cannot certify a full trajectory')
        earlier_fens.update(indexed['confirmed_fens'])
    return registered


def _manifest(p):
    return {'schema':'mtdp-two-arena-joint-manifest-v1',
            **{k:p[k] for k in ('study_id','event_order','analysis','engines','exclusions_sha256',
                                'implementation_commit','implementation_sha256','synthetic_rehearsal')},
            'proposal_sha256':digest(_bytes(p)), 'scientific_freeze':False, 'publication_required':True,
            'events':{event:{k:p['events'][event][k] for k in (
                'pdn_sha256','benchmark_targets','target_plies','full_signature_strata','game_status_counts')}
                      for event in study.EVENTS}}


def _methods(root):
    commit = _git(root, 'rev-parse', 'HEAD').decode().strip()
    files = {n:digest((root/n).read_bytes()) for n in (MODULE,*replay.DEPENDENCIES)}
    for name, expected in files.items():
        if digest(_git(root,'show',f'{commit}:{name}')) != expected:
            raise ValueError('Commit bundle implementation before preparing publication')
    return {'commit':commit,'files_sha256':files}


def _payload_inputs(root, payloads, p, allow_synthetic):
    with tempfile.TemporaryDirectory(prefix='mtdp-two-arena-input-check-') as temp:
        directory = Path(temp)
        for event in study.EVENTS:
            (directory/event).mkdir()
            for name in INPUT_NAMES:
                (directory/event/name).write_bytes(payloads[f'{event}/{name}'])
        synthetic = _synthetic(directory)
        if synthetic and not allow_synthetic:
            raise ValueError('Synthetic bytes can never authorize scoring')
        if synthetic != p['synthetic_rehearsal']:
            raise ValueError('Synthetic flag does not match raw inputs')
        if acquisition.check(root,directory) != p['input_check']:
            raise ValueError('Final acquisition inputs differ from joint proposal')
        for event in study.EVENTS:
            if digest(payloads[f'{event}/first.pdn']) != p['events'][event]['pdn_sha256']:
                raise ValueError('Event export differs from replayed population')
            games = read_games(directory/event/'first.pdn')
            expected = {f'mtdp-lidraughts-{event}.pdn:{g.index}' for g in games}
            e = p['events'][event]
            if set(e['game_audit']) != expected or set(e['whole_event_index']['game_audit']) != expected:
                raise ValueError('Whole-event game audit is incomplete')


def validate_payloads(root, payloads, *, allow_synthetic=False):
    acquisition._clock_gate()  # no public clock override, even for a prepared local bundle
    if set(payloads) != FILES | {'publication.json'}:
        raise ValueError('Joint publication payload inventory incomplete')
    pub = json.loads(payloads['publication.json'])
    if (pub.get('schema') != 'mtdp-two-arena-publication-v1' or pub.get('scientific_freeze') is not False
            or type(pub.get('synthetic_rehearsal')) is not bool
            or pub.get('state') != ('synthetic_rehearsal_only' if pub['synthetic_rehearsal'] else 'prepared_not_published')
            or set(pub.get('files', {})) != FILES):
        raise ValueError('Invalid joint publication preparation state')
    if pub['synthetic_rehearsal'] and not allow_synthetic:
        raise ValueError('Synthetic bundle can never authorize scoring')
    for name, entry in pub['files'].items():
        if entry != {'sha256':digest(payloads[name]),'bytes':len(payloads[name])}:
            raise ValueError(f'Joint publication bytes changed: {name}')
    if digest(payloads['registration.json']) != study.REGISTRATION_SHA or digest(payloads['protocol.md']) != study.PROTOCOL_SHA:
        raise ValueError('Joint registration or protocol changed')
    _prestart(payloads['prestart-publication.json'])
    p = json.loads(payloads['proposal.json']); validate_proposal(root,p)
    if payloads['proposal.json'] != _bytes(p):
        raise ValueError('Canonical proposal bytes required')
    if pub['synthetic_rehearsal'] != p['synthetic_rehearsal']:
        raise ValueError('Synthetic publication state differs from proposal')
    if json.loads(payloads['manifest.json']) != _manifest(p):
        raise ValueError('Prepared manifest differs from joint proposal')
    if not pub['synthetic_rehearsal']:
        _reproduction(json.loads(payloads['reproduction.json']),payloads['proposal.json'])
    methods = pub['bundle_implementation']
    if (not _sha(methods.get('commit'),40) or set(methods.get('files_sha256',{})) != {MODULE,*replay.DEPENDENCIES}
            or any(not _sha(v) for v in methods['files_sha256'].values())):
        raise ValueError('Bundle method inventory incomplete')
    _payload_inputs(root,payloads,p,allow_synthetic)
    _validate_audit(payloads,p,allow_synthetic)
    return pub,p


def _compose(root, acquired, proposals, reproduction, output, *, synthetic=False):
    acquisition.check(root,acquired)
    if len(proposals) != 2 or proposals[0].resolve() == proposals[1].resolve() or proposals[0].samefile(proposals[1]):
        raise ValueError('Two distinct joint proposal files required')
    raw = proposals[0].read_bytes()
    if raw != proposals[1].read_bytes():
        raise ValueError('Joint proposal reproduction differs')
    p = json.loads(raw)
    payloads = {'proposal.json':raw,'manifest.json':_bytes(_manifest(p)),
                'reproduction.json':_bytes(reproduction),'registration.json':(root/study.REGISTRATION).read_bytes(),
                'protocol.md':(root/study.PROTOCOL).read_bytes(),
                'prestart-publication.json':(root/PRESTART).read_bytes()}
    payloads['acquisition-audit.json'] = _bytes(_audit_acquisition(acquired))
    payloads.update({f'{event}/{name}':(acquired/event/name).read_bytes() for event in study.EVENTS for name in INPUT_NAMES})
    pub = {'schema':'mtdp-two-arena-publication-v1','scientific_freeze':False,
           'state':'synthetic_rehearsal_only' if synthetic else 'prepared_not_published',
           'synthetic_rehearsal':synthetic,'bundle_implementation':_methods(root),
           'files':{name:{'sha256':digest(data),'bytes':len(data)} for name,data in sorted(payloads.items())}}
    payloads['publication.json'] = _bytes(pub)
    validate_payloads(root,payloads,allow_synthetic=synthetic)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in payloads.items():
        path = output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return pub


def prepare(root, acquired, exclusions, adapter, executable, output):
    acquisition.check(root,acquired)
    if _synthetic(acquired):
        raise ValueError('Synthetic input refused by production preparation')
    output.mkdir(parents=True,exist_ok=False)
    runs,paths = [],[]
    # Keep both child outputs and technical errors, even if one child fails.
    for seed in (7,61):
        path = output/f'proposal-{seed}.json'
        command = [sys.executable,'-m','research.mtdp.jass_benchmark.two_arena_replay',
                   '--root',str(root.resolve()),'--directory',str(acquired.resolve()),
                   '--exclusions',str(exclusions.resolve()),'--adapter',str(adapter.resolve()),
                   '--executable',str(executable.resolve()),'--output',str(path.resolve())]
        run = subprocess.run(command,cwd=root,env={**os.environ,'PYTHONHASHSEED':str(seed),
                             'PYTHONPATH':os.pathsep.join((str(root.resolve()),str(adapter.resolve())))},capture_output=True)
        (output/f'proposal-{seed}.stdout').write_bytes(run.stdout)
        (output/f'proposal-{seed}.stderr').write_bytes(run.stderr)
        entry = {'hash_seed':seed,'exit_status':run.returncode}
        if path.exists():entry['proposal_sha256'] = digest(path.read_bytes())
        runs.append(entry)
        (output/'reproduction-attempts.json').write_bytes(_bytes({'runs':runs,'scientific_freeze':False}))
        if run.returncode:
            raise ValueError(f'Joint proposal subprocess failed for seed {seed}; diagnostics retained')
        paths.append(path)
    return _compose(root,acquired,paths,{'kind':'subprocess_hash_seed_reproduction','runs':runs},output/'bundle')


def tree_entries(root, directory, prefix):
    relative = _safe_path(prefix)
    if _git(root,'ls-tree','--name-only','HEAD','--',relative).strip():
        raise ValueError('Joint publication prefix already exists')
    payloads = {n:(directory/n).read_bytes() for n in FILES | {'publication.json'}}
    validate_payloads(root,payloads)
    return [{'path':f'{relative}/{n}','mode':'100644','type':'blob','content':data.decode('utf-8')}
            for n,data in sorted(payloads.items())]


def verify_publication(root, prefix, commit):
    acquisition._clock_gate()
    if not _sha(commit,40):raise ValueError('Exact published joint commit SHA required')
    relative = _safe_path(prefix)
    ref = f'refs/remotes/origin/{study.BRANCH}'
    _git(root,'fetch','--no-tags','origin',f'refs/heads/{study.BRANCH}:{ref}')
    head = _git(root,'rev-parse',ref).decode().strip()
    _git(root,'merge-base','--is-ancestor',commit,head)
    payloads = {n:_git(root,'show',f'{commit}:{relative}/{n}') for n in FILES | {'publication.json'}}
    pub,p = validate_payloads(root,payloads)
    pre = _prestart(payloads['prestart-publication.json'])
    for ancestor,files in (
            (pre['published_commit'],{study.REGISTRATION:study.REGISTRATION_SHA,study.PROTOCOL:study.PROTOCOL_SHA}),
            (p['implementation_commit'],p['implementation_sha256']),
            (pub['bundle_implementation']['commit'],pub['bundle_implementation']['files_sha256'])):
        _git(root,'merge-base','--is-ancestor',ancestor,commit)
        for name,expected in files.items():
            _safe_path(name)
            if digest(_git(root,'show',f'{ancestor}:{name}')) != expected:
                raise ValueError('Published joint implementation or registration bytes differ')
    return {'schema':'mtdp-two-arena-publication-verification-v1','published_commit':commit,
            'observed_branch_head':head,'events':list(study.EVENTS),'manifest_sha256':digest(payloads['manifest.json']),
            'proposal_sha256':digest(payloads['proposal.json']),'registration_sha256':study.REGISTRATION_SHA,
            'scientific_freeze':True,'verified_at_utc':study._now().isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','verify','export-tree'))
    parser.add_argument('--root',type=Path,required=True)
    for name in ('acquired','exclusions','adapter','executable','output','directory'):
        parser.add_argument(f'--{name}',type=Path)
    parser.add_argument('--commit');parser.add_argument('--prefix');a = parser.parse_args()
    required = {'prepare':('acquired','exclusions','adapter','executable','output'),
                'verify':('prefix','commit'),'export-tree':('directory','prefix')}[a.mode]
    if any(getattr(a,n) is None for n in required):parser.error(f'{a.mode} requires {required}')
    result = (prepare(a.root,a.acquired,a.exclusions,a.adapter,a.executable,a.output) if a.mode == 'prepare' else
              verify_publication(a.root,a.prefix,a.commit) if a.mode == 'verify' else tree_entries(a.root,a.directory,a.prefix))
    if a.mode == 'verify' and a.output is not None:
        with a.output.open('xb') as stream:stream.write(_bytes(result))
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':main()
