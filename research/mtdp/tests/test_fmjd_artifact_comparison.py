"""Content equality must not be inferred from ZIP size or aggregate counts."""
import io
import json
import zipfile
from pathlib import Path

import pytest
from research.mtdp.fmjd_artifact_comparison import compare, load, sha, MANIFEST

BASE = Path(__file__).resolve().parents[1] / 'validation/fmjd-archive-comparison-2026-11-19'


def inputs():
    return (BASE / 'earlier.zip').read_bytes(), (BASE / 'later.zip').read_bytes()


def rewrite(raw, change, update_manifest=False):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files = {n: z.read(n) for n in z.namelist()}
    name, value = change; files[name] = value
    if update_manifest:
        m = json.loads(files[MANIFEST]); m['files'][name] = {'bytes': len(value), 'sha256': sha(value)}
        files[MANIFEST] = json.dumps(m).encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for n, b in files.items():
            z.writestr(n, b)
    return out.getvalue()


def test_archival_data_equal_without_claiming_full_zip_equality():
    a, b = inputs(); r = compare(a, b, sha(a), sha(b))
    assert r['all_data_byte_identical'] and r['data_member_count'] == 9
    assert not r['archive_byte_identical'] and not r['zip_member_order_equal']
    assert set(r['provenance_changes']) == {'dilf_sha', 'dilf_source_sha'}
    assert r['changed_members'] == ['mtdp-artifact-manifest.json', 'mtdp-fmjd-provenance.json']


def test_wrong_source_digest_rejected():
    a, _ = inputs()
    with pytest.raises(ValueError, match='Archive digest'):
        load(a, '0'*64)


def test_updated_outer_zip_digest_does_not_hide_internal_data_corruption():
    a, _ = inputs(); b = rewrite(a, ('mtdp-trajectories.jsonl', b'changed'))
    with pytest.raises(ValueError, match='Internal manifest'):
        load(b, sha(b))


def test_legitimate_changed_data_cannot_be_discarded_as_provenance():
    a, _ = inputs(); b = rewrite(a, ('mtdp-turn-control.json', b'{}\n'), update_manifest=True)
    r = compare(a, b, sha(a), sha(b))
    assert not r['all_data_byte_identical']
    assert r['changed_data_members'] == ['mtdp-turn-control.json']


def test_unlisted_extra_file_rejected():
    a, _ = inputs(); b = rewrite(a, ('extra.json', b'{}'))
    with pytest.raises(ValueError, match='archive member'):
        load(b, sha(b))


def test_invalid_provenance_commit_sha_rejected_even_with_valid_manifest():
    a, _ = inputs()
    with zipfile.ZipFile(io.BytesIO(a)) as z:
        provenance = json.loads(z.read('mtdp-fmjd-provenance.json'))
    provenance['draught_master_sha'] = 'not-a-commit'
    b = rewrite(a, ('mtdp-fmjd-provenance.json',
                    json.dumps(provenance).encode()), update_manifest=True)
    with pytest.raises(ValueError, match='Invalid provenance commit SHA'):
        load(b, sha(b))


def test_invalid_provenance_ref_rejected_even_with_valid_manifest():
    a, _ = inputs()
    with zipfile.ZipFile(io.BytesIO(a)) as z:
        provenance = json.loads(z.read('mtdp-fmjd-provenance.json'))
    provenance['draught_master_requested_ref'] = ''
    b = rewrite(a, ('mtdp-fmjd-provenance.json',
                    json.dumps(provenance).encode()), update_manifest=True)
    with pytest.raises(ValueError, match='Invalid requested FMJD ref'):
        load(b, sha(b))
