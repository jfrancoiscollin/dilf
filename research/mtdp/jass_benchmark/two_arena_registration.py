"""Pinned two-arena registration and temporal gates; no games or scores fetched."""
import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.mtdp.jass_benchmark.named_arena_inputs import utc
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest

PREFIX = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
REGISTRATION = PREFIX + 'two-named-arenas-20261118-registration.json'
PROTOCOL = PREFIX + 'TWO_NAMED_ARENAS_PREREGISTRATION_2026-11-18.md'
REGISTRATION_SHA = '072f0326c09e79c9f8245b741b02786b67408b38bcb9c6b0cbb08bc1218bdb27'
PROTOCOL_SHA = 'c2f46a4e37b2ca33d233a4913d5ab9dd601531475d1c1dcfbe70dee3a7e5b961'
EVENTS = ('s7ahYqL4', 'D9PF2OSW')
STARTS = ('2026-11-18T23:00:00+00:00', '2026-11-19T02:00:00+00:00')
FINAL_GATE = utc('2026-11-19T02:57:00+00:00')
BRANCH = 'research/mtdp-foundation'
MODULE = 'research/mtdp/jass_benchmark/two_arena_registration.py'


def _now():
    return datetime.now(timezone.utc)


def validate(record):
    if (record.get('schema') != 'mtdp-two-named-arenas-preregistration-v1'
            or record.get('study_id') != 'two-named-arenas-20261118' or record.get('cohort_count') != 2
            or len(record.get('events', [])) != 2
            or tuple(r['event']['id'] for r in record['events']) != EVENTS
            or record.get('no_future_games_or_scores_accessed') is not True
            or record.get('reserve_entire_events_from_D1') is not True):
        raise ValueError('Exact two-event prospective registration changed')
    for entry, start in zip(record['events'], STARTS, strict=True):
        event, facts, receipt = entry['event'], entry['prestart_facts'], entry['receipt']
        if (event['createdBy'] != 'lidraughts' or event['system'] != 'arena' or event['variant'] != 'standard'
                or event['clock'] != {'limit': 300, 'increment': 0} or event['minutes'] != 57
                or utc(event['startsAt']) != utc(start)):
            raise ValueError('Registered official standard 5+0 format or start changed')
        if (any(facts.get(k) != v for k,v in event.items()) or facts.get('isFinished') is True
                or type(facts.get('secondsToStart')) is not int or facts['secondsToStart'] <= 0
                or not utc(receipt['requested_at_utc']) <= utc(receipt['retrieved_at_utc']) < utc(start)
                or not utc(record['registered_at_utc']) < utc(start)
                or receipt['url'] != f"https://lidraughts.org/api/tournament/{event['id']}"
                or not re.fullmatch('[0-9a-f]{64}', receipt['sha256']) or receipt['bytes'] <= 0):
            raise ValueError('Pre-start metadata evidence is incomplete or retrospective')
    analysis = record['analysis']
    expected = {'total_node_budgets': [10000,50000,200000], 'primary_total_node_budget':50000,
                'verification_fraction':0.1, 'source_ranking_scan_successor_depth':12,
                'geometry_source_scan_successor_depth':16, 'target_scan_successor_depth':16,
                'bootstrap_resamples':10000, 'bootstrap_seed':20261113, 'percentile_indices':[249,9749]}
    if any(analysis.get(k) != v for k,v in expected.items()) or utc(record['all_final_inputs_gate_utc']) != FINAL_GATE:
        raise ValueError('Registered references, budgets or analysis settings changed')
    return record


def load(root):
    raw = (root / REGISTRATION).read_bytes()
    if digest(raw) != REGISTRATION_SHA or digest((root / PROTOCOL).read_bytes()) != PROTOCOL_SHA:
        raise ValueError('Two-arena registration or protocol hash changed')
    record = validate(json.loads(raw))
    for name, expected in record['method_files_sha256'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or digest((root/name).read_bytes()) != expected:
            raise ValueError('Frozen scientific selector/control method changed')
    return record


def final_gate(record, metadata, now):
    validate(record)
    if now.tzinfo is None or now < FINAL_GATE:
        raise ValueError('Joint final-input gate is closed until both scheduled finishes')
    if set(metadata) != set(EVENTS):
        raise ValueError('Both named final metadata records are required')
    for entry in record['events']:
        event = entry['event']; facts = metadata[event['id']]
        if (facts.get('isFinished') is not True or facts.get('secondsToStart',0) != 0
                or any(facts.get(k) != v for k,v in event.items() if k != 'startsAt')
                or utc(facts['startsAt']) != utc(event['startsAt'])):
            raise ValueError('A named event is unfinished or its registered format changed')
    return {'events': list(EVENTS), 'all_final_metadata_valid':True, 'scientific_freeze':False}


def verify_before_start(root, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('An exact publication commit SHA is required')
    record = load(root)
    if _now() >= utc(STARTS[0]):
        raise ValueError('Live pre-start publication verification is closed')
    ref = f'refs/remotes/origin/{BRANCH}'
    subprocess.run(['git','-C',str(root),'fetch','--no-tags','origin',f'refs/heads/{BRANCH}:{ref}'],check=True,capture_output=True)
    head = subprocess.check_output(['git','-C',str(root),'rev-parse',ref],text=True).strip()
    subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',commit,head],check=True)
    for name, expected in ((REGISTRATION,REGISTRATION_SHA),(PROTOCOL,PROTOCOL_SHA),(MODULE,digest((root/MODULE).read_bytes()))):
        if digest(subprocess.check_output(['git','-C',str(root),'show',f'{commit}:{name}'])) != expected:
            raise ValueError('Published registration snapshot or verification method differs')
    observed = _now()
    if observed >= utc(STARTS[0]):
        raise ValueError('Publication was not observed before the first event')
    return {'schema':'mtdp-two-arena-live-prestart-publication-v1','published_commit':commit,
            'observed_branch_head':head,'verified_at_utc':observed.isoformat(),'events':list(EVENTS),
            'registration_sha256':REGISTRATION_SHA,'protocol_sha256':PROTOCOL_SHA,
            'publication_seen_before_all_starts':True,'scientific_freeze':False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('check','verify-before-start','final-metadata'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--commit')
    p.add_argument('--metadata',type=Path,action='append');p.add_argument('--output',type=Path)
    a = p.parse_args();record=load(a.root)
    if a.mode=='verify-before-start':
        if not a.commit:p.error('--commit required')
        result=verify_before_start(a.root,a.commit)
    elif a.mode=='final-metadata':
        if _now()<FINAL_GATE:raise ValueError('Joint final-input gate is closed')
        if len(a.metadata or [])!=2:p.error('two --metadata paths required')
        records=[json.loads(f.read_bytes()) for f in a.metadata]
        result=final_gate(record,{r['id']:r for r in records},_now())
    else:result={'events':list(EVENTS),'registration_valid':True,'scientific_freeze':False,'final_gate_utc':FINAL_GATE.isoformat()}
    if a.output is not None:
        with a.output.open('xb') as f:f.write((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
