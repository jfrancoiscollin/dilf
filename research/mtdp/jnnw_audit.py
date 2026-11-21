"""Read-only, bounded structural audit for Jass JNNW v1 files.

Schema source: jfrancoiscollin/jass@f1c1f892, pattern_jass/tools/train_stream.py.
Structural checks are NOT FMJD legality or independent-game certification.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import struct

HEADER = struct.Struct("<4sI")
RECORD = struct.Struct("<QQQQBib")
MAGIC = b"JNNW"
BOARD_MASK = (1 << 50) - 1


def inspect(path: str | Path, *, max_records: int = 1000) -> dict:
    """Validate file framing, then sample at most max_records records from start."""
    if max_records < 0:
        raise ValueError("max_records must be nonnegative")
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular file required")
    size = path.stat().st_size
    if size < HEADER.size:
        raise ValueError("truncated header")
    with path.open("rb") as stream:
        magic, count = HEADER.unpack(stream.read(HEADER.size))
        if magic != MAGIC:
            raise ValueError("bad JNNW magic")
        if size != HEADER.size + count * RECORD.size:
            raise ValueError("JNNW length/count mismatch")
        reasons: dict[str, int] = {}
        scanned = 0
        for _ in range(min(count, max_records)):
            raw = stream.read(RECORD.size)
            if len(raw) != RECORD.size:
                raise ValueError("truncated record")
            wm, wk, bm, bk, stm, score, wdl = RECORD.unpack(raw)
            scanned += 1
            bad = []
            if (wm | wk | bm | bk) & ~BOARD_MASK:
                bad.append("outside_50_squares")
            if (wm & wk) or (wm & bm) or (wm & bk) or (wk & bm) or (wk & bk) or (bm & bk):
                bad.append("overlapping_pieces")
            if stm not in (0, 1):
                bad.append("invalid_stm")
            if wdl not in (-1, 0, 1):
                bad.append("invalid_wdl")
            for reason in bad:
                reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "schema": "mtdp.jnnw_structural_audit.v1",
        "source_format": "jass.jnnw.38b",
        "record_count": count,
        "file_size_bytes": size,
        "records_inspected": scanned,
        "records_not_inspected": count - scanned,
        "structural_flags": dict(sorted(reasons.items())),
        "fmjd_legality_verified": False,
        "trajectory_verified": False,
        "independent_cohort_qualified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--max-records", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(inspect(args.file, max_records=args.max_records), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
