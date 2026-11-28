"""An exhaustive frame must not be selected on interventions or observed depth losses."""
import json
from pathlib import Path

import pytest
from research.mtdp.jass_benchmark import full_frozen_residual_replay as f


def inputs():
    root = Path(__file__).resolve().parents[3]
    plan = json.loads((root / f.PLAN).read_bytes())
    report = json.loads((root / (f.shared.audit.BASE + 'two-named-arenas-telemetry-audit.json')).read_bytes())
    return plan, report


def test_the_whole_frozen_frame_is_retained_including_zero_effect_cases():
    plan, report = inputs()
    assert f.validate_plan(plan, report) is None
    assert len(plan['cases']) == 114
    assert sum(r['reported_intervention'] is None for r in plan['cases']) == 105


@pytest.mark.parametrize('fault', ('only_interventions', 'drop_budget', 'duplicate', 'owner', 'target'))
def test_filtered_or_relabelled_frames_are_rejected(fault):
    plan, report = inputs()
    if fault == 'only_interventions':
        plan['cases'] = [r for r in plan['cases'] if r['reported_intervention'] is not None]
    elif fault == 'drop_budget':
        plan['cases'] = [r for r in plan['cases'] if r['budget'] != 10000]
    elif fault == 'duplicate':
        plan['cases'][-1] = plan['cases'][0]
    elif fault == 'owner':
        plan['cases'][0]['owner'] = 'other'
    else:
        plan['target_reference_access_allowed'] = True
    with pytest.raises(ValueError):
        f.validate_plan(plan, report)


def test_publication_gate_precedes_output_and_binary_access(monkeypatch, tmp_path):
    def blocked(*args):
        raise ValueError('unpublished exhaustive collector')
    monkeypatch.setattr(f, 'published', blocked)
    monkeypatch.setattr(f.shared, 'restore_binaries', lambda *a: pytest.fail('binary before gate'))
    with pytest.raises(ValueError, match='unpublished'):
        f.run(tmp_path, 'x', tmp_path / 'out', tmp_path / 'bin')
    assert list(tmp_path.iterdir()) == []
