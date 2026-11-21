"""In-memory HTTP/future-clock engineering fixtures only."""
import json
from pathlib import Path
import pytest
from research.mtdp.jass_benchmark import two_arena_acquisition as a

ROOT=Path(__file__).resolve().parents[3]
NOW=a.study.utc('2026-11-19T03:00:00Z')


@pytest.fixture
def transport(monkeypatch):
    calls=[];record=a.study.load(ROOT)
    monkeypatch.setattr(a.study,'_now',lambda:NOW)
    monkeypatch.setattr(a.time,'sleep',lambda *x:None)
    metadata={e['event']['id']:{**e['event'],'isFinished':True,'secondsToStart':0} for e in record['events']}
    def fetch(url,metadata=False):
        calls.append(url)
        event=url.split('/')[-1] if metadata else url.split('/')[-2]
        raw=a._bytes(transport_metadata[event]) if metadata else b'[Event "Synthetic input test"]\n[Synthetic "true"]\n*\n'
        return raw,{'url':url,'request_id':str(len(calls)),'requested_at_utc':NOW.isoformat(),
                    'retrieved_at_utc':NOW.isoformat(),'sha256':a.digest(raw),'bytes':len(raw)}
    transport_metadata=metadata
    monkeypatch.setattr(a,'_fetch',fetch)
    return calls,metadata,fetch


def test_real_clock_blocks_before_network_or_directory(monkeypatch,tmp_path):
    monkeypatch.setattr(a.study,'_now',lambda:a.study.utc('2026-11-19T00:00:00Z'))
    monkeypatch.setattr(a,'_fetch',lambda *x,**y:pytest.fail('premature HTTP'))
    with pytest.raises(ValueError,match='closed'):a.acquire(ROOT,tmp_path/'out')
    assert not (tmp_path/'out').exists()
    with pytest.raises(ValueError,match='closed'):a.check(ROOT,tmp_path/'absent')


def test_both_metadata_then_four_distinct_final_gets(tmp_path,transport):
    calls,metadata,fetch=transport
    r=a.acquire(ROOT,tmp_path/'out')
    assert len(calls)==6 and all('/games' not in x for x in calls[:2])
    assert list(r['events'])==list(a.study.EVENTS) and r['scientific_freeze'] is False
    assert r==a.check(ROOT,tmp_path/'out')


def test_second_unfinished_means_no_game_requests(tmp_path,transport):
    calls,metadata,fetch=transport;metadata[a.study.EVENTS[1]]['isFinished']=False
    with pytest.raises(ValueError,match='unfinished'):a.acquire(ROOT,tmp_path/'out')
    assert len(calls)==2 and not any('/games' in x for x in calls)
    assert (tmp_path/'out/acquisition.json').exists()


def test_divergent_pair_is_kept_and_retried(monkeypatch,tmp_path,transport):
    calls,metadata,fetch=transport
    def divergent(url,**kwargs):
        raw,r=fetch(url,**kwargs)
        if len(calls)==4:raw+=b' ';r.update(sha256=a.digest(raw),bytes=len(raw))
        return raw,r
    monkeypatch.setattr(a,'_fetch',divergent)
    a.acquire(ROOT,tmp_path/'out');d=tmp_path/'out'/a.study.EVENTS[0]
    assert (d/'attempt-01/first.pdn').read_bytes()!=(d/'attempt-01/repeat.pdn').read_bytes()
    assert (d/'attempt-02/downloads.json').exists()


def test_repeat_failure_preserves_first_bytes_and_receipt(monkeypatch,tmp_path,transport):
    calls,metadata,fetch=transport
    def failed(url,**kwargs):
        if len(calls)==3:raise OSError('repeat transport failed')
        return fetch(url,**kwargs)
    monkeypatch.setattr(a,'_fetch',failed)
    with pytest.raises(OSError,match='repeat'):a.acquire(ROOT,tmp_path/'out')
    d=tmp_path/'out'/a.study.EVENTS[0]/'attempt-01'
    assert (d/'first.pdn').exists() and (d/'first-download.json').exists()


@pytest.mark.parametrize('tamper',['bytes','request_id'])
def test_changed_export_or_reused_identity_is_refused(tmp_path,transport,tamper):
    a.acquire(ROOT,tmp_path/'out');d=tmp_path/'out'/a.study.EVENTS[1]
    if tamper=='bytes':(d/'repeat.pdn').write_bytes(b'changed')
    else:
        p=d/'downloads.json';r=json.loads(p.read_bytes());r['independent_repeat']['request_id']=r['first']['request_id'];p.write_bytes(a._bytes(r))
    with pytest.raises(ValueError):a.check(ROOT,tmp_path/'out')


def test_existing_output_never_overwritten(tmp_path,transport):
    d=tmp_path/'out';d.mkdir();(d/'prior').write_bytes(b'keep')
    with pytest.raises(FileExistsError):a.acquire(ROOT,d)
    assert not transport[0] and (d/'prior').read_bytes()==b'keep'
