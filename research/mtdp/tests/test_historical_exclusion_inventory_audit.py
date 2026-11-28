"""Synthetic accounting checks; the large actual artifact is audited explicitly."""
from copy import deepcopy

import pytest

from research.mtdp.historical_exclusion_inventory_audit import reconcile


def inputs():
    first = {'file': 'old.pdn', 'games': 2, 'sha256': 'a' * 64}
    added = {'file': 'added.pdn', 'games': 1, 'sha256': 'b' * 64}
    base = {'sources': [first], 'confirmed_fens': ['f1'],
            'archive': {'archived_files': 1, 'excluded_fens': 1}}
    history = {'sources': [first], 'confirmed_fens': ['f1', 'f2'],
               'game_audit': {'old.pdn:1': {'status': 'indexed', 'trajectory_sha256': 'c' * 64},
                              'old.pdn:2': {'status': 'quarantined'}},
               'fingerprints': ['c' * 64], 'status_counts': {'indexed': 1, 'quarantined': 1}}
    combined = {'sources': [first, added], 'confirmed_fens': ['f1', 'f2', 'f3'],
                'added_event_game_audit': {'added.pdn:1': {'status': 'indexed', 'trajectory_sha256': 'c' * 64}},
                'added_event_status_counts': {'indexed': 1}, 'fingerprints': ['c' * 64],
                'public_game_ids': ['Public01'], 'normalized_token_sequence_sha256': ['d' * 64]}
    reserved = {'events': [{'reserved_event_id': 'present', 'pdn_sha256': 'b' * 64,
                           'games': [{'public_game_id': 'Public01'}]},
                          {'reserved_event_id': 'missing', 'pdn_sha256': 'e' * 64,
                           'games': [{'public_game_id': 'Public02'}]}]}
    return base, history, combined, reserved


def test_reconciles_cross_source_duplicates_and_quarantine_without_qualification():
    report = reconcile(*inputs())
    assert report['source_game_records'] == 3
    assert report['complete_replay_game_records'] == 2
    assert report['unique_complete_trajectories'] == 1
    assert report['duplicate_complete_trajectory_records'] == 1
    assert report['quarantined_game_records'] == 1
    assert report['reserved_events_missing_as_sources'] == ['missing']
    assert report['missing_reserved_source_game_entries'] == 1
    assert report['complete_historical_exclusion_registry'] is False
    assert report['independent_cohort_qualified'] is False


@pytest.mark.parametrize('case', ['missing_index', 'guessed_quarantine', 'wrong_count',
                                 'lost_fen', 'lost_public_id', 'wrong_union'])
def test_incomplete_or_inconsistent_historical_evidence_is_rejected(case):
    base, history, combined, reserved = deepcopy(inputs())
    if case == 'missing_index':
        history['game_audit'].pop('old.pdn:2')
    elif case == 'guessed_quarantine':
        history['game_audit']['old.pdn:2']['trajectory_sha256'] = 'f' * 64
    elif case == 'wrong_count':
        history['status_counts']['indexed'] = 2
    elif case == 'lost_fen':
        combined['confirmed_fens'].remove('f2')
    elif case == 'lost_public_id':
        combined['public_game_ids'] = []
    else:
        combined['fingerprints'] = []
    with pytest.raises(ValueError):
        reconcile(base, history, combined, reserved)
