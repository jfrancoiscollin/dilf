"""Compare archived FMJD engineering outputs without running an engine.

Validate each internal manifest before comparing bytes. Provenance is reported
separately and never silently removed to assert whole-archive equality.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

DATA = frozenset('mtdp-trajectories.jsonl mtdp-signature-collisions.json mtdp-spatial-dynamics.json mtdp-turn-control.json mtdp-legal-collisions.json mtdp-signature-ablation.json mtdp-successors.json mtdp-local-neighborhood.json mtdp-quarantine.jsonl'.split())
PROVENANCE = 'mtdp-fmjd-provenance.json'
MANIFEST = 'mtdp-artifact-manifest.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(raw, expected_sha256):
    if sha(raw) != expected_sha256:
        raise ValueError('Archive digest does not match the recorded source')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != DATA | {PROVENANCE, MANIFEST}:
            raise ValueError('Duplicate, missing or unexpected archive member')
        files = {n: archive.read(n) for n in names}
    manifest = json.loads(files[MANIFEST])
    if (manifest.get('schema_version') != 'mtdp-artifact-manifest-v1'
            or set(manifest.get('files', {})) != DATA | {PROVENANCE}):
        raise ValueError('Incomplete internal manifest inventory')
    for name, info in manifest['files'].items():
        if info != {'bytes': len(files[name]), 'sha256': sha(files[name])}:
            raise ValueError('Internal manifest digest/size mismatch: ' + name)
    provenance = json.loads(files[PROVENANCE])
    required = {'schema_version', 'dilf_sha', 'dilf_source_sha',
                'draught_master_requested_ref', 'draught_master_sha'}
    if (set(provenance) != required
            or provenance['schema_version'] != 'mtdp-fmjd-provenance-v1'):
        raise ValueError('Unexpected provenance schema')
    return files, provenance, names


def compare(left, right, left_sha256, right_sha256):
    a, ap, an = load(left, left_sha256)
    b, bp, bn = load(right, right_sha256)
    members = {n: {'left_sha256': sha(a[n]), 'right_sha256': sha(b[n]),
                   'left_bytes': len(a[n]), 'right_bytes': len(b[n]),
                   'byte_identical': a[n] == b[n]}
               for n in sorted(a)}
    return {'schema': 'mtdp-fmjd-archive-content-comparison-v1',
        'scope': 'historical_engineering_archive_audit_no_new_cohort_or_efficacy',
        'left_archive': {'bytes': len(left), 'sha256': sha(left)},
        'right_archive': {'bytes': len(right), 'sha256': sha(right)},
        'archive_byte_identical': left == right,
        'zip_member_order_equal': an == bn,
        'internal_manifest_entries_verified_per_archive': 10,
        'data_member_count': len(DATA),
        'all_data_byte_identical': all(a[n] == b[n] for n in DATA),
        'changed_data_members': sorted(n for n in DATA if a[n] != b[n]),
        'changed_members': sorted(n for n in a if a[n] != b[n]),
        'provenance_changes': {k: {'left': ap[k], 'right': bp[k]} for k in sorted(ap) if ap[k] != bp[k]},
        'fmjd_revision_equal': ap['draught_master_sha'] == bp['draught_master_sha'],
        'members': members, 'engine_calls': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('left', 'right', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('left-sha256', 'right-sha256'):
        p.add_argument('--'+name, required=True)
    a = p.parse_args()
    result = compare(a.left.read_bytes(), a.right.read_bytes(), a.left_sha256, a.right_sha256)
    with a.output.open('xb') as f:
        f.write((json.dumps(result, sort_keys=True, indent=2)+'\n').encode())
    print(json.dumps({k: result[k] for k in ('all_data_byte_identical', 'changed_members', 'provenance_changes')}, sort_keys=True))


if __name__ == '__main__':
    main()
