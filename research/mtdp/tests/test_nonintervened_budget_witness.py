"""The cost witness is a separate fixed mask, never a widened intervention experiment."""
import pytest
from research.mtdp.jass_benchmark import nonintervened_budget_witness as w


def fixture():
    rows = [{'path': str(b), 'event': 'e', 'fen': 'f', 'owner': 'g', 'budget': b,
             'verification_nodes': 3, 'reported_intervention': None,
             'control_native_depth_delta': -1 if b == 10000 else 0} for b in (10000, 50000, 200000)]
    cases = [{k: r[k] for k in ('path', 'event', 'fen', 'owner', 'budget',
                               'verification_nodes', 'reported_intervention')} for r in rows]
    return {'cases': cases, 'target_reference_access_allowed': False,
            'original_nine_case_plan_may_be_expanded': False}, {'rows': rows}


def test_all_three_budgets_are_kept_even_if_only_one_loses_depth():
    plan, report = fixture()
    assert w.validate_plan(plan, report) is None
    assert len(plan['cases']) == 3


@pytest.mark.parametrize('fault', ('drop_zero', 'extra_position', 'intervention', 'target'))
def test_mask_and_no_target_gate_fail_closed(fault):
    plan, report = fixture()
    if fault == 'drop_zero':
        plan['cases'] = plan['cases'][:1]
    elif fault == 'extra_position':
        report['rows'].append({**report['rows'][0], 'fen': 'another'})
    elif fault == 'intervention':
        report['rows'][0]['reported_intervention'] = 'forced'
    else:
        plan['target_reference_access_allowed'] = True
    with pytest.raises(ValueError):
        w.validate_plan(plan, report)


def test_publication_gate_precedes_output_and_binary_access(monkeypatch, tmp_path):
    def blocked(*args):
        raise ValueError('unpublished witness')
    monkeypatch.setattr(w, 'published', blocked)
    monkeypatch.setattr(w.shared, 'restore_binaries', lambda *args: pytest.fail('binary before gate'))
    with pytest.raises(ValueError, match='unpublished'):
        w.run(tmp_path, 'x', tmp_path / 'out', tmp_path / 'bin')
    assert list(tmp_path.iterdir()) == []
