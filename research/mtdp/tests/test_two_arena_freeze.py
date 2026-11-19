"""Joint publication barriers; all games/clocks/transports here are fixtures."""
import base64
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import two_arena_freeze as bundle
from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.two_arena_rehearsal import game
from research.mtdp.jass_benchmark.named_arena_rehearsal import FIXTURE_FEN

ROOT = Path(__file__).resolve().parents[3]
FUTURE = datetime(2026,11,19,3,tzinfo=timezone.utc)


@pytest.fixture
def payloads(monkeypatch):
    """Empty population, but nonempty manufactured exports with valid receipts."""
    monkeypatch.setattr(study,'_now',lambda:FUTURE)
    reg = study.load(ROOT)
    events, inputs, data = {}, {}, {}
    for i,event in enumerate(study.EVENTS):
        raw = game(f'FIXTURE{i}',FIXTURE_FEN)  # explicitly Synthetic-tagged, never a real result
        metadata = _bytes({**reg['events'][i]['event'],'isFinished':True,'secondsToStart':0})
        receipts = _bytes({role:{'url':f'https://lidraughts.org/api/tournament/{event}/games',
                               'sha256':bundle.digest(raw),'bytes':len(raw),
                               'request_id':f'fixture-{i}-{role}','requested_at_utc':FUTURE.isoformat(),
                               'retrieved_at_utc':FUTURE.isoformat()} for role in ('first','independent_repeat')})
        data.update({f'{event}/first.pdn':raw,f'{event}/repeat.pdn':raw,
                     f'{event}/metadata.json':metadata,f'{event}/downloads.json':receipts})
        inputs[event] = {'pdn_sha256':bundle.digest(raw),'bytes':len(raw),
                         'metadata_sha256':bundle.digest(metadata),'download_receipts_sha256':bundle.digest(receipts)}
        game_id = f'mtdp-lidraughts-{event}.pdn:1'
        status = 'accepted' if i == 0 else 'excluded_token_sequence'
        events[event] = {'pdn_sha256':bundle.digest(raw),'candidate_targets':[],'benchmark_targets':[],
                         'target_plies':{},'game_status_counts':{status:1},'game_audit':{game_id:{'status':status}},
                         'full_signature_strata':{a:{'equal':0,'different':0} for a in ('L','LCB')},
                         'jass_catalogue':{'positions':[],'targets':0,'target_action_occurrences':0,
                                           'distinct_positions':0,'distinct_sources':0},
                         'whole_event_index':{'game_audit':{game_id:{'status':'indexed'}},'confirmed_fens':[]}}
    p = {'schema':'mtdp-two-arena-joint-proposal-v1','study_id':reg['study_id'],
         'event_order':list(study.EVENTS),'events':events,'scientific_freeze':False,'synthetic_rehearsal':True,
         'registration_sha256':study.REGISTRATION_SHA,'protocol_sha256':study.PROTOCOL_SHA,
         'exclusions_sha256':bundle.replay.EXCLUSIONS_SHA,'analysis':reg['analysis'],
         'engines':{**reg['engines'],'jass_catalogue_sha256':bundle.replay.CATALOGUE_SHA},
         'implementation_commit':'a'*40,'implementation_sha256':{n:'b'*64 for n in bundle.replay.DEPENDENCIES},
         'input_check':{'schema':'mtdp-two-arena-final-input-check-v1','registration_sha256':study.REGISTRATION_SHA,
                        'protocol_sha256':study.PROTOCOL_SHA,'events':inputs,'scientific_freeze':False,
                        'scope':'joint_final_input_receipts_only_population_and_published_freeze_still_required'}}
    data.update({'proposal.json':_bytes(p),'manifest.json':_bytes(bundle._manifest(p)),
                 'reproduction.json':_bytes({'kind':'synthetic_unit_fixture'}),
                 'registration.json':(ROOT/study.REGISTRATION).read_bytes(),
                 'protocol.md':(ROOT/study.PROTOCOL).read_bytes(),
                 'prestart-publication.json':(ROOT/bundle.PRESTART).read_bytes()})
    audit_files = {n:v for n,v in data.items() if n.startswith(tuple(e+'/' for e in study.EVENTS))}
    audit_files['acquisition.json'] = _bytes(p['input_check'])
    for i,event in enumerate(study.EVENTS):
        raw = data[f'{event}/metadata.json']
        audit_files[f'{event}/metadata-download.json'] = _bytes({
            'url':f'https://lidraughts.org/api/tournament/{event}','sha256':bundle.digest(raw),'bytes':len(raw),
            'request_id':f'fixture-meta-{i}','requested_at_utc':FUTURE.isoformat(),'retrieved_at_utc':FUTURE.isoformat()})
    data['acquisition-audit.json'] = _bytes({'schema':'mtdp-two-arena-raw-acquisition-audit-v1',
        'scientific_freeze':False,'files':{n:{'sha256':bundle.digest(v),'bytes':len(v),
        'content_base64':base64.b64encode(v).decode()} for n,v in audit_files.items()}})
    pub = {'schema':'mtdp-two-arena-publication-v1','scientific_freeze':False,
           'synthetic_rehearsal':True,'state':'synthetic_rehearsal_only',
           'bundle_implementation':{'commit':'a'*40,'files_sha256':{n:'b'*64 for n in (bundle.MODULE,*bundle.replay.DEPENDENCIES)}}}
    data['publication.json'] = _bytes(pub)
    return rehash(data)


def rehash(data):
    pub = json.loads(data['publication.json'])
    pub['files'] = {n:{'sha256':bundle.digest(v),'bytes':len(v)} for n,v in data.items() if n != 'publication.json'}
    data['publication.json'] = _bytes(pub)
    return data


def test_empty_synthetic_bundle_valid_only_for_diagnostic(payloads):
    pub,p = bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)
    assert not pub['scientific_freeze'] and all(not e['benchmark_targets'] for e in p['events'].values())
    with pytest.raises(ValueError,match='Synthetic'):
        bundle.validate_payloads(ROOT,payloads)


def test_stripping_synthetic_flags_cannot_authorize_raw_fixture(payloads):
    p = json.loads(payloads['proposal.json']);p['synthetic_rehearsal'] = False
    payloads['proposal.json'] = _bytes(p);payloads['manifest.json'] = _bytes(bundle._manifest(p))
    payloads['reproduction.json'] = _bytes({'kind':'subprocess_hash_seed_reproduction','runs':[
        {'hash_seed':s,'exit_status':0,'proposal_sha256':bundle.digest(payloads['proposal.json'])} for s in (7,61)]})
    pub = json.loads(payloads['publication.json']);pub.update(synthetic_rehearsal=False,state='prepared_not_published')
    payloads['publication.json'] = _bytes(pub);rehash(payloads)
    with pytest.raises(ValueError,match='Synthetic bytes'):
        bundle.validate_payloads(ROOT,payloads)


@pytest.mark.parametrize('name',['registration.json','protocol.md','prestart-publication.json','proposal.json',
                                 f'{study.EVENTS[0]}/repeat.pdn'])
def test_changed_inventory_bytes_refused(payloads,name):
    payloads[name] += b' '
    with pytest.raises(ValueError,match='bytes changed'):
        bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


def test_rehashed_prestart_tamper_still_refused(payloads):
    proof = json.loads(payloads['prestart-publication.json']);proof['verified_at_utc'] = FUTURE.isoformat()
    payloads['prestart-publication.json'] = _bytes(proof);rehash(payloads)
    with pytest.raises(ValueError,match='pre-start publication receipt changed'):
        bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


@pytest.mark.parametrize('mutation', ['budget','inventory','mask','source_depth','self_freeze','mapping'])
def test_proposal_contract_mutations(payloads,mutation):
    p = json.loads(payloads['proposal.json'])
    if mutation == 'budget':p['analysis']['primary_total_node_budget'] = 200000
    elif mutation == 'inventory':p['implementation_sha256'].pop(bundle.replay.DEPENDENCIES[-1])
    elif mutation == 'mask':p['events'][study.EVENTS[0]]['full_signature_strata']['LCB']['equal'] = 1
    elif mutation == 'source_depth':p['analysis']['source_ranking_scan_successor_depth'] = 16
    elif mutation == 'self_freeze':p['scientific_freeze'] = True
    else:p['events'][study.EVENTS[0]]['jass_catalogue']['positions'] = [{'fen':'extra'}]
    with pytest.raises(ValueError):bundle.validate_proposal(ROOT,p)


def test_manifest_cannot_self_declare_publication(payloads):
    m = json.loads(payloads['manifest.json']);m['scientific_freeze'] = True
    payloads['manifest.json'] = _bytes(m);rehash(payloads)
    with pytest.raises(ValueError,match='manifest differs'):
        bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


def test_raw_metadata_transport_receipt_cannot_be_omitted(payloads):
    audit = json.loads(payloads['acquisition-audit.json'])
    audit['files'].pop(f'{study.EVENTS[0]}/metadata-download.json')
    payloads['acquisition-audit.json'] = _bytes(audit);rehash(payloads)
    with pytest.raises(ValueError,match='metadata or acquisition receipts missing'):
        bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


def test_rehashed_raw_audit_cannot_disagree_with_final_inputs(payloads):
    audit = json.loads(payloads['acquisition-audit.json']);name = f'{study.EVENTS[0]}/first.pdn'
    raw = b'changed export'
    audit['files'][name] = {'sha256':bundle.digest(raw),'bytes':len(raw),'content_base64':base64.b64encode(raw).decode()}
    payloads['acquisition-audit.json'] = _bytes(audit);rehash(payloads)
    with pytest.raises(ValueError,match='audit differs from final inputs'):
        bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


def test_raw_failed_attempt_bytes_retained_without_interpreting_continuations(payloads,tmp_path):
    # Divergent attempts are provenance, never an alternative selectable population.
    acquired = tmp_path/'acquired';acquired.mkdir()
    audit = json.loads(payloads['acquisition-audit.json'])
    for name,entry in audit['files'].items():
        path = acquired/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(base64.b64decode(entry['content_base64']))
    failed = acquired/study.EVENTS[0]/'attempt-01'/'first.pdn';failed.parent.mkdir()
    failed.write_bytes(bytes([0,255,13,10]))
    audit = bundle._audit_acquisition(acquired)
    assert base64.b64decode(audit['files'][failed.relative_to(acquired).as_posix()]['content_base64']) == failed.read_bytes()
    payloads['acquisition-audit.json'] = _bytes(audit);rehash(payloads)
    bundle.validate_payloads(ROOT,payloads,allow_synthetic=True)


def test_acquisition_audit_refuses_symlink(tmp_path):
    outside = tmp_path/'outside';outside.write_bytes(b'fixture')
    acquired = tmp_path/'acquired';acquired.mkdir();(acquired/'alias').symlink_to(outside)
    with pytest.raises(ValueError,match='symlinks'):bundle._audit_acquisition(acquired)


def test_joint_clock_precedes_any_file_or_remote_access(monkeypatch,tmp_path):
    monkeypatch.setattr(study,'_now',lambda:datetime(2026,11,19,2,tzinfo=timezone.utc))
    monkeypatch.setattr(bundle,'_git',lambda *a:pytest.fail('Git reached before clock gate'))
    with pytest.raises(ValueError,match='closed'):
        bundle.verify_publication(tmp_path,'research/cohort','a'*40)
    with pytest.raises(ValueError,match='closed'):
        bundle.prepare(ROOT,tmp_path/'missing',tmp_path,tmp_path,tmp_path,tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_failed_child_retains_diagnostics_without_bundle(monkeypatch,tmp_path):
    monkeypatch.setattr(bundle.acquisition,'check',lambda *a:{})
    monkeypatch.setattr(bundle,'_synthetic',lambda *a:False)
    monkeypatch.setattr(bundle.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=17,stdout=b'partial',stderr=b'fixture technical error'))
    output = tmp_path/'out'
    with pytest.raises(ValueError,match='diagnostics retained'):
        bundle.prepare(ROOT,tmp_path,tmp_path,tmp_path,tmp_path,output)
    assert (output/'proposal-7.stdout').read_bytes() == b'partial'
    assert (output/'proposal-7.stderr').read_bytes() == b'fixture technical error'
    assert json.loads((output/'reproduction-attempts.json').read_bytes())['runs'][0]['exit_status'] == 17
    assert not (output/'bundle').exists()


def test_unpushed_local_commit_is_not_a_remote_freeze(monkeypatch,tmp_path):
    monkeypatch.setattr(study,'_now',lambda:FUTURE)
    def git(path,*args):
        return subprocess.check_output(['git','-C',str(path),*args],stderr=subprocess.DEVNULL)
    origin = tmp_path/'origin.git';subprocess.run(['git','init','--bare',str(origin)],check=True,capture_output=True)
    local = tmp_path/'local';subprocess.run(['git','clone',str(origin),str(local)],check=True,capture_output=True)
    git(local,'config','user.name','fixture');git(local,'config','user.email','fixture@example.invalid')
    git(local,'checkout','-b',study.BRANCH)
    (local/'file').write_text('parent');git(local,'add','file');git(local,'commit','-m','parent')
    git(local,'push','origin',study.BRANCH)
    (local/'file').write_text('unpublished');git(local,'commit','-am','unpublished')
    commit = git(local,'rev-parse','HEAD').decode().strip()
    monkeypatch.setattr(bundle,'validate_payloads',lambda *a:pytest.fail('Unpublished payload reached validation'))
    with pytest.raises(subprocess.CalledProcessError):
        bundle.verify_publication(local,'unpublished/bundle',commit)


@pytest.mark.parametrize('prefix',['','.', '../cohort','/tmp/cohort'])
def test_unsafe_repository_paths_refused(prefix):
    with pytest.raises(ValueError):bundle._safe_path(prefix)


def test_exact_publication_sha_required(monkeypatch,tmp_path):
    monkeypatch.setattr(study,'_now',lambda:FUTURE)
    monkeypatch.setattr(bundle,'_git',lambda *a:pytest.fail('Git reached for abbreviated commit'))
    with pytest.raises(ValueError,match='Exact published'):
        bundle.verify_publication(tmp_path,'research/cohort','abc123')


def test_pushed_temporary_git_bundle_and_method_bytes_are_verified(payloads,monkeypatch,tmp_path):
    """Manufactured empty cohorts and a filesystem-only Git origin; no live result."""
    def git(path,*args):
        return subprocess.check_output(['git','-C',str(path),*args],stderr=subprocess.DEVNULL)
    local = tmp_path/'local';origin = tmp_path/'origin.git'
    subprocess.run(['git','init',str(local)],check=True,capture_output=True)
    subprocess.run(['git','init','--bare',str(origin)],check=True,capture_output=True)
    git(local,'remote','add','origin',str(origin));git(local,'checkout','-b',study.BRANCH)
    git(local,'config','user.name','fixture');git(local,'config','user.email','fixture@example.invalid')
    names = {bundle.MODULE,*bundle.replay.DEPENDENCIES,study.REGISTRATION,study.PROTOCOL,bundle.PRESTART,
             *study.load(ROOT)['method_files_sha256']}
    for name in names:
        path = local/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    git(local,'add','.')
    git(local,'commit','--allow-empty','-m','fixture method snapshot')
    implementation = git(local,'rev-parse','HEAD').decode().strip()
    # This filesystem-only Git fixture has its own history. Keep the real pinned
    # receipt-byte/time validation, substituting only its Git ancestor for this
    # temporary origin; no dependency on missing CI shallow-checkout ancestors.
    original_prestart = bundle._prestart
    monkeypatch.setattr(bundle,'_prestart',lambda raw:{**original_prestart(raw),'published_commit':implementation})
    acquired = tmp_path/'acquired';acquired.mkdir()
    p = json.loads(payloads['proposal.json']);p['synthetic_rehearsal'] = False
    p['implementation_commit'] = implementation
    p['implementation_sha256'] = {n:bundle.digest((local/n).read_bytes()) for n in bundle.replay.DEPENDENCIES}
    # Only this in-memory positive contract fixture omits Synthetic tags.
    # It is never exported to the real research repository or a live remote.
    for event in study.EVENTS:
        (acquired/event).mkdir()
        for name in bundle.INPUT_NAMES:
            (acquired/event/name).write_bytes(payloads[f'{event}/{name}'])
        raw = (acquired/event/'first.pdn').read_bytes().replace(b'[Synthetic "true"]'+bytes([13,10]),b'')
        for name in ('first.pdn','repeat.pdn'):(acquired/event/name).write_bytes(raw)
        receipts = json.loads((acquired/event/'downloads.json').read_bytes())
        for entry in receipts.values():entry.update(sha256=bundle.digest(raw),bytes=len(raw))
        (acquired/event/'downloads.json').write_bytes(_bytes(receipts))
        p['events'][event]['pdn_sha256'] = bundle.digest(raw)
    p['input_check'] = bundle.acquisition.check(local,acquired)
    (acquired/'acquisition.json').write_bytes(_bytes(p['input_check']))
    old_audit = json.loads(payloads['acquisition-audit.json'])
    for event in study.EVENTS:
        name = f'{event}/metadata-download.json'
        (acquired/name).write_bytes(base64.b64decode(old_audit['files'][name]['content_base64']))
    proposals = [tmp_path/f'proposal-{seed}.json' for seed in (7,61)]
    for path in proposals:path.write_bytes(_bytes(p))
    reproduction = {'kind':'subprocess_hash_seed_reproduction','runs':[
        {'hash_seed':seed,'exit_status':0,'proposal_sha256':bundle.digest(_bytes(p))} for seed in (7,61)]}
    prefix = 'research/fixture-joint-bundle'
    pub = bundle._compose(local,acquired,proposals,reproduction,local/prefix)
    assert pub['scientific_freeze'] is False
    git(local,'add',prefix);git(local,'commit','-m','fixture publication')
    commit = git(local,'rev-parse','HEAD').decode().strip()
    # A prepared and even committed local bundle is still not a remote freeze.
    git(local,'push','origin',implementation+':refs/heads/'+study.BRANCH)
    with pytest.raises(subprocess.CalledProcessError):bundle.verify_publication(local,prefix,commit)
    git(local,'push','origin',study.BRANCH)
    receipt = bundle.verify_publication(local,prefix,commit)
    assert receipt['scientific_freeze'] is True and receipt['published_commit'] == commit
    assert receipt['observed_branch_head'] == commit
    entries = bundle.tree_entries(local,local/prefix,'research/new-fixture-prefix')
    assert all(e['content'].encode() == (local/prefix/e['path'].split('research/new-fixture-prefix/')[1]).read_bytes() for e in entries)
    with pytest.raises(ValueError,match='already exists'):bundle.tree_entries(local,local/prefix,prefix)
    # Rehashing every envelope cannot certify false historical method bytes.
    data = {n:(local/prefix/n).read_bytes() for n in bundle.FILES | {'publication.json'}}
    false_p = json.loads(data['proposal.json']);false_p['implementation_sha256'][bundle.replay.MODULE] = '0'*64
    data['proposal.json'] = _bytes(false_p);data['manifest.json'] = _bytes(bundle._manifest(false_p))
    repro = json.loads(data['reproduction.json'])
    for run in repro['runs']:run['proposal_sha256'] = bundle.digest(data['proposal.json'])
    data['reproduction.json'] = _bytes(repro);rehash(data)
    for name,raw in data.items():(local/prefix/name).write_bytes(raw)
    git(local,'add',prefix);git(local,'commit','-m','fixture false method digest');git(local,'push','origin',study.BRANCH)
    bad = git(local,'rev-parse','HEAD').decode().strip()
    with pytest.raises(ValueError,match='implementation or registration bytes differ'):
        bundle.verify_publication(local,prefix,bad)
