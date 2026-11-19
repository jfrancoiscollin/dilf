"""A historical archive can restore exact bytes, never replace a new acquisition."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from research.mtdp.jass_benchmark import historical_replay_inputs as h


def packed(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for n, v in files:
            z.writestr(n, v)
    return out.getvalue()


@pytest.fixture
def specimen():
    pdn = b'[Event "fixture"]\r\n1. 31-26 *\r\n'
    name = 'previous-pdn/mtdp-lidraughts-fixture.pdn'
    sha = hashlib.sha256(pdn).hexdigest()
    log = {'candidate': {k: {'sha256': h.CANDIDATE_SHA} for k in ('first', 'independent_repeat')},
           'previous': {'fixture': {'sha256': sha}}}
    return [(name, pdn), ('downloads.json', json.dumps(log).encode())], {name: sha}


def test_preserves_original_CRLF_and_receipts(specimen):
    files, expected = specimen
    actual = h.validate(packed(files), expected)
    assert actual[files[0][0]] == files[0][1]
    assert actual['downloads.json'] == files[1][1]


@pytest.mark.parametrize('fault', ('missing', 'extra', 'duplicate', 'mutated'))
def test_incomplete_ambiguous_or_corrupt_archive_is_rejected(specimen, fault):
    files, expected = specimen
    if fault == 'missing':
        files = files[1:]
    elif fault == 'extra':
        files = files + [('extra.pdn', b'new')]
    elif fault == 'duplicate':
        files = files + [files[0]]
    else:
        files = [(files[0][0], b'mutated'), files[1]]
    with pytest.raises(ValueError):
        h.validate(packed(files), expected)


def test_changed_receipt_is_not_accepted_as_new_independent_download(specimen):
    files, expected = specimen
    log = json.loads(files[1][1])
    log['candidate']['first']['sha256'] = '0' * 64
    files[1] = ('downloads.json', json.dumps(log).encode())
    with pytest.raises(ValueError, match='receipt'):
        h.validate(packed(files), expected)


def test_real_pinned_inputs_restore_offline_and_refuse_overwrite(tmp_path):
    root = Path(__file__).resolve().parents[3]
    smoke = tmp_path / 'scan-engineering-smoke.json'
    smoke.write_bytes(b'preserved')
    report = h.restore(root, tmp_path)
    assert len(report['files']) == 20 and report['fresh_http_requests'] == 0
    assert report['scientific_freeze'] is False and smoke.read_bytes() == b'preserved'
    assert (tmp_path / 'mtdp-lidraughts-fFgE7oED.pdn').read_bytes() == (tmp_path / 'independent-repeat.pdn').read_bytes()
    with pytest.raises(ValueError, match='overwrite'):
        h.restore(root, tmp_path)
