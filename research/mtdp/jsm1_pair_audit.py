"""Strict bounded-memory JNNW/JSM1 compatibility audit, never corpus admission."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from .r2_snapshot_diversity import _path, _digest_file, HEADER, RECORD, jnnw_key

META = struct.Struct('<QQB')
MANIFEST_SHA = 'e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c'
PAIRS = (
 ('ee8d685cea331940-m2-d8.jnnw.gz', '42b184456375bb58-m2-d8.jsm.jsm1.gz'),
 ('15261c89bd6520e1-f2m.raw.jnnw.gz', '6b12a94012803365-f2m.raw.jsm.jsm1.gz'),
 ('6ac60a9b3d0ede59-m2.fit.jnnw.gz', '756de534a71e5ace-m2.fit.jsm.jsm1.gz'),
 ('79e605f3139e510f-f2m-extra.jnnw.gz', 'a54a1c81ce17e21b-f2m-extra.jsm.jsm1.gz'),
 ('9b7db67a87025baf-turnover1to1.jnnw.gz', 'acf3bbf4a28e7b44-turnover1to1.jsm.jsm1.gz'),
 ('f1522b2afbd9feab-f2m-common.jnnw.gz', 'cc0e423f6e5c1a91-f2m-common.jsm.jsm1.gz'),
)


def audit_pair(root: Path, position: dict, metadata: dict, *, sample_budget: int = 1024) -> dict:
    """Check every row structurally; retain at most 1024 metadata IDs per pair.

    Same row count and compatible source names do NOT prove semantic alignment.
    No reference score or label is reported, used for selection, or evaluated.
    """
    count = position['record_count']
    if type(count) is not int or not 0 < count <= 20_000_000:
        raise ValueError('invalid position row count')
    if type(sample_budget) is not int or not 1 <= sample_budget <= 1024:
        raise ValueError('invalid sample budget')
    if (position['format'], position['record_count_unit']) != ('jnnw', 'positions'):
        raise ValueError('unexpected position format/unit')
    if (metadata['format'], metadata['record_count_unit']) != ('jsm1', 'metadata_rows'):
        raise ValueError('unexpected metadata format/unit')
    if type(metadata['record_count']) is not int or metadata['record_count'] != count:
        raise ValueError('pair row count mismatch')
    paths = []
    for obj in (position, metadata):
        path = _path(root, obj['path'])
        if path.stat().st_size != obj['stored_bytes'] or _digest_file(path) != obj['stored_sha256']:
            raise ValueError('stored source integrity mismatch')
        paths.append(path)
    digests = [hashlib.sha256(), hashlib.sha256()]
    lengths = [0, 0]
    quota = min(sample_budget, count)
    picks = {(i * count) // quota for i in range(quota)}
    games, openings = set(), set()
    seeded = sampled = 0
    with gzip.open(paths[0], 'rb') as pf, gzip.open(paths[1], 'rb') as mf:
        for i, (fh, magic) in enumerate(((pf, b'JNNW'), (mf, b'JSM1'))):
            header = fh.read(HEADER.size)
            if len(header) != HEADER.size or HEADER.unpack(header) != (magic, count):
                raise ValueError('pair header mismatch')
            digests[i].update(header)
            lengths[i] += len(header)
        for offset in range(0, count, 65536):
            rows = min(65536, count - offset)
            chunks = [pf.read(rows * RECORD.size), mf.read(rows * META.size)]
            if len(chunks[0]) != rows * RECORD.size or len(chunks[1]) != rows * META.size:
                raise ValueError('truncated pair records')
            for i, chunk in enumerate(chunks):
                digests[i].update(chunk)
                lengths[i] += len(chunk)
            for i, (game, opening, seed) in enumerate(META.iter_unpack(chunks[1])):
                if seed not in (0, 1):
                    raise ValueError('invalid JSM1 seeded byte')
                seeded += seed
                # Validate board occupancy, trait and WDL, without retaining scores.
                jnnw_key(chunks[0][i * RECORD.size:(i + 1) * RECORD.size])
                if offset + i in picks:
                    games.add(game)
                    openings.add(opening)
                    sampled += 1
        if pf.read(1) or mf.read(1):
            raise ValueError('trailing pair data')
    for i, obj in enumerate((position, metadata)):
        if lengths[i] != obj['uncompressed_bytes'] or digests[i].hexdigest() != obj['uncompressed_sha256']:
            raise ValueError('uncompressed source integrity mismatch')
    return {
        'position_path': position['path'], 'metadata_path': metadata['path'],
        'position_stored_sha256': position['stored_sha256'],
        'metadata_stored_sha256': metadata['stored_sha256'],
        'rows_structurally_checked': count, 'seeded_rows': seeded,
        'metadata_rows_sampled': sampled, 'distinct_sampled_game_ids': len(games),
        'distinct_sampled_opening_ids': len(openings),
        'row_alignment_authenticated': False, 'ply_available': False,
        'independent_cohort_admitted': False,
    }


def audit(root: Path) -> dict:
    raw = (root / 'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('unpinned snapshot manifest')
    manifest = json.loads(raw)
    objects = {x['path']: x for x in manifest['objects']}
    reports = []
    for position, metadata in PAIRS:
        p, m = ('objects/' + x for x in (position, metadata))
        reports.append(audit_pair(root, objects[p], objects[m]))
    return {
        'schema': 'mtdp.jsm1_pair_structural_audit.v1',
        'manifest_sha256': MANIFEST_SHA, 'pairs': reports,
        'rows_structurally_checked': sum(x['rows_structurally_checked'] for x in reports),
        'sampling': 'first 1024 evenly spaced metadata indices per pair; not random',
        'source_generation_alignment_authenticated': False,
        'external_game_event_identity_authenticated': False,
        'historical_exclusions_checked': False,
        'row_alignment_authenticated': False,
        'independent_cohort_admitted': False,
        'safe_decision_pruning_claim': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    with args.output.open('x', encoding='utf-8') as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write('\n')


if __name__ == '__main__':
    main()
