"""Capture fresh traces for the published nine-case, post-hoc residual-node diagnostic."""
import argparse
import gzip
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from research.mtdp.jass_benchmark import two_arena_telemetry_audit as audit
from research.mtdp.jass_benchmark.metered_control import execute
from research.mtdp.jass_benchmark.metered_engine_smoke import _position_identity
from research.mtdp.jass_benchmark.metered_probe_adapter import parse_receipt

MODULE = 'research/mtdp/jass_benchmark/mechanistic_residual_replay.py'
PLAN = audit.BASE + 'two-named-arenas-mechanistic-residual-plan.json'
PLAN_COMMIT = '6313090d84ec6f61d919288053b2b36d663d112f'
ARMS = ('control', 'native_full', 'LCB_full', 'LCB_residual', 'native_residual')


def clean_env(forced=None):
    env = {k: v for k, v in os.environ.items() if k not in (
        'MTDP_DEPTH_ONE_WINNER', 'JASS_EGDB_PATH', 'JASS_EGDB_MTC_PATH')}
    env['JASS_TRACE_ROOT'] = '0'
    if forced is not None:
        env['MTDP_DEPTH_ONE_WINNER'] = forced
    return env


def parse_main(raw, fen, limit, prefix, native, forced=None):
    lines = raw.splitlines()
    if len(lines) != 1:
        raise ValueError('Expected one main trace receipt')
    v = lines[0].split('\t')
    if len(v) < 12 or _position_identity(v[0]) != _position_identity(fen):
        raise ValueError('Main trace identity differs')
    issued, nodes, depth = map(int, v[1:4])
    if int(v[7]) < 0:
        raise ValueError('Invalid elapsed time in raw main receipt')
    legal, order = v[9].split(','), v[10].split(',')
    if (issued != limit or not 0 <= nodes <= limit or depth < 1
            or v[4] not in ('nodes', 'depth_ceiling') or legal != list(native)
            or len(order) != len(set(order)) or set(order) != set(legal)
            or order[:len(prefix)] != list(prefix) or v[5] not in legal
            or (v[4] == 'nodes' and nodes != limit)
            or (v[4] == 'depth_ceiling' and nodes == limit)):
        raise ValueError('Main trace budget, stop or legal order differs')
    attempts = []
    for text in v[11:]:
        fields = text.split(':')
        if len(fields) != 8:
            raise ValueError('Missing detailed depth attempt')
        d, attempt, complete, all_actions, after = map(int, fields[:5])
        visited = fields[5].split(',') if fields[5] else []
        best, expected = fields[6], fields[7].split(',')
        if (complete not in (0, 1) or all_actions not in (0, 1)
                or not 0 <= after <= nodes or d < 1
                or (best not in legal and (complete or best != '-'))
                or len(expected) != len(set(expected)) or set(expected) != set(legal)
                or visited != expected[:len(visited)]
                or (all_actions and visited != expected)
                or (attempts and after < attempts[-1]['nodes_after'])):
            raise ValueError('Invalid completed, legal or metered attempt trace')
        attempts.append({'depth': d, 'attempt': attempt, 'completed': bool(complete),
                         'all_actions_searched': bool(all_actions), 'nodes_after': after,
                         'visited': visited, 'best_move': best, 'expected_order': expected})
    first = attempts[0]
    if not (first['depth'] == 1 and first['completed'] and first['all_actions_searched']):
        raise ValueError('Main trace has no completed depth one')
    if forced is not None and first['best_move'] != forced:
        raise ValueError('Requested intervention was not applied at depth one')
    for previous, current in zip(attempts, attempts[1:]):
        if current['depth'] != previous['depth']:
            if not previous['completed'] or current['depth'] != previous['depth'] + 1:
                raise ValueError('Depth transition lacks a committed predecessor')
            if current['expected_order'][0] != previous['best_move']:
                raise ValueError('Previous best did not propagate to the next root order')
    summary = {'nodes': nodes, 'depth_ceiling': v[4] == 'depth_ceiling',
               'best_move': v[5], 'score': int(v[6]), 'completed_depth': depth, 'stop': v[4]}
    if not any(a['depth'] == depth and a['completed'] and a['best_move'] == summary['best_move'] for a in attempts):
        raise ValueError('Final summary is absent from completed attempts')
    return {'summary': summary, 'legal': legal, 'initial_order': order,
            'pv': v[8].split(',') if v[8] else [], 'attempts': attempts}


def published(root, commit):
    if Path(__file__).resolve() != (root / MODULE).resolve() or not audit.runtime.freeze._sha(commit, 40):
        raise ValueError('Exact collector checkout and published SHA required')
    subprocess.run(['git', '-C', str(root), 'fetch', 'origin', 'research/mtdp-foundation'], check=True, capture_output=True)
    branch = 'refs/remotes/origin/research/mtdp-foundation'
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', commit, branch], check=True)
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', PLAN_COMMIT, commit], check=True)
    if (root / MODULE).read_bytes() != audit.runtime._blob(root, commit, MODULE):
        raise ValueError('Collector is not the published implementation')
    plan, _ = audit.pinned(root, PLAN_COMMIT, PLAN)
    if (root / PLAN).read_bytes() != audit.runtime._blob(root, commit, PLAN):
        raise ValueError('Published collector uses another diagnostic plan')
    report = audit.analyze(root)  # verifies all original files/methods; no target reference
    if (audit.runtime.digest(audit.runtime._bytes(report)) != plan['parent_audit_sha256']
            or plan['cases'] != report['next_diagnostic_mask']['cases'] or len(plan['cases']) != 9
            or plan['target_reference_access_allowed'] is not False):
        raise ValueError('Published nine-case mask or no-target scope changed')
    # Pin every imported scientific dependency, including the parser and selector.
    for name in (audit.__file__,):
        path = Path(name).resolve().relative_to(root.resolve()).as_posix()
        if (root / path).read_bytes() != audit.runtime._blob(root, commit, path):
            raise ValueError('Published audit dependency differs')
    return plan


def restore_binaries(root, directory, plan):
    receipt, _ = audit.pinned(root, audit.FREEZE, plan['build_receipt_path'], plan['build_receipt_sha256'])
    binaries = {}
    directory.mkdir(parents=True, exist_ok=True)
    for role in ('probe', 'main'):
        r = receipt['binaries'][role]
        compressed = (root / r['archive_path']).read_bytes()
        if audit.runtime.digest(compressed) != r['archive_sha256']:
            raise ValueError('Pinned binary archive changed')
        raw = gzip.decompress(compressed)
        if audit.runtime.digest(raw) != r['sha256']:
            raise ValueError('Pinned executable changed')
        path = directory / role
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('Refusing to overwrite another executable')
        if not path.exists():
            path.write_bytes(raw)
        path.chmod(0o755)
        binaries[role] = path
    return binaries


class Recorder:
    def __init__(self, destination):
        self.destination = destination
        self.calls = []

    def run(self, binary, args, payload, *, phase, limit, prefix, forced=None):
        result = subprocess.run([str(binary.resolve()), *args], input=payload,
                                text=True, capture_output=True, env=clean_env(forced))
        raw = {'phase': phase, 'issued_limit': limit, 'prefix': prefix, 'forced': forced,
               'stdin': payload, 'argv_options': args, 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr}
        path = self.destination / f'{len(self.calls):03d}.json'
        with path.open('xb') as stream:
            stream.write(audit.runtime._bytes(raw))
        if result.returncode:
            raise RuntimeError(f'Engine failed; complete raw receipt retained at {path}')
        return raw

    def probe(self, binary, fen, mode, limit, prefix, native=None):
        raw = self.run(binary, [], ' '.join([mode, fen, str(limit), *prefix]) + '\n',
                       phase=mode, limit=limit, prefix=prefix)
        parsed = parse_receipt(raw['stdout'], mode=mode, fen=fen, issued_limit=limit,
                               requested_move=prefix[0] if mode == 'probe' else None,
                               expected_legal_order=native)
        self.calls.append({'phase': mode, 'issued_limit': limit, 'prefix': prefix, 'receipt': parsed})
        return parsed

    def main(self, binary, fen, phase, limit, prefix, native, forced=None):
        raw = self.run(binary, ['--initial-only', '--record-depth-ceiling'],
                       ' '.join([fen, str(limit), *prefix]) + '\n',
                       phase=phase, limit=limit, prefix=prefix, forced=forced)
        parsed = parse_main(raw['stdout'], fen, limit, prefix, native, forced)
        self.calls.append({'phase': phase, 'issued_limit': limit, 'prefix': prefix,
                           'forced': forced, 'receipt': parsed})
        return parsed


def replay_case(root, case, binaries, directory):
    original, _ = audit.pinned(root, audit.DECISIONS, audit.PREFIX + case['path'])
    fen, budget, prefix = case['fen'], case['budget'], original['LCB_prefix']
    directory.mkdir(parents=True, exist_ok=False)
    rec = Recorder(directory)
    first = rec.probe(binaries['probe'], fen, 'preliminary', budget // 10, prefix)
    native = first['native_order']
    if native != [r['move'] for r in original['verification_receipts'][1:]]:
        raise ValueError('Fresh legal order differs from original probe inventory')
    mains = {}
    def preliminary(limit):
        if limit != budget // 10:
            raise ValueError('Different preliminary allowance')
        return first
    def probe(move, limit):
        return rec.probe(binaries['probe'], fen, 'probe', limit, [move], native)
    def main(forced, limit):
        mains['control'] = rec.main(binaries['main'], fen, 'control', limit, prefix, native, forced)
        return mains['control']['summary']
    verification = execute(total_nodes=budget, native_order=native,
                           preliminary=preliminary, probe=probe, main=main)
    if (any(verification[k] != original[k] for k in verification)
            or first['nodes'] != original['preliminary_nodes']
            or mains['control']['summary'] != original['control_main']):
        raise ValueError('Fresh selector, node charges or control summary does not reproduce original')
    for name, pref, limit, old_key in (
        ('native_full', [], budget, 'native_baseline'),
        ('LCB_full', prefix, budget, 'lcb_baseline'),
        ('LCB_residual', prefix, budget - verification['verification_nodes'], None),
        ('native_residual', [], budget - verification['verification_nodes'], None),
    ):
        mains[name] = rec.main(binaries['main'], fen, name, limit, pref, native)
        if old_key and mains[name]['summary'] != original[old_key]:
            raise ValueError('Fresh baseline summary does not reproduce original')
        if mains[name]['summary']['depth_ceiling']:
            raise ValueError('Unexpected depth ceiling retained in raw diagnostic')
    nodes = sum(c['receipt']['nodes'] if c['phase'] in ('preliminary', 'probe')
                else c['receipt']['summary']['nodes'] for c in rec.calls)
    if nodes != 5 * budget - 2 * verification['verification_nodes']:
        raise ValueError('Supplementary diagnostic node conservation failed')
    return {'case': case, 'original_summaries_reproduced': True,
            'verification': verification, 'main': mains, 'calls': rec.calls, 'actual_nodes_all_five_arms': nodes}


def run(root, commit, output, runtime_dir):
    plan = published(root, commit)  # before opening output, binaries or any engine
    output.mkdir(parents=True, exist_ok=False)
    (output / 'raw').mkdir()
    observed = subprocess.check_output(['git', '-C', str(root), 'rev-parse',
                                       'refs/remotes/origin/research/mtdp-foundation']).decode().strip()
    proof = {'schema': 'mtdp-mechanistic-collector-publication-v1', 'collector_commit': commit,
             'observed_research_branch_head': observed, 'plan_commit': PLAN_COMMIT,
             'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'scientific_freeze': False,
             'scope': plan['scope']}
    (output / 'publication.json').write_bytes(audit.runtime._bytes(proof))
    binaries = restore_binaries(root, runtime_dir, plan)
    status = {'collector_commit': commit, 'complete': False, 'completed_cases': [], 'scope': plan['scope']}
    (output / 'status.json').write_bytes(audit.runtime._bytes(status))
    rows = []
    try:
        for i, case in enumerate(plan['cases']):
            row = replay_case(root, case, binaries, output / 'raw' / f'{i:02d}')
            rows.append(row)
            status['completed_cases'].append(case['path'])
            (output / 'status.json').write_bytes(audit.runtime._bytes(status))
        total = sum(r['actual_nodes_all_five_arms'] for r in rows)
        if total > plan['max_total_search_nodes']:
            raise ValueError('Published search ceiling exceeded')
        report = {'schema': 'mtdp-mechanistic-residual-replay-v1', 'scope': plan['scope'],
                  'collector_commit': commit, 'plan_sha256': audit.runtime.digest((root / PLAN).read_bytes()),
                  'new_independent_cohort': False, 'target_references_opened': 0,
                  'raw_receipts_count': sum(len(r['calls']) for r in rows),
                  'actual_nodes_all_five_arms': total, 'rows': rows}
        (output / 'normalized.json').write_bytes(audit.runtime._bytes(report))
        status.update(complete=True, normalized_sha256=audit.runtime.digest(audit.runtime._bytes(report)), actual_nodes=total)
    except Exception as error:
        status.update(error=type(error).__name__, detail=str(error))
        raise
    finally:
        (output / 'status.json').write_bytes(audit.runtime._bytes(status))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'output', 'runtime'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--collector-commit', required=True)
    a = p.parse_args()
    report = run(a.root, a.collector_commit, a.output, a.runtime)
    print(json.dumps({'cases': len(report['rows']), 'actual_nodes': report['actual_nodes_all_five_arms'],
                      'raw_receipts': report['raw_receipts_count']}))


if __name__ == '__main__':
    main()
