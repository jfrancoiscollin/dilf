"""Post-hoc Q3 cost/quality grid, all old points; no search or new reference."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

PLAN_SHA='217b7864681d5fd706f3c1da1005a5614344aed6e8eae4fe055521b9dacea4f6'
PLAN_COMMIT='17e7cc2ab65ffefdc99ba48ca21d65181187c475'
BASE=Path('research/mtdp/jass_benchmark/spatial-jass/replication')
ROLE={'native_full':'native','control':'control','LCB_full':'lcb'}


def sha(raw):return hashlib.sha256(raw).hexdigest()

def exact(n,d):
    value=Fraction(n,d)
    return dict(numerator=value.numerator,denominator=value.denominator)


def index_rows(rows):
    indexed={}
    for r in rows:
        key=r['event'],r['fen']
        if key in indexed:raise ValueError('Duplicate position in archived grid')
        indexed[key]=r
    if not indexed:raise ValueError('Empty archived grid')
    return indexed


def contrast(candidate, reference, budget, reference_budget):
    if candidate.keys()!=reference.keys() or not candidate:
        raise ValueError('Cost/quality contrast needs exactly the same complete positions')
    rows=[]
    for key in sorted(reference):
        a,b=candidate[key],reference[key]
        if a['owner']!=b['owner']:raise ValueError('Owner changed across budgets')
        ordinary=a['ordinary'] and b['ordinary']
        delta=a['regret']-b['regret'] if ordinary else None
        rows.append(dict(event=key[0],fen=key[1],owner=a['owner'],candidate_move=a['move'],reference_move=b['move'],
            candidate_regret=a['regret'],reference_regret=b['regret'],regret_delta=delta,
            candidate_category=a['category'],reference_category=b['category']))
    complete=all(r['regret_delta'] is not None for r in rows);n=len(rows)
    deltas=[r['regret_delta'] for r in rows if r['regret_delta'] is not None]
    cs=sum(r['candidate_regret'] for r in rows) if complete else None
    rs=sum(r['reference_regret'] for r in rows) if complete else None
    return dict(positions=n,owners=len({r['owner'] for r in rows}),ordinary_comparison_complete=complete,
        nonordinary_pairs=n-len(deltas),regret_sum=cs,reference_regret_sum=rs,
        mean_regret_scan_units=exact(cs,n) if complete else None,
        mean_paired_regret_delta_scan_units=exact(sum(deltas),n) if complete else None,
        improved=sum(v<0 for v in deltas),equal=sum(v==0 for v in deltas),worse=sum(v>0 for v in deltas),
        worst_increase_scan_units=max(deltas) if complete else None,
        best_decrease_scan_units=min(deltas) if complete else None,
        optimum_hits=sum(r['candidate_regret']==0 for r in rows) if complete else None,
        total_nodes=budget*n,reference_total_nodes=reference_budget*n,node_cost_ratio=exact(budget,reference_budget),
        mean_not_above_reference_observed=(cs<=rs) if complete else None,
        all_positions_not_worse_observed=all(v<=0 for v in deltas) if complete else None,
        cheaper_with_no_observed_mean_increase=(budget<reference_budget and cs<=rs) if complete else None,
        independent_quality_gate_passed=False,exact_wdl_preservation_established=False,rows=rows)


def cell(q, telemetry, arm, budget):
    if arm not in ROLE:raise ValueError('Only original full-budget arms are eligible')
    role=ROLE[arm];r=q['arms'][arm];t=telemetry[role]
    if (q['total_budget']!=budget or telemetry['budget']!=budget or q['owner']!=telemetry['owner']
            or r['move']!=t['best_move'] or t['depth_ceiling'] is not False or t['stop']!='nodes'
            or type(t['nodes']) is not int or t['nodes']<0 or q['main_nodes'][arm]!=t['nodes']):
        raise ValueError('Frozen move/node receipt does not match quality cell')
    verification=q['verification_nodes']
    if type(verification) is not int or verification<0 or verification!=telemetry['verification_nodes']:
        raise ValueError('Verification charge changed')
    if (t['nodes']+(verification if arm=='control' else 0)!=budget
            or (arm=='control' and verification>budget//10)):
        raise ValueError('Arm total cost is not its complete metered budget')
    ordinary=r['best_category']==r['candidate_category']=='ordinary'
    regret=r['ordinary_regret_centimen']
    if ordinary:
        if (type(r['covered']) is not bool or r['covered']!=(regret==0) or type(regret) is not int or regret<0
                or regret!=q['best_reference_score']-r['score']
                or regret!=q[arm+'_regret'] or (regret==0)!=(r['move'] in q['optimal_moves'])
                or int(regret==0)!=q[arm+'_optimal']):
            raise ValueError('Archived ordinary regret/optimum fields disagree')
    elif regret is not None:
        raise ValueError('Nonordinary category cannot become numeric regret')
    return dict(owner=q['owner'],ordinary=ordinary,regret=regret,move=r['move'],category=r['candidate_category'])


def analyze(root):
    root=Path(root)
    raw=(root/'research/mtdp/validation/q3-archived-budget-quality-plan-2026-11-28.json').read_bytes()
    if sha(raw)!=PLAN_SHA:raise ValueError('Archived contrast plan changed')
    plan=json.loads(raw);inputs={}
    for name,expected in plan['inputs'].items():
        p=BASE/name;data=(root/p).read_bytes()
        published=subprocess.check_output(['git','-C',str(root),'show',plan['input_snapshot']+':'+str(p)])
        if sha(data)!=expected or data!=published:raise ValueError('Published archived input changed: '+name)
        inputs[name]=json.loads(data)
    proof=inputs['full-frozen-residual-quality-ci-verification-2026-11-19.json']
    if proof['downloaded_and_every_member_compared'] is not True or proof['engine_calls_in_quality_reconciliation']!=0:
        raise ValueError('Prior closed quality proof unavailable')
    quality=inputs['full-frozen-residual-quality-results.json'];telemetry=inputs['two-named-arenas-telemetry-audit.json']
    costs={}
    for row in telemetry['rows']:
        key=row['budget'],row['event'],row['fen']
        if key in costs:raise ValueError('Duplicate metered receipt')
        costs[key]=row
    cohorts={b:index_rows(quality['budgets'][str(b)]['rows']) for b in plan['budgets']}
    ref_budget=plan['reference']['budget'];keys=set(cohorts[ref_budget])
    if (len(keys)!=plan['expected_positions'] or len({r['owner'] for r in cohorts[ref_budget].values()})!=plan['expected_owners']
            or sorted({e for e,f in keys})!=plan['events'] or any(set(c)!=keys for c in cohorts.values())
            or set(costs)!={(b,e,f) for b in plan['budgets'] for e,f in keys}):
        raise ValueError('Historical cohort/budget coverage changed')
    cells={}
    for budget,cohort in cohorts.items():
        for arm in plan['arms']:
            cells[budget,arm]={key:cell(q,costs[budget,*key],arm,budget) for key,q in cohort.items()}
            if any(q['best_reference_score']!=cohorts[ref_budget][key]['best_reference_score'] for key,q in cohort.items()):
                raise ValueError('Reference optimum changed between budgets')
    reference=cells[ref_budget,plan['reference']['arm']];points=[]
    for budget in plan['budgets']:
        for arm in plan['arms']:
            values=cells[budget,arm];point=contrast(values,reference,budget,ref_budget)
            point.update(arm=arm,budget=budget,by_event={e:contrast({k:v for k,v in values.items() if k[0]==e},
                {k:v for k,v in reference.items() if k[0]==e},budget,ref_budget) for e in plan['events']})
            points.append(point)
    return dict(schema='mtdp-q3-archived-budget-quality-v1',question='Q3',plan_commit=PLAN_COMMIT,plan_sha256=PLAN_SHA,
        input_snapshot=plan['input_snapshot'],input_sha256=plan['inputs'],scope=plan['scope'],reference=plan['reference'],
        positions=38,owner_games=31,independent_positions_not_multiplied_by_budgets=True,points=points,
        cheaper_points_with_no_observed_mean_increase=[dict(arm=p['arm'],budget=p['budget']) for p in points if p['cheaper_with_no_observed_mean_increase']],
        time_savings_established=False,exact_wdl_outcomes_available=False,independent_candidate_promoted=False,
        score_units='integer Scan units, 0.01 HUB; not calibrated material pawns',reference_is_empirical_scan16=True,
        engine_calls=0,new_reference_scores_acquired=0,new_cohorts_reserved=False,new_signature_campaign=False,
        confidence_intervals_computed=False,budget_selected_for_future_test=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=analyze(a.root)
    with a.output.open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps([dict(arm=p['arm'],budget=p['budget'],regret_sum=p['regret_sum'],mean_delta=p['mean_paired_regret_delta_scan_units'],
        worse=p['worse'],better=p['improved'],worst_increase=p['worst_increase_scan_units'],cheaper_mean_pass=p['cheaper_with_no_observed_mean_increase']) for p in report['points']],indent=2))


if __name__=='__main__':main()
