"""Exploratory equal-depth check after the named primary result; no new signature."""
import argparse
import json
import subprocess
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark import named_arena_execution as runtime
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.best_move_audit import compare_scores

TARGET_PACKET = 'research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc-target16.json'


def compare(manifest, sources, targets):
    output = {}
    for arm in ('L', 'LCB'):
        rows = [{'fen': t['target_fen'], 'games': t['target_games'],
                 **compare_scores(sources[t['source_fens'][arm]], targets[t['target_fen']])}
                for t in manifest['benchmark_targets']]
        ordinary = [r['a_to_b']['ordinary_regret_centimen'] for r in rows
                    if r['a_to_b']['ordinary_regret_centimen'] is not None]
        output[arm] = {'positions': len(rows), 'optimal_sets_intersect': sum(r['optimal_sets_overlap'] for r in rows),
                       'source_pick_target_optimal': sum(r['a_to_b']['best_centimen'] == r['a_to_b']['transferred_centimen'] for r in rows),
                       'ordinary_positions': len(ordinary), 'mean_regret': fmean(ordinary) if ordinary else None,
                       'max_regret': max(ordinary) if ordinary else None, 'rows': rows}
    return output


def audit(root, directory, freeze, reference_commit, adapter, binary, output):
    manifest, proof = runtime.published_manifest(root, directory, freeze)
    method = runtime.execution_fingerprints(root, freeze)
    for ancestor, descendant in ((freeze, reference_commit), (reference_commit, proof['observed_branch_head'])):
        subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', ancestor, descendant], check=True)
    raw = runtime._blob(root, reference_commit, TARGET_PACKET)
    target = json.loads(raw)
    if (target.get('role') != 'target' or target.get('publication_verification', {}).get('published_commit') != freeze
            or target.get('execution_sha256') != method or target.get('scan_ini_sha256') != runtime.SCAN_INI_SHA256):
        raise ValueError('Sensitivity target differs from the published primary reference')
    pins = runtime.scan_fingerprints(binary, manifest['engine'])
    targets = runtime.validate_reference(target, runtime.expected_actions(manifest, 'target'), pins, proof['manifest_sha256'], 16)
    expected = runtime.expected_actions(manifest, 'source')
    output.mkdir(parents=True, exist_ok=False)
    try:
        if expected:
            engine = runtime.checked_engine(adapter)
            with runtime.Scan(binary, depth=16) as scan:
                source = runtime.score_manifest(manifest, engine, scan, role='source')
        else:
            source = {'role': 'source', 'action_scores_centimen': {}}
        source.update(schema='mtdp-jass-scan-reference-v1', cohort_sha256=proof['manifest_sha256'],
                      scan_binary_sha256=pins['scan_linux'], scan_eval_sha256=pins['data/eval'], scan_ini_sha256=pins['scan.ini'],
                      scan_successor_depth=16, publication_verification=proof, execution_sha256=method,
                      scope='exploratory_source16_sensitivity_after_primary_not_new_holdout', primary_source_usable=False)
        sources = runtime.validate_reference(source, expected, pins, proof['manifest_sha256'], 16)
        (output / 'source16.json').write_bytes(_bytes(source))
        report = {'schema': 'mtdp-named-source16-sensitivity-v1', 'scope': source['scope'],
                  'freeze_commit': freeze, 'primary_reference_commit': reference_commit,
                  'source_sha256': runtime.digest(_bytes(source)), 'target_sha256': runtime.digest(raw),
                  'source_depth': 16, 'target_depth': 16,
                  'implementation_sha256': runtime.digest(Path(__file__).read_bytes()),
                  'geometry': compare(manifest, sources, targets)}
        (output / 'comparison.json').write_bytes(_bytes(report))
        return report
    except Exception as error:
        (output / 'FAILED.json').write_bytes(_bytes({'error': type(error).__name__, 'detail': str(error)}))
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'adapter', 'scan', 'output'):
        p.add_argument(f'--{name}', type=Path, required=True)
    for name in ('directory', 'freeze', 'reference-commit'):
        p.add_argument(f'--{name}', required=True)
    a = p.parse_args(); r = audit(a.root, a.directory, a.freeze, a.reference_commit, a.adapter, a.scan, a.output)
    print(json.dumps({arm: {k:v for k,v in row.items() if k != 'rows'} for arm,row in r['geometry'].items()}, sort_keys=True))


if __name__ == '__main__': main()
