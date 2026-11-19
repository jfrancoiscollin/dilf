"""Stdlib-only check of the node audit against all original published receipts."""
import argparse
import hashlib
import json
from pathlib import Path

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'


def verify(root, report_path):
    raw = report_path.read_bytes()
    report = json.loads(raw)
    original = root / (BASE + 'two-named-arenas-decisions')
    expected = report['frozen_file_sha256']
    rows = {r['path']: r for r in report['rows']}
    decision_paths = set(expected) - {'source12.json', 'plan.json'}
    assert len(rows) == len(report['rows']) == len(decision_paths) == 114
    assert rows.keys() == decision_paths
    originals = []
    for name, sha in expected.items():
        data = (original / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha
        if name not in decision_paths:
            continue
        r = json.loads(data)
        emitted = rows[name]
        calls = r['verification_receipts']
        spent = 0
        for call in calls:
            assert call['issued_limit'] == r['budget'] // 10 - spent
            assert 0 <= call['nodes'] <= call['issued_limit']
            spent += call['nodes']
        assert spent == r['verification_nodes']
        assert spent + r['main_nodes'] == r['budget']
        assert calls[0]['nodes'] == r['preliminary_nodes']
        assert spent == emitted['preliminary_nodes'] + emitted['probe_nodes']
        for arm in ('control_main', 'native_baseline', 'lcb_baseline'):
            assert r[arm]['depth_ceiling'] is False
            assert r[arm]['nodes'] == (r['budget'] - spent if arm == 'control_main' else r['budget'])
        assert emitted['control_native_same_move'] == (r['control_main']['best_move'] == r['native_baseline']['best_move'])
        assert emitted['control_native_depth_delta'] == r['control_main']['completed_depth'] - r['native_baseline']['completed_depth']
        assert emitted['control_native_score_delta'] == r['control_main']['score'] - r['native_baseline']['score']
        assert emitted['reported_intervention'] == r['intervention']
        assert emitted['main_attempt_trace_retained'] == ('attempts' in r['control_main'])
        assert emitted['full_verification_evidence_retained'] == all(
            all(k in c for k in ('completed', 'score', 'alpha_before', 'beta')) for c in calls)
        originals.append(r)
    totals = {}
    for budget in (10000, 50000, 200000):
        chosen = [r for r in originals if r['budget'] == budget]
        summary = report['by_budget'][str(budget)]
        assert len(chosen) == summary['receipts'] == summary['unique_positions'] == 38
        interventions = [r for r in chosen if r['intervention'] is not None]
        assert len(interventions) == summary['reported_intervention_receipts'] == 3
        spent = sum(r['verification_nodes'] for r in chosen)
        assert spent == summary['verification_nodes_sum']
        assert spent / (38 * budget) == summary['verification_fraction_of_control_total']
        assert sum(r['main_nodes'] for r in chosen) + spent == 38 * budget
        totals[str(budget)] = spent
    unique = len({r['fen'] for r in originals if r['intervention'] is not None})
    assert unique == report['all']['reported_intervention_unique_positions'] == 3
    assert sum(totals.values()) == report['all']['verification_nodes_sum']
    assert {r['path'] for r in report['next_diagnostic_mask']['cases']} == {
        n for n, r in rows.items() if r['reported_intervention'] is not None}
    return {'schema': 'mtdp-telemetry-independent-verification-v1',
            'report_sha256': hashlib.sha256(raw).hexdigest(), 'original_receipts_checked': len(originals),
            'verification_nodes_by_budget': totals, 'unique_intervention_positions': unique,
            'node_conservation_and_summary_deltas_checked': True,
            'no_unsupported_depth_one_causal_attribution': True, 'new_engine_searches': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'report', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = verify(a.root, a.report)
    with a.output.open('x') as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
