"""Post-hoc descriptive full-quiet-signature labels; no scoring or selection."""
import argparse
import json
from pathlib import Path
from statistics import fmean, median
from pedagogy.game import parse_fen
from research.mtdp.successor_audit import _quiet_signature
from research.mtdp.jass_benchmark.named_arena_execution import published_manifest
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest


def annotate(manifest, comparison):
    if (comparison.get('schema') != 'mtdp-named-source16-sensitivity-v1'
            or comparison.get('source_depth') != 16 or comparison.get('target_depth') != 16):
        raise ValueError('Expected the explicitly exploratory equal-depth comparison')
    targets = {t['target_fen']: t for t in manifest['benchmark_targets']}
    output = {}
    for arm in ('L', 'LCB'):
        rows = comparison['geometry'][arm]['rows']
        if len(rows) != len(targets) or {r['fen'] for r in rows} != set(targets):
            raise ValueError('Annotation cannot change the frozen population')
        labelled = []
        for row in rows:
            target = targets[row['fen']]
            if row['games'] != target['target_games']:
                raise ValueError('Annotation game ownership changed')
            a = _quiet_signature(parse_fen(target['source_fens'][arm]))
            b = _quiet_signature(parse_fen(target['target_fen']))
            if a is None or b is None:
                raise ValueError('Full quiet signature is undefined for this pair')
            labelled.append({**row, 'same_full_quiet_signature': a == b})
        strata = {}
        for equal in (True, False):
            chosen = [r for r in labelled if r['same_full_quiet_signature'] == equal]
            costs = [r['a_to_b']['ordinary_regret_centimen'] for r in chosen
                     if r['a_to_b']['ordinary_regret_centimen'] is not None]
            bad = [v for v in costs if v > 0]
            strata[str(equal).lower()] = {
                'positions': len(chosen), 'owner_games': len({g for r in chosen for g in r['games']}),
                'optimal_sets_disjoint': sum(not r['optimal_sets_overlap'] for r in chosen),
                'source_pick_target_optimal': sum(r['a_to_b']['best_centimen'] == r['a_to_b']['transferred_centimen'] for r in chosen),
                'ordinary_positions': len(costs), 'mean_regret': fmean(costs) if costs else None,
                'median_regret': median(costs) if costs else None, 'max_regret': max(costs) if costs else None,
                'positive_cost_positions': len(bad), 'positive_cost_mean': fmean(bad) if bad else None}
        output[arm] = {'strata': strata, 'rows': labelled}
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--directory', required=True)
    p.add_argument('--freeze', required=True); p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    manifest, proof = published_manifest(a.root, a.directory, a.freeze)
    raw = a.comparison.read_bytes(); comparison = json.loads(raw)
    if comparison.get('freeze_commit') != a.freeze:
        raise ValueError('Sensitivity comparison is from another freeze')
    result = {'schema': 'mtdp-posthoc-full-quiet-signature-annotation-v1', 'scope': 'exploratory_annotation_no_new_holdout_or_signature_selection',
              'freeze_commit': a.freeze, 'comparison_sha256': digest(raw), 'implementation_sha256': digest(Path(__file__).read_bytes()),
              'publication_verification': proof, 'geometry': annotate(manifest, comparison)}
    with a.output.open('xb') as f: f.write(_bytes(result))
    print(json.dumps({k:v['strata'] for k,v in result['geometry'].items()}, sort_keys=True))


if __name__ == '__main__': main()
