"""H13 synthetic pre-freeze audit of primary versus conditional top-3 inference.

No corpus or reference engine is read. Calls existing D1 reporting utilities
without changing their scientific behavior or any frozen H13 analysis.
"""
import argparse
import json
from pathlib import Path

from research.mtdp.decision_equivalence.aggregate import aggregate_paired
from research.mtdp.decision_equivalence.clustered_bootstrap import clustered_difference
from research.mtdp.decision_equivalence.paired_cluster_report import paired_cluster_report
from research.mtdp.decision_equivalence.paired_order_audit import paired_order_audit

REPETITIONS = 2000
SEED = 20261120


def observations():
    return [{'id': f'p{i}', 'game_id': f'synthetic-g{i}',
             'legal': ['a', 'b', 'c', 'd'],
             'candidate': ['a', 'b', 'c', 'd'],
             'baseline': ['d', 'a', 'b', 'c'],
             'scores': {'a': 0, 'b': 0, 'c': 0 if i < 2 else 9, 'd': 9}}
            for i in range(4)]


def compare(rows):
    aggregate = aggregate_paired([{**r, 'proposed': r['candidate']} for r in rows])
    # The primary mask uses legal action count only, as the existing D1 contract requires.
    primary_rows = []
    for r in rows:
        result = paired_order_audit(r['legal'], r['candidate'], r['baseline'], r['scores'])
        if len(r['legal']) >= 4:
            primary_rows.append({'game_id': r['game_id'],
                                 'candidate': result['candidate_minus_baseline']['recall_at_3'],
                                 'baseline': 0})
    primary = clustered_difference(primary_rows, metric='recall_at_3',
                                   repetitions=REPETITIONS, seed=SEED)
    conditional = paired_cluster_report(rows, metric='recall_at_3',
                                        repetitions=REPETITIONS, seed=SEED,
                                        top3_population='conditional_informative')
    d1_primary = paired_cluster_report(rows, metric='recall_at_3',
                                       repetitions=REPETITIONS, seed=SEED,
                                       top3_population='fixed_n_ge_4')
    for field in ('n_clusters', 'n_observations', 'candidate_minus_baseline',
                  'ci95', 'repetitions', 'seed'):
        assert d1_primary[field] == primary[field]
    assert d1_primary['top3_population_is_primary_fixed'] is True
    assert conditional['top3_population_is_primary_fixed'] is False
    return {'aggregate': aggregate, 'primary_fixed_legal_count_bootstrap': primary,
            'new_d1_bridge_conditional_bootstrap': conditional,
            'new_d1_bridge_primary_bootstrap': d1_primary}


def audit():
    rows = observations()
    original = compare(rows)
    primary = original['primary_fixed_legal_count_bootstrap']
    conditional = original['new_d1_bridge_conditional_bootstrap']
    assert primary['n_observations'] == primary['n_clusters'] == 4
    assert primary['candidate_minus_baseline'] == -0.5
    assert primary['ci95'] == [-1.0, 0.0]
    assert conditional['n_observations'] == conditional['n_clusters'] == 2
    assert conditional['candidate_minus_baseline'] == -1.0
    assert conditional['ci95'] == [-1.0, -1.0]
    assert original['aggregate']['primary_score_blind_n_ge_4']['delta_recall3'] == -0.5
    changed = [{**r, 'scores': dict(r['scores'])} for r in rows]
    changed[2]['scores']['c'] = 0
    after = compare(changed)
    assert after['primary_fixed_legal_count_bootstrap']['n_observations'] == 4
    assert after['new_d1_bridge_conditional_bootstrap']['n_observations'] == 3
    assert [r['legal'] for r in changed] == [r['legal'] for r in rows]
    return {'schema': 'mtdp-h13-synthetic-estimand-compatibility-audit-v2',
            'synthetic_only': True, 'independent_cohort_qualified': False,
            'new_reference_scores_acquired': False, 'observations': rows,
            'original': original, 'one_tie_changed_legal_population_unchanged': after,
            'primary_estimate_matches_conditional_estimate': False,
            'conditional_interval_is_primary_interval': False,
            'interpretation': 'The conditional D1 branch uses informative_at_3; its interval cannot accompany the fixed-population primary estimate. The explicit fixed_n_ge_4 branch now reproduces that primary estimate and interval.',
            'next_action': 'Use explicit fixed_n_ge_4 mode for fixed-population top-3 inference and conditional_informative only for the labelled secondary diagnostic. Keep exclusions and independent admission gates before any future freeze.',
            'scope': 'synthetic pre-freeze interpretation check; no change to D1 modules or frozen H13 studies'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    value = audit()
    with a.output.open('xb') as out:
        out.write((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({'synthetic_only': True, 'primary_mean': -0.5,
                      'primary_ci95': [-1, 0], 'conditional_mean': -1,
                      'conditional_ci95': [-1, -1]}))


if __name__ == '__main__':
    main()
