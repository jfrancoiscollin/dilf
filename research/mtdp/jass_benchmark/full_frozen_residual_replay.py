"""Exhaustive, separately published residual-node controls on all 114 frozen receipts."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from research.mtdp.jass_benchmark import mechanistic_residual_replay as shared

MODULE = 'research/mtdp/jass_benchmark/full_frozen_residual_replay.py'
PLAN = shared.audit.BASE + 'full-frozen-residual-control-plan.json'
PLAN_COMMIT = 'aba44edc68f87d31e534b4be6c69c718c89df2d9'
SHARED_COMMIT = '3b89ca824c173530e3b475ece9d3dbb3f1500dd6'


def validate_plan(plan, report):
    cases = [{k: r[k] for k in ('path', 'event', 'fen', 'owner', 'budget',
                               'verification_nodes', 'reported_intervention')} for r in report['rows']]
    if (plan['cases'] != cases or len(cases) != 114
            or len({r['fen'] for r in cases}) != 38
            or len({(r['event'], r['owner']) for r in cases}) != 31
            or {r['budget'] for r in cases} != {10000, 50000, 200000}
            or any(sum(r['budget'] == b for r in cases) != 38 for b in (10000, 50000, 200000))
            or plan.get('target_reference_access_allowed') is not False
            or plan.get('primary_methods_results_and_prior_masks_may_be_modified') is not False):
        raise ValueError('Full frozen frame, budgets or no-target scope changed')


def published(root, commit):
    if Path(__file__).resolve() != (root / MODULE).resolve() or not shared.audit.runtime.freeze._sha(commit, 40):
        raise ValueError('Exact published full-frame collector and checkout required')
    subprocess.run(['git', '-C', str(root), 'fetch', 'origin', 'research/mtdp-foundation'], check=True, capture_output=True)
    for a, b in ((PLAN_COMMIT, commit), (commit, 'refs/remotes/origin/research/mtdp-foundation')):
        subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', a, b], check=True)
    for path in (MODULE, PLAN):
        if (root / path).read_bytes() != shared.audit.runtime._blob(root, commit, path):
            raise ValueError('Collector or full-frame plan is not the published version')
    for path in (shared.MODULE, 'research/mtdp/jass_benchmark/two_arena_telemetry_audit.py'):
        if (root / path).read_bytes() != shared.audit.runtime._blob(root, SHARED_COMMIT, path):
            raise ValueError('Previously validated shared method changed')
    plan, _ = shared.audit.pinned(root, PLAN_COMMIT, PLAN)
    report = shared.audit.analyze(root)
    if shared.audit.runtime.digest(shared.audit.runtime._bytes(report)) != plan['parent_audit_sha256']:
        raise ValueError('Parent telemetry differs from the original frozen campaign')
    validate_plan(plan, report)
    return plan


def run(root, commit, output, runtime_dir):
    plan = published(root, commit)  # before any output or engine access
    old_plan, _ = shared.audit.pinned(root, shared.PLAN_COMMIT, shared.PLAN)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'raw').mkdir()
    observed = subprocess.check_output(['git', '-C', str(root), 'rev-parse',
                                       'refs/remotes/origin/research/mtdp-foundation']).decode().strip()
    publication = {'schema': 'mtdp-full-residual-publication-v1', 'collector_commit': commit,
                   'observed_research_branch_head': observed, 'plan_commit': PLAN_COMMIT,
                   'verified_at_utc': datetime.now(timezone.utc).isoformat(),
                   'scientific_freeze': False, 'scope': plan['scope']}
    (output / 'publication.json').write_bytes(shared.audit.runtime._bytes(publication))
    binaries = shared.restore_binaries(root, runtime_dir, old_plan)
    status = {'collector_commit': commit, 'complete': False, 'completed_cases': [], 'scope': plan['scope']}
    (output / 'status.json').write_bytes(shared.audit.runtime._bytes(status))
    rows = []
    try:
        for i, case in enumerate(plan['cases']):
            row = shared.replay_case(root, case, binaries, output / 'raw' / f'{i:03d}')
            rows.append(row)
            status['completed_cases'].append(case['path'])
            (output / 'status.json').write_bytes(shared.audit.runtime._bytes(status))
        total = sum(r['actual_nodes_all_five_arms'] for r in rows)
        if total > plan['max_total_search_nodes_per_execution']:
            raise ValueError('Full-frame search ceiling exceeded')
        report = {'schema': 'mtdp-full-frozen-residual-replay-v1', 'scope': plan['scope'],
                  'collector_commit': commit, 'plan_sha256': shared.audit.runtime.digest((root / PLAN).read_bytes()),
                  'new_independent_cohort': False, 'target_references_opened': 0,
                  'raw_receipts_count': sum(len(r['calls']) for r in rows),
                  'actual_nodes_all_five_arms': total, 'rows': rows}
        raw = shared.audit.runtime._bytes(report)
        (output / 'normalized.json').write_bytes(raw)
        status.update(complete=True, normalized_sha256=shared.audit.runtime.digest(raw), actual_nodes=total)
    except Exception as error:
        status.update(error=type(error).__name__, detail=str(error))
        raise
    finally:
        (output / 'status.json').write_bytes(shared.audit.runtime._bytes(status))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'output', 'runtime'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--collector-commit', required=True)
    a = p.parse_args()
    r = run(a.root, a.collector_commit, a.output, a.runtime)
    print(json.dumps({'contexts': len(r['rows']), 'actual_nodes': r['actual_nodes_all_five_arms'],
                      'raw_receipts': r['raw_receipts_count']}))


if __name__ == '__main__':
    main()
