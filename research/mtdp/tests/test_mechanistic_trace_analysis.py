"""Raw receipts must independently support the normalized mechanistic result."""
import io
import json
import tarfile
from pathlib import Path

import pytest
from research.mtdp.jass_benchmark import mechanistic_trace_analysis as a


def main_with_best(values):
    return {'attempts': [{'depth': d, 'best_move': best, 'completed': completed}
                         for d, best, completed in values]}


def test_temporary_agreement_is_not_labelled_stable_through_later_depths():
    left = main_with_best([(1, 'a', True), (2, 'x', True), (3, 'a', True)])
    right = main_with_best([(1, 'b', True), (2, 'x', True), (3, 'b', True)])
    assert a.convergence(left, right)['first_stable_same_best_within_common_horizon'] is None


def test_convergence_is_limited_to_shared_completed_horizon():
    left = main_with_best([(1, 'a', True), (2, 'x', True), (3, 'x', True), (4, 'z', False)])
    right = main_with_best([(1, 'b', True), (2, 'x', True), (3, 'x', True), (4, 'y', True)])
    result = a.convergence(left, right)
    assert result['common_completed_depth'] == 3
    assert result['first_stable_same_best_within_common_horizon'] == 2


def test_raw_archive_rejects_unexpected_path_without_extracting_it(tmp_path):
    path = tmp_path / 'bad.tar.gz'
    with tarfile.open(path, 'w:gz') as archive:
        info = tarfile.TarInfo('../outside.json')
        info.size = 2
        archive.addfile(info, io.BytesIO(b'{}'))
    with pytest.raises(ValueError):
        a.read_archive(path)
    assert not (tmp_path.parent / 'outside.json').exists()


def real_inputs():
    root = Path(__file__).resolve().parents[3]
    files = a.read_archive(root / (a.BASE + 'mechanistic-residual-raw-seed7.tar.gz'))
    plan = json.loads((root / (a.BASE + 'two-named-arenas-mechanistic-residual-plan.json')).read_bytes())
    return root, files, plan


def test_changed_raw_main_score_invalidates_normalized_receipt():
    root, files, plan = real_inputs()
    raw_name = next(n for n in sorted(files) if n.startswith('raw/')
                    and json.loads(files[n])['phase'] == 'control')
    raw = json.loads(files[raw_name])
    v = raw['stdout'].split('\t')
    v[6] = str(int(v[6]) + 1)
    raw['stdout'] = '\t'.join(v)
    files[raw_name] = json.dumps(raw).encode()
    with pytest.raises(AssertionError):
        a.validate(root, files, plan)


def test_omitting_one_raw_receipt_cannot_leave_an_accepted_complete_run():
    root, files, plan = real_inputs()
    files.pop('raw/00/000.json')
    with pytest.raises((AssertionError, KeyError)):
        a.validate(root, files, plan)
