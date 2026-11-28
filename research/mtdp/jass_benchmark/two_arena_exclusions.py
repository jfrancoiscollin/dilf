"""Extend immutable historical exclusions with every P1RUlfJc game/prefix.

No new-cohort PDN, future position, score or engine search is read.
"""
import argparse
import json
from pathlib import Path
from collections import Counter

from research.mtdp.jass_benchmark.two_arena_registration import load, REGISTRATION_SHA
from research.mtdp.jass_benchmark.named_arena_replay import (
    checked_registry, checked_history_index, checked_engine, index_games, token_fingerprint,
    REGISTRY_SHA, INDEX_SHA,
)
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest, public_ids
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.pdn import read_games
from research.mtdp.jass_cohort import ADAPTER_COMMIT

PDN = 'research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc/mtdp-lidraughts-P1RUlfJc.pdn'
MODULE = 'research/mtdp/jass_benchmark/two_arena_exclusions.py'


def combine(registry, historical, extension, public, tokens):
    if not set(registry['confirmed_fens']).issubset(historical['confirmed_fens']):
        raise ValueError('Historical index lost an existing registry FEN')
    if len(public) != len(set(public)):
        raise ValueError('Added historical export repeats a public game ID')
    old_fingerprints = set(historical['fingerprints'])
    for row in extension['game_audit'].values():
        if row['status'] == 'quarantined' and 'trajectory_sha256' in row:
            raise ValueError('A quarantined game cannot certify a full trajectory')
    return {'public_game_ids': sorted(set(registry['public_game_ids']) | set(public)),
            'normalized_token_sequence_sha256': sorted(set(registry['normalized_token_sequence_sha256']) | set(tokens)),
            'fingerprints': sorted(old_fingerprints | set(extension['fingerprints'])),
            'confirmed_fens': sorted(set(historical['confirmed_fens']) | set(extension['confirmed_fens'])),
            'added_event_game_audit': extension['game_audit'],
            'added_event_status_counts': extension['status_counts'],
            'added_complete_trajectories_already_historical': len(old_fingerprints & set(extension['fingerprints']))}


def prepare(root, registry_path, index_path, adapter):
    registration = load(root)
    registry = checked_registry(root, registry_path)
    historical = checked_history_index(root, index_path, registry)
    expected = registration['exclude_additional_event']
    path = root / PDN
    if digest(path.read_bytes()) != expected['pdn_sha256']:
        raise ValueError('Whole frozen P1RUlfJc export changed')
    games = read_games(path)
    if len(games) != expected['games']:
        raise ValueError('Whole historical arena game count changed')
    engine = checked_engine(adapter)
    extension = index_games([(path, expected['games'])], engine)
    combined = combine(registry, historical, extension, public_ids(path), [token_fingerprint(g) for g in games])
    return {'schema': 'mtdp-two-arena-historical-exclusions-v1', 'study_id': registration['study_id'],
            'registration_sha256': REGISTRATION_SHA, 'base_registry_sha256': REGISTRY_SHA,
            'base_canonical_history_sha256': INDEX_SHA, 'adapter_commit': ADAPTER_COMMIT,
            'added_event': expected, 'sources': registry['sources'] + [{'file': path.name, 'games': len(games), 'sha256': expected['pdn_sha256']}],
            'implementation_sha256': digest((root/MODULE).read_bytes()), **combined,
            'scope': 'historical_exclusions_only_no_future_cohort_data_or_scores',
            'fen_scope': 'all_legally_confirmed_prefixes_including_quarantined_games_no_guessed_continuation',
            'scientific_freeze': False}


def summary(value):
    return {'schema':'mtdp-two-arena-historical-exclusions-summary-v1','study_id':value['study_id'],
            'exclusions_sha256':digest(_bytes(value)), 'sources':len(value['sources']),
            'historical_games':sum(r['games'] for r in value['sources']),
            'public_ids':len(value['public_game_ids']), 'token_fingerprints':len(value['normalized_token_sequence_sha256']),
            'complete_trajectory_fingerprints':len(value['fingerprints']), 'confirmed_fens':len(value['confirmed_fens']),
            'added_event':value['added_event'], 'added_event_status_counts':value['added_event_status_counts'],
            'added_complete_trajectories_already_historical':value['added_complete_trajectories_already_historical'],
            'implementation_sha256':value['implementation_sha256'], 'scientific_freeze':False,
            'scope':value['scope']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','base-registry','base-index','adapter','output'):
        p.add_argument(f'--{name}',type=Path,required=True)
    p.add_argument('--summary',type=Path);a=p.parse_args()
    result=prepare(a.root,a.base_registry,a.base_index,a.adapter)
    with a.output.open('xb') as f:f.write(_bytes(result))
    small=summary(result)
    if a.summary is not None:
        with a.summary.open('xb') as f:f.write(_bytes(small))
    print(json.dumps(small,sort_keys=True))


if __name__=='__main__':main()
