"""Post-hoc whole-owner/event deletion diagnostic of already frozen outcomes.

No engine calls, new scores, signature changes, bootstrap CI or efficacy test.
All original sampling owners remain, including owners absent from the stratum.
"""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

INPUT = 'research/mtdp/jass_benchmark/spatial-jass/replication/two-named-arenas-results.json'
INPUT_SHA = '3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7'
EVENTS = ('s7ahYqL4', 'D9PF2OSW')


def ratio(total, count):
    if count == 0:
        return None
    f = Fraction(total, count)
    return {'numerator': f.numerator, 'denominator': f.denominator, 'value': float(f)}


def deletion_table(rows, population, fields):
    """Delete entire (event, owner) groups, never individual selected positions."""
    units = sorted({(r['event'], r['owner']) for r in population})
    if not units or any((r['event'], r['owner']) not in units for r in rows):
        raise ValueError('Invalid complete sampling frame')
    if len({(r['event'], r['fen']) for r in rows}) != len(rows):
        raise ValueError('Repeated target in estimand')
    if any(type(r[f]) is not int for r in rows for f in fields):
        raise ValueError('Integer ordinary outcomes required')
    def summary(selected):
        return {'positions': len(selected), 'totals': {f: sum(r[f] for r in selected) for f in fields},
                'means': {f: ratio(sum(r[f] for r in selected), len(selected)) for f in fields}}
    deleted = []
    for event, owner in units:
        kept = [r for r in rows if (r['event'], r['owner']) != (event, owner)]
        deleted.append({'deleted_event': event, 'deleted_owner': owner,
                        'deleted_positions': len(rows)-len(kept), **summary(kept)})
    return {'full': summary(rows), 'sampling_owners': len(units),
            'contributing_owners': len({(r['event'], r['owner']) for r in rows}),
            'delete_one_owner': deleted,
            'delete_one_event': [{'deleted_event': event,
                                  **summary([r for r in rows if r['event'] != event])}
                                 for event in sorted({r['event'] for r in population})]}


def analyze(root):
    raw = (Path(root) / INPUT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA:
        raise ValueError('Frozen primary outcome bytes changed')
    r = json.loads(raw)
    if (r['schema'] != 'mtdp-two-arena-registered-results-v1' or
            r['primary_geometry_mask'] != 'frozen_LCB_full_signature_equal' or
            r['primary_total_node_budget'] != 50000 or r['target_depth'] != 16):
        raise ValueError('Primary reference contract changed')
    population = r['budgets']['50000']['rows']
    geometry = [x for x in r['geometry']['LCB']['rows'] if x['LCB_full_equal'] is True]
    if len(population) != 38 or len(geometry) != 26:
        raise ValueError('Frozen populations changed')
    if {x['event'] for x in population} != set(EVENTS):
        raise ValueError('Frozen events changed')
    for row in population:
        for arm in ('control', 'native', 'lcb'):
            if row['arms'][arm]['best_category'] != 'ordinary' or row['arms'][arm]['candidate_category'] != 'ordinary':
                raise ValueError('Nonordinary reference outcome')
        for arm in ('native', 'lcb'):
            if row['control_minus_'+arm] != row['control_regret'] - row[arm+'_regret']:
                raise ValueError('Contrast arithmetic changed')
    return {'schema': 'mtdp-frozen-owner-deletion-diagnostic-v1',
            'scope': 'post_hoc_sensitivity_of_existing_outcomes_not_independent_confirmation',
            'input_sha256': INPUT_SHA, 'score_unit': r['score_unit'],
            'geometry': deletion_table(geometry, population, ('ordinary_regret', 'disjoint', 'pick_optimal')),
            'jass_50000': deletion_table(population, population, ('control_minus_native', 'control_minus_lcb')),
            'new_scores_acquired': False, 'new_engine_nodes': 0,
            'signature_or_selection_changed': False, 'new_cohort_qualified': False,
            'confidence_interval_or_pvalue': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.root)
    with a.output.open('x') as f:
        f.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: result[k]['full'] for k in ('geometry', 'jass_50000')}, sort_keys=True))


if __name__ == '__main__':
    main()
