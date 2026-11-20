"""Synthetic union/accounting checks; real closed exports run in pinned CI."""
from copy import deepcopy

import pytest

from research.mtdp.closed_reserved_exclusions import combine


def inputs():
    base = {'sources': [{'file': 'old.pdn', 'games': 3}], 'fingerprints': ['a' * 64],
            'confirmed_fens': ['old'], 'public_game_ids': ['OldGame1'],
            'normalized_token_sequence_sha256': ['b' * 64]}
    counts = {'unique_complete_trajectories': 1, 'complete_replay_game_records': 2,
              'quarantined_game_records': 1}
    extension = {'game_audit': {'new.pdn:1': {'status': 'indexed', 'trajectory_sha256': 'a' * 64},
                                 'new.pdn:2': {'status': 'quarantined', 'confirmed_prefix_positions': 2}},
                 'status_counts': {'indexed': 1, 'quarantined': 1},
                 'fingerprints': ['a' * 64], 'confirmed_fens': ['old', 'prefix']}
    return base, counts, extension, [{'file': 'new.pdn', 'games': 2}], ['NewGame1'], ['c' * 64]


def test_union_preserves_prefixes_quarantines_and_cross_base_duplicates():
    result = combine(*inputs())
    assert result['accounting'] == {'source_count': 2, 'source_game_records': 5,
        'extension_game_records': 2, 'complete_replay_game_records': 3,
        'quarantined_game_records': 2, 'unique_complete_trajectories': 1,
        'duplicate_complete_trajectory_records': 2, 'confirmed_prefix_fens': 2}
    assert result['extension_complete_trajectories_already_base'] == 1
    assert result['confirmed_fens'] == ['old', 'prefix']
    assert result['public_game_ids'] == ['NewGame1', 'OldGame1']


@pytest.mark.parametrize('case', ['missing_game', 'guessed_quarantine', 'wrong_status',
                                 'wrong_union', 'wrong_base', 'duplicate_filename'])
def test_invalid_extension_cannot_become_a_historical_cache(case):
    base, counts, ext, sources, public, tokens = deepcopy(inputs())
    if case == 'missing_game':
        ext['game_audit'].pop('new.pdn:2')
    elif case == 'guessed_quarantine':
        ext['game_audit']['new.pdn:2']['trajectory_sha256'] = 'd' * 64
    elif case == 'wrong_status':
        ext['status_counts']['indexed'] = 2
    elif case == 'wrong_union':
        ext['fingerprints'] = []
    elif case == 'wrong_base':
        counts['quarantined_game_records'] = 2
    else:
        base['sources'][0]['file'] = 'new.pdn'
    with pytest.raises(ValueError):
        combine(base, counts, ext, sources, public, tokens)
