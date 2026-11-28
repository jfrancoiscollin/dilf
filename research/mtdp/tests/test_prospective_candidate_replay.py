"""No-target-score regressions for the new Lidraughts candidate replay gate."""

import gzip
import hashlib
import json

import pytest

from research.mtdp.jass_benchmark import prospective_candidate_replay as gate


def test_prior_fens_accept_only_exact_position_manifest_schema():
    assert gate.prior_rows([{"fen": "W:W31:B1"}, {"fen": "W:W31:B1"}]) == {"W:W31:B1"}
    assert gate.prior_rows({"targets": [{"target_fen": "B:W31:B1"}]}) == {"B:W31:B1"}
    with pytest.raises(ValueError, match="FEN"):
        gate.prior_rows([{"source_fen": "W:W31:B1"}])
    with pytest.raises(ValueError, match="catalogue"):
        gate.prior_rows({"unrelated": []})


def test_reject_unsafe_previous_path_before_access(tmp_path):
    previous = {
        "prior_manifests": {"../outside.json": "0" * 64},
        "eligible_shards": [],
    }
    with pytest.raises(ValueError, match="Unsafe"):
        gate.validated_archive_fens(tmp_path, previous)


def test_reject_mismatched_previous_digest(tmp_path):
    path = tmp_path / "wrong.json.gz"
    path.write_bytes(gzip.compress(json.dumps([{"fen": "W:W31:B1"}]).encode()))
    previous = {
        "prior_manifests": {"wrong.json.gz": "0" * 64},
        "eligible_shards": [],
    }
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        gate.validated_archive_fens(tmp_path, previous)


def test_early_fail_on_changed_candidate_before_any_scoring(tmp_path):
    pdn = tmp_path / "mtdp-lidraughts-fFgE7oED.pdn"
    pdn.write_text("tampered")
    with pytest.raises((FileNotFoundError, ValueError)):
        gate.audit(tmp_path, pdn, tmp_path / "historical")


def test_explicitly_separated_candidate_and_archive_identity():
    assert gate.EXPECTED_EVENT == "fFgE7oED"
    assert gate.EXPECTED_PDN_SHA256 == (
        "916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2"
    )
    assert gate.PROTOCOL.endswith("TOTAL_BUDGET_TIEBREAK_PROTOCOL.md")
    assert "scan" not in gate.EXPECTED_EVENT.lower()
