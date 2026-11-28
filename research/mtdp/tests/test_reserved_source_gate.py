"""Known reserved exports stay excluded after byte/identity changes."""
from pathlib import Path
import re

import pytest

from research.mtdp.reserved_source_gate import screen
from research.mtdp.reserved_source_inventory import BASE, sha

ROOT = Path(__file__).resolve().parents[3]
RAW = (ROOT / BASE / 'two-named-arenas-final/s7ahYqL4/first.pdn').read_bytes()
FIRST = re.split(rb'(?=\[Event )', RAW)[1]


@pytest.mark.parametrize('case', ['formatting', 'partial', 'renamed-site'])
def test_reserved_real_game_remains_excluded_after_reexport(case):
    candidate = RAW + b'\n' if case == 'formatting' else FIRST
    if case == 'renamed-site':
        candidate = re.sub(rb'\[Site "[^"]*"\]', b'[Site "https://lidraughts.org/Fake1234"]', candidate)
    assert sha(candidate) != sha(RAW)
    report = screen(candidate, sha(candidate), ROOT)
    assert report['status'] == 'blocked_reserved_overlap'
    assert not report['independent_cohort_qualified']
    assert not report['eligible_for_freeze']
    assert len(report['findings']) == report['candidate_games']
    for finding in report['findings']:
        assert 'reserved_source_digest' not in finding['reasons']
        assert 'reserved_normalized_notation' in finding['reasons']
        if case != 'renamed-site':
            assert 'reserved_public_game_id' in finding['reasons']


def test_reserved_public_id_still_blocks_when_notation_changes():
    # A different valid opening notation removes token equality; public ID remains.
    site = re.search(rb'\[Site "[^"]*"\]', FIRST).group()
    raw = b'[Event "synthetic"]\n' + site + b'\n[FEN "W:W32:B1"]\n1. 32-28 *\n'
    report = screen(raw, sha(raw), ROOT)
    assert report['findings'] == [{'source_game_index': 1, 'reasons': ['reserved_public_game_id']}]


def test_no_known_match_never_grants_independent_qualification():
    raw = b'[Event "synthetic"]\n[Site "https://lidraughts.org/Fake1234"]\n[FEN "W:W32:B1"]\n1. 32-28 *\n'
    report = screen(raw, sha(raw), ROOT)
    assert not report['findings']
    assert report['status'] == 'no_known_reserved_match_not_qualified'
    assert report['independent_cohort_qualified'] is False
    assert report['eligible_for_freeze'] is False


def test_screen_rejects_tampered_bytes_before_screening():
    with pytest.raises(ValueError, match='digest mismatch'):
        screen(FIRST + b'\n', sha(FIRST), ROOT)


def test_screen_requires_complete_pinned_reserved_sources(tmp_path):
    with pytest.raises(FileNotFoundError):
        screen(FIRST, sha(FIRST), tmp_path)


def test_cli_writes_rejection_and_returns_nonzero_for_whole_mixed_export(tmp_path):
    import json
    import subprocess
    import sys

    raw = FIRST + b'[Event "synthetic"]\n[FEN "W:W32:B1"]\n1. 32-28 *\n'
    candidate, output = tmp_path / 'candidate.pdn', tmp_path / 'audit.json'
    candidate.write_bytes(raw)
    result = subprocess.run([sys.executable, '-m', 'research.mtdp.reserved_source_gate',
                             '--root', str(ROOT), '--candidate', str(candidate),
                             '--expected-sha256', sha(raw), '--output', str(output)],
                            capture_output=True, text=True)
    assert result.returncode == 2
    report = json.loads(output.read_bytes())
    assert report['candidate_games'] == 2
    assert len(report['findings']) == 1
    assert report['status'] == 'blocked_reserved_overlap'
    assert report['eligible_for_freeze'] is False
