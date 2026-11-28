"""Offline consistency verification of full native observer evidence, no search."""
import argparse
import json
from pathlib import Path
from research.mtdp.jass_benchmark import q3_native_binding as native
from research.mtdp.jass_benchmark.q3_cost_receipt import audit


def verify(directory, plan):
    directory=Path(directory)
    rows=[json.loads(line) for line in (directory/'trials.jsonl').read_text().splitlines()]
    previous=None
    for row in rows:
        start,end=row['outer_start_ns'],row['outer_end_ns']
        if (type(start) is not int or type(end) is not int or start<0 or end<start
                or row['total_elapsed_ns']!=end-start or (previous is not None and start<previous)):
            raise ValueError('Invalid external trial clocks')
        previous=end
        if row['status']!='completed':
            continue  # Never converts failures into completed observations.
        raw=row['raw']
        if raw['returncode']!=0:
            raise ValueError('Completed trial has nonzero return code')
        result=native.parse_native(raw['stdout'],plan['fen'],plan['node_budget'])
        if (row['semantic_search']!=native.semantic(result) or row['measured_nodes']!=result['nodes']
                or row['internal_search_us']!=result['internal_search_us']):
            raise ValueError('Reported semantic/timing data differs from raw native output')
        bounds=result['internal_search_us']*1000<=end-start
        if row['arm']=='instrumented':
            cost=row['cost_receipt'];checked=audit(cost)
            if (checked!=row['cost_audit'] or cost['trial_id']!=str(row['index'])
                    or cost['position_id']!=plan['fen'] or cost['arm']!='native'
                    or cost['node_budget']!=plan['node_budget'] or cost['status']!='completed'
                    or cost['start_ns']<start or cost['end_ns']>end
                    or row['observer_outside_recorder_ns']!=end-start-checked['total_elapsed_ns']):
                raise ValueError('Reported cost differs from complete envelope/stage receipts')
            bounds=bounds and checked['equal_node_comparable'] and result['internal_search_us']*1000<=checked['phase_elapsed_ns']['search']
        elif any(row[k] is not None for k in ['cost_receipt','cost_audit','observer_outside_recorder_ns']):
            raise ValueError('Plain trial unexpectedly contains recorder evidence')
        if row['timing_bounds_pass']!=bool(bounds):
            raise ValueError('Reported timing verdict differs from raw clocks')
    calculated=native.summarize(rows,plan)
    published=json.loads((directory/'summary.json').read_text())
    if calculated!=published:
        raise ValueError('Observer summary does not reproduce from all retained trials')
    files={name:dict(bytes=(directory/name).stat().st_size,sha256=native.sha((directory/name).read_bytes()))
           for name in ['summary.json','trials.jsonl','provenance.json']}
    return dict(schema='mtdp-q3-native-evidence-verification-v1',question='Q3',files=files,
        binding_passed=calculated['binding_passed'],total_trials=len(rows),
        total_measured_nodes=calculated['total_measured_nodes'],
        raw_outputs_and_external_and_recorder_clocks_reconciled=True,
        common_search_semantic_sha256=(native.sha((json.dumps(rows[0]['semantic_search'],sort_keys=True)+'\n').encode())
            if calculated['all_search_semantics_equal'] else None),
        execution_authenticity_proven=False,independent_quality_or_speed_gain_established=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();value=verify(a.directory,native.load_plan(a.root))
    with a.output.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(value,sort_keys=True))


if __name__=='__main__':main()
