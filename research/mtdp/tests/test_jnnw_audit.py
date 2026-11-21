"""Synthetic structural tests only; no R2 or FMJD execution."""
import struct

import pytest

from research.mtdp.jnnw_audit import inspect


def make_file(tmp_path, rows, *, declared=None):
    p = tmp_path / "sample.jnnw"
    p.write_bytes(struct.pack("<4sI", b"JNNW", len(rows) if declared is None else declared)
                  + b"".join(struct.pack("<QQQQBib", *row) for row in rows))
    return p


def test_valid_and_bounded(tmp_path):
    rows = [(1, 0, 2, 0, 0, 12, 1), (0, 4, 0, 8, 1, -5, -1)]
    report = inspect(make_file(tmp_path, rows), max_records=1)
    assert (report["record_count"], report["records_inspected"], report["records_not_inspected"]) == (2, 1, 1)
    assert report["structural_flags"] == {}
    assert not report["fmjd_legality_verified"]


def test_invalid_bitboards_and_labels(tmp_path):
    p = make_file(tmp_path, [(1 << 50, 0, 0, 0, 2, 0, 3), (1, 1, 0, 0, 1, 0, 0)])
    flags = inspect(p)["structural_flags"]
    assert flags == {"invalid_stm": 1, "invalid_wdl": 1,
                     "outside_50_squares": 1, "overlapping_pieces": 1}


def test_reject_bad_framing(tmp_path):
    p = make_file(tmp_path, [(1, 0, 2, 0, 0, 0, 0)], declared=2)
    with pytest.raises(ValueError, match="length/count"):
        inspect(p)
    p.write_bytes(b"BAD!" + p.read_bytes()[4:])
    with pytest.raises(ValueError, match="magic"):
        inspect(p)


def test_zero_limit_and_negative_limit(tmp_path):
    p = make_file(tmp_path, [(1, 0, 2, 0, 0, 0, 0)])
    assert inspect(p, max_records=0)["records_inspected"] == 0
    with pytest.raises(ValueError, match="nonnegative"):
        inspect(p, max_records=-1)
