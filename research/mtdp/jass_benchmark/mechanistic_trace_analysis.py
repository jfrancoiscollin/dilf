"""Independent stdlib-only validation and descriptive comparisons of archived raw replays."""
import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
ARMS = ('control', 'native_full', 'LCB_full', 'LCB_residual', 'native_residual')
PAIRS = {'force_at_equal_residual': ('control', 'LCB_residual'),
         'LCB_budget_effect': ('LCB_residual', 'LCB_full'),
         'native_budget_effect': ('native_residual', 'native_full'),
         'control_vs_native_residual': ('control', 'native_residual')}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_archive(path):
    files = {}
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            if (not member.isfile() or member.name in files or
                member.name not in ('normalized.json', 'status.json', 'publication.json')
                and re.fullmatch(r'raw/\d{2}/\d{3}\.json', member.name) is None):
                raise ValueError('Unexpected, repeated or non-file raw archive member')
            files[member.name] = archive.extractfile(member).read()
    return files


def raw_probe(stdout):
    v = stdout.strip('\n').split('\t')
    assert len(v) == 15 and v[0] == 'mtdp-probe-v1' and v[1] in ('preliminary', 'probe')
    complete = v[5] == '1'
    p = {'nodes': int(v[4]), 'completed': complete, 'score': int(v[7]) if complete else None,
         'alpha_before': int(v[8]), 'beta': int(v[9]), 'native_order': v[14].split(','),
         'stop': v[11], 'bound': v[10].lower(), 'visited': int(v[12]), 'legal_count': int(v[13])}
    p['winner' if v[1] == 'preliminary' else 'move'] = v[6] if complete or v[1] == 'probe' else None
    assert complete and p['nodes'] > 0 and p['bound'] == 'exact' and p['stop'] == 'none'
    assert p['alpha_before'] == -31000 < p['score'] < p['beta'] == 31000
    return p


def raw_main(stdout):
    v = stdout.strip('\n').split('\t')
    assert len(v) >= 12 and int(v[7]) >= 0
    attempts = []
    for item in v[11:]:
        p = item.split(':')
        assert len(p) == 8
        attempts.append({'depth': int(p[0]), 'attempt': int(p[1]), 'completed': p[2] == '1',
                         'all_actions_searched': p[3] == '1', 'nodes_after': int(p[4]),
                         'visited': p[5].split(',') if p[5] else [],
                         'best_move': p[6], 'expected_order': p[7].split(',')})
    return {'summary': {'nodes': int(v[2]), 'depth_ceiling': v[4] == 'depth_ceiling',
                        'best_move': v[5], 'score': int(v[6]), 'completed_depth': int(v[3]), 'stop': v[4]},
            'legal': v[9].split(','), 'initial_order': v[10].split(','),
            'pv': v[8].split(',') if v[8] else [], 'attempts': attempts}


def best_by_depth(main):
    return {a['depth']: a['best_move'] for a in main['attempts'] if a['completed']}


def convergence(left, right):
    """Agreement through the common completed horizon only, not a deeper guarantee."""
    a, b = best_by_depth(left), best_by_depth(right)
    shared = sorted(a.keys() & b.keys())
    stable = next((d for i, d in enumerate(shared) if all(a[x] == b[x] for x in shared[i:])), None)
    return {'common_completed_depth': max(shared) if shared else None,
            'first_stable_same_best_within_common_horizon': stable,
            'shared_completed_best': [[d, a[d], b[d]] for d in shared]}


def validate(root, files, plan):
    report = json.loads(files['normalized.json'])
    status, publication = (json.loads(files[n]) for n in ('status.json', 'publication.json'))
    assert status['complete'] is True and status['normalized_sha256'] == sha(files['normalized.json'])
    assert report['scope'] == publication['scope'] == plan['scope']
    assert report['collector_commit'] == status['collector_commit'] == publication['collector_commit']
    assert publication['scientific_freeze'] is False
    assert report['plan_sha256'] == sha((root / (BASE + 'two-named-arenas-mechanistic-residual-plan.json')).read_bytes())
    audit_raw = (root / (BASE + 'two-named-arenas-telemetry-audit.json')).read_bytes()
    assert sha(audit_raw) == plan['parent_audit_sha256']
    old_hashes = json.loads(audit_raw)['frozen_file_sha256']
    assert len(report['rows']) == len(plan['cases']) == 9
    expected_names = {'normalized.json', 'status.json', 'publication.json'}
    for i, (row, case) in enumerate(zip(report['rows'], plan['cases'], strict=True)):
        assert row['case'] == case and row['original_summaries_reproduced'] is True
        old_raw = (root / (BASE + 'two-named-arenas-decisions/' + case['path'])).read_bytes()
        assert sha(old_raw) == old_hashes[case['path']]
        old = json.loads(old_raw)
        calls = row['calls']
        for j, call in enumerate(calls):
            name = f'raw/{i:02d}/{j:03d}.json'
            expected_names.add(name)
            raw = json.loads(files[name])
            assert raw['returncode'] == 0 and raw['phase'] == call['phase']
            assert raw['issued_limit'] == call['issued_limit'] and raw['prefix'] == call['prefix']
            assert raw['forced'] == call.get('forced')
            if call['phase'] in ('preliminary', 'probe'):
                assert raw['argv_options'] == []
                assert raw['stdin'] == ' '.join([call['phase'], case['fen'], str(call['issued_limit']), *call['prefix']]) + '\n'
                parsed = raw_probe(raw['stdout'])
                assert raw['stdout'].split('\t')[2] == case['fen']
            else:
                assert raw['argv_options'] == ['--initial-only', '--record-depth-ceiling']
                assert raw['stdin'] == ' '.join([case['fen'], str(call['issued_limit']), *call['prefix']]) + '\n'
                parsed = raw_main(raw['stdout'])
                assert parsed == row['main'][call['phase']]
            assert parsed == call['receipt']
        first = calls[0]['receipt']
        native = first['native_order']
        probes = [c for c in calls if c['phase'] == 'probe']
        assert [c['receipt']['move'] for c in probes] == native
        scores = {c['receipt']['move']: c['receipt']['score'] for c in probes}
        best = max(scores.values())
        assert scores[first['winner']] == first['score'] == best
        tied = [move for move in native if scores[move] == best]
        selected = tied[0] if len(tied) > 1 and tied[0] != first['winner'] else None
        v = row['verification']
        assert selected == case['reported_intervention'] == v['intervention'] and selected is not None
        assert all(v[k] == old[k] for k in v)
        spent = sum(c['receipt']['nodes'] for c in calls if c['phase'] in ('preliminary', 'probe'))
        assert spent == case['verification_nodes'] == v['verification_nodes']
        residual = case['budget'] - spent
        for arm in ARMS:
            main = row['main'][arm]
            s = main['summary']
            assert s['depth_ceiling'] is False
            assert s['nodes'] == (residual if arm in ('control', 'LCB_residual', 'native_residual') else case['budget'])
            if arm in ('control', 'native_full', 'LCB_full'):
                key = {'control': 'control_main', 'native_full': 'native_baseline', 'LCB_full': 'lcb_baseline'}[arm]
                assert s == old[key]
        control = row['main']['control']
        assert control['attempts'][0]['best_move'] == selected
        assert next(a for a in control['attempts'] if a['depth'] == 2)['expected_order'][0] == selected
        assert row['actual_nodes_all_five_arms'] == spent + sum(row['main'][a]['summary']['nodes'] for a in ARMS)
    assert set(files) == expected_names
    total = sum(r['actual_nodes_all_five_arms'] for r in report['rows'])
    assert total == report['actual_nodes_all_five_arms'] == status['actual_nodes'] <= plan['max_total_search_nodes']
    assert report['raw_receipts_count'] == sum(len(r['calls']) for r in report['rows'])
    return report


def analyze(report):
    rows = []
    for r in report['rows']:
        mains = r['main']
        pairwise = {}
        for name, (left, right) in PAIRS.items():
            a, b = (mains[k]['summary'] for k in (left, right))
            pairwise[name] = {'same_nodes': a['nodes'] == b['nodes'],
                              'same_final_move': a['best_move'] == b['best_move'],
                              'depth_delta': a['completed_depth'] - b['completed_depth'],
                              'Jass_score_delta': a['score'] - b['score']}
        rows.append({'case': r['case'], 'fresh_preliminary_LCB_winner': r['calls'][0]['receipt']['winner'],
                     'fresh_selected_native_tie': r['verification']['intervention'],
                     'depth1_best': {k: v['attempts'][0]['best_move'] for k, v in mains.items()},
                     'depth2_first': {k: next(a for a in v['attempts'] if a['depth'] == 2)['expected_order'][0] for k, v in mains.items()},
                     'final': {k: v['summary'] for k, v in mains.items()}, 'pairs': pairwise,
                     'control_LCB_residual_convergence': convergence(mains['control'], mains['LCB_residual'])})
    summary = {name: {'contexts': len(rows),
                     'same_final_move': sum(r['pairs'][name]['same_final_move'] for r in rows),
                     'different_depth': sum(r['pairs'][name]['depth_delta'] != 0 for r in rows),
                     'different_Jass_score': sum(r['pairs'][name]['Jass_score_delta'] != 0 for r in rows),
                     'different_move_paths': [r['case']['path'] for r in rows if not r['pairs'][name]['same_final_move']]}
               for name in PAIRS}
    return {'schema': 'mtdp-mechanistic-residual-analysis-v1', 'scope': report['scope'],
            'unique_positions': len({r['case']['fen'] for r in rows}), 'contexts': len(rows),
            'fresh_depth1_intervention_and_depth2_propagation_verified': len(rows),
            'actual_nodes_per_execution': report['actual_nodes_all_five_arms'],
            'comparisons': summary, 'rows': rows,
            'limitations': ['same_three_positions_post_hoc_no_independent_efficacy_claim',
                            'Jass_scores_at_different_depths_are_not_Scan_regrets',
                            'nonintervened_depth_loss_case_is_outside_this_mask']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('root', 'archive7', 'archive61', 'output', 'proof'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args()
    plan = json.loads((a.root / (BASE + 'two-named-arenas-mechanistic-residual-plan.json')).read_bytes())
    files = [read_archive(path) for path in (a.archive7, a.archive61)]
    reports = [validate(a.root, f, plan) for f in files]
    assert files[0]['normalized.json'] == files[1]['normalized.json']
    assert files[0]['status.json'] == files[1]['status.json']
    # Check the whole raw envelope too: no other field, warning or stdout
    # difference may be hidden by semantic normalization.
    for name in files[0]:
        if not name.startswith('raw/'):
            continue
        envelopes = [json.loads(f[name]) for f in files]
        for envelope in envelopes:
            if envelope['phase'] not in ('preliminary', 'probe'):
                fields = envelope['stdout'].split('\t')
                fields[7] = '<elapsed>'
                envelope['stdout'] = '\t'.join(fields)
        assert envelopes[0] == envelopes[1]
    result = analyze(reports[0])
    encoded = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    with a.output.open('xb') as stream:
        stream.write(encoded)
    proof = {'schema': 'mtdp-mechanistic-raw-independent-verification-v1',
             'normalized_sha256': sha(files[0]['normalized.json']), 'results_sha256': sha(encoded),
             'hash_seeds': [7, 61], 'normalized_byte_identical': True,
             'all_raw_envelopes_identical_except_main_elapsed': True,
             'actual_nodes_both_executions': sum(r['actual_nodes_all_five_arms'] for r in reports),
             'all_raw_receipts_and_original_summaries_checked': True,
             'raw_archive_sha256': {str(seed): sha(path.read_bytes()) for seed, path in ((7, a.archive7), (61, a.archive61))},
             'raw_file_sha256': {str(seed): {n: sha(v) for n, v in sorted(f.items())} for seed, f in zip((7, 61), files, strict=True)}}
    with a.proof.open('x') as stream:
        stream.write(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'contexts': result['contexts'], 'unique_positions': result['unique_positions'],
                      'comparisons': result['comparisons']}, sort_keys=True))


if __name__ == '__main__':
    main()
