"""Publication-bound Scan references for the registered named arena.

No local manifest, clock/depth override or publication-receipt file is accepted.
The Jass three-arm campaign adapter is a separate next gate.
"""
import argparse
import json
import subprocess
from pathlib import Path

from research.mtdp.jass_benchmark.named_freeze_bundle import verify_publication
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256, score_manifest
from research.mtdp.best_move_audit import Scan
from research.mtdp.jass_benchmark.depth_sensitivity import validate_reference
from research.mtdp.top_k_transfer import _action

METHOD_FILES = (
    'research/mtdp/jass_benchmark/named_arena_execution.py',
    'research/mtdp/jass_benchmark/named_freeze_bundle.py',
    'research/mtdp/jass_benchmark/named_arena_replay.py',
    'research/mtdp/jass_benchmark/named_arena_inputs.py',
    'research/mtdp/jass_benchmark/candidate_jass_catalogue.py',
    'research/mtdp/jass_benchmark/prospective_candidate_replay.py',
    'research/mtdp/jass_scan_reference.py',
    'research/mtdp/best_move_audit.py',
    'research/mtdp/draught_master_adapter.py',
    'research/mtdp/successor_audit.py',
    'research/mtdp/top_k_transfer.py',
    'research/mtdp/jass_benchmark/depth_sensitivity.py',
    'research/mtdp/jass_cohort.py',
    'research/mtdp/pdn.py',
)


def _blob(root, commit, path):
    return subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{path}'])


def published_manifest(root, directory, commit):
    """Recheck the live remote, then use committed bytes, never the worktree."""
    proof = verify_publication(root, directory, commit)
    raw = _blob(root, commit, f'{Path(directory).as_posix()}/manifest.json')
    if (proof.get('scientific_freeze') is not True or proof.get('published_commit') != commit
            or proof.get('manifest_sha256') != digest(raw)):
        raise ValueError('Published snapshot and verification receipt differ')
    return json.loads(raw), proof


def execution_fingerprints(root, commit):
    """Require the running reference method to have been committed by freeze."""
    if Path(__file__).resolve() != (root / METHOD_FILES[0]).resolve():
        raise ValueError('Execution module was imported from another checkout')
    fingerprints = {}
    for name in METHOD_FILES:
        raw = (root / name).read_bytes()
        if raw != _blob(root, commit, name):
            raise ValueError(f'Execution method changed after freeze: {name}')
        fingerprints[name] = digest(raw)
    return fingerprints


def scan_fingerprints(binary, settings):
    binary = binary.resolve()
    fingerprints = {'scan_linux': digest(binary.read_bytes()),
                    'data/eval': digest((binary.parent / 'data/eval').read_bytes()),
                    'scan.ini': digest((binary.parent / 'scan.ini').read_bytes())}
    if (fingerprints['scan_linux'] != settings['scan_binary_sha256']
            or fingerprints['data/eval'] != SCAN_EVAL_SHA256
            or fingerprints['scan.ini'] != SCAN_INI_SHA256):
        raise ValueError('Scan binary, evaluation or configuration changed')
    return fingerprints


def expected_actions(manifest, role):
    expected = {}
    for row in manifest['targets']:
        fen = row[f'{role}_fen']
        actions = {_action(m) for m in row['legal_moves']}
        if len(actions) != len(row['legal_moves']) or not actions:
            raise ValueError('Ambiguous or empty frozen action catalogue')
        if expected.setdefault(fen, actions) != actions:
            raise ValueError('Conflicting frozen action catalogues')
    return expected


def score_reference(root, directory, commit, adapter, binary, role, output):
    if role not in ('source', 'target'):
        raise ValueError('An explicit source or target role is required')
    # No engine input, engine call or output creation may precede remote proof.
    manifest, proof = published_manifest(root, directory, commit)
    method = execution_fingerprints(root, commit)
    if output.exists():
        raise ValueError('Refusing to overwrite an existing reference')
    fingerprints = scan_fingerprints(binary, manifest['engine'])
    depth = manifest['engine']['scan_successor_depth' if role == 'source' else 'target_scan_successor_depth']
    if depth != (12 if role == 'source' else 16):
        raise ValueError('Registered reference depth changed')
    expected = expected_actions(manifest, role)
    if expected:
        engine = checked_engine(adapter)
        with Scan(binary, depth=depth) as scan:
            report = score_manifest(manifest, engine, scan, role=role)
    else:
        report = {'role': role, 'action_scores_centimen': {}}
    if report.get('role') != role:
        raise ValueError('Reference role differs from the requested side')
    report.update(schema='mtdp-jass-scan-reference-v1', cohort_sha256=proof['manifest_sha256'],
                  scan_binary_sha256=fingerprints['scan_linux'], scan_eval_sha256=fingerprints['data/eval'],
                  scan_ini_sha256=fingerprints['scan.ini'], scan_successor_depth=depth,
                  publication_verification=proof, execution_sha256=method,
                  scope='named_arena_reference_after_verified_publication_not_quality_result')
    validate_reference(report, expected, fingerprints, proof['manifest_sha256'], depth)
    # Exclusive creation also refuses a concurrent writer after the initial check.
    with output.open('xb') as stream:
        stream.write((json.dumps(report, sort_keys=True, separators=(',', ':')) + '\n').encode())
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'adapter', 'scan', 'output'):
        p.add_argument(f'--{key}', type=Path, required=True)
    p.add_argument('--directory', required=True)
    p.add_argument('--commit', required=True)
    p.add_argument('--role', choices=('source', 'target'), required=True)
    a = p.parse_args()
    report = score_reference(a.root, a.directory, a.commit, a.adapter, a.scan, a.role, a.output)
    print(json.dumps({k: report[k] for k in ('cohort_sha256', 'role', 'scan_successor_depth', 'publication_verification')}, sort_keys=True))


if __name__ == '__main__':
    main()
