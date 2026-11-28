"""The complete original frame and every raw engine receipt must remain auditable."""
import json
from pathlib import Path

import pytest
from research.mtdp.jass_benchmark import full_frozen_residual_analysis as a


def inputs():
    root = Path(__file__).resolve().parents[3]
    files = a.read_archive(root / (a.BASE + 'full-frozen-residual-raw-seed7.tar.gz'))
    plan = json.loads((root / (a.BASE + 'full-frozen-residual-control-plan.json')).read_bytes())
    return root, files, plan


def test_intervention_only_subset_cannot_be_presented_as_the_complete_frame():
    root, files, plan = inputs()
    norm = json.loads(files['normalized.json'])
    norm['rows'] = [r for r in norm['rows'] if r['case']['reported_intervention'] is not None]
    files['normalized.json'] = json.dumps(norm).encode()
    status = json.loads(files['status.json'])
    status['normalized_sha256'] = a.sha(files['normalized.json'])
    files['status.json'] = json.dumps(status).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_changed_raw_score_is_rejected_even_if_node_sums_still_match():
    root, files, plan = inputs()
    name = next(n for n in sorted(files) if n.startswith('raw/') and json.loads(files[n])['phase'] == 'control')
    raw = json.loads(files[name])
    v = raw['stdout'].split('\t')
    v[6] = str(int(v[6]) + 1)
    raw['stdout'] = '\t'.join(v)
    files[name] = json.dumps(raw).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_no_raw_probe_can_be_omitted_from_a_complete_run():
    root, files, plan = inputs()
    files.pop('raw/000/000.json')
    with pytest.raises((AssertionError, KeyError)):
        a.validate(root, files, plan)


def test_owner_relabelling_cannot_change_the_frozen_sampling_frame():
    root, files, plan = inputs()
    plan['cases'][0]['owner'] = 'another-game'
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_extra_raw_case_cannot_be_hidden_outside_the_fixed_inventory():
    root, files, plan = inputs()
    files['raw/114/000.json'] = files['raw/000/000.json']
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)
