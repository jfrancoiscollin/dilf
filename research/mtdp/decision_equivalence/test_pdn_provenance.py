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


from research.mtdp.decision_equivalence.admission_gate import audit_with_pdn_bytes


def _historical_row(digest=None):
    row = {"game_id": "historical-1", "event_id": "historical-event",
           "tournament_id": "historical-tournament", "split": "train",
           "fen": "W:W31:B20", "ply": 1}
    if digest is not None:
        row["source_pdn_sha256"] = digest
    return row


def test_admission_gate_requires_actual_bytes(tmp_path):
    path = tmp_path / "historical.pdn"
    path.write_bytes(b'[Event "historical"]\\n1. 32-28\\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    report = audit_with_pdn_bytes([_historical_row(digest)], {"historical-1": path})
    assert report["pdn_bytes_verified"] is True
    assert report["verified_games"] == 1
    assert report["game_membership_verified"] is False
    assert report["fmjd_legality_verified"] is False
    assert report["independent_cohort_qualified"] is False


def test_admission_gate_rejects_digest_free_manifest(tmp_path):
    path = tmp_path / "historical.pdn"
    path.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="missing or invalid PDN digest"):
        audit_with_pdn_bytes([_historical_row()], {"historical-1": path})


def test_admission_gate_preserves_reserved_event_exclusion(tmp_path):
    path = tmp_path / "historical.pdn"
    path.write_bytes(b"fixture")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    row = _historical_row(digest)
    row["event_id"] = "fFgE7oED"
    with pytest.raises(ValueError, match="reserved"):
        audit_with_pdn_bytes([row], {"historical-1": path})
