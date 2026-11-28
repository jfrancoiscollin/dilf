import copy,json
from pathlib import Path
from datetime import timedelta
import pytest
from research.mtdp.jass_benchmark import two_arena_registration as gate

ROOT=Path(__file__).resolve().parents[3]


def record():return json.loads((ROOT/gate.REGISTRATION).read_bytes())


def test_pinned_registration_and_method_load():
    assert tuple(x['event']['id'] for x in gate.load(ROOT)['events'])==gate.EVENTS


@pytest.mark.parametrize('mutation',['count','id','format','start','countdown','observed_late','depth','budgets','seed'])
def test_retrospective_or_changed_design_is_refused(mutation):
    r=record();e=r['events'][0]
    if mutation=='count':r['events'].pop()
    elif mutation=='id':e['event']['id']='other'
    elif mutation=='format':e['event']['clock']['limit']=180
    elif mutation=='start':e['event']['startsAt']='2026-11-18T22:00:00Z'
    elif mutation=='countdown':e['prestart_facts']['secondsToStart']=0
    elif mutation=='observed_late':e['receipt']['retrieved_at_utc']='2026-11-19T00:00:00Z'
    elif mutation=='depth':r['analysis']['source_ranking_scan_successor_depth']=16
    elif mutation=='budgets':r['analysis']['total_node_budgets']=[50000]
    else:r['analysis']['bootstrap_seed']=1
    with pytest.raises(ValueError):gate.validate(r)


def final_records(r):return {e['event']['id']:{**e['event'],'isFinished':True,'secondsToStart':0} for e in r['events']}


def test_joint_finish_not_first_finish_controls_gate():
    r=record()
    with pytest.raises(ValueError,match='closed'):gate.final_gate(r,{},gate.utc('2026-11-19T00:01:00Z'))
    assert gate.final_gate(r,final_records(r),gate.FINAL_GATE)['all_final_metadata_valid']


@pytest.mark.parametrize('mutation',['unfinished','missing','variant','start'])
def test_both_final_events_must_match(mutation):
    r=record();m=final_records(r);e=m[gate.EVENTS[1]]
    if mutation=='unfinished':e['isFinished']=False
    elif mutation=='missing':m.pop(gate.EVENTS[1])
    elif mutation=='variant':e['variant']='brazilian'
    else:e['startsAt']='2026-11-19T03:00:00Z'
    with pytest.raises(ValueError):gate.final_gate(r,m,gate.FINAL_GATE+timedelta(minutes=1))


def test_mutable_commit_or_late_prestart_proof_fails_without_fetch(monkeypatch):
    monkeypatch.setattr(gate.subprocess,'run',lambda *a,**k:pytest.fail('premature fetch'))
    with pytest.raises(ValueError,match='exact'):gate.verify_before_start(ROOT,'HEAD')
    monkeypatch.setattr(gate,'_now',lambda:gate.utc(gate.STARTS[0]))
    with pytest.raises(ValueError,match='closed'):gate.verify_before_start(ROOT,'a'*40)


def test_protocol_byte_change_is_refused(tmp_path):
    for name in (gate.REGISTRATION,gate.PROTOCOL):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    (tmp_path/gate.PROTOCOL).write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):gate.load(tmp_path)
