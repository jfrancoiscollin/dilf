"""Restore byte-pinned historical CI inputs; NEVER a fresh prospective acquisition."""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
ARCHIVE = BASE + 'historical-replay/pdn-inputs.zip'
ARCHIVE_SHA = '4c6b2941a4e18be4df016341f62de314657f215622440999843ea05ee58c5ed3'
ORIGINAL_ARTIFACT_SHA = '6e66b724b6f97f5f98c945b50288c4c25eab4fb5b6b1a8e2bb827a4dcbaf3ca5'
CANDIDATE_SHA = '916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2'


def expected_inputs(root):
    p = json.loads((root / (BASE + 'CARZrQpl/provenance.json')).read_bytes())
    rows = [r for r in [*p['inputs']['exclusions'], *p['inputs']['event']]
            if r['file'].startswith('mtdp-lidraughts-')]
    if len(rows) != 18 or len({r['file'] for r in rows}) != 18:
        raise ValueError('Historical inventory changed')
    expected = {'previous-pdn/' + r['file']: r['sha256'] for r in rows}
    expected.update({'mtdp-lidraughts-fFgE7oED.pdn': CANDIDATE_SHA,
                     'independent-repeat.pdn': CANDIDATE_SHA})
    return expected


def validate(raw, expected):
    """Validate complete inventory and every raw PDN before any output is opened."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) | {'downloads.json'}:
            raise ValueError('Missing, extra or duplicate historical ZIP member')
        if any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):
            raise ValueError('Unsafe historical ZIP path')
        data = {name: archive.read(name) for name in names}
    for name, sha in expected.items():
        if not data[name] or hashlib.sha256(data[name]).hexdigest() != sha:
            raise ValueError(f'Historical PDN digest changed: {name}')
    log = json.loads(data['downloads.json'])
    # Preserve the actual older download receipts, without pretending that
    # restored copies are newly independent HTTP requests.
    for key in ('first', 'independent_repeat'):
        if log['candidate'][key]['sha256'] != CANDIDATE_SHA:
            raise ValueError('Original candidate receipt differs from pinned PDN')
    for name, sha in expected.items():
        if name.startswith('previous-pdn/'):
            event = Path(name).name.removeprefix('mtdp-lidraughts-').removesuffix('.pdn')
            if log['previous'][event]['sha256'] != sha:
                raise ValueError('Original historical receipt differs from pinned PDN')
    return data


def restore(root, output):
    raw = (root / ARCHIVE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA:
        raise ValueError('Historical replay ZIP digest changed')
    expected = expected_inputs(root)
    data = validate(raw, expected)
    data['archived-downloads.json'] = data.pop('downloads.json')
    report = {'schema': 'mtdp-historical-pdn-archive-restoration-v1',
              'scope': 'previously_verified_historical_inputs_not_fresh_prospective_acquisition',
              'fresh_http_requests': 0, 'scientific_freeze': False,
              'source_run_id': 44453019237, 'source_artifact_id': 14496378916,
              'source_artifact_zip_sha256': ORIGINAL_ARTIFACT_SHA,
              'repacked_inputs_zip_sha256': ARCHIVE_SHA,
              'original_receipts': 'archived-downloads.json',
              'files': {n: {'bytes': len(data[n]), 'sha256': sha} for n, sha in sorted(expected.items())}}
    data['archival-replay-restoration.json'] = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    if any((output / n).exists() for n in data):
        raise ValueError('Historical restoration would overwrite an existing input')
    for name, content in sorted(data.items()):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(content)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = restore(a.root, a.output)
    print(json.dumps({'historical_pdn_copies': len(report['files']), 'fresh_http_requests': 0}))


if __name__ == '__main__':
    main()
