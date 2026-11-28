"""Post-hoc crossed-depth decomposition; archived vectors only, no engine or fit."""
import argparse
import json
from collections import Counter
from pathlib import Path

from research.mtdp.jass_benchmark import two_arena_depth20 as depth

BASE = depth.BASE
PLAN_COMMIT = '0a7b0e8cda8da5985298b500f7f9b2a276379fe5'
ARCHIVE_COMMIT = '5fe7c88e562ae7be79f1f6839f4a6226a220ec4b'
DEPTH20_SHA = '6076aba12d4e3427b33c6bc9c6ee101c57df1a99109b3638339c1e3570709f90'
PLAN_SHA = 'c5c0a23506956968046c4c54888f39b41665970cd69d9294b647b6d5d7b6f1ee'
SCOPE = 'post_hoc_crossed_depth_same_26_pairs_no_new_independent_cohort_or_causal_claim'
CELLS = ('S16_T16', 'S16_T20', 'S20_T16', 'S20_T20')
EFFECTS = ('target_at_source16', 'source_at_target20', 'source_at_target16',
           'target_at_source20', 'matched_total', 'interaction')


def archived(root, commit, name, sha=None):
    """Offline replay: demand the exact previously published bytes, fail closed."""
    path = BASE + name
    raw = (root / path).read_bytes()
    if raw != depth.runtime._blob(root, commit, path):
        raise ValueError(f'Archived input changed: {name}')
    digest = depth.runtime.digest(raw)
    if sha is not None and digest != sha:
        raise ValueError(f'Pinned input digest changed: {name}')
    return json.loads(raw), digest


def crossed_rows(selected, sources, targets):
    cells = {f'S{s}_T{t}': depth.compared_rows(selected, sources[s], targets[t])
             for s in (16, 20) for t in (16, 20)}
    result = []
    for case in zip(*(cells[k] for k in CELLS), strict=True):
        a, b, c, d = case
        identity = {(r['event'], r['fen'], r['source_fen'], r['owner']) for r in case}
        if len(identity) != 1:
            raise ValueError('Crossed-depth pair or ownership changed')
        # Every difference uses the SAME all-four-ordinary denominator. This
        # prevents a spurious additive identity between different subgroups.
        values = [r['ordinary_regret'] for r in case]
        eligible = all(v is not None for v in values)
        effects = dict.fromkeys(EFFECTS)
        if eligible:
            aa, bb, cc, dd = values
            effects = dict(zip(EFFECTS, (bb-aa, dd-bb, cc-aa, dd-cc, dd-aa, dd-bb-cc+aa)))
            if effects['target_at_source16'] + effects['source_at_target20'] != effects['matched_total']:
                raise ValueError('Forward path identity failed')
            if effects['source_at_target16'] + effects['target_at_source20'] != effects['matched_total']:
                raise ValueError('Reverse path identity failed')
        result.append({'event': a['event'], 'fen': a['fen'], 'owner': a['owner'],
                       'source_pick_changed': a['optimal_a'][0] != c['optimal_a'][0],
                       'all_four_ordinary': eligible, 'cells': dict(zip(CELLS, case)), **effects})
    return result


def summarize(rows, population):
    return {
        'positions': len(rows),
        'all_four_ordinary_positions': sum(r['all_four_ordinary'] for r in rows),
        'source_pick_changes': sum(r['source_pick_changed'] for r in rows),
        'cell_category_patterns': dict(Counter('|'.join(
            r['cells'][k]['a_to_b']['best_category'] + '/' +
            r['cells'][k]['a_to_b']['transferred_category'] for k in CELLS) for r in rows)),
        'cells': {k: depth.analysis._summary_geometry([r['cells'][k] for r in rows], population)
                  for k in CELLS},
        'effects_same_all_four_ordinary_mask': {
            k: depth.analysis.bootstrap(rows, population, k) for k in EFFECTS},
    }


def analyze(root):
    # All pins resolve offline. No published_plan(), HTTP or Scan invocation.
    joint, manifest_sha = archived(root, depth.FREEZE, 'two-named-arenas-final/manifest.json',
                                  'c079ca061d3645b42ce93235854e032de2be43a4cb08d8cea5ddbc1d92f1b5aa')
    old, _ = archived(root, depth.RESULT_COMMIT, 'two-named-arenas-results.json', depth.RESULT_SHA)
    newer, _ = archived(root, ARCHIVE_COMMIT, 'two-named-arenas-depth20-results.json', DEPTH20_SHA)
    plan, plan_sha = archived(root, PLAN_COMMIT, 'two-named-arenas-depth20-plan.json', PLAN_SHA)
    for name, sha in plan['method_files_sha256'].items():
        if depth.runtime.digest((root / name).read_bytes()) != sha:
            raise ValueError(f'Published analysis dependency changed: {name}')
    selected, flat, identity = depth.subset(joint)
    if identity != plan['pairs'] or depth.runtime.digest(depth.runtime._bytes(identity)) != plan['mask_sha256']:
        raise ValueError('Previously frozen mask, sources or mappings changed')
    methods = depth.runtime.method(root, depth.FREEZE)
    proof = {'published_commit': depth.FREEZE, 'manifest_sha256': manifest_sha}
    sources, targets, hashes = {}, {}, {}
    for role, output in (('source', sources), ('target', targets)):
        name16 = f'two-named-arenas-{role}16.json'
        p16, hashes[name16] = archived(root, depth.RESULT_COMMIT, name16, old[f'{role}16_sha256'])
        output[16] = depth.analysis._reference(joint, proof, methods, p16, role+'16')
        name20 = f'two-named-arenas-{role}20-exploratory.json'
        p20, hashes[name20] = archived(root, ARCHIVE_COMMIT, name20, newer[f'{role}20_sha256'])
        output[20] = depth.validate_packet(p20, role, plan, plan_sha, PLAN_COMMIT, flat)
    rows = crossed_rows(selected, sources, targets)
    population = [{'event': e, 'fen': t['target_fen'], 'owner': t['bootstrap_owner']}
                  for e in depth.runtime.study.EVENTS for t in joint['events'][e]['benchmark_targets']]
    estimates = {}
    for scope in ('all', *depth.runtime.study.EVENTS):
        chosen = rows if scope == 'all' else [r for r in rows if r['event'] == scope]
        frame = population if scope == 'all' else [r for r in population if r['event'] == scope]
        estimates[scope] = summarize(chosen, frame)
        # Byte-pinned matched-depth results must be reproduced exactly, CIs included.
        for key, expected in (
            ('S16_T16', old['geometry']['LCB']['estimates'][scope]['LCB_full_equal']),
            ('S20_T20', newer['summaries'][scope]['Scan20']),
        ):
            if estimates[scope]['cells'][key] != expected:
                raise ValueError('A previously reported matched-depth result changed')
    return {'schema': 'mtdp-two-arena-crossed-depth-v1', 'scope': SCOPE,
            'new_independent_cohort': False, 'new_engine_searches': 0,
            'primary_results_unchanged': True, 'parent_freeze_commit': depth.FREEZE,
            'parent_primary_results_commit': depth.RESULT_COMMIT,
            'parent_depth20_archive_commit': ARCHIVE_COMMIT,
            'input_sha256': hashes, 'mask_sha256': plan['mask_sha256'],
            'score_unit': old['score_unit'], 'bootstrap_scope': old['bootstrap_scope'],
            'effect_denominator': 'all_four_ordinary_pairs_only_no_categorical_subtraction',
            'rows': rows, 'estimates': estimates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    with args.output.open('xb') as stream:
        stream.write(depth.runtime._bytes(report))
    print(json.dumps({'scope': SCOPE, 'positions': len(report['rows']), 'new_engine_searches': 0}))


if __name__ == '__main__':
    main()
