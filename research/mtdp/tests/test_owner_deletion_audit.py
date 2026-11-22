"""Unequal cluster sizes, zero-stratum owners and immutable primary inputs."""
import json
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark.owner_deletion_audit import analyze, deletion_table, ratio, INPUT

ROOT = Path(__file__).resolve().parents[3]


def row(event, owner, fen, cost):
    return dict(event=event, owner=owner, fen=fen, cost=cost)


def test_whole_owner_deletion_differs_from_deleting_one_position():
    rows = [row('a', 'g', '1', 100), row('a', 'g', '2', 200), row('a', 'h', '3', 0)]
    result = deletion_table(rows, rows, ('cost',))
    dropped = result['delete_one_owner'][0]
    assert dropped['deleted_positions'] == 2
    assert dropped['positions'] == 1
    assert dropped['totals']['cost'] == 0
    assert result['full']['means']['cost'] == ratio(300, 3)


def test_zero_stratum_owner_stays_in_full_sampling_frame():
    rows = [row('a', 'g', '1', 3)]
    frame = rows + [row('a', 'h', '2', 0)]
    result = deletion_table(rows, frame, ('cost',))
    assert result['sampling_owners'] == 2
    assert result['contributing_owners'] == 1
    assert result['delete_one_owner'][1]['deleted_positions'] == 0
    assert result['delete_one_owner'][1]['means']['cost'] == ratio(3, 1)
    assert result['delete_one_owner'][0]['means']['cost'] is None


def test_same_owner_label_in_two_events_is_two_units():
    rows = [row('a', 'g', '1', 3), row('b', 'g', '2', 7)]
    result = deletion_table(rows, rows, ('cost',))
    assert result['sampling_owners'] == 2
    assert [x['totals']['cost'] for x in result['delete_one_owner']] == [7, 3]
    assert [x['totals']['cost'] for x in result['delete_one_event']] == [7, 3]


@pytest.mark.parametrize('rows,frame', [
    ([row('a', 'g', '1', 1)], [row('a', 'h', '2', 2)]),
    ([row('a', 'g', '1', 1), row('a', 'g', '1', 2)], [row('a', 'g', '1', 1)]),
    ([row('a', 'g', '1', True)], [row('a', 'g', '1', 1)]),
])
def test_invalid_frame_duplicate_target_or_noninteger_outcome_fails(rows, frame):
    with pytest.raises(ValueError):
        deletion_table(rows, frame, ('cost',))


def test_changed_archive_is_rejected(tmp_path):
    p = tmp_path / INPUT
    p.parent.mkdir(parents=True)
    p.write_text('{}')
    with pytest.raises(ValueError, match='bytes changed'):
        analyze(tmp_path)


def test_real_report_reproduces_exact_primary_totals_and_sampling_frame():
    r = analyze(ROOT)
    assert r['geometry']['full']['totals'] == {'ordinary_regret': 743, 'disjoint': 14, 'pick_optimal': 11}
    assert r['geometry']['sampling_owners'] == 31
    assert r['geometry']['contributing_owners'] == 22
    assert len(r['geometry']['delete_one_owner']) == 31
    assert r['jass_50000']['full']['totals'] == {'control_minus_native': 0, 'control_minus_lcb': 11}
    expected = ROOT / 'research/mtdp/validation/frozen-owner-deletion-2026-11-22.json'
    assert r == json.loads(expected.read_text())
