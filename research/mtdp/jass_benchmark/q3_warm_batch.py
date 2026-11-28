"""Representation-cache batch accounting, not TT reuse or a speed experiment.

Setup is charged once to the fixed planned denominator, including failures and
not-run slots. Unknown nodes remain unknown; payload bytes are not process RSS.
"""
from contextlib import contextmanager
import re
from time import perf_counter_ns
from research.mtdp.jass_benchmark.q3_cost_receipt import integer

SCHEMA='mtdp-q3-warm-representation-batch-v1'
SETUP_PHASES=('cache_build','cache_load')
QUERY_PHASES=('setup','signature','lookup','verification','fallback','search')
STATUSES=('completed','fallback','error','timeout','not_run')
CACHE_RESULTS=('hit','miss','bypass','not_run')


def stages(rows, start, end, phases, failed):
    if type(rows) is not list:
        raise ValueError('Stages must be a list')
    previous=start;duration=known=unknown=overruns=0
    for row in rows:
        if type(row) is not dict or set(row)!={'phase','start_ns','end_ns','nodes','issued_nodes'} or row['phase'] not in phases:
            raise ValueError('Unexpected batch stage')
        a=integer(row['start_ns'],'stage start');b=integer(row['end_ns'],'stage end')
        if a<previous or b<a or b>end:
            raise ValueError('Overlapping or out-of-envelope batch stage')
        previous=b;duration+=b-a;nodes=row['nodes'];issued=row['issued_nodes']
        if issued is not None:integer(issued,'issued engine cap',1)
        if nodes is None:
            if not failed:raise ValueError('Successful work has unknown engine nodes')
            unknown+=1
        else:
            integer(nodes,'measured engine nodes')
            if nodes and issued is None:raise ValueError('Uncapped engine stage')
            known+=nodes;overruns+=issued is not None and nodes>issued
    return dict(stage_elapsed_ns=duration,known_nodes=known,unknown_node_stages=unknown,issued_cap_overruns=overruns)


def audit(batch):
    if type(batch) is not dict or set(batch)!={
        'schema','batch_id','cache_kind','cache_definition_sha256','tt_reused','os_cache_controlled',
        'planned_queries','setup_node_limit','batch_node_limit','setup_status','setup_stages',
        'queries','start_ns','end_ns','cache_payload_bytes'}:
        raise ValueError('Unexpected warm-batch fields')
    if (batch['schema']!=SCHEMA or batch['cache_kind']!='representation'
            or batch['tt_reused'] is not False or batch['os_cache_controlled'] is not False):
        raise ValueError('Warm representation cache cannot certify TT/OS reuse')
    if (type(batch['batch_id']) is not str or not batch['batch_id']
            or type(batch['cache_definition_sha256']) is not str
            or re.fullmatch('[0-9a-f]{64}',batch['cache_definition_sha256']) is None):
        raise ValueError('Missing batch/cache identity')
    plan=batch['planned_queries']
    if type(plan) is not list or not plan:raise ValueError('Nonempty fixed query plan required')
    keys=[];limits=[]
    for p in plan:
        if type(p) is not dict or set(p)!={'query_id','node_limit'} or type(p['query_id']) is not str or not p['query_id']:
            raise ValueError('Invalid planned query')
        keys.append(p['query_id']);limits.append(integer(p['node_limit'],'query node allocation'))
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate planned query')
    setup_limit=integer(batch['setup_node_limit'],'setup allocation')
    total_limit=integer(batch['batch_node_limit'],'batch allocation')
    if total_limit!=setup_limit+sum(limits):raise ValueError('Setup allocation missing from fixed batch budget')
    queries=batch['queries']
    if type(queries) is not list or any(type(q) is not dict for q in queries) or [q.get('query_id') for q in queries]!=keys:
        raise ValueError('All planned slots required in fixed order, including not-run')
    start=integer(batch['start_ns'],'batch start');end=integer(batch['end_ns'],'batch end')
    if end<start:raise ValueError('Batch clock reversed')
    if batch['setup_status'] not in ('completed','error','timeout') or not batch['setup_stages']:
        raise ValueError('Warm construction/load receipt required')
    first=integer(queries[0]['start_ns'],'first query start')
    if not start<=first<=end:raise ValueError('Query outside batch')
    setup=stages(batch['setup_stages'],start,first,SETUP_PHASES,batch['setup_status']!='completed')
    previous=first;query_ns=known=unknown=overruns=0;within_queries=True
    statuses=dict.fromkeys(STATUSES,0);cache=dict.fromkeys(CACHE_RESULTS,0)
    for q,limit in zip(queries,limits,strict=True):
        if set(q)!={'query_id','cache_result','status','start_ns','end_ns','stages'}:
            raise ValueError('Unexpected query receipt fields')
        a=integer(q['start_ns'],'query start');b=integer(q['end_ns'],'query end')
        status=q['status'];hit=q['cache_result']
        if a<previous or b<a or b>end or status not in STATUSES or hit not in CACHE_RESULTS:
            raise ValueError('Invalid query clocks/status/cache outcome')
        if (status=='not_run')!=(hit=='not_run') or (status=='not_run' and (a!=b or q['stages'])):
            raise ValueError('Not-run slots cannot contain executed work')
        if status in ('completed','fallback') and not q['stages']:
            raise ValueError('Completed query needs measured stages')
        cost=stages(q['stages'],a,b,QUERY_PHASES,status in ('error','timeout'))
        previous=b;query_ns+=b-a;known+=cost['known_nodes'];unknown+=cost['unknown_node_stages'];overruns+=cost['issued_cap_overruns']
        within_queries=within_queries and cost['unknown_node_stages']==0 and cost['known_nodes']<=limit and cost['issued_cap_overruns']==0
        statuses[status]+=1;cache[hit]+=1
    if batch['cache_payload_bytes'] is not None:integer(batch['cache_payload_bytes'],'cache payload bytes')
    n=len(plan);setup_ns=first-start;total_ns=end-start
    all_unknown=unknown+setup['unknown_node_stages'];all_known=known+setup['known_nodes']
    return dict(schema='mtdp-q3-warm-batch-audit-v1',planned_queries=n,attempted_queries=n-statuses['not_run'],
        status_counts=statuses,cache_counts=cache,setup_elapsed_ns=setup_ns,
        setup_stage_elapsed_ns=setup['stage_elapsed_ns'],setup_orchestration_elapsed_ns=setup_ns-setup['stage_elapsed_ns'],
        query_elapsed_ns=query_ns,between_queries_and_finalization_ns=total_ns-setup_ns-query_ns,
        total_elapsed_ns=total_ns,setup_amortization=dict(numerator_ns=setup_ns,denominator_planned_queries=n),
        total_amortization=dict(numerator_ns=total_ns,denominator_planned_queries=n),
        known_measured_nodes=all_known,unknown_node_stages=all_unknown,
        total_measured_nodes=None if all_unknown else all_known,
        setup_measured_nodes=None if setup['unknown_node_stages'] else setup['known_nodes'],
        issued_cap_overruns=overruns+setup['issued_cap_overruns'],
        within_setup_node_limit=setup['unknown_node_stages']==0 and setup['known_nodes']<=setup_limit and setup['issued_cap_overruns']==0,
        within_query_node_limits=bool(within_queries),
        within_batch_node_limit=all_unknown==0 and all_known<=total_limit and overruns+setup['issued_cap_overruns']==0,
        all_planned_succeeded=batch['setup_status']=='completed' and statuses['error']==statuses['timeout']==statuses['not_run']==0,
        cache_payload_bytes=batch['cache_payload_bytes'],payload_is_peak_process_memory=False,
        includes_recorder_construction_and_audit=False,
        fixed_quality_or_speed_gain_established=False,execution_authenticity_proven=False)


class WarmBatchRecorder:
    def __init__(self, *, batch_id, planned_queries, setup_node_limit, cache_definition_sha256, clock=perf_counter_ns):
        self.clock=clock;self.active=False;self.closed=False
        self.raw=dict(schema=SCHEMA,batch_id=batch_id,cache_kind='representation',cache_definition_sha256=cache_definition_sha256,
            tt_reused=False,os_cache_controlled=False,planned_queries=[dict(p) for p in planned_queries],setup_node_limit=setup_node_limit,
            batch_node_limit=setup_node_limit+sum(p['node_limit'] for p in planned_queries),
            setup_status='completed',setup_stages=[],queries=[],start_ns=clock(),end_ns=0,cache_payload_bytes=None)

    @contextmanager
    def setup(self, phase):
        if self.closed or self.active or self.raw['queries'] or phase not in SETUP_PHASES:raise ValueError('Invalid setup sequence')
        self.active=True
        row=dict(phase=phase,start_ns=self.clock(),end_ns=None,nodes=None,issued_nodes=None)
        try:yield row
        except BaseException as exc:
            self.raw['setup_status']='timeout' if isinstance(exc,TimeoutError) else 'error';raise
        finally:
            row['end_ns']=self.clock();self.raw['setup_stages'].append(row);self.active=False

    def _next(self, query_id):
        index=len(self.raw['queries'])
        if self.closed or self.active or index>=len(self.raw['planned_queries']) or self.raw['planned_queries'][index]['query_id']!=query_id:
            raise ValueError('Query missing, nested, duplicate or reordered')

    @contextmanager
    def query(self, query_id, cache_result):
        self._next(query_id);self.active=True
        q=dict(query_id=query_id,cache_result=cache_result,status='completed',start_ns=self.clock(),end_ns=None,stages=[])
        recorder=_Query(q,self.clock)
        try:yield recorder
        except BaseException as exc:q['status']='timeout' if isinstance(exc,TimeoutError) else 'error';raise
        finally:q['end_ns']=self.clock();self.raw['queries'].append(q);self.active=False

    def skip(self, query_id):
        self._next(query_id);now=self.clock()
        self.raw['queries'].append(dict(query_id=query_id,cache_result='not_run',status='not_run',start_ns=now,end_ns=now,stages=[]))

    def finish(self, *, cache_payload_bytes):
        if self.closed or self.active:raise ValueError('Active/closed batch')
        self.raw['end_ns']=self.clock();self.raw['cache_payload_bytes']=cache_payload_bytes
        result=audit(self.raw);self.closed=True
        return self.raw,result


class _Query:
    def __init__(self, raw, clock):self.raw=raw;self.clock=clock;self.active=False
    @contextmanager
    def stage(self, phase):
        if self.active or self.raw['end_ns'] is not None or phase not in QUERY_PHASES:raise ValueError('Invalid query stage')
        self.active=True;row=dict(phase=phase,start_ns=self.clock(),end_ns=None,nodes=None,issued_nodes=None)
        try:yield row
        finally:row['end_ns']=self.clock();self.raw['stages'].append(row);self.active=False
