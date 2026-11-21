"""A non-intervened witness must retain its complete fixed frame and raw evidence."""
import json
from pathlib import Path

import pytest
from research.mtdp.jass_benchmark import budget_witness_analysis as a


def inputs():
    root = Path(__file__).resolve().parents[3]
    files = a.read_archive(root / (a.BASE + 'nonintervened-budget-raw-seed7.tar.gz'))
    plan = json.loads((root / (a.BASE + 'nonintervened-budget-witness-plan.json')).read_bytes())
    return root, files, plan


def test_an_injected_force_cannot_be_relabelled_as_a_nonintervened_witness():
    root, files, plan = inputs()
    name = next(n for n in sorted(files) if n.startswith('raw/') and json.loads(files[n])['phase'] == 'control')
    raw = json.loads(files[name])
    raw['forced'] = '20-24'
    files[name] = json.dumps(raw).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_dropping_zero_difference_budgets_remains_invalid_after_rehashing():
    root, files, plan = inputs()
    norm = json.loads(files['normalized.json'])
    norm['rows'] = norm['rows'][:1]
    files['normalized.json'] = json.dumps(norm).encode()
    status = json.loads(files['status.json'])
    status['normalized_sha256'] = a.sha(files['normalized.json'])
    files['status.json'] = json.dumps(status).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_a_missing_raw_probe_cannot_leave_a_valid_complete_run():
    root, files, plan = inputs()
    files.pop('raw/00/000.json')
    with pytest.raises((AssertionError, KeyError)):
        a.validate(root, files, plan)


def test_raw_input_must_match_the_recorded_position_and_limit():
    root, files, plan = inputs()
    raw = json.loads(files['raw/00/000.json'])
    raw['stdin'] = raw['stdin'].replace('1000', '999')
    files['raw/00/000.json'] = json.dumps(raw).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)
