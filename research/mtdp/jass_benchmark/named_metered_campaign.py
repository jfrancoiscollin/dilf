"""Registered three-arm Jass decisions; accepts source scores only, after freeze."""
import argparse
import json
from pathlib import Path

from research.mtdp.jass_benchmark.named_arena_execution import (
    _blob, published_manifest, execution_fingerprints, expected_actions,
)
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest
from research.mtdp.jass_benchmark.metered_engine_smoke import technical_smoke
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.depth_sensitivity import validate_reference
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256
from research.mtdp.jass_cohort import JASS_COMMIT

BUILD_RECEIPT = 'research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc-runner-builds.json'
METHOD_FILES = (
    'research/mtdp/jass_benchmark/named_metered_campaign.py',
    'research/mtdp/jass_benchmark/metered_engine_smoke.py',
    'research/mtdp/jass_benchmark/metered_probe_adapter.py',
    'research/mtdp/jass_benchmark/metered_control.py',
    'research/mtdp/jass_benchmark/total_budget.py',
    'research/mtdp/jass_benchmark/prospective_tiebreak.py',
    'research/mtdp/jass_benchmark/offline_top3_control.py',
)
BUILD_INPUTS = (
    'research/mtdp/jass_preflight/first-root-action.patch',
    'research/mtdp/jass_preflight/initial-only.patch',
    'research/mtdp/jass_preflight/depth-one-winner.patch',
    'research/mtdp/jass_preflight/metered_probe.cpp',
    'research/mtdp/jass_preflight/targets.cmake',
    'research/mtdp/jass_preflight/move_key.hpp',
    'research/mtdp/jass_benchmark/runner.cpp',
)


def checked_build(root, commit, probe, main):
    raw = _blob(root, commit, BUILD_RECEIPT)
    lock = json.loads(raw)
    if (lock.get('schema') != 'mtdp-named-jass-runner-builds-v1' or lock.get('jass_commit') != JASS_COMMIT
            or lock.get('configuration') != {'build_type': 'Release', 'simd': False, 'native': False, 'main_initial_only': True}
            or set(lock.get('build_inputs', {})) != set(BUILD_INPUTS)):
        raise ValueError('Unregistered Jass build receipt')
    for name, expected in lock['build_inputs'].items():
        if digest(_blob(root, commit, name)) != expected:
            raise ValueError('Committed Jass patch or harness differs from build receipt')
    for role, path in (('probe', probe), ('main', main)):
        if digest(path.read_bytes()) != lock['binaries'][role]['sha256']:
            raise ValueError('Jass executable differs from the pre-freeze build receipt')
    return {'receipt_sha256': digest(raw), 'binaries': lock['binaries']}


def source_scores(manifest, proof, source, method):
    if (source.get('role') != 'source' or source.get('publication_verification', {}).get('published_commit') != proof['published_commit']
            or source.get('publication_verification', {}).get('scientific_freeze') is not True
            or source.get('execution_sha256') != method or source.get('scan_ini_sha256') != SCAN_INI_SHA256):
        raise ValueError('Source reference is not bound to the verified published method')
    return validate_reference(source, expected_actions(manifest, 'source'),
                              {'scan_linux': manifest['engine']['scan_binary_sha256'], 'data/eval': SCAN_EVAL_SHA256},
                              proof['manifest_sha256'], 12)


def campaign(root, directory, commit, source_path, probe, main, output):
    manifest, proof = published_manifest(root, directory, commit)
    method = execution_fingerprints(root, commit)
    for name in METHOD_FILES:
        if (root / name).read_bytes() != _blob(root, commit, name):
            raise ValueError('Jass campaign method changed after freeze')
    build = checked_build(root, commit, probe, main)
    raw = source_path.read_bytes()
    scores = source_scores(manifest, proof, json.loads(raw), method)
    if manifest['engine']['jass_node_budgets'] != [10000, 50000, 200000]:
        raise ValueError('Registered total budgets changed')
    targets = sorted(manifest['benchmark_targets'], key=lambda r: r['target_fen'])
    if len({r['target_fen'] for r in targets}) != len(targets):
        raise ValueError('Duplicate frozen target')
    output.mkdir(parents=True, exist_ok=False)
    plan = {'schema': 'mtdp-named-metered-campaign-v1', 'event': manifest['event'],
            'publication_verification': proof, 'source_sha256': digest(raw), 'build': build,
            'planned_targets': len(targets), 'budgets': [10000, 50000, 200000],
            'scope': 'prospective_three_arm_decisions_no_target_reference_access'}
    (output / 'plan.json').write_bytes(_bytes(plan))
    counts = {}
    for budget in plan['budgets']:
        destination = output / str(budget); destination.mkdir()
        paired = 0
        for index, target in enumerate(targets):
            prefix = candidate_lists(target['legal_moves'], scores[target['source_fens']['LCB']])[1]['transfer']
            try:
                receipt = technical_smoke(probe, main, target['target_fen'], total_nodes=budget, prefix=prefix,
                                          expected_legal_keys=[m['jass_key'] for m in target['legal_moves']])
            except Exception as error:
                (destination / f'{index:05d}-FAILED.json').write_bytes(_bytes({
                    'target_fen': target['target_fen'], 'budget': budget, 'error': type(error).__name__, 'detail': str(error)}))
                raise
            row = {'event': manifest['event'], 'fen': target['target_fen'], 'games': target['target_games'],
                   'budget': budget, 'LCB_prefix': prefix, **receipt}
            (destination / f'{index:05d}.json').write_bytes(_bytes(row))
            paired += receipt['paired_comparable']
        counts[str(budget)] = {'planned': len(targets), 'recorded': len(targets), 'paired_comparable': paired,
                               'depth_ceiling_excluded': len(targets) - paired}
    result = {**plan, 'complete': True, 'counts': counts}
    (output / 'complete.json').write_bytes(_bytes(result))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'source', 'probe', 'main', 'output'):
        p.add_argument(f'--{name}', type=Path, required=True)
    p.add_argument('--directory', required=True); p.add_argument('--commit', required=True)
    a = p.parse_args()
    print(json.dumps(campaign(a.root, a.directory, a.commit, a.source, a.probe, a.main, a.output), sort_keys=True))


if __name__ == '__main__':
    main()
