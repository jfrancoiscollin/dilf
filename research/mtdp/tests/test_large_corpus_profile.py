"""Offline synthetic tests; no Cloudflare read or corpus-size claims."""
import gzip
import json
import struct

import pytest

from research.mtdp.large_corpus_profile import profile
from research.mtdp.r2_source_preflight import EXPECTED_PREFIXES


def fixture(tmp_path, rows_by_file):
    objects = []
    for i in range(5):
        for gen in ("g1", "g2"):
            key = f"{EXPECTED_PREFIXES[f'c{i}']}/artefacts/{gen}-selfplay.jnnw.gz"
            idx = len(objects)
            rows = rows_by_file.get(idx, [(1 << idx, 0, 0, 1 << (idx + 11), 0, 1, 1)])
            target = tmp_path / key
            target.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(target, "wb") as f:
                f.write(struct.pack("<4sI", b"JNNW", len(rows)))
                for row in rows:
                    f.write(struct.pack("<QQQQBib", *row))
            objects.append({"cell": f"c{i}", "generation": gen,
                            "key": key, "verified_present": False, "sha256": None})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema": "mtdp.r2_source_inventory.v1",
                                    "bucket": "jass-data", "objects": objects}))
    return manifest


def test_diversity_and_cross_file_repeat(tmp_path):
    a = (1, 0, 2, 0, 0, 10, 1)
    b = (1, 0, 2, 0, 0, 40, -1)  # Same board+stm, different score and WDL.
    c = (4, 0, 8, 0, 1, 0, 0)
    manifest = fixture(tmp_path, {0: [a, b, c], 1: [a, c]})
    out = profile(manifest, tmp_path, max_sampled=100)
    assert out["full_streamed_records"] == 13
    assert out["sampled_records"] == 13
    assert out["distinct_exact_sampled_positions"] == 10
    assert out["sampled_duplicate_occurrences"] == 3
    assert out["exact_positions_seen_in_multiple_files"] == 2
    assert out["exact_positions_with_multiple_raw_wdl_labels"] == 1
    assert not out["r2_access_performed"] and not out["safe_strategic_compression_claim"]


def test_bounded_sampling_and_invalid_flags(tmp_path):
    rows = [(1, 0, 2, 0, 0, 0, 0) for _ in range(11)]
    rows[5] = (1 << 50, 0, 0, 0, 2, 0, 3)
    manifest = fixture(tmp_path, {0: rows})
    out = profile(manifest, tmp_path, max_sampled=20)
    assert out["sampled_records"] == 11
    assert out["structural_flags_all_streamed_records"] == {
        "invalid_stm": 1, "invalid_wdl": 1, "outside_50_squares": 1}
    assert out["valid_sampled_records"] <= 11
    with pytest.raises(ValueError, match="ceiling"):
        profile(manifest, tmp_path, max_sampled=100001)


def test_truncated_gzip_rejected(tmp_path):
    manifest = fixture(tmp_path, {})
    key = json.loads(manifest.read_text())["objects"][0]["key"]
    p = tmp_path / key
    p.write_bytes(p.read_bytes()[:-6])
    with pytest.raises((EOFError, OSError, ValueError)):
        profile(manifest, tmp_path)


def test_source_symlink_rejected(tmp_path):
    manifest = fixture(tmp_path, {})
    key = json.loads(manifest.read_text())["objects"][0]["key"]
    p = tmp_path / key
    real = tmp_path / "real.gz"
    p.rename(real)
    p.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        profile(manifest, tmp_path)
