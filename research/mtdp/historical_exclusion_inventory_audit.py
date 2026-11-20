"""Reconcile existing FMJD exclusion artifact without replay or target scores.

The ZIP and three input members are pinned. This reports source coverage and
quarantines; it never certifies full historical completeness or independence.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from research.mtdp.reserved_source_inventory import build

ARTIFACT_SHA = '2768da137051e006a96b2fb0ac5b58ff5778e53fb0371d9fcd982a3948852165'
MEMBERS = {
    'P1RUlfJc-exclusions.json': '25b3ca1a6f0a096c264c8f136135a37fd7d5bb23c04af76a39b4915a611d192e',
    'P1RUlfJc-canonical-history.json': 'eafd1e7b1c447b69f96d307b38a1c7c0fbd8fa9dd9b68f8afe555e3faa02d1b6',
    'two-arena-exclusions.json': '8dac5c60e1eaa10ff8e3e27f5c1fb0d0307edaeaec438e7c9bdc33b3e666dc32',
}


def check_game_audit(sources, game_audit):
    expected = {f"{s['file']}:{i}" for s in sources for i in range(1, s['games'] + 1)}
    if len(expected) != sum(s['games'] for s in sources) or set(game_audit) != expected:
        raise ValueError('Incomplete or duplicate source/index game audit')
    fingerprints = []
    for row in game_audit.values():
        if row['status'] == 'quarantined':
            if 'trajectory_sha256' in row:
                raise ValueError('Quarantine cannot certify a complete trajectory')
        elif row['status'] in ('indexed', 'duplicate'):
            value = row['trajectory_sha256']
            if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Invalid trajectory fingerprint')
            fingerprints.append(value)
        else:
            raise ValueError('Unknown historical game status')
    return Counter(row['status'] for row in game_audit.values()), fingerprints


def reconcile(base, history, combined, reserved):
    if base['sources'] != history['sources'] or combined['sources'][:-1] != history['sources']:
        raise ValueError('Historical source inventory changed')
    old_counts, old_fp = check_game_audit(history['sources'], history['game_audit'])
    added_counts, added_fp = check_game_audit(combined['sources'][-1:], combined['added_event_game_audit'])
    if dict(old_counts) != history['status_counts'] or dict(added_counts) != combined['added_event_status_counts']:
        raise ValueError('Declared status counts do not match per-game evidence')
    if set(old_fp) != set(history['fingerprints']) or set(old_fp + added_fp) != set(combined['fingerprints']):
        raise ValueError('Unique complete-trajectory union changed')
    if not set(base['confirmed_fens']) <= set(history['confirmed_fens']) <= set(combined['confirmed_fens']):
        raise ValueError('Historical confirmed FEN coverage was lost')
    source_digests = {s['sha256'] for s in combined['sources']}
    covered = [e['reserved_event_id'] for e in reserved['events'] if e['pdn_sha256'] in source_digests]
    missing = [e['reserved_event_id'] for e in reserved['events'] if e['pdn_sha256'] not in source_digests]
    for event in reserved['events']:
        if event['reserved_event_id'] in covered and not {r['public_game_id'] for r in event['games']} <= set(combined['public_game_ids']):
            raise ValueError('Covered reserved source lost public game IDs')
    status = old_counts + added_counts
    n_games = sum(s['games'] for s in combined['sources'])
    complete_records = len(old_fp + added_fp)
    unique = len(set(old_fp + added_fp))
    if complete_records + status['quarantined'] != n_games:
        raise ValueError('Replay/quarantine denominator does not reconcile')
    return {'sources': combined['sources'], 'source_count': len(combined['sources']),
            'source_game_records': n_games, 'status_counts': dict(sorted(status.items())),
            'complete_replay_game_records': complete_records,
            'unique_complete_trajectories': unique,
            'duplicate_complete_trajectory_records': complete_records - unique,
            'quarantined_game_records': status['quarantined'],
            'confirmed_prefix_fens': len(combined['confirmed_fens']),
            'public_game_ids': len(combined['public_game_ids']),
            'normalized_notation_fingerprints': len(combined['normalized_token_sequence_sha256']),
            'older_archive_coverage': base['archive'],
            'reserved_events_present_as_sources': covered,
            'reserved_events_missing_as_sources': missing,
            'missing_reserved_source_game_entries': sum(len(e['games']) for e in reserved['events'] if e['reserved_event_id'] in missing),
            'complete_historical_exclusion_registry': False,
            'independent_cohort_qualified': False}


def audit(root, archive_path, *, expected_archive_sha256=ARTIFACT_SHA,
          source_run_id=44730344598, source_artifact_id=14625817620):
    raw = archive_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_archive_sha256:
        raise ValueError('Downloaded artifact ZIP digest changed')
    with zipfile.ZipFile(archive_path) as z:
        data = {}
        for name, digest in MEMBERS.items():
            if z.namelist().count(name) != 1:
                raise ValueError('Missing or duplicated pinned member')
            payload = z.read(name)
            if hashlib.sha256(payload).hexdigest() != digest:
                raise ValueError('Historical exclusion member digest changed')
            data[name] = json.loads(payload)
    result = reconcile(data['P1RUlfJc-exclusions.json'], data['P1RUlfJc-canonical-history.json'],
                       data['two-arena-exclusions.json'], build(root))
    return {'schema': 'mtdp-h13-historical-exclusion-reconciliation-v1',
            'source_run_id': source_run_id, 'source_artifact_id': source_artifact_id,
            'source_artifact_zip_sha256': expected_archive_sha256, 'member_sha256': MEMBERS,
            'engine_revision_of_existing_replay': '0e5189fbb251bf5eaf2e613d0f878bb17c740311',
            'new_engine_calls': 0, 'new_reference_scores_acquired': False,
            'scientific_freeze': False, **result,
            'next_action': 'D1/H43 reconcile the two later reserved sources and all other historical manifests/aliases before declaring full coverage. Keep H13 whole-event/public-ID/notation screening active; do not admit a new cohort on these counts alone.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--expected-archive-sha256')
    p.add_argument('--source-run-id', type=int)
    p.add_argument('--source-artifact-id', type=int)
    a = p.parse_args()
    supplied = (a.expected_archive_sha256, a.source_run_id, a.source_artifact_id)
    if any(x is not None for x in supplied) and not all(x is not None for x in supplied):
        p.error('A fresh artifact requires all three GitHub provenance arguments')
    kwargs = {} if a.expected_archive_sha256 is None else {
        'expected_archive_sha256': a.expected_archive_sha256,
        'source_run_id': a.source_run_id, 'source_artifact_id': a.source_artifact_id}
    result = audit(a.root, a.archive, **kwargs)
    with a.output.open('xb') as out:
        out.write((json.dumps(result, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({k: result[k] for k in ('source_count', 'source_game_records',
                     'unique_complete_trajectories', 'quarantined_game_records',
                     'confirmed_prefix_fens', 'reserved_events_missing_as_sources')}))


if __name__ == '__main__':
    main()
