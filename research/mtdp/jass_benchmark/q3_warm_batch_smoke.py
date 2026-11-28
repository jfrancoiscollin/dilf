"""CPU-only synthetic cache exercise, not Jass or a strategic abstraction."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns
from research.mtdp.jass_benchmark.q3_warm_batch import WarmBatchRecorder, audit


def exercise(interrupted):
    outer_start=perf_counter_ns()
    b=WarmBatchRecorder(batch_id='synthetic-interrupted' if interrupted else 'synthetic-full-plan',
        planned_queries=[dict(query_id=str(i),node_limit=0) for i in range(3)],
        setup_node_limit=0,cache_definition_sha256=hashlib.sha256(b'toy-cache-v1-not-a-strategic-signature').hexdigest())
    with b.setup('cache_build') as s:
        s.update(nodes=0,issued_nodes=None);cache={'synthetic-key':b'x'}
    with b.query('0','hit') as q:
        with q.stage('lookup') as s:
            s.update(nodes=0,issued_nodes=None)
            assert cache['synthetic-key']==b'x'
    if interrupted:
        try:
            with b.query('1','bypass') as q:
                with q.stage('lookup') as s:
                    s.update(nodes=0,issued_nodes=None)
                    raise TimeoutError('deliberately simulated CPU-only timeout, no engine')
        except TimeoutError:pass
        b.skip('2')
    else:
        with b.query('1','miss') as q:
            with q.stage('lookup') as s:s.update(nodes=0,issued_nodes=None);assert cache.get('missing') is None
            with q.stage('fallback') as s:s.update(nodes=0,issued_nodes=None);value=b'fallback'
            q.raw['status']='fallback'
        try:
            with b.query('2','bypass') as q:
                with q.stage('lookup') as s:
                    s.update(nodes=0,issued_nodes=None)
                    raise ValueError('deliberately simulated CPU-only error, no engine')
        except ValueError:pass
    raw,checked=b.finish(cache_payload_bytes=sum(len(v) for v in cache.values()))
    outer_end=perf_counter_ns()
    return dict(outer_start_ns=outer_start,outer_end_ns=outer_end,total_elapsed_ns=outer_end-outer_start,
        primary_total_amortization=dict(numerator_ns=outer_end-outer_start,denominator_planned_queries=3),batch=raw,audit=checked)


def verify(traces):
    if type(traces) is not list or len(traces)!=2:raise ValueError('Two fixed synthetic scenarios required')
    results=[]
    for i,trace in enumerate(traces):
        raw=trace['batch'];computed=audit(raw)
        if computed!=trace['audit']:raise ValueError('Batch audit differs from retained raw costs')
        a,b=trace['outer_start_ns'],trace['outer_end_ns']
        if (type(a) is not int or type(b) is not int or not a<=raw['start_ns']<=raw['end_ns']<=b
                or trace['total_elapsed_ns']!=b-a
                or trace['primary_total_amortization']!=dict(numerator_ns=b-a,denominator_planned_queries=3)):
            raise ValueError('External observer envelope inconsistent')
        expected_statuses=(dict(completed=1,fallback=1,error=1,timeout=0,not_run=0) if i==0
                           else dict(completed=1,fallback=0,error=0,timeout=1,not_run=1))
        if (computed['status_counts']!=expected_statuses or computed['planned_queries']!=3
                or computed['total_measured_nodes']!=0 or computed['setup_amortization']['denominator_planned_queries']!=3
                or computed['total_amortization']['denominator_planned_queries']!=3
                or computed['setup_elapsed_ns']+computed['query_elapsed_ns']+computed['between_queries_and_finalization_ns']!=computed['total_elapsed_ns']):
            raise ValueError('Synthetic contract denominator, simulated failure or node accounting changed')
        results.append(dict(scenario=i,planned_queries=3,attempted_queries=computed['attempted_queries'],
            status_counts=computed['status_counts'],cache_counts=computed['cache_counts'],
            setup_amortization_denominator=3,total_amortization_denominator=3,total_measured_nodes=0,
            outer_includes_recorder_finalization=True,primary_amortization_uses_outer_envelope=True,all_cost_envelopes_reconcile=True,
            payload_bytes=computed['cache_payload_bytes'],payload_is_peak_memory=False,
            all_planned_succeeded=computed['all_planned_succeeded'],eligible_for_quality_comparison=False))
    return dict(schema='mtdp-q3-warm-batch-synthetic-contract-v1',question='Q3',scenarios=results,
        planned_slots=6,attempted_queries=5,engine_calls=0,new_scan_scores=0,new_signatures=0,
        failures_are_deliberately_simulated=True,synthetic_only=True,new_cohorts_reserved=False,
        actual_jass_warm_cache_validated=False,quality_or_compute_gain_established=False,
        next_decision='Require a separately validated Q1/Q2 candidate and its cache definition/admission packet before real warm-cache integration or a quality/cost campaign.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    traces=[exercise(False),exercise(True)];report=verify(traces)
    for name,value in [('traces.json',traces),('contract.json',report)]:
        (a.output_dir/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True,indent=2))


if __name__=='__main__':main()
