"""No rules engine or target-score access: reserved identity handoff only."""
from pathlib import Path

import pytest

from research.mtdp.reserved_source_inventory import build, encoded, game_inventory, sha

RAW = (b'[Event "synthetic"]\n[Site "https://lidraughts.org/Abcd1234"]\n'
       b'1. 32-28 17-22 *\n')


def test_reserved_game_identity_is_bound_to_exact_bytes_and_one_based_index():
    assert game_inventory(RAW, sha(RAW), 1) == [
        {'game_id': sha(RAW) + ':1', 'source_game_index': 1, 'public_game_id': 'Abcd1234'}]


@pytest.mark.parametrize('raw,digest,count,match', [
    (RAW + b'\n', sha(RAW), 1, 'bytes changed'),
    (RAW, sha(RAW), 2, 'count changed'),
    (RAW + RAW, sha(RAW + RAW), 2, 'Repeated public'),
    (RAW.replace(b'lidraughts.org', b'example.org'), None, 1, 'public game'),
    (RAW + b'31-27', None, 1, 'after result'),
])
def test_reserved_inventory_rejects_corrupt_or_ambiguous_identity(raw, digest, count, match):
    with pytest.raises(ValueError, match=match):
        game_inventory(raw, digest or sha(raw), count)


def test_reserved_inventory_reproduces_committed_complete_four_export_handoff():
    root = Path(__file__).resolve().parents[3]
    value = build(root)
    assert value['games'] == 606
    assert {e['reserved_event_id']: len(e['games']) for e in value['events']} == {
        'fFgE7oED': 157, 'P1RUlfJc': 241, 's7ahYqL4': 147, 'D9PF2OSW': 61}
    assert value['exclusion_only']
    assert not value['independent_cohort_qualified']
    assert not value['event_labels_externally_authenticated']
    assert not value['complete_historical_fen_trajectory_registry']
    assert encoded(value) == (root / 'research/mtdp/validation/h13-reserved-source-inventory.json').read_bytes()
