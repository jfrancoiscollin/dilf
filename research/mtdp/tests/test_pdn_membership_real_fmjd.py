"""Small source/index proof checks using the exact downstream FMJD revision.

General unit CI may skip without the optional engine. The dedicated downstream
step sets MTDP_REQUIRE_REAL_FMJD=1, making a missing or wrong engine a failure.
These synthetic games are not an admitted independent research cohort.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from pedagogy.game import initial_state, parse_fen, state_from_pieces, state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.pdn import PdnReplayError
from research.mtdp.pdn_membership_proof import prove_pdn_position

FMJD_REVISION = '0e5189fbb251bf5eaf2e613d0f878bb17c740311'


@pytest.fixture(scope='module')
def real_engine():
    try:
        from backend import game_engine
    except ImportError as exc:
        if os.environ.get('MTDP_REQUIRE_REAL_FMJD') == '1':
            raise AssertionError('Required pinned real FMJD engine is unavailable') from exc
        pytest.skip('Optional pinned FMJD dependency unavailable; dedicated downstream CI requires it')
    directory = Path(game_engine.__file__).resolve().parent
    actual = subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == FMJD_REVISION, 'Wrong FMJD revision; do not substitute a different rules engine'
    print(json.dumps({'real_fmjd_revision_verified': actual, 'synthetic_membership_checks_only': True}))
    return create_engine()


def source(tmp_path, raw):
    path = tmp_path / 'synthetic.pdn'
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_real_fmjd_authenticated_quiet_sequence(real_engine, tmp_path):
    path, digest = source(tmp_path, b'[Event "synthetic"]\n1. 32-28 17-22 *\n')
    # Independent expected occupancy, not another call to the replay helper.
    expected = state_from_pieces(white_men=(set(range(31, 51)) - {32}) | {28},
                                 black_men=(set(range(1, 21)) - {17}) | {22}, turn='white')
    result = prove_pdn_position(path, digest, 1, 2, state_to_fen(expected), real_engine)
    assert result['source_pdn_sha256'] == digest and result['verified_ply'] == 2
    assert result['pdn_bytes_verified'] and result['source_index_membership_verified']
    assert result['fmjd_legality_verified']
    assert result['manifest_game_id_binding_verified'] is False
    assert result['independent_cohort_qualified'] is False


def test_real_fmjd_rejects_late_illegal_move_for_initial_observation(real_engine, tmp_path):
    path, digest = source(tmp_path, b'[Event "synthetic"]\n1. 32-28 17-22 2. 32-28 *\n')
    with pytest.raises(PdnReplayError, match='ply 3'):
        prove_pdn_position(path, digest, 1, 0, state_to_fen(initial_state()), real_engine)


def test_real_fmjd_rejects_quiet_move_when_capture_is_mandatory(real_engine, tmp_path):
    fen = 'W:W32:B27'
    legal = real_engine.legal_moves(parse_fen(fen))
    assert legal and all(m.is_capture for m in legal)
    assert any(m.path == (32, 21) for m in legal)
    raw = b'[Event "synthetic"]\n[FEN "W:W32:B27"]\n1. 32-28 *\n'
    path, digest = source(tmp_path, raw)
    with pytest.raises(PdnReplayError, match='ply 1'):
        prove_pdn_position(path, digest, 1, 0, fen, real_engine)
