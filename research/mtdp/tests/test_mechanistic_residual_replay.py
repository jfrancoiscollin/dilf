"""A detailed trace must prove application and preserve raw evidence before interpretation."""
from pathlib import Path
from types import SimpleNamespace

import pytest
from research.mtdp.jass_benchmark import mechanistic_residual_replay as m

FEN = 'W:W31:B20'


def raw(elapsed='123'):
    fields = [FEN, '100', '100', '2', 'nodes', 'b', '7', elapsed, 'b', 'a,b', 'b,a',
              '1:1:1:1:10:b,a:a:b,a', '2:1:1:1:80:a,b:b:a,b',
              '3:1:0:0:100:b:b:b,a']
    return '\t'.join(fields) + '\n'


def test_normalization_excludes_elapsed_only_but_keeps_attempts_and_best_moves():
    a = m.parse_main(raw(), FEN, 100, ['b'], ['a', 'b'], 'a')
    assert a == m.parse_main(raw('999'), FEN, 100, ['b'], ['a', 'b'], 'a')
    assert [r['best_move'] for r in a['attempts']] == ['a', 'b', 'b']
    assert a['attempts'][1]['expected_order'][0] == 'a'
    assert a['summary']['best_move'] == 'b' and a['summary']['completed_depth'] == 2
    assert not a['attempts'][-1]['completed']


def test_requested_depth_one_intervention_requires_actual_trace_evidence():
    with pytest.raises(ValueError, match='not applied'):
        m.parse_main(raw().replace('10:b,a:a:b,a', '10:b,a:b:b,a'), FEN, 100, ['b'], ['a', 'b'], 'a')


def test_next_depth_order_must_propagate_previous_best():
    with pytest.raises(ValueError, match='propagate'):
        m.parse_main(raw().replace('80:a,b:b:a,b', '80:b,a:b:b,a'), FEN, 100, ['b'], ['a', 'b'], 'a')


@pytest.mark.parametrize('old,new', [('100\t100\t2', '100\t101\t2'),
                                    ('80:a,b:b:a,b', '110:a,b:b:a,b'),
                                    ('1:1:1:1:10', '1:1:0:1:10'),
                                    ('123', '-1')])
def test_unmetered_incomplete_or_malformed_trace_is_not_silently_accepted(old, new):
    with pytest.raises(ValueError):
        m.parse_main(raw().replace(old, new), FEN, 100, ['b'], ['a', 'b'], 'a')


def test_fresh_environment_rejects_inherited_intervention_and_tablebases(monkeypatch):
    for k in ('MTDP_DEPTH_ONE_WINNER', 'JASS_EGDB_PATH', 'JASS_EGDB_MTC_PATH'):
        monkeypatch.setenv(k, 'unrelated')
    env = m.clean_env()
    assert all(k not in env for k in ('MTDP_DEPTH_ONE_WINNER', 'JASS_EGDB_PATH', 'JASS_EGDB_MTC_PATH'))
    assert m.clean_env('a')['MTDP_DEPTH_ONE_WINNER'] == 'a'


def test_failed_engine_stdout_stderr_and_payload_are_retained(monkeypatch, tmp_path):
    monkeypatch.setattr(m.subprocess, 'run', lambda *a, **kw:
                        SimpleNamespace(returncode=7, stdout='partial evidence', stderr='failed engine'))
    recorder = m.Recorder(tmp_path)
    with pytest.raises(RuntimeError, match='retained'):
        recorder.run(Path('/fake'), [], 'input\n', phase='probe', limit=10, prefix=['a'])
    import json
    saved = json.loads((tmp_path / '000.json').read_bytes())
    assert saved['stdout'] == 'partial evidence' and saved['stderr'] == 'failed engine'
    assert saved['returncode'] == 7 and saved['stdin'] == 'input\n'


def test_publication_gate_precedes_any_output_or_binary(monkeypatch, tmp_path):
    def blocked(*args):
        raise ValueError('unpublished collector')
    monkeypatch.setattr(m, 'published', blocked)
    monkeypatch.setattr(m, 'restore_binaries', lambda *a: pytest.fail('binary access before gate'))
    with pytest.raises(ValueError, match='unpublished'):
        m.run(tmp_path, 'x', tmp_path / 'out', tmp_path / 'bin')
    assert list(tmp_path.iterdir()) == []
