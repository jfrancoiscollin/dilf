"""Bounded Q3 native engineering smoke; no candidate, Scan or strength test."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import median
import subprocess
from time import perf_counter_ns

from research.mtdp.jass_benchmark.q3_cost_receipt import CostRecorder
from research.mtdp.jass_benchmark.metered_engine_smoke import _position_identity

PLAN_SHA = 'adfc2af7b2e1de79d34af6eead720d70665397692eba394b33620217ffc4f2b8'
PROTOCOL_COMMIT = '964039909a65530d8f489f17055e8fc55bf627ef'
JASS_COMMIT = 'cfe07fce6385b980553a898e9651d53419589ebc'
LEGAL = {'31-26','31-27','32-27','32-28','33-28','33-29','34-29','34-30','35-30'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_plan(root):
    raw=(Path(root)/'research/mtdp/validation/q3-native-binding-plan-2026-11-28.json').read_bytes()
    if sha(raw)!=PLAN_SHA:
        raise ValueError('Native binding plan changed')
    return json.loads(raw)


def parse_native(raw, fen, budget):
    lines=raw.splitlines()
    if len(lines)!=1:
        raise ValueError('Expected one native receipt')
    p=lines[0].split('\t')
    if len(p)<12 or _position_identity(p[0])!=_position_identity(fen):
        raise ValueError('Native position or trace missing')
    issued,nodes,depth,score,elapsed=map(int,(p[1],p[2],p[3],p[6],p[7]))
    legal=p[9].split(',');order=p[10].split(',')
    if issued!=budget or nodes!=budget or depth<1 or p[4]!='nodes' or elapsed<0:
        raise ValueError('Incomplete native budget or timing')
    if len(legal)!=9 or set(legal)!=LEGAL or order!=legal or p[5] not in legal:
        raise ValueError('Native legal inventory/order changed')
    first=p[11].split(':')
    if len(first)!=6 or first[0]!='1' or first[2:4]!=['1','1'] or first[5].split(',')!=legal:
        raise ValueError('Missing complete first-depth native inventory')
    return dict(fen=p[0],nodes=nodes,completed_depth=depth,best_move=p[5],
                score=score,stop=p[4],pv=p[8],legal=legal,order=order,
                attempts=p[11:],internal_search_us=elapsed)


def semantic(result):
    return {k:v for k,v in result.items() if k!='internal_search_us'}


def config(binary, fen, budget):
    env={k:v for k,v in os.environ.items() if not k.startswith(('JASS_','MTDP_'))}
    env['JASS_TRACE_ROOT']='0'
    return [str(Path(binary).resolve())],f'{fen} {budget}\n',env


def trial(binary, plan, index, arm):
    # The outer clock charges the observer's own constructor/finalize/audit.
    start=perf_counter_ns();recorder=None;cost=None;audited=None;result=None
    raw=dict(stdout='',stderr='',returncode=None);error=None;status='completed'
    try:
        if arm=='instrumented':
            recorder=CostRecorder(trial_id=str(index),position_id=plan['fen'],arm='native',node_budget=plan['node_budget'])
            with recorder.stage('setup') as stage:
                args,payload,env=config(binary,plan['fen'],plan['node_budget'])
                stage.update(nodes=0,issued_nodes=None)
            with recorder.stage('search') as stage:
                stage['issued_nodes']=plan['node_budget']
                process=subprocess.run(args,input=payload,text=True,capture_output=True,
                    timeout=plan['subprocess_timeout_seconds'],env=env,check=False)
                raw=dict(stdout=process.stdout,stderr=process.stderr,returncode=process.returncode)
                if process.returncode:
                    raise ValueError('Native process failed')
                result=parse_native(process.stdout,plan['fen'],plan['node_budget'])
                stage['nodes']=result['nodes']
        elif arm=='plain':
            args,payload,env=config(binary,plan['fen'],plan['node_budget'])
            process=subprocess.run(args,input=payload,text=True,capture_output=True,
                timeout=plan['subprocess_timeout_seconds'],env=env,check=False)
            raw=dict(stdout=process.stdout,stderr=process.stderr,returncode=process.returncode)
            if process.returncode:
                raise ValueError('Native process failed')
            result=parse_native(process.stdout,plan['fen'],plan['node_budget'])
        else:
            raise ValueError('Unknown technical arm')
    except subprocess.TimeoutExpired as exc:
        status='timeout';error=str(exc)
        def decoded(v):return v.decode(errors='replace') if isinstance(v,bytes) else (v or '')
        raw=dict(stdout=decoded(exc.stdout),stderr=decoded(exc.stderr),returncode=None)
    except (ValueError,OSError) as exc:
        status='error';error=str(exc)
    if recorder is not None:
        try:
            cost,audited=recorder.finish(status)
        except ValueError as exc:
            cost=recorder.receipt;status='error' if status=='completed' else status
            error=(error or '')+'; cost receipt rejected: '+str(exc)
    end=perf_counter_ns()
    outer=end-start
    inner=None if audited is None else audited['total_elapsed_ns']
    bounds=(result is not None and result['internal_search_us']*1000<=outer
        and (audited is None or (result['internal_search_us']*1000<=audited['phase_elapsed_ns']['search']
            and inner<=outer and audited['equal_node_comparable'])))
    return dict(index=index,arm=arm,status=status,error=error,outer_start_ns=start,outer_end_ns=end,
        total_elapsed_ns=outer,internal_search_us=None if result is None else result['internal_search_us'],
        cost_receipt=cost,cost_audit=audited,observer_outside_recorder_ns=None if inner is None else outer-inner,
        timing_bounds_pass=bool(bounds),measured_nodes=None if result is None else result['nodes'],
        semantic_search=None if result is None else semantic(result),raw=raw)


def summarize(rows, plan):
    expected=[arm for pair in plan['orders'] for arm in pair]
    if len(rows)!=len(expected) or any(r['index']!=i or r['arm']!=expected[i] for i,r in enumerate(rows)):
        raise ValueError('Incomplete or reordered native binding trials')
    successful=[r for r in rows if r['status']=='completed' and r['timing_bounds_pass']]
    same=(len(successful)==len(rows) and all(r['semantic_search']==rows[0]['semantic_search'] for r in rows))
    pairs=[]
    for i in range(0,len(rows),2):
        pair={r['arm']:r for r in rows[i:i+2]};a,b=pair['plain'],pair['instrumented']
        good=all(r['status']=='completed' and r['timing_bounds_pass'] for r in pair.values())
        pairs.append(dict(pair=i//2,valid=good,plain_ns=a['total_elapsed_ns'],instrumented_ns=b['total_elapsed_ns'],
            delta_ns=b['total_elapsed_ns']-a['total_elapsed_ns'],
            ratio=b['total_elapsed_ns']/a['total_elapsed_ns'] if a['total_elapsed_ns'] else None))
    complete=len(successful)==10 and same
    return dict(schema='mtdp-q3-native-binding-summary-v1',question='Q3',protocol_commit=PROTOCOL_COMMIT,
        plan_sha256=PLAN_SHA,total_trials=len(rows),successful_trials=len(successful),failed_trials=len(rows)-len(successful),
        total_measured_nodes=sum(r['measured_nodes'] for r in rows if r['measured_nodes'] is not None),
        unknown_node_trials=sum(r['measured_nodes'] is None for r in rows),all_search_semantics_equal=same,
        binding_passed=complete,paired_observer_costs=pairs,
        median_observer_delta_ns=median(p['delta_ns'] for p in pairs) if complete else None,
        median_observer_ratio=median(p['ratio'] for p in pairs) if complete and all(p['ratio'] is not None for p in pairs) else None,
        observer_cost_is_machine_and_schedule_specific=True,causal_overhead_established=False,
        native_process_and_tt_fresh=True,os_cache_controlled=False,warm_cache_validated=False,
        independent_quality_or_speed_gain_established=False,new_scan_scores=0,new_cohorts_reserved=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['root','jass','binary','output-dir']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();plan=load_plan(a.root)
    head=subprocess.check_output(['git','-C',str(a.jass),'rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(a.jass),'status','--porcelain'],text=True)
    if head!=JASS_COMMIT or dirty:
        raise ValueError('Native Jass checkout not clean/pinned')
    a.output_dir.mkdir(parents=True,exist_ok=False)
    provenance=dict(jass_commit=head,binary_sha256=sha(a.binary.read_bytes()),
        frozen_recipe_sha256=sha((a.root/'research/mtdp/jass_preflight/targets.cmake').read_bytes()),
        runner_source_sha256=sha((a.root/'research/mtdp/jass_benchmark/runner.cpp').read_bytes()),
        binding_source_sha256=sha(Path(__file__).read_bytes()),
        recorder_source_sha256=sha((a.root/'research/mtdp/jass_benchmark/q3_cost_receipt.py').read_bytes()))
    rows=[]
    for pair in plan['orders']:
        for arm in pair:
            row=trial(a.binary,plan,len(rows),arm);rows.append(row)
            with (a.output_dir/'trials.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
    report=summarize(rows,plan)
    for name,value in [('summary.json',report),('provenance.json',provenance)]:
        (a.output_dir/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True,indent=2))
    if not report['binding_passed']:raise SystemExit(1)


if __name__=='__main__':main()
