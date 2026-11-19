"""Independent stdlib-only recomputation from archived raw vectors (no analysis imports)."""
import argparse
import hashlib
import json
import random
from pathlib import Path
from statistics import fmean

EVENTS = ('s7ahYqL4', 'D9PF2OSW')
CELLS = ('S16_T16', 'S16_T20', 'S20_T16', 'S20_T20')
EFFECTS = ('target_at_source16', 'source_at_target20', 'source_at_target16',
           'target_at_source20', 'matched_total', 'interaction')
BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication'


def action(row):
    return (tuple(row['action'][0]), tuple(row['action'][1]), row['action'][2])


def verify(root, report_path):
    base = root / BASE
    report_raw = report_path.read_bytes()
    report = json.loads(report_raw)
    manifest = json.loads((base / 'two-named-arenas-final/manifest.json').read_bytes())
    packets = {}
    for name, expected in report['input_sha256'].items():
        raw = (base / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
        p = json.loads(raw)
        packets[(p['role'], p['scan_successor_depth'])] = {
            fen: {action(a): a['score'] for a in vec} for fen, vec in p['action_scores_centimen'].items()}
    frozen = [(e, t) for e in EVENTS for t in manifest['events'][e]['benchmark_targets']]
    selected = [(e, t) for e, t in frozen if t['same_full_quiet_signature']['LCB']]
    assert len(selected) == len(report['rows']) == 26
    rows = []
    for (event, t), emitted in zip(selected, report['rows'], strict=True):
        assert (emitted['event'], emitted['fen'], emitted['owner']) == (event, t['target_fen'], t['bootstrap_owner'])
        row = {'event': event, 'owner': t['bootstrap_owner']}
        costs, picks = [], []
        for key in CELLS:
            sd, td = map(int, (key[1:3], key[5:7]))
            s = packets['source', sd][t['source_fens']['LCB']]
            d = packets['target', td][t['target_fen']]
            assert s.keys() == d.keys()
            src_opt = sorted(a for a in s if s[a] == max(s.values()))
            dst_opt = sorted(a for a in d if d[a] == max(d.values()))
            chosen = src_opt[0]
            b, v = max(d.values()), d[chosen]
            category = lambda value: 'win' if value > 8000 else 'loss' if value < -8000 else 'ordinary'
            cost = b-v if category(b) == category(v) == 'ordinary' else None
            r = emitted['cells'][key]
            assert r['a_to_b']['best_category'] == category(b)
            assert r['a_to_b']['transferred_category'] == category(v)
            assert r['optimal_a'] == json.loads(json.dumps(src_opt))
            assert r['optimal_b'] == json.loads(json.dumps(dst_opt))
            assert r['a_to_b']['best_centimen'] == b and r['a_to_b']['transferred_centimen'] == v
            expected = {'ordinary_regret': cost, 'positive_regret': cost if cost is not None and cost > 0 else None,
                        'disjoint': int(not set(src_opt).intersection(dst_opt)), 'pick_optimal': int(v == b)}
            for field, value in expected.items():
                assert r[field] == value
                row[key + ':' + field] = value
            costs.append(cost)
            picks.append(chosen)
        assert emitted['source_pick_changed'] == (picks[0] != picks[2])
        eligible = all(x is not None for x in costs)
        assert emitted['all_four_ordinary'] == eligible
        effects = [None] * 6
        if eligible:
            a, b, c, d = costs
            effects = [b-a, d-b, c-a, d-c, d-a, d-b-c+a]
            assert effects[0] + effects[1] == effects[2] + effects[3] == effects[4]
        for field, value in zip(EFFECTS, effects, strict=True):
            assert emitted[field] == value
            row[field] = value
        rows.append(row)
    checked = {}
    for scope in ('all', *EVENTS):
        chosen = rows if scope == 'all' else [r for r in rows if r['event'] == scope]
        owners = {e: sorted({t['bootstrap_owner'] for ev, t in frozen if ev == e})
                  if scope in ('all', e) else [] for e in EVENTS}
        fields = [*EFFECTS, *(k + ':' + f for k in CELLS
                             for f in ('ordinary_regret', 'positive_regret', 'disjoint', 'pick_optimal'))]
        checked[scope] = {}
        for field in fields:
            values = [r[field] for r in chosen if r[field] is not None]
            # Draw game identities; expand all their rows. No production helpers
            # or precomputed group totals enter this independent calculation.
            by_owner = {(e, g): [r[field] for r in chosen if r['event'] == e and r['owner'] == g
                                 and r[field] is not None] for e in EVENTS for g in owners[e]}
            rng = random.Random(20261113)
            distribution = []
            for _ in range(10000):
                draw = [v for e in EVENTS for g in rng.choices(owners[e], k=len(owners[e]))
                        for v in by_owner[e, g]]
                if draw:
                    distribution.append(sum(draw) / len(draw))
            undefined = 10000-len(distribution)
            distribution.sort()
            ci = [distribution[249], distribution[9749]] if not undefined else None
            observed = report['estimates'][scope]
            expected = (observed['effects_same_all_four_ordinary_mask'][field] if field in EFFECTS
                        else observed['cells'][field.split(':')[0]]['bootstrap'][field.split(':')[1]])
            assert expected['positions'] == len(values)
            assert expected['mean'] == (fmean(values) if values else None)
            assert expected['undefined_draws'] == undefined and expected['ci95'] == ci
            checked[scope][field] = ci
    return {'schema': 'mtdp-crossed-depth-independent-verification-v1',
            'report_sha256': hashlib.sha256(report_raw).hexdigest(),
            'raw_vector_cells_checked': len(rows) * 4,
            'all_points_ties_categories_and_effects_checked': True,
            'independently_recomputed_intervals': checked,
            'new_engine_searches': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'report', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = verify(a.root, a.report)
    with a.output.open('x') as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'raw_vector_cells_checked': result['raw_vector_cells_checked'], 'verified': True}))


if __name__ == '__main__':
    main()
