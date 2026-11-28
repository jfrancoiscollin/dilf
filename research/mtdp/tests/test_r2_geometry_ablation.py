"""Synthetic geometry-coarsening checks; no FMJD, no R2, no scores."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest

from research.mtdp.r2_geometry_ablation import occupancy_signature, profile
from research.mtdp.r2_snapshot_diversity import BOARD


def _record(wm, wk, bm, bk, stm, wdl=1):
    return struct.pack("<QQQQBib", wm, wk, bm, bk, stm, 0, wdl)


def _obj(root, filename, fmt, raw, count):
    path = root / "objects" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = gzip.compress(raw) if filename.endswith(".gz") else raw
    path.write_bytes(stored)
    return {
        "path": "objects/" + filename,
        "format": fmt,
        "stored_bytes": len(stored),
        "stored_sha256": hashlib.sha256(stored).hexdigest(),
        "uncompressed_bytes": len(raw),
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": count, "record_count_unit": "positions",
    }


def _fixtures(tmp_path):
    r2, hist = tmp_path / "r2", tmp_path / "hist"
    r2.mkdir()
    hist.mkdir()
    # Three distinct states with equal material and stm; A and B are in
    # the same first row; C lies in the next row.
    a = _record(1 << 0, 0, 1 << 1, 0, 0, 1)
    b = _record(1 << 1, 0, 1 << 0, 0, 0, -1)
    c = _record(1 << 5, 0, 1 << 6, 0, 0, 0)
    hdr = lambda n: b"JNNW" + struct.pack("<I", n)
    ro = _obj(r2, "train.jnnw.gz", "jnnw", hdr(3) + a + b + c, 3)
    rf = _obj(r2, "sample.fen", "fen", b"# comment\nW:W1:B2 # note\n", 1)
    ho = _obj(hist, "old.jnnw.gz", "jnnw", hdr(1) + a, 1)
    manifests = {}
    for label, root, objects, schema in (
        ("r2", r2, [ro, rf], "dilf.r2_positions_snapshot.v1"),
        ("historical", hist, [ho], "dilf.recovered_positions_snapshot.v1"),
    ):
        payload = json.dumps({
            "schema": schema, "objects": objects,
            "sources": [{"object_path": obj["path"]} for obj in objects],
        }, sort_keys=True).encode("utf-8")
        (root / "manifest.json").write_bytes(payload)
        manifests[label] = hashlib.sha256(payload).hexdigest()
    return r2, hist, manifests


def test_material_only_same_but_row_signature_changes():
    a = BOARD.pack(1, 0, 2, 0, 0)
    b = BOARD.pack(2, 0, 1, 0, 0)
    c = BOARD.pack(1 << 5, 0, 1 << 6, 0, 0)
    assert occupancy_signature(a, rows_per_zone=10) == occupancy_signature(b, rows_per_zone=10)
    assert occupancy_signature(a, rows_per_zone=1) == occupancy_signature(b, rows_per_zone=1)
    assert occupancy_signature(a, rows_per_zone=1) != occupancy_signature(c, rows_per_zone=1)
    assert occupancy_signature(a, rows_per_zone=2) == occupancy_signature(c, rows_per_zone=2)
    with pytest.raises(ValueError):
        occupancy_signature(a, rows_per_zone=3)


def test_trait_and_kings_not_coalesced():
    a = BOARD.pack(1, 0, 2, 0, 0)
    black_trait = BOARD.pack(1, 0, 2, 0, 1)
    white_king = BOARD.pack(0, 1, 2, 0, 0)
    assert occupancy_signature(a, rows_per_zone=10) != occupancy_signature(black_trait, rows_per_zone=10)
    assert occupancy_signature(a, rows_per_zone=10) != occupancy_signature(white_king, rows_per_zone=10)
    with pytest.raises(ValueError, match="overlapping"):
        occupancy_signature(BOARD.pack(1, 1, 0, 0, 0), rows_per_zone=10)


def test_pinned_sample_summary(tmp_path):
    r2, hist, sha = _fixtures(tmp_path)
    report = profile(r2, hist, sample_budget=5, expected_sha256=sha)
    assert report["sampled_records"] == report["accepted_sampled_records"] == 5
    assert report["exact_distinct_positions"] == 3
    assert report["gross_manifest_position_records"] == 5
    assert report["classes"]["material_only"]["signature_classes"] == 1
    assert report["classes"]["material_only"]["upper_bound_representatives_removed_if_collapse_all"] == 2
    assert report["classes"]["material_only"]["classes_with_multiple_raw_wdl_labels"] == 1
    assert report["classes"]["rows_per_zone_1"]["signature_classes"] == 2
    assert report["classes"]["rows_per_zone_1"]["distinct_positions_in_multi_position_classes"] == 2
    assert not report["decisional_equivalence_proven"]
    assert not report["position_legality_verified"]


def test_reject_wrong_manifest_sha(tmp_path):
    r2, hist, sha = _fixtures(tmp_path)
    bad = dict(sha)
    bad["historical"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        profile(r2, hist, sample_budget=5, expected_sha256=bad)


def test_source_corruption_fail_closed(tmp_path):
    r2, hist, sha = _fixtures(tmp_path)
    p = hist / "objects/old.jnnw.gz"
    p.write_bytes(p.read_bytes()[:-1])
    with pytest.raises(ValueError, match="digest/size mismatch"):
        profile(r2, hist, sample_budget=5, expected_sha256=sha)


def test_bounds_and_reproducibility(tmp_path):
    r2, hist, sha = _fixtures(tmp_path)
    with pytest.raises(ValueError, match="bounded"):
        profile(r2, hist, sample_budget=100001, expected_sha256=sha)
    first = profile(r2, hist, sample_budget=5, expected_sha256=sha)
    second = profile(r2, hist, sample_budget=5, expected_sha256=sha)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
