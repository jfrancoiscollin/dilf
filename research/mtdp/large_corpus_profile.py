"""Offline bounded JNNW diversity pilot on already-local R2 source copies.

No network access, game independence proof, legal replay or move evaluation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from research.mtdp.jnnw_audit import HEADER, RECORD, BOARD_MASK
from research.mtdp.r2_source_preflight import validate_manifest

DEFAULT_MAX_SAMPLED = 100_000
DEFAULT_MAX_DECLARED = 20_000_000


def _problems(wm: int, wk: int, bm: int, bk: int, stm: int, wdl: int) -> list[str]:
    reasons = []
    if (wm | wk | bm | bk) & ~BOARD_MASK:
        reasons.append("outside_50_squares")
    if sum(x.bit_count() for x in (wm, wk, bm, bk)) != (wm | wk | bm | bk).bit_count():
        reasons.append("overlapping_pieces")
    if stm not in (0, 1):
        reasons.append("invalid_stm")
    if wdl not in (-1, 0, 1):
        reasons.append("invalid_wdl")
    return reasons


def _source_file(root: Path, key: str) -> Path:
    if key.startswith("/") or ".." in Path(key).parts:
        raise ValueError("unsafe source key")
    root = root.resolve(strict=True)
    path = root / key
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"missing, nonregular or symlinked local source: {key}")
    if not path.resolve(strict=True).is_relative_to(root):
        raise ValueError("source path escapes local root")
    return path


def profile(
    manifest: str | Path,
    local_root: str | Path,
    *,
    max_sampled: int = DEFAULT_MAX_SAMPLED,
    max_declared_per_file: int = DEFAULT_MAX_DECLARED,
) -> dict[str, Any]:
    if max_sampled < 0 or max_sampled > 100_000:
        raise ValueError("max_sampled must be between zero and preregistered pilot ceiling 100000")
    if max_declared_per_file < 1:
        raise ValueError("max_declared_per_file must be positive")
    preflight = validate_manifest(manifest)
    keys = preflight["source_keys"]
    root = Path(local_root)
    paths = [_source_file(root, key) for key in keys]
    nfiles = len(keys)
    quotas = [max_sampled // nfiles + (i < max_sampled % nfiles) for i in range(nfiles)]
    flags = Counter()
    total_seen = 0
    sampled = 0
    valid_sampled = 0
    by_material = Counter()
    by_stm = Counter()
    by_wdl = Counter()
    positions: dict[bytes, tuple[int, set[int], set[int]]] = {}
    file_stats = []
    for i, (key, path) in enumerate(zip(keys, paths)):
        file_flags = Counter()
        local_size = path.stat().st_size
        with path.open("rb") as stream:
            compressed_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        with gzip.open(path, "rb") as stream:
            raw_header = stream.read(HEADER.size)
            if len(raw_header) != HEADER.size:
                raise ValueError(f"truncated JNNW header: {key}")
            magic, count = HEADER.unpack(raw_header)
            if magic != b"JNNW":
                raise ValueError(f"invalid JNNW magic: {key}")
            if count > max_declared_per_file:
                raise ValueError(f"declared count exceeds safety ceiling: {key}")
            quota = min(quotas[i], count)
            next_sample = 0
            for index in range(count):
                raw = stream.read(RECORD.size)
                if len(raw) != RECORD.size:
                    raise ValueError(f"truncated JNNW record {index}: {key}")
                wm, wk, bm, bk, stm, score, wdl = RECORD.unpack(raw)
                reasons = _problems(wm, wk, bm, bk, stm, wdl)
                file_flags.update(reasons)
                total_seen += 1
                # Full sequential gzip decompression; only keep bounded indices.
                if next_sample >= quota or index != (next_sample * count) // quota:
                    continue
                next_sample += 1
                sampled += 1
                if reasons:
                    continue
                valid_sampled += 1
                by_material[str(sum(x.bit_count() for x in (wm, wk, bm, bk)))] += 1
                by_stm[str(stm)] += 1
                by_wdl[str(wdl)] += 1
                board = raw[:33]  # Four bitboards + side to move; exclude score and WDL.
                if board not in positions:
                    positions[board] = (1, {i}, {wdl})
                else:
                    occurrences, files, labels = positions[board]
                    files.add(i)
                    labels.add(wdl)
                    positions[board] = (occurrences + 1, files, labels)
            if stream.read(1):
                raise ValueError(f"extra uncompressed bytes after declared records: {key}")
        flags.update(file_flags)
        file_stats.append({
            "source_key": key,
            "compressed_sha256_local": compressed_sha256,
            "compressed_size_bytes_local": local_size,
            "declared_and_read_records": count,
            "sampled_records": next_sample,
            "structural_flags_all_records": dict(sorted(file_flags.items())),
        })
    return {
        "schema": "mtdp.local_jnnw_diversity_pilot.v1",
        "source_manifest_schema": "mtdp.r2_source_inventory.v1",
        "local_sources_hashed": len(file_stats),
        "r2_access_performed": False,
        "r2_remote_identity_authenticated": False,
        "external_game_identity_authenticated": False,
        "fmjd_legality_verified": False,
        "trajectory_verified": False,
        "independent_cohort_qualified": False,
        "safe_strategic_compression_claim": False,
        "sampling_method": "per_source_evenly_spaced_record_indices_v1",
        "sampling_note": "Nonrandom; equal per-file quotas; not a representative sample or game-level split.",
        "full_streamed_records": total_seen,
        "sampled_records": sampled,
        "valid_sampled_records": valid_sampled,
        "invalid_sampled_records": sampled - valid_sampled,
        "structural_flags_all_streamed_records": dict(sorted(flags.items())),
        "distinct_exact_sampled_positions": len(positions),
        "sampled_duplicate_occurrences": valid_sampled - len(positions),
        "exact_positions_with_repeated_occurrences": sum(v[0] > 1 for v in positions.values()),
        "exact_positions_seen_in_multiple_files": sum(len(v[1]) > 1 for v in positions.values()),
        "exact_positions_with_multiple_raw_wdl_labels": sum(len(v[2]) > 1 for v in positions.values()),
        "raw_label_note": "Raw WDL disagreement, not an error or strategic decision disagreement.",
        "sampled_by_total_piece_count": dict(sorted(by_material.items(), key=lambda kv: int(kv[0]))),
        "sampled_by_side_to_move": dict(sorted(by_stm.items())),
        "sampled_by_raw_wdl": dict(sorted(by_wdl.items())),
        "sources": file_stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--local-root", type=Path, required=True,
                        help="local mirror containing files at manifest-relative paths")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-sampled", type=int, default=DEFAULT_MAX_SAMPLED)
    args = parser.parse_args()
    result = profile(args.manifest, args.local_root, max_sampled=args.max_sampled)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({"sampled": result["sampled_records"],
                      "distinct": result["distinct_exact_sampled_positions"],
                      "record_count": result["full_streamed_records"]}, sort_keys=True))


if __name__ == "__main__":
    main()
