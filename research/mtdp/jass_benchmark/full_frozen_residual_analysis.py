"""Independent validation and descriptive full-frame residual controls; no target scores."""
import argparse
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark.mechanistic_trace_analysis import raw_main, raw_probe, sha

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
ARMS = ('control', 'native_full', 'LCB_full', 'LCB_residual', 'native_residual')
PAIRS = {'force_at_equal_residual': ('control', 'LCB_residual'),
         'LCB_budget_effect': ('LCB_residual', 'LCB_full'),
         'native_budget_effect': ('native_residual', 'native_full'),
         'order_at_residual_budget': ('LCB_residual', 'native_residual'),
         'order_at_full_budget': ('LCB_full', 'native_full'),
         'control_vs_native_full': ('control', 'native_full')}


def read_archive(path):
    files = {}
    with tarfile.open(path, 'r:gz') as archive:
        for m in archive:
            if (not m.isfile() or m.name in files or m.name not in ('normalized.json', 'status.json', 'publication.json')
                    and re.fullmatch(r'raw/\d{3}/\d{3}\.json', m.name) is None):
                raise ValueError('Unexpected full-frame raw archive member')
            files[m.name] = archive.extractfile(m).read()
    return files


def validate(root, files, plan):
    norm = json.loads(files['normalized.json'])
    status, pub = (json.loads(files[n]) for n in ('status.json', 'publication.json'))
    assert status['complete'] is True and status['normalized_sha256'] == sha(files['normalized.json'])
    assert norm['collector_commit'] == status['collector_commit'] == pub['collector_commit']
    assert norm['scope'] == pub['scope'] == plan['scope'] and pub['scientific_freeze'] is False
    assert norm['target_references_opened'] == 0 and norm['new_independent_cohort'] is False
    assert norm['plan_sha256'] == sha((root / (BASE + 'full-frozen-residual-control-plan.json')).read_bytes())
    audit_raw = (root / (BASE + 'two-named-arenas-telemetry-audit.json')).read_bytes()
    assert sha(audit_raw) == plan['parent_audit_sha256']
    hashes = json.loads(audit_raw)['frozen_file_sha256']
    assert len(norm['rows']) == len(plan['cases']) == 114
    names = {'normalized.json', 'status.json', 'publication.json'}
    for i, (row, case) in enumerate(zip(norm['rows'], plan['cases'], strict=True)):
        assert row['case'] == case and row['original_summaries_reproduced'] is True
        old_raw = (root / (BASE + 'two-named-arenas-decisions/' + case['path'])).read_bytes()
        assert sha(old_raw) == hashes[case['path']]
        old = json.loads(old_raw)
        for j, call in enumerate(row['calls']):
            name = f'raw/{i:03d}/{j:03d}.json'
            names.add(name)
            raw = json.loads(files[name])
            assert raw['returncode'] == 0 and raw['phase'] == call['phase']
            assert raw['issued_limit'] == call['issued_limit'] and raw['prefix'] == call['prefix']
            assert raw['forced'] == call.get('forced')
            probe = call['phase'] in ('preliminary', 'probe')
            lead = [call['phase']] if probe else []
            assert raw['stdin'] == ' '.join([*lead, case['fen'], str(call['issued_limit']), *call['prefix']]) + '\n'
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
        assert scores[first['winner']] == first['score'] == best
        tied = [m for m in first['native_order'] if scores[m] == best]
        selected = tied[0] if len(tied) > 1 and tied[0] != first['winner'] else None
        reason = 'verified_tie' if selected is not None else 'verified_tie_same_winner' if len(tied) > 1 else 'verified_unique_best'
        v = row['verification']
        assert v['intervention'] == selected == case['reported_intervention'] and v['decision_reason'] == reason
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
        control = row['main']['control']
        if selected is not None:
            assert control['attempts'][0]['best_move'] == selected
            assert next(a for a in control['attempts'] if a['depth'] == 2)['expected_order'][0] == selected
        else:
            assert control == row['main']['LCB_residual']
        assert row['actual_nodes_all_five_arms'] == spent + sum(row['main'][a]['summary']['nodes'] for a in ARMS)
    assert set(files) == names
    assert status['completed_cases'] == [c['path'] for c in plan['cases']]
    assert len({r['case']['fen'] for r in norm['rows']}) == 38
    assert len({(r['case']['event'], r['case']['owner']) for r in norm['rows']}) == 31
    assert all(sum(r['case']['budget'] == b for r in norm['rows']) == 38 for b in (10000, 50000, 200000))
    total = sum(r['actual_nodes_all_five_arms'] for r in norm['rows'])
    assert total == norm['actual_nodes_all_five_arms'] == status['actual_nodes'] <= plan['max_total_search_nodes_per_execution']
    assert norm['raw_receipts_count'] == sum(len(r['calls']) for r in norm['rows'])
    return norm


def summarize(rows):
    comparisons = {}
    for name in PAIRS:
        comparisons[name] = {
            'contexts': len(rows), 'same_final_move': sum(r['pairs'][name]['same_final_move'] for r in rows),
            'depth_delta_counts': dict(sorted(Counter(str(r['pairs'][name]['depth_delta']) for r in rows).items())),
            'different_Jass_score': sum(r['pairs'][name]['Jass_score_delta'] != 0 for r in rows),
            'changed_move_paths': [r['case']['path'] for r in rows if not r['pairs'][name]['same_final_move']],
            'changed_depth_paths': [r['case']['path'] for r in rows if r['pairs'][name]['depth_delta']]}
    return {'contexts': len(rows), 'unique_positions': len({r['case']['fen'] for r in rows}),
            'owner_games': len({(r['case']['event'], r['case']['owner']) for r in rows}),
            'interventions': sum(r['selected'] is not None for r in rows), 'comparisons': comparisons}


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
        rows.append({'case': r['case'], 'reason': r['verification']['decision_reason'],
                     'selected': r['verification']['intervention'],
                     'preliminary_winner': r['calls'][0]['receipt']['winner'],
                     'depth1_best': {a: r['main'][a]['attempts'][0]['best_move'] for a in ARMS},
                     'final': {a: r['main'][a]['summary'] for a in ARMS}, 'pairs': pairs})
    return {'schema': 'mtdp-full-frozen-residual-analysis-v1', 'scope': norm['scope'],
            'target_references_opened': 0, 'actual_nodes_per_execution': norm['actual_nodes_all_five_arms'],
            'all': summarize(rows), 'by_budget': {str(b): summarize([r for r in rows if r['case']['budget'] == b])
                                                for b in (10000, 50000, 200000)},
            'by_event': {e: summarize([r for r in rows if r['case']['event'] == e])
                         for e in sorted({r['case']['event'] for r in rows})},
            'rows': rows, 'limitations': ['already_known_population_post_hoc_not_independent_efficacy_validation',
                                         'Jass_scores_at_different_depths_are_not_Scan_regrets',
                                         'supplementary_arms_match_main_nodes_not_total_verification_cost']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'archive7', 'archive61', 'output', 'proof'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    plan = json.loads((a.root / (BASE + 'full-frozen-residual-control-plan.json')).read_bytes())
    files = [read_archive(path) for path in (a.archive7, a.archive61)]
    norms = [validate(a.root, f, plan) for f in files]
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
    result = analyze(norms[0])
    raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    with a.output.open('xb') as stream:
        stream.write(raw)
    proof = {'schema': 'mtdp-full-residual-independent-verification-v1',
             'normalized_sha256': sha(files[0]['normalized.json']), 'results_sha256': sha(raw),
             'hash_seeds': [7, 61], 'normalized_byte_identical': True,
             'all_raw_envelopes_identical_except_main_elapsed': True,
             'all_raw_receipts_and_original_summaries_checked': True,
             'actual_nodes_both_executions': sum(n['actual_nodes_all_five_arms'] for n in norms),
             'raw_receipts_both_executions': sum(n['raw_receipts_count'] for n in norms),
             'raw_archive_sha256': {str(seed): sha(path.read_bytes()) for seed, path in ((7, a.archive7), (61, a.archive61))},
             'raw_file_sha256': {str(seed): {n: sha(v) for n, v in sorted(f.items())} for seed, f in zip((7, 61), files, strict=True)}}
    with a.proof.open('x') as stream:
        stream.write(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'all': result['all'], 'nodes_per_execution': result['actual_nodes_per_execution']}, sort_keys=True))


if __name__ == '__main__':
    main()
