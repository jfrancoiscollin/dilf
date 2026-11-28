"""Receipt counts across budgets are not independent positions or causal effects."""
import pytest
from research.mtdp.jass_benchmark import two_arena_telemetry_audit as a


@pytest.fixture
def specimen():
    target = {'target_fen': 't', 'target_games': ['g'], 'legal_moves': [{'jass_key': 'a'}, {'jass_key': 'b'}]}
    main = {'best_move': 'b', 'nodes': 86, 'depth_ceiling': False,
            'completed_depth': 5, 'score': 7, 'stop': 'nodes'}
    row = {'event': 'e', 'fen': 't', 'games': ['g'], 'budget': 100, 'LCB_prefix': ['b'],
           'native_legal_actions': 2, 'preliminary_nodes': 3, 'verification_nodes': 8,
           'verification_receipts': [{'phase': 'preliminary', 'issued_limit': 10, 'nodes': 3},
                                     {'phase': 'probe', 'move': 'a', 'issued_limit': 7, 'nodes': 2},
                                     {'phase': 'probe', 'move': 'b', 'issued_limit': 5, 'nodes': 3}],
           'main_limit': 92, 'main_nodes': 92, 'control_main': {**main, 'nodes': 92},
           'native_baseline': {**main, 'nodes': 100, 'completed_depth': 6, 'score': 2},
           'lcb_baseline': {**main, 'nodes': 100}, 'paired_comparable': True, 'complete_budget': True,
           'decision_reason': 'verified_tie', 'intervention': 'a'}
    return row, target


def test_same_move_does_not_suppress_depth_or_score_differences(specimen):
    row, target = specimen
    r = a.audit_row(row, target, 100, ['b'], 'e/100/00000.json', 'g')
    assert r['control_native_same_move']
    assert r['control_native_depth_delta'] == -1 and r['control_native_score_delta'] == 5
    assert r['preliminary_nodes'] + r['probe_nodes'] == r['verification_nodes'] == 8
    assert r['control_main_nodes'] + r['verification_nodes'] == r['budget']
    assert not r['full_verification_evidence_retained'] and not r['main_attempt_trace_retained']


def test_repeating_a_position_at_three_budgets_does_not_triple_unique_count(specimen):
    row, target = specimen
    r = a.audit_row(row, target, 100, ['b'], 'case', 'g')
    s = a.summarize([r, {**r, 'budget': 200}, {**r, 'budget': 400}])
    assert s['reported_intervention_receipts'] == 3
    assert s['reported_intervention_unique_positions'] == s['unique_positions'] == 1
    assert s['verification_nodes_sum'] == 24 and s['verification_fraction_of_control_total'] == 24 / 700


@pytest.mark.parametrize('field,change', [
    ('preliminary_nodes', 4), ('intervention', None), ('decision_reason', 'verified_unique_best')])
def test_reported_reason_and_node_evidence_cannot_be_silently_inconsistent(specimen, field, change):
    row, target = specimen
    row[field] = change
    with pytest.raises(ValueError):
        a.audit_row(row, target, 100, ['b'], 'case', 'g')


def test_duplicate_probe_is_rejected_even_when_total_node_accounting_matches(specimen):
    row, target = specimen
    row['verification_receipts'][2]['move'] = 'a'
    with pytest.raises(ValueError, match='Repeated'):
        a.audit_row(row, target, 100, ['b'], 'case', 'g')


def test_missing_phase_cannot_be_relabelled_as_a_verified_decision(specimen):
    row, target = specimen
    row['verification_receipts'][0]['phase'] = 'probe'
    with pytest.raises(ValueError, match='phase sequence'):
        a.audit_row(row, target, 100, ['b'], 'case', 'g')


def test_changed_frozen_bytes_are_rejected_before_analysis(monkeypatch, tmp_path):
    (tmp_path / 'data.json').write_bytes(b'{}')
    monkeypatch.setattr(a.runtime, '_blob', lambda *args: b'{"different":1}')
    with pytest.raises(ValueError, match='Frozen receipt bytes changed'):
        a.pinned(tmp_path, 'published', 'data.json')
