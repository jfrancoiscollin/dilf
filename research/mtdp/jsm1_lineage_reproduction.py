"""Reproduce historical byte transforms; no game identity or cohort admission."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .jsm1_pair_audit import MANIFEST_SHA, PAIRS
from .r2_snapshot_diversity import _path, _digest_file

JASS_COMMIT = '336bb98451a205266d6646c4d801027af4b30294'
FRONTIER_SHA = '16724d0cd8748f3f2980bb210524f246f4838bea871c34cfe0f64a7b9260ce44'
STEMS = ('m2-d8', 'f2m.raw', 'm2.fit', 'f2m-extra', 'turnover1to1', 'f2m-common')


def extract_verified(root: Path, obj: dict, destination: Path) -> None:
    source = _path(root, obj['path'])
    if source.stat().st_size != obj['stored_bytes'] or _digest_file(source) != obj['stored_sha256']:
        raise ValueError('stored source integrity mismatch')
    digest, size = hashlib.sha256(), 0
    with gzip.open(source, 'rb') as reader, destination.open('xb') as writer:
        while chunk := reader.read(1 << 20):
            digest.update(chunk)
            size += len(chunk)
            if size > obj['uncompressed_bytes']:
                raise ValueError('decompressed source exceeds manifest size')
            writer.write(chunk)
    if size != obj['uncompressed_bytes'] or digest.hexdigest() != obj['uncompressed_sha256']:
        raise ValueError('decompressed source integrity mismatch')


def compare_pair(data: Path, meta: Path, expected: tuple[dict, dict]) -> dict:
    checks = {}
    for kind, path, obj in zip(('data', 'metadata'), (data, meta), expected):
        observed = _digest_file(path)
        checks[kind] = dict(expected_sha256=obj['uncompressed_sha256'],
                            observed_sha256=observed,
                            matches=observed == obj['uncompressed_sha256'])
    checks['both_payloads_reproduced'] = all(checks[x]['matches'] for x in ('data', 'metadata'))
    return checks


def reproduce(root: Path, frontier: Path, work: Path) -> dict:
    if _digest_file(frontier) != FRONTIER_SHA:
        raise ValueError('unpinned historical transform source')
    raw = (root / 'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('unpinned snapshot manifest')
    objects = {o['path']: o for o in json.loads(raw)['objects']}
    # Refuse any preexisting work directory or outputs.
    work.mkdir(parents=True, exist_ok=False)
    refs = {}
    for stem, pair in zip(STEMS, PAIRS):
        refs[stem] = tuple(objects['objects/' + name] for name in pair)
    # Only these three source pairs feed the historical transformation chain.
    for stem in ('f2m-common', 'f2m-extra', 'm2-d8'):
        for suffix, obj in zip(('jnnw', 'jsm'), refs[stem]):
            extract_verified(root, obj, work / f'{stem}.{suffix}')

    def pair(stem):
        return [str(work / f'{stem}.{suffix}') for suffix in ('jnnw', 'jsm')]

    def run(name, args, output_stem, reference_stem):
        subprocess.run([sys.executable, str(frontier), *args,
                        '--out-data', pair(output_stem)[0], '--out-meta', pair(output_stem)[1],
                        '--manifest', str(work / f'{name}.json')], check=True,
                       stdout=subprocess.DEVNULL)
        return compare_pair(*(Path(p) for p in pair(output_stem)), refs[reference_stem])

    steps = {}
    steps['f2m_reconstruction'] = run('merge', [
        'merge', '--pair', *pair('f2m-common'), '--pair', *pair('f2m-extra'),
        '--renamespace-nested'], 'reconstructed-f2m', 'f2m.raw')
    steps['turnover_1_1'] = run('mix', [
        'mix', '--source', 'PARENT', *pair('reconstructed-f2m'), '1',
        '--source', 'FRESH', *pair('m2-d8'), '1',
        '--target-records', '2000000', '--seed', '141421', '--namespace-openings'],
        'reconstructed-turnover', 'turnover1to1')
    steps['opening_split'] = run('split', [
        'split', '--data', pair('reconstructed-turnover')[0],
        '--meta', pair('reconstructed-turnover')[1],
        '--holdout-mod', '10', '--seed', '577215'], 'reconstructed-fit', 'm2.fit')
    return dict(schema='mtdp.jsm1_historical_transform_reproduction.v1',
                jass_code_commit=JASS_COMMIT, frontier_sha256=FRONTIER_SHA,
                snapshot_manifest_sha256=MANIFEST_SHA, steps=steps,
                all_output_payloads_reproduced=all(s['both_payloads_reproduced'] for s in steps.values()),
                generated_source_game_identity_authenticated=False,
                ply_or_complete_trajectories_authenticated=False,
                historical_exclusions_checked=False,
                independent_cohort_admitted=False,
                new_engine_scores_computed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--frontier', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('refusing to replace output')
    result = reproduce(a.root, a.frontier, a.work)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
