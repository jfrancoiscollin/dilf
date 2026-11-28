"""Synthetic-only, off-network snapshot audit fixtures."""
import gzip
import hashlib
import json
import struct

import pytest

from research.mtdp.r2_snapshot_diversity import (
    fen_key, jnnw_key, _quota, profile, BOARD,
)


def rec(wm, wk, bm, bk, stm, wdl):
    return struct.pack("<QQQQBib", wm, wk, bm, bk, stm, 40, wdl)


def add_object(root, path, fmt, content, count, unit="positions"):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    stored = gzip.compress(content) if path.endswith(".gz") else content
    target.write_bytes(stored)
    return {
        "path": path, "format": fmt, "record_count": count,
        "record_count_unit": unit, "stored_bytes": len(stored),
        "stored_sha256": hashlib.sha256(stored).hexdigest(),
        "uncompressed_bytes": len(content),
        "uncompressed_sha256": hashlib.sha256(content).hexdigest(),
    }


def make_tree(tmp_path):
    r2, hist = tmp_path / "r2", tmp_path / "historical"
    r2.mkdir()
    hist.mkdir()
    a = rec(1, 0, 2, 0, 0, 1)
    b = rec(4, 0, 8, 0, 1, 0)
    c = rec(16, 0, 32, 0, 0, 1)
    d = rec(64, 0, 128, 0, 1, -1)
    aa = rec(1, 0, 2, 0, 0, -1)
    binary = b"JNNW" + struct.pack("<I", 3) + a + b + c
    old = b"JNNW" + struct.pack("<I", 2) + aa + d
    fen = b"# positional fixture\nW:W1:B2 # A\nB:W3:B4 # B\n"
    obj1 = add_object(r2, "objects/train.jnnw.gz", "jnnw", binary, 3)
    obj2 = add_object(r2, "objects/positions.fen", "fen", fen, 2)
    obj3 = add_object(hist, "objects/old.jnnw.gz", "jnnw", old, 2)
    metadata = add_object(r2, "objects/sidecar.jsm", "jsm1", b"meta", 10000000,
                          "metadata_rows")
    (r2 / "manifest.json").write_text(json.dumps({
        "schema": "dilf.r2_positions_snapshot.v1",
        "objects": [obj1, obj2, metadata],
        "sources": [{"object_path": obj1["path"]}],
    }))
    (hist / "manifest.json").write_text(json.dumps({
        "schema": "dilf.recovered_positions_snapshot.v1",
        "objects": [obj3],
        "sources": [{"object_path": obj3["path"]}],
    }))
    return r2, hist


def test_cross_snapshot_exact_diversity(tmp_path):
    roots = make_tree(tmp_path)
    result = profile(list(roots), max_sampled=7)
    assert result["expected_position_records"] == 7
    assert result["position_object_count"] == 3
    assert result["sampled_records"] == result["accepted_sampled"] == 7
    assert result["distinct_exact_sampled_positions"] == 4
    assert result["repeated_sample_observations"] == 3
    assert result["distinct_positions_sampled_from_both_snapshots"] == 1
    assert result["distinct_positions_sampled_from_multiple_objects"] == 2
    assert result["distinct_positions_with_divergent_raw_wdl"] == 1
    assert result["manifest_record_counts_including_metadata"]["r2/jsm1"] == 10000000
    assert not result["r2_api_called"] and not result["safe_decision_pruning_claim"]


def test_quota_and_strict_fen():
    assert _quota([4, 4, 1], 2) == [1, 1, 0]
    assert _quota([1, 1, 1], 100) == [1, 1, 1]
    assert fen_key("W:W1,K7:B2 # annotated") == BOARD.pack(1, 1 << 6, 2, 0, 0)
    assert fen_key("B:W3:B4") == jnnw_key(rec(4, 0, 8, 0, 1, 1))[0]
    for bad in ("W:W1:B1", "W:W1,1:B2", "X:W1:B2", "B:W0:B2",
                "B:W1:B51", "W:W1:B2 some trailing text"):
        with pytest.raises(ValueError):
            fen_key(bad)


def test_detect_modified_snapshot(tmp_path):
    r2, hist = make_tree(tmp_path)
    obj = r2 / "objects/train.jnnw.gz"
    obj.write_bytes(obj.read_bytes() + b"x")
    with pytest.raises(ValueError, match="size mismatch"):
        profile([r2, hist], max_sampled=7)


def test_reject_untrusted_source_mapping(tmp_path):
    r2, hist = make_tree(tmp_path)
    p = r2 / "manifest.json"
    m = json.loads(p.read_text())
    m["sources"][0]["object_path"] = "objects/missing.jnnw.gz"
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="missing referenced"):
        profile([r2, hist], max_sampled=7)


def test_reject_symlink(tmp_path):
    r2, hist = make_tree(tmp_path)
    p = r2 / "objects/positions.fen"
    real = r2 / "real.fen"
    p.rename(real)
    p.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        profile([r2, hist], max_sampled=7)


def test_bound_and_invalid_jnnw(tmp_path):
    r2, hist = make_tree(tmp_path)
    with pytest.raises(ValueError, match="budget"):
        profile([r2, hist], max_sampled=100001)
    p = r2 / "objects/train.jnnw.gz"
    invalid = (b"JNNW" + struct.pack("<I", 3) + rec(1, 1, 0, 0, 0, 1)
               + rec(4, 0, 8, 0, 1, 0) + rec(16, 0, 32, 0, 0, 1))
    obj = json.loads((r2 / "manifest.json").read_text())
    obj["objects"][0] = add_object(r2, "objects/train.jnnw.gz", "jnnw", invalid, 3)
    (r2 / "manifest.json").write_text(json.dumps(obj))
    result = profile([r2, hist], max_sampled=7)
    assert result["sampled_records"] == 7
    assert result["rejected_sampled"] == 1
    assert result["sampled_reject_reasons"] == {"overlapping pieces": 1}
