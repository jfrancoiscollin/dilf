"""Source/index/position proof regression tests; no independent D1 admission."""
import hashlib

import pytest

from pedagogy.game import state_to_fen
from research.mtdp.pdn import parse_games, validated_trajectory
from research.mtdp.pdn_membership_proof import prove_pdn_position
from research.mtdp.tests.test_pdn import MockRules

GOOD = b'[Event "A"]\n1. 32-28 17-22 *\n'
BAD = b'[Event "A"]\n1. 32-28 18-23 *\n'


def _source(tmp_path, data=GOOD):
    path = tmp_path / "source.pdn"
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def _fen(data=GOOD, ply=2):
    game = parse_games(data.decode())[0]
    return state_to_fen(validated_trajectory(game, MockRules())[ply][2])


def test_proves_authenticated_source_and_legal_position(tmp_path):
    path, digest = _source(tmp_path)
    result = prove_pdn_position(path, digest, 1, 2, _fen(), MockRules())
    assert result["pdn_bytes_verified"] is True
    assert result["source_index_membership_verified"] is True
    assert result["fmjd_legality_verified"] is True
    assert result["manifest_game_id_binding_verified"] is False
    assert result["independent_cohort_qualified"] is False


@pytest.mark.parametrize("index,ply", [(2, 2), (1, 3), (0, 1), (True, 1), (1, -1)])
def test_rejects_invalid_index_or_ply(tmp_path, index, ply):
    path, digest = _source(tmp_path)
    with pytest.raises(ValueError):
        prove_pdn_position(path, digest, index, ply, _fen(), MockRules())


def test_rejects_tampered_bytes(tmp_path):
    path, digest = _source(tmp_path)
    path.write_bytes(GOOD + b"\n")
    with pytest.raises(ValueError, match="digest"):
        prove_pdn_position(path, digest, 1, 2, _fen(), MockRules())


def test_rejects_forged_fen(tmp_path):
    path, digest = _source(tmp_path)
    with pytest.raises(ValueError, match="FEN"):
        prove_pdn_position(path, digest, 1, 2, _fen(ply=1), MockRules())


def test_rejects_illegal_move_even_for_earlier_observation(tmp_path):
    path, digest = _source(tmp_path, BAD)
    with pytest.raises(ValueError):
        prove_pdn_position(path, digest, 1, 0, _fen(ply=0), MockRules())


def test_rejects_invalid_digest(tmp_path):
    path, _ = _source(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        prove_pdn_position(path, "x" * 64, 1, 2, _fen(), MockRules())
