"""Q3 evidence gap in authenticated old receipts; never rerun search/quality."""
import argparse
import json
from pathlib import Path
from research.mtdp.jass_benchmark import two_arena_telemetry_audit as old
from research.mtdp.jass_benchmark.two_arena_execution import _bytes, digest


def analyze(root):
    root=Path(root)
    telemetry=old.analyze(root)
    retained=json.loads((root/old.BASE/'two-named-arenas-telemetry-audit.json').read_text())
    if telemetry != retained:
        raise ValueError('Existing frozen node audit no longer reproduces')
    complete,complete_sha=old.pinned(root,old.DECISIONS,old.PREFIX+'complete.json')
    packets=[old.pinned(root,old.DECISIONS,old.PREFIX+r['path'],complete['files'][r['path']])[0]
             for r in telemetry['rows']]
    arms=('native_baseline','lcb_baseline','control_main')
    return dict(schema='mtdp-q3-archived-cost-coverage-v1',question='Q3',
        scope='existing frozen two-arena node receipts only; no new efficacy population',
        decisions_commit=old.DECISIONS,complete_sha256=complete_sha,
        reproduced_node_audit_sha256=digest((root/old.BASE/'two-named-arenas-telemetry-audit.json').read_bytes()),
        position_budget_receipts=len(packets),unique_positions=telemetry['all']['unique_positions'],
        budgets=list(old.BUDGETS),node_accounting_reproduced=True,
        archived_verification_nodes=telemetry['all']['verification_nodes_sum'],
        archived_control_total_nodes=telemetry['all']['control_total_nodes'],
        outer_elapsed_ns_fields=sum('total_elapsed_ns' in p for p in packets),
        complete_phase_timing_fields=sum('phase_elapsed_ns' in p for p in packets),
        cache_setup_mode_fields=sum('cache_mode' in p for p in packets),
        arm_elapsed_ns_fields={arm:sum('elapsed_ns' in p[arm] for p in packets) for arm in arms},
        time_missing_is_not_zero=True,wall_time_gain_established=False,
        fixed_quality_cost_reduction_established=False,
        historical_negative_quality_conclusions_unchanged=True,
        engine_searches=0,new_target_scores_opened=0,new_signatures_computed=0,
        independent_cohort_qualified=False,new_cohorts_reserved=False,
        next_decision='Retain old equal-node result; use explicit total-cost receipts only after Q1/Q2 gate, never reconstruct missing times from nodes.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=analyze(a.root)
    with a.output.open('xb') as f:f.write(_bytes(report))
    print(json.dumps(report,sort_keys=True,indent=2))


if __name__=='__main__':main()
