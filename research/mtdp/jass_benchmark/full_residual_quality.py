"""Fixed Scan16 reconciliation of all archived residual controls; zero engine calls.

Implementation must be published before loading the target packet. All original
points and intervals are reproduced before supplementary contrasts are emitted.
"""
import argparse
import copy
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark import full_frozen_residual_analysis as raw
from research.mtdp.jass_benchmark import two_arena_analysis as original
from research.mtdp.jass_benchmark.depth_sensitivity import regret
from research.mtdp.top_k_transfer import _action

BASE = raw.BASE
MODULE = 'research/mtdp/jass_benchmark/full_residual_quality.py'
PLAN = BASE + 'full-frozen-residual-quality-plan.json'
DATA_COMMIT = '176340e4971b1dba6de626447f9e8e00fb27b023'
FREEZE = '3fa9a56a3fa60954d5391d7e1b302c07e04f1f04'
CONTRASTS = {'control_minus_LCB_residual': ('control', 'LCB_residual'),
             'control_minus_native_residual': ('control', 'native_residual'),
             'LCB_residual_minus_LCB_full': ('LCB_residual', 'LCB_full'),
             'native_residual_minus_native_full': ('native_residual', 'native_full')}
LEGACY = {'native': 'native_full', 'lcb': 'LCB_full', 'control': 'control'}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pinned(root, commit, path, expected=None):
    b = (root / path).read_bytes()
    if b != original.runtime._blob(root, commit, path) or expected is not None and sha(b) != expected:
        raise ValueError('Published input or digest changed: ' + path)
    return b


def gate(root, commit):
    """Publication, ancestry and all input hashes checked before target access."""
    if Path(__file__).resolve() != (root / MODULE).resolve():
        raise ValueError('Imported implementation is outside the selected checkout')
    subprocess.run(['git', '-C', str(root), 'fetch', 'origin', 'research/mtdp-foundation'], check=True, capture_output=True)
    for a, b in ((DATA_COMMIT, commit), (commit, 'origin/research/mtdp-foundation')):
        subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', a, b], check=True)
    pinned(root, commit, MODULE)
    plan = json.loads(pinned(root, DATA_COMMIT, PLAN))
    if plan['engine_calls_allowed'] != 0 or plan['new_independent_cohort'] is not False:
        raise ValueError('No-engine existing-cohort scope changed')
    pinned(root, DATA_COMMIT, raw.__name__.replace('.', '/') + '.py')
    pinned(root, DATA_COMMIT, original.MODULE, plan['parent_analysis_sha256'])
    pinned(root, DATA_COMMIT, BASE + 'full-frozen-residual-results.json', plan['parent_results_sha256'])
    control_plan = json.loads(pinned(root, DATA_COMMIT, BASE + 'full-frozen-residual-control-plan.json'))
    norms = []
    for seed in ('7', '61'):
        path = BASE + f'full-frozen-residual-raw-seed{seed}.tar.gz'
        pinned(root, DATA_COMMIT, path, plan['parent_raw_archive_sha256'][seed])
        files = raw.read_archive(root / path)
        raw.validate(root, files, control_plan)
        if sha(files['normalized.json']) != plan['parent_normalized_sha256']:
            raise ValueError('Normalized decisions changed')
        norms.append(json.loads(files['normalized.json']))
    if norms[0] != norms[1]:
        raise ValueError('Replicate decisions differ')
    return plan, norms[0]


def compare_arms(main, scores, actions):
    """Never subtract categorical scores; retain ties and every arm."""
    if set(main) != set(raw.ARMS) or set(actions.values()) != set(scores):
        raise ValueError('Incomplete arms or target action mapping')
    best = max(scores.values())
    return {a: {'move': m['summary']['best_move'],
                'score': scores[actions[m['summary']['best_move']]],
                **regret(best, scores[actions[m['summary']['best_move']]])}
            for a, m in main.items()}


def estimates(rows, population, fields):
    return {scope: {k: original.bootstrap(
        rows if scope == 'all' else [r for r in rows if r['event'] == scope],
        population if scope == 'all' else [r for r in population if r['event'] == scope], k)
        for k in fields} for scope in ('all', *original.runtime.study.EVENTS)}


def analyze(root, commit):
    plan, normalized = gate(root, commit)  # MUST precede reference packet read
    joint, proof = original.runtime.published(root, BASE + 'two-named-arenas-final', FREEZE)
    methods = original.runtime.method(root, FREEZE)
    target = json.loads(pinned(root, plan['reference_commit'], plan['reference_path'], plan['reference_sha256']))
    scores = original._reference(joint, proof, methods, target, 'target16')
    old = json.loads(pinned(root, plan['reference_commit'], BASE + 'two-named-arenas-results.json',
                            plan['parent_primary_results_sha256']))
    targets = {(e, t['target_fen']): t for e in original.runtime.study.EVENTS
               for t in joint['events'][e]['benchmark_targets']}
    population = [{'event': e, 'fen': f, 'owner': t['bootstrap_owner']} for (e, f), t in targets.items()]
    result = {'schema': 'mtdp-full-residual-quality-v1', 'analysis_commit': commit,
              'analysis_sha256': sha((root / MODULE).read_bytes()), 'plan_sha256': sha((root / PLAN).read_bytes()),
              'reference_sha256': plan['reference_sha256'], 'normalized_sha256': plan['parent_normalized_sha256'],
              'scope': plan['scope'], 'score_unit': plan['score_unit'], 'engine_calls': 0,
              'primary_budget': 50000, 'budgets': {}, 'original_estimates_exact': True}
    for budget in (10000, 50000, 200000):
        prior = old['budgets'][str(budget)]
        old_rows = {(r['event'], r['fen']): r for r in prior['rows']}
        rows, legacy = [], []
        for r in normalized['rows']:
            c = r['case']
            if c['budget'] != budget:
                continue
            key = c['event'], c['fen']; t = targets[key]; before = old_rows[key]
            if c['owner'] != t['bootstrap_owner'] or not before['paired']:
                raise ValueError('Ownership or primary eligibility changed')
            actions = {m['jass_key']: _action(m) for m in t['legal_moves']}
            arms = compare_arms(r['main'], scores[c['fen']], actions)
            row = {'event': c['event'], 'fen': c['fen'], 'owner': c['owner'], 'arms': arms,
                   'best_reference_score': max(scores[c['fen']].values()),
                   'optimal_moves': sorted(k for k, a in actions.items() if scores[c['fen']][a] == max(scores[c['fen']].values())),
                   'total_budget': budget, 'verification_nodes': c['verification_nodes'],
                   'main_nodes': {a: r['main'][a]['summary']['nodes'] for a in raw.ARMS}}
            for a in raw.ARMS:
                row[a + '_regret'] = arms[a]['ordinary_regret_centimen']
                row[a + '_optimal'] = int(arms[a]['covered'])
            for name, (a, b) in CONTRASTS.items():
                x, y = row[a + '_regret'], row[b + '_regret']
                row[name] = x - y if x is not None and y is not None else None
            restored = copy.deepcopy(before)
            for old_arm, arm in LEGACY.items():
                if arms[arm] != before['arms'][old_arm]:
                    raise ValueError('Original arm score, action or category not reproduced')
                restored['arms'][old_arm] = arms[arm]
                restored[old_arm + '_regret'] = row[arm + '_regret']
                restored[old_arm + '_optimal'] = row[arm + '_optimal']
            for comparator in ('native', 'lcb'):
                x, y = restored['control_regret'], restored[comparator + '_regret']
                restored['control_minus_' + comparator] = x-y if x is not None and y is not None else None
            if restored != before:
                raise ValueError('Original row not reproduced')
            legacy.append(restored); rows.append(row)
        if len(rows) != 38 or len({r['fen'] for r in rows}) != 38:
            raise ValueError('Full frozen frame required')
        fields = ('native_regret', 'lcb_regret', 'control_regret', 'control_minus_native', 'control_minus_lcb')
        boot = estimates(legacy, population, fields)
        for scope, observed in boot.items():
            chosen = legacy if scope == 'all' else [r for r in legacy if r['event'] == scope]
            reconstructed = {'planned': len(chosen), 'paired': len(chosen), 'depth_ceiling_excluded': 0,
                'control_native_agreement': sum(r['control_native_agreement'] for r in chosen),
                'optimum_hits_paired': {a: sum(r[a+'_optimal'] or 0 for r in chosen) for a in LEGACY}, 'bootstrap': observed}
            if reconstructed != prior['estimates'][scope]:
                raise ValueError('Original points or intervals not reproduced: ' + scope)
        new_fields = [a + '_regret' for a in raw.ARMS] + list(CONTRASTS)
        result['budgets'][str(budget)] = {'rows': rows, 'bootstrap': estimates(rows, population, new_fields),
            'optimum_hits': {a: sum(r[a + '_optimal'] for r in rows) for a in raw.ARMS},
            'category_transitions': {a: dict(Counter(r['arms'][a]['best_category'] + '/' + r['arms'][a]['candidate_category'] for r in rows)) for a in raw.ARMS},
            'original_estimates_reproduced': prior['estimates']}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--analysis-commit', required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    result = analyze(a.root.resolve(), a.analysis_commit)
    with a.output.open('xb') as stream:
        stream.write(original.runtime._bytes(result))
    print(json.dumps({'original_estimates_exact': result['original_estimates_exact'],
                      'primary': result['budgets']['50000']['bootstrap']['all']}, sort_keys=True))


if __name__ == '__main__':
    main()
