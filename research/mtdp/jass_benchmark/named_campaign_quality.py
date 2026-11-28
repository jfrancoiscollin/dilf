"""Registered named-arena quality audit; keep every target and budget visible."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from research.mtdp.best_move_audit import compare_scores
from research.mtdp.jass_benchmark.named_arena_execution import published_manifest, execution_fingerprints, expected_actions
from research.mtdp.jass_benchmark.named_metered_campaign import source_scores
from research.mtdp.jass_benchmark.depth_sensitivity import validate_reference, regret
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest
from research.mtdp.top_k_transfer import _action

ARMS = {'native': 'native_baseline', 'lcb': 'lcb_baseline', 'control': 'control_main'}


def bootstrap(values):
    groups = defaultdict(list)
    for game, value in values:
        groups[game].append(value)
    units = [(sum(v), len(v)) for _, v in sorted(groups.items())]
    result = {'positions': len(values), 'games': len(units), 'resamples': 10000, 'seed': 20261113,
              'mean': fmean(v for _, v in values) if values else None, 'ci95': None}
    if len(units) < 2:
        return result
    rng = random.Random(20261113); distribution = []
    for _ in range(10000):
        selected = rng.choices(units, k=len(units))
        distribution.append(sum(s for s, n in selected) / sum(n for s, n in selected))
    distribution.sort()
    result['ci95'] = [distribution[int(9999 * q)] for q in (0.025, 0.975)]
    return result


def check_receipt(row, target, budget, prefix):
    if (row['fen'] != target['target_fen'] or row['games'] != target['target_games']
            or row['budget'] != budget or row['LCB_prefix'] != prefix
            or row['native_legal_actions'] != len(target['legal_moves'])):
        raise ValueError('Decision identity, prefix or legal count changed')
    spent = 0
    for call in row['verification_receipts']:
        if (type(call['nodes']) is not int or call['issued_limit'] != budget // 10 - spent
                or not 0 <= call['nodes'] <= call['issued_limit']):
            raise ValueError('Invalid verification accounting')
        spent += call['nodes']
    if (spent != row['verification_nodes'] or spent > budget // 10
            or row['main_limit'] != budget - spent or row['main_nodes'] != row['control_main']['nodes']):
        raise ValueError('Control did not account for the complete total budget')
    keys = {m['jass_key'] for m in target['legal_moves']}
    paired = True
    for label, field in ARMS.items():
        r = row[field]; limit = budget - spent if label == 'control' else budget
        if (r['best_move'] not in keys or type(r['nodes']) is not int or not 0 <= r['nodes'] <= limit
                or type(r['depth_ceiling']) is not bool
                or (r['depth_ceiling'] and r['nodes'] == limit)
                or (not r['depth_ceiling'] and r['nodes'] != limit)):
            raise ValueError('Illegal winner, unaccounted nodes or false ceiling')
        paired &= not r['depth_ceiling']
    if row['paired_comparable'] != paired or row['complete_budget'] != (not row['control_main']['depth_ceiling']):
        raise ValueError('Pairing flag disagrees with actual node receipts')
    return paired


def analyze(root, directory, commit, source_path, target_path, receipts):
    manifest, proof = published_manifest(root, directory, commit)
    source_raw, target_raw = source_path.read_bytes(), target_path.read_bytes()
    method = execution_fingerprints(root, commit)
    source = source_scores(manifest, proof, json.loads(source_raw), method)
    reference = json.loads(target_raw)
    if (reference.get('role') != 'target' or reference.get('publication_verification', {}).get('published_commit') != commit
            or reference.get('publication_verification', {}).get('scientific_freeze') is not True
            or reference.get('execution_sha256') != method or reference.get('scan_ini_sha256') != SCAN_INI_SHA256):
        raise ValueError('Target reference is not from the same published freeze')
    scores = validate_reference(reference, expected_actions(manifest, 'target'),
                                {'scan_linux': manifest['engine']['scan_binary_sha256'], 'data/eval': SCAN_EVAL_SHA256},
                                proof['manifest_sha256'], 16)
    complete = json.loads((receipts / 'complete.json').read_bytes())
    targets = sorted(manifest['benchmark_targets'], key=lambda r: r['target_fen'])
    if (complete.get('complete') is not True or complete['publication_verification']['published_commit'] != commit
            or complete['publication_verification']['manifest_sha256'] != proof['manifest_sha256']
            or complete['source_sha256'] != digest(source_raw) or complete['planned_targets'] != len(targets)
            or complete['budgets'] != [10000, 50000, 200000]):
        raise ValueError('Incomplete or foreign decision campaign')
    geometry = {arm: [] for arm in ('L', 'LCB')}
    for t in targets:
        for arm in geometry:
            geometry[arm].append({'fen': t['target_fen'], 'games': t['target_games'],
                                  **compare_scores(source[t['source_fens'][arm]], scores[t['target_fen']])})
    budgets = {}
    for budget in (10000, 50000, 200000):
        files = sorted((receipts / str(budget)).glob('*.json'))
        if len(files) != len(targets) or [f.name for f in files] != [f'{i:05d}.json' for i in range(len(targets))]:
            raise ValueError('Missing or extra decision receipts')
        rows, differences = [], {arm: [] for arm in ('native', 'lcb')}
        for path, t in zip(files, targets, strict=True):
            r = json.loads(path.read_bytes())
            prefix = candidate_lists(t['legal_moves'], source[t['source_fens']['LCB']])[1]['transfer']
            paired = check_receipt(r, t, budget, prefix)
            by_key = {m['jass_key']: _action(m) for m in t['legal_moves']}
            target_scores = scores[t['target_fen']]; best = max(target_scores.values())
            arms = {a: {'move': r[field]['best_move'], 'score': target_scores[by_key[r[field]['best_move']]],
                         **regret(best, target_scores[by_key[r[field]['best_move']]])} for a, field in ARMS.items()}
            if paired:
                for comparator in differences:
                    x, y = arms['control']['ordinary_regret_centimen'], arms[comparator]['ordinary_regret_centimen']
                    if x is not None and y is not None:
                        differences[comparator].append((min(t['target_games']), x - y))
            rows.append({'fen': t['target_fen'], 'games': t['target_games'], 'paired': paired, 'arms': arms,
                         'verification_nodes': r['verification_nodes'], 'intervention': r['intervention'],
                         'decision_reason': r['decision_reason']})
        ordinary = lambda arm: [r['arms'][arm]['ordinary_regret_centimen'] for r in rows if r['paired'] and r['arms'][arm]['ordinary_regret_centimen'] is not None]
        budgets[str(budget)] = {'planned': len(rows), 'paired': sum(r['paired'] for r in rows),
            'optimum_hits_paired': {a: sum(r['paired'] and r['arms'][a]['covered'] for r in rows) for a in ARMS},
            'ordinary_regret_paired': {a: {'n': len(ordinary(a)), 'mean': fmean(ordinary(a)) if ordinary(a) else None} for a in ARMS},
            'control_minus_native': bootstrap(differences['native']), 'control_minus_lcb': bootstrap(differences['lcb']),
            'ceiling_excluded': sum(not r['paired'] for r in rows),
            'optimum_hits_paired': {a: sum(r['paired'] and r['arms'][a]['covered'] for r in rows) for a in ARMS},
            'ordinary_regret_paired': {a: {'n': len(ordinary(a)), 'mean': fmean(ordinary(a)) if ordinary(a) else None} for a in ARMS},
            'control_minus_native': bootstrap(differences['native']), 'control_minus_lcb': bootstrap(differences['lcb']),
            'verification_nodes_mean': fmean(r['verification_nodes'] for r in rows) if rows else None,
            'verified_interventions': sum(r['intervention'] is not None for r in rows),
            'control_native_agreement': sum(r['arms']['control']['move'] == r['arms']['native']['move'] for r in rows),
            'changed_choice_cases': [r for r in rows if r['arms']['control']['move'] != r['arms']['native']['move']], 'rows': rows}
    return {'schema': 'mtdp-named-campaign-quality-v1', 'event': manifest['event'], 'published_commit': commit,
            'manifest_sha256': proof['manifest_sha256'], 'source_sha256': digest(source_raw), 'target_sha256': digest(target_raw),
            'primary_budget': 50000, 'scope': 'one_preregistered_named_arena_no_tournament_generality_or_Elo',
            'score_unit': 'integer Scan reference unit = 0.01 HUB, not a fixed material-man valuation',
            'bootstrap_owner': 'lexicographically smallest frozen target game ID; whole-game resampling',
            'geometry_source12_target16_descriptive': geometry, 'budgets': budgets}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'source', 'target', 'receipts', 'output'):
        p.add_argument(f'--{name}', type=Path, required=True)
    p.add_argument('--directory', required=True); p.add_argument('--commit', required=True)
    a = p.parse_args(); report = analyze(a.root, a.directory, a.commit, a.source, a.target, a.receipts)
    with a.output.open('xb') as f: f.write(_bytes(report))
    print(json.dumps({b: {k:r[k] for k in ('paired', 'optimum_hits_paired', 'control_minus_native')} for b,r in report['budgets'].items()}, sort_keys=True))


if __name__ == '__main__': main()
