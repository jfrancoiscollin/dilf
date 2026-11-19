"""Independent stdlib recalculation from archived decisions and Scan vectors."""
import argparse
import hashlib
import json
import random
import tarfile
from collections import defaultdict, Counter
from pathlib import Path
from statistics import fmean

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
EVENTS = ('s7ahYqL4', 'D9PF2OSW')
ARMS = ('control', 'native_full', 'LCB_full', 'LCB_residual', 'native_residual')
PAIRS = {'control_minus_LCB_residual': ('control', 'LCB_residual'),
         'control_minus_native_residual': ('control', 'native_residual'),
         'LCB_residual_minus_LCB_full': ('LCB_residual', 'LCB_full'),
         'native_residual_minus_native_full': ('native_residual', 'native_full')}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def boot(rows, frame, field):
    owners = {e: sorted({r['owner'] for r in frame if r['event'] == e}) for e in EVENTS}
    grouped = defaultdict(list)
    for r in rows:
        if r[field] is not None:
            grouped[r['event'], r['owner']].append(r[field])
    values = [v for vs in grouped.values() for v in vs]
    rng = random.Random(20261113); samples = []
    for _ in range(10000):
        selected = []
        for e in EVENTS:
            for g in rng.choices(owners[e], k=len(owners[e])):
                selected.extend(grouped[e, g])
        if selected:
            samples.append(sum(selected) / len(selected))
    samples.sort()
    return {'positions': len(values), 'owner_games': sum(bool(v) for v in grouped.values()),
        'sampling_owner_games': {e: len(gs) for e, gs in owners.items()},
        'mean': fmean(values) if values else None, 'resamples': 10000, 'seed': 20261113,
        'percentile_indices': [249, 9749], 'undefined_draws': 10000-len(samples),
        'ci95': [samples[249], samples[9749]] if len(samples) == 10000 and sum(map(len, owners.values())) > 1 else None}


def action(a):
    return tuple(a[0]), tuple(a[1]), a[2]


def category(score):
    return 'win' if score > 8000 else 'loss' if score < -8000 else 'ordinary'


def verify(root, report):
    plan = json.loads((root / (BASE + 'full-frozen-residual-quality-plan.json')).read_bytes())
    reference_raw = (root / plan['reference_path']).read_bytes()
    assert digest(reference_raw) == plan['reference_sha256'] == report['reference_sha256']
    manifest = json.loads((root / (BASE + 'two-named-arenas-final/manifest.json')).read_bytes())
    targets = {(e, t['target_fen']): t for e in EVENTS for t in manifest['events'][e]['benchmark_targets']}
    frame = [{'event': e, 'fen': f, 'owner': t['bootstrap_owner']} for (e, f), t in targets.items()]
    assert len(frame) == 38 and len({(r['event'], r['owner']) for r in frame}) == 31
    scores = json.loads(reference_raw)['action_scores_centimen']
    raw = (root / (BASE + 'full-frozen-residual-raw-seed7.tar.gz')).read_bytes()
    assert digest(raw) == plan['parent_raw_archive_sha256']['7']
    with tarfile.open(root / (BASE + 'full-frozen-residual-raw-seed7.tar.gz')) as tar:
        normalized_raw = tar.extractfile('normalized.json').read()
    assert digest(normalized_raw) == plan['parent_normalized_sha256'] == report['normalized_sha256']
    normalized = json.loads(normalized_raw)['rows']; assert len(normalized) == 114
    ci_count = cells = 0
    legacy_names = {'native': 'native_full', 'lcb': 'LCB_full', 'control': 'control'}
    for budget in (10000, 50000, 200000):
        table = report['budgets'][str(budget)]; observed = {(r['event'], r['fen']): r for r in table['rows']}
        assert len(table['rows']) == len(observed) == 38 and set(observed) == set(targets)
        rebuilt = []
        for n in normalized:
            c = n['case']
            if c['budget'] != budget:
                continue
            key = c['event'], c['fen']; row = observed[key]; target = targets[key]
            assert row['owner'] == target['bootstrap_owner'] == c['owner']
            vector = {action(v['action']): v['score'] for v in scores[c['fen']]}
            actions = {m['jass_key']: action(m['action']) for m in target['legal_moves']}
            assert set(actions.values()) == set(vector)
            best = max(vector.values()); r = {'event': c['event'], 'fen': c['fen'], 'owner': c['owner']}
            assert row['best_reference_score'] == best
            assert row['optimal_moves'] == sorted(k for k, a in actions.items() if vector[a] == best)
            for a in ARMS:
                move = n['main'][a]['summary']['best_move']; score = vector[actions[move]]
                bc, cc = category(best), category(score)
                cost = best-score if bc == cc == 'ordinary' else None
                assert row['arms'][a] == {'move': move, 'score': score, 'best_category': bc,
                    'candidate_category': cc, 'ordinary_regret_centimen': cost, 'covered': score == best}
                r[a+'_regret'] = cost; r[a+'_optimal'] = int(score == best); cells += 1
            for name, (a, b) in PAIRS.items():
                x, y = r[a+'_regret'], r[b+'_regret']
                r[name] = x-y if x is not None and y is not None else None
            for field, v in r.items():
                assert row[field] == v
            rebuilt.append(r)
        for a in ARMS:
            assert table['optimum_hits'][a] == sum(r[a+'_optimal'] for r in rebuilt)
            assert table['category_transitions'][a] == dict(Counter(row['arms'][a]['best_category']+'/'+row['arms'][a]['candidate_category'] for row in observed.values()))
        fields = [a+'_regret' for a in ARMS]+list(PAIRS)
        for scope in ('all', *EVENTS):
            rows = rebuilt if scope == 'all' else [r for r in rebuilt if r['event'] == scope]
            population = frame if scope == 'all' else [r for r in frame if r['event'] == scope]
            for field in fields:
                assert boot(rows, population, field) == table['bootstrap'][scope][field]
                ci_count += 1
            old = table['original_estimates_reproduced'][scope]
            assert old['planned'] == old['paired'] == len(rows) and old['depth_ceiling_excluded'] == 0
            assert old['control_native_agreement'] == len(rows)
            assert old['optimum_hits_paired'] == {a: sum(r[b+'_optimal'] for r in rows) for a, b in legacy_names.items()}
            for r in rows:
                for a, b in legacy_names.items():
                    r[a+'_regret'] = r[b+'_regret']
                r['control_minus_native'] = r['control_regret']-r['native_regret']
                r['control_minus_lcb'] = r['control_regret']-r['lcb_regret']
            for field, value in old['bootstrap'].items():
                assert boot(rows, population, field) == value
                ci_count += 1
    return {'schema': 'mtdp-full-residual-quality-independent-v1', 'arm_cells_recomputed': cells,
            'bootstrap_estimates_recomputed': ci_count, 'all_equal': True,
            'report_sha256': digest((json.dumps(report, sort_keys=True, indent=2)+'\n').encode()),
            'reference_sha256': digest(reference_raw), 'engine_calls': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'report', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); result = verify(a.root, json.loads(a.report.read_bytes()))
    with a.output.open('xb') as f:
        f.write((json.dumps(result, sort_keys=True, indent=2)+'\n').encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
