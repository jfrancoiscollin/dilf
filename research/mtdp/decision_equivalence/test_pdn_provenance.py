"""Synthetic, score-free provenance tests; not an independent FMJD cohort."""
import hashlib

import pytest

from research.mtdp.decision_equivalence.pdn_provenance import verify_pdn_sources


def test_verified_bytes_and_shared_pdn(tmp_path):
    path = tmp_path / "game.pdn"
    path.write_bytes(b'[Event "fixture"]\n1. 32-28\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = [{"game_id": gid, "source_pdn_sha256": digest} for gid in ("a", "b")]
    assert verify_pdn_sources(rows, {"a": path, "b": path}) == {"a": digest, "b": digest}


def test_missing_digest_rejected(tmp_path):
    path = tmp_path / "game.pdn"
    path.write_bytes(b"test")
    with pytest.raises(ValueError, match="missing or invalid"):
        verify_pdn_sources([{"game_id": "a"}], {"a": path})


def test_tampered_bytes_rejected(tmp_path):
    path = tmp_path / "game.pdn"
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="do not match"):
        verify_pdn_sources([{"game_id": "a", "source_pdn_sha256": "0" * 64}], {"a": path})


def test_inconsistent_game_digest_rejected(tmp_path):
    path = tmp_path / "game.pdn"
    path.write_bytes(b"test")
    rows = [{"game_id": "a", "source_pdn_sha256": d * 64} for d in "ab"]
    with pytest.raises(ValueError, match="inconsistent"):
        verify_pdn_sources(rows, {"a": path})


def test_unmapped_games_rejected(tmp_path):
    with pytest.raises(ValueError, match="source map"):
        verify_pdn_sources([{"game_id": "a", "source_pdn_sha256": "a" * 64}], {})
