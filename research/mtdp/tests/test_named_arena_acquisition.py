"""Simulated HTTP only; never requests the prospective arena."""
import io
import json
from datetime import datetime, timezone
from http.client import IncompleteRead
from pathlib import Path
import pytest
from research.mtdp.jass_benchmark import named_arena_acquisition as gate
from research.mtdp.jass_benchmark.named_arena_inputs import EVENT, registration
ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 11, 18, 21, tzinfo=timezone.utc)
PDN = b'[Event "SYNTHETIC fixture"]\n[Site "https://lidraughts.org/SYNTH001"]\n*\n'

class Response(io.BytesIO):
    def getcode(self): return 200

def install(monkeypatch, payloads, finished=True):
    metadata = {**registration(ROOT)['event'], 'isFinished': finished, 'secondsToStart': 0, 'quote': 'omitted fixture prose'}
    sequence, calls = iter(payloads), []
    def open_fixture(request, timeout):
        calls.append(request.full_url)
        assert request.headers['Cache-control'] == 'no-cache'
        if not request.full_url.endswith('/games'):
            return Response(json.dumps(metadata).encode())
        data = next(sequence)
        if isinstance(data, Exception): raise data
        return Response(data)
    monkeypatch.setattr(gate, '_now', lambda: NOW)
    monkeypatch.setattr(gate, 'urlopen', open_fixture)
    monkeypatch.setattr(gate.time, 'sleep', lambda _: None)
    return calls

def test_prefinish_refusal_precedes_network_and_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, '_now', lambda: NOW.replace(hour=20, minute=56))
    monkeypatch.setattr(gate, 'urlopen', lambda *a, **k: pytest.fail('premature HTTP'))
    with pytest.raises(ValueError, match='scheduled finish'): gate.acquire(ROOT, tmp_path / 'run')
    assert not (tmp_path / 'run').exists()

def test_separate_gets_receipts_and_fact_projection(monkeypatch, tmp_path):
    calls = install(monkeypatch, [PDN, PDN]); out = tmp_path / 'run'
    result = gate.acquire(ROOT, out)
    log = json.loads((out / 'final-downloads.json').read_bytes())
    assert len(calls) == 3 and calls[1] == calls[2]
    assert log['candidate']['first']['request_id'] != log['candidate']['independent_repeat']['request_id']
    assert result['scientific_freeze'] is False
    assert 'quote' not in json.loads((out / 'final-metadata.json').read_bytes())
    assert log['metadata']['sha256'] != log['metadata']['projection_sha256']

def test_unfinished_event_never_downloads_games(monkeypatch, tmp_path):
    calls = install(monkeypatch, [], False)
    with pytest.raises(ValueError, match='not confirmed finished'): gate.acquire(ROOT, tmp_path / 'run')
    assert len(calls) == 1

def test_different_pair_is_preserved_and_retried(monkeypatch, tmp_path):
    changed = PDN.replace(b'fixture', b'changed fixture')
    calls = install(monkeypatch, [PDN, changed, PDN, PDN]); out = tmp_path / 'run'
    assert gate.acquire(ROOT, out)['matching_pair'] == 2 and len(calls) == 5
    assert (out / 'attempt-01/repeat.pdn').read_bytes() == changed
    assert json.loads((out / 'attempt-01/downloads.json').read_bytes())['matching'] is False

@pytest.mark.parametrize('failure', [OSError('fixture transient'), IncompleteRead(b'short', 100)])
def test_transport_failure_retried_and_recorded(monkeypatch, tmp_path, failure):
    calls = install(monkeypatch, [failure, PDN, PDN]); out = tmp_path / 'run'
    gate.acquire(ROOT, out)
    attempts = json.loads((out / 'final-downloads.json').read_bytes())['candidate']['first']['attempts']
    assert len(calls) == 4 and len(attempts) == 2 and attempts[0]['error'] == type(failure).__name__

def test_exhausted_retries_never_create_final_exports(monkeypatch, tmp_path):
    install(monkeypatch, [OSError('fixture')] * 4); out = tmp_path / 'run'
    with pytest.raises(gate.AcquisitionError): gate.acquire(ROOT, out)
    result = json.loads((out / 'acquisition.json').read_bytes())
    assert result['scientific_freeze'] is False and len(result['failed_request_attempts']) == 4
    assert not (out / f'mtdp-lidraughts-{EVENT}.pdn').exists()

def test_existing_output_never_overwritten(monkeypatch, tmp_path):
    calls = install(monkeypatch, []); out = tmp_path / 'run'; out.mkdir()
    (out / 'keep').write_bytes(b'original')
    with pytest.raises(FileExistsError): gate.acquire(ROOT, out)
    assert calls == [] and (out / 'keep').read_bytes() == b'original'
