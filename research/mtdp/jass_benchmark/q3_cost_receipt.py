"""Opt-in Q3 cold-cache total-cost recorder; no engine, quality or efficacy claim.

Exclusive stages are nested inside one monotonic envelope. Gaps are charged as
orchestration overhead, never subtracted from total wall time. Engine nodes
must be supplied from actual receipts, including aborted calls.
"""
from contextlib import contextmanager
from time import perf_counter_ns

SCHEMA = 'mtdp-q3-cold-total-cost-v1'
PHASES = ('setup', 'signature', 'lookup', 'verification', 'fallback', 'search')
STATUSES = ('completed', 'depth_ceiling', 'timeout', 'error')


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid ' + label)
    return value


def audit(receipt):
    if type(receipt) is not dict or set(receipt) != {
        'schema', 'trial_id', 'position_id', 'arm', 'cache_mode', 'node_budget',
        'start_ns', 'end_ns', 'status', 'stages'
    }:
        raise ValueError('Unexpected total-cost receipt fields')
    if receipt['schema'] != SCHEMA or receipt['cache_mode'] != 'cold':
        raise ValueError('Unsupported cost schema or cache setup accounting')
    for key in ('trial_id', 'position_id', 'arm'):
        if type(receipt[key]) is not str or not receipt[key]:
            raise ValueError('Missing cost receipt identity')
    budget = integer(receipt['node_budget'], 'node budget', 1)
    start = integer(receipt['start_ns'], 'envelope start')
    end = integer(receipt['end_ns'], 'envelope end')
    if end < start or receipt['status'] not in STATUSES or type(receipt['stages']) is not list:
        raise ValueError('Invalid envelope, status or stages')
    previous = start
    phase_ns = dict.fromkeys(PHASES, 0)
    phase_nodes = dict.fromkeys(PHASES, 0)
    exceeded_calls = 0
    for row in receipt['stages']:
        if type(row) is not dict or set(row) != {'phase', 'start_ns', 'end_ns', 'nodes', 'issued_nodes'}:
            raise ValueError('Unexpected stage fields')
        phase = row['phase']
        if phase not in PHASES:
            raise ValueError('Unknown cost phase')
        a = integer(row['start_ns'], 'stage start')
        b = integer(row['end_ns'], 'stage end')
        nodes = integer(row['nodes'], 'measured nodes')
        issued = row['issued_nodes']
        if a < previous or b < a or b > end:
            raise ValueError('Stages overlap, reverse or leave envelope')
        if issued is None:
            if nodes:
                raise ValueError('Engine nodes require an issued cap')
        else:
            integer(issued, 'issued cap', 1)
            exceeded_calls += nodes > issued
        previous = b
        phase_ns[phase] += b-a
        phase_nodes[phase] += nodes
    total_ns = end-start
    total_nodes = sum(phase_nodes.values())
    return dict(total_elapsed_ns=total_ns, measured_nodes=total_nodes,
        phase_elapsed_ns=phase_ns, phase_nodes=phase_nodes,
        orchestration_elapsed_ns=total_ns-sum(phase_ns.values()),
        issued_cap_overruns=exceeded_calls,
        within_node_budget=total_nodes <= budget and exceeded_calls == 0,
        equal_node_comparable=(receipt['status'] == 'completed'
            and total_nodes == budget and exceeded_calls == 0),
        status=receipt['status'], execution_authenticity_proven=False,
        quality_measured=False, runtime_gain_established=False)


class CostRecorder:
    """Caller opens before setup/cache work and closes after final fallback.

    Do not use concurrent/nested stages. A stage covering a subprocess must
    include launch, parsing, failure handling and receipt extraction. Nodes
    are unknown until explicitly supplied; missing measurements fail closed.
    """
    def __init__(self, *, trial_id, position_id, arm, node_budget, clock=perf_counter_ns):
        self.clock = clock
        self.active = False
        self.closed = False
        self.receipt = dict(schema=SCHEMA, trial_id=trial_id, position_id=position_id,
            arm=arm, cache_mode='cold', node_budget=node_budget,
            start_ns=clock(), end_ns=0, status='error', stages=[])

    @contextmanager
    def stage(self, phase):
        if self.closed or self.active or phase not in PHASES:
            raise ValueError('Closed recorder, nested stage or unknown phase')
        self.active = True
        row = dict(phase=phase, start_ns=self.clock(), end_ns=None,
                   nodes=None, issued_nodes=None)
        try:
            yield row
        finally:
            row['end_ns'] = self.clock()
            self.active = False
            self.receipt['stages'].append(row)

    def finish(self, status):
        if self.active or self.closed:
            raise ValueError('Active or closed recorder')
        self.receipt['end_ns'] = self.clock()
        self.receipt['status'] = status
        result = audit(self.receipt)
        self.closed = True
        return self.receipt, result
