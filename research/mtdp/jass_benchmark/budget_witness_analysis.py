"""Independent raw-receipt validation of the separate one-position budget witness."""
import argparse
import json
from pathlib import Path

from research.mtdp.jass_benchmark.mechanistic_trace_analysis import read_archive, raw_main, raw_probe, sha

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
ARMS = ('control', 'native_full', 'LCB_full', 'LCB_residual', 'native_residual')
PAIRS = {'control_vs_LCB_residual': ('control', 'LCB_residual'),
         'LCB_budget_effect': ('LCB_residual', 'LCB_full'),
         'native_budget_effect': ('native_residual', 'native_full'),
         'order_at_residual_budget': ('LCB_residual', 'native_residual'),
         'order_at_full_budget': ('LCB_full', 'native_full')}


def validate(root, files, plan):
    norm = json.loads(files['normalized.json'])
    status, publication = (json.loads(files[n]) for n in ('status.json', 'publication.json'))
    assert status['complete'] is True and status['normalized_sha256'] == sha(files['normalized.json'])
    assert norm['collector_commit'] == status['collector_commit'] == publication['collector_commit']
    assert norm['scope'] == publication['scope'] == plan['scope']
    assert publication['scientific_freeze'] is False
    assert norm['plan_sha256'] == sha((root / (BASE + 'nonintervened-budget-witness-plan.json')).read_bytes())
    audit_raw = (root / (BASE + 'two-named-arenas-telemetry-audit.json')).read_bytes()
    assert sha(audit_raw) == plan['parent_audit_sha256']
    hashes = json.loads(audit_raw)['frozen_file_sha256']
    assert len(norm['rows']) == len(plan['cases']) == 3
    names = {'normalized.json', 'status.json', 'publication.json'}
    for i, (row, case) in enumerate(zip(norm['rows'], plan['cases'], strict=True)):
        assert row['case'] == case and case['reported_intervention'] is None
        old_raw = (root / (BASE + 'two-named-arenas-decisions/' + case['path'])).read_bytes()
        assert sha(old_raw) == hashes[case['path']]
        old = json.loads(old_raw)
        for j, call in enumerate(row['calls']):
            name = f'raw/{i:02d}/{j:03d}.json'
            names.add(name)
            raw = json.loads(files[name])
            assert raw['returncode'] == 0 and raw['forced'] is None and call.get('forced') is None
            assert raw['phase'] == call['phase'] and raw['issued_limit'] == call['issued_limit']
            assert raw['prefix'] == call['prefix']
            probe = call['phase'] in ('preliminary', 'probe')
            payload = [call['phase']] if probe else []
            assert raw['stdin'] == ' '.join([*payload, case['fen'], str(call['issued_limit']), *call['prefix']]) + '\n'
            assert raw['argv_options'] == ([] if probe else ['--initial-only', '--record-depth-ceiling'])
            parsed = raw_probe(raw['stdout']) if probe else raw_main(raw['stdout'])
            assert parsed == call['receipt']
            if not probe:
                assert parsed == row['main'][call['phase']]
        first = row['calls'][0]['receipt']
        probes = [c['receipt'] for c in row['calls'] if c['phase'] == 'probe']
        assert [p['move'] for p in probes] == first['native_order']
        scores = {p['move']: p['score'] for p in probes}
        best = max(scores.values())
        assert [m for m in first['native_order'] if scores[m] == best] == [first['winner']]
        assert best == first['score']
        v = row['verification']
        assert v['intervention'] is None and v['decision_reason'] == 'verified_unique_best'
        assert all(v[k] == old[k] for k in v)
        spent = sum(c['receipt']['nodes'] for c in row['calls'] if c['phase'] in ('preliminary', 'probe'))
        assert spent == case['verification_nodes'] == v['verification_nodes']
        residual = case['budget'] - spent
        for arm in ARMS:
            s = row['main'][arm]['summary']
            assert s['depth_ceiling'] is False
            assert s['nodes'] == (case['budget'] if arm in ('native_full', 'LCB_full') else residual)
            if arm in ('control', 'native_full', 'LCB_full'):
                key = {'control': 'control_main', 'native_full': 'native_baseline', 'LCB_full': 'lcb_baseline'}[arm]
                assert s == old[key]
        assert row['main']['control'] == row['main']['LCB_residual']
        assert row['actual_nodes_all_five_arms'] == spent + sum(row['main'][a]['summary']['nodes'] for a in ARMS)
    assert set(files) == names
    assert {r['case']['budget'] for r in norm['rows']} == {10000, 50000, 200000}
    assert len({r['case']['fen'] for r in norm['rows']}) == 1
    total = sum(r['actual_nodes_all_five_arms'] for r in norm['rows'])
    assert total == norm['actual_nodes_all_five_arms'] == status['actual_nodes'] <= plan['max_total_search_nodes_per_execution']
    assert norm['raw_receipts_count'] == sum(len(r['calls']) for r in norm['rows'])
    return norm


def analyze(norm):
    rows = []
    for r in norm['rows']:
        pairs = {}
        for name, (left, right) in PAIRS.items():
            a, b = (r['main'][k]['summary'] for k in (left, right))
            pairs[name] = {'same_main_nodes': a['nodes'] == b['nodes'],
                           'same_final_move': a['best_move'] == b['best_move'],
                           'depth_delta': a['completed_depth'] - b['completed_depth'],
                           'Jass_score_delta': a['score'] - b['score']}
        milestones = {}
        for arm in ('LCB_full', 'native_full'):
            main = r['main'][arm]
            depth = main['summary']['completed_depth']
            last = [a for a in main['attempts'] if a['depth'] == depth and a['completed']][-1]
            milestones[arm] = {'full_completed_depth': depth, 'completion_nodes_after': last['nodes_after'],
                               'residual_limit': r['case']['budget'] - r['case']['verification_nodes']}
        rows.append({'case': r['case'], 'fresh_unique_best': r['calls'][0]['receipt']['winner'],
                     'control_LCB_residual_entire_trace_identical': r['main']['control'] == r['main']['LCB_residual'],
                     'final': {k: r['main'][k]['summary'] for k in ARMS}, 'comparisons': pairs,
                     'full_budget_depth_completion_nodes': milestones,
                     'depth_interaction_LCB_minus_native': pairs['LCB_budget_effect']['depth_delta'] - pairs['native_budget_effect']['depth_delta']})
    return {'schema': 'mtdp-nonintervened-witness-analysis-v1', 'scope': norm['scope'],
            'contexts': len(rows), 'unique_positions': 1, 'target_references_opened': 0,
            'actual_nodes_per_execution': norm['actual_nodes_all_five_arms'], 'rows': rows,
            'limitations': ['post_hoc_known_depth_loss_witness_not_independent_validation',
                            'Jass_scores_at_different_depths_are_not_Scan_regrets',
                            'original_nine_intervention_mask_unchanged']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'archive7', 'archive61', 'output', 'proof'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    plan = json.loads((a.root / (BASE + 'nonintervened-budget-witness-plan.json')).read_bytes())
    files = [read_archive(path) for path in (a.archive7, a.archive61)]
    runs = [validate(a.root, f, plan) for f in files]
    assert files[0]['normalized.json'] == files[1]['normalized.json']
    assert files[0]['status.json'] == files[1]['status.json']
    for name in files[0]:
        if name.startswith('raw/'):
            envelopes = [json.loads(f[name]) for f in files]
            for envelope in envelopes:
                if envelope['phase'] not in ('preliminary', 'probe'):
                    v = envelope['stdout'].split('\t')
                    v[7] = '<elapsed>'
                    envelope['stdout'] = '\t'.join(v)
            assert envelopes[0] == envelopes[1]
    result = analyze(runs[0])
    encoded = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    with a.output.open('xb') as stream:
        stream.write(encoded)
    proof = {'schema': 'mtdp-nonintervened-witness-independent-verification-v1',
             'normalized_sha256': sha(files[0]['normalized.json']), 'results_sha256': sha(encoded),
             'hash_seeds': [7, 61], 'normalized_byte_identical': True,
             'all_raw_envelopes_identical_except_main_elapsed': True,
             'all_raw_receipts_and_original_summaries_checked': True,
             'actual_nodes_both_executions': sum(r['actual_nodes_all_five_arms'] for r in runs),
             'raw_archive_sha256': {str(seed): sha(path.read_bytes()) for seed, path in ((7, a.archive7), (61, a.archive61))},
             'raw_file_sha256': {str(seed): {n: sha(v) for n, v in sorted(f.items())} for seed, f in zip((7, 61), files, strict=True)}}
    with a.proof.open('x') as stream:
        stream.write(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'contexts': result['contexts'], 'nodes_per_execution': result['actual_nodes_per_execution'],
                      'depth_interactions': [r['depth_interaction_LCB_minus_native'] for r in result['rows']]}))


if __name__ == '__main__':
    main()
