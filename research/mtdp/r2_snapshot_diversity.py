"""Read-only diversity pilot for GitHub-published Jass R2 + historical snapshots.

Checks file SHA-256, gzip integrity and JNNW framing; samples deterministic
record indices. No R2 calls, FMJD legality tests, score-based selection,
engine invocations, confidence intervals or strategic-equivalence claims.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

RECORD = struct.Struct("<QQQQBib")
HEADER = struct.Struct("<4sI")
BOARD = struct.Struct("<QQQQB")
BOARD_MASK = (1 << 50) - 1
FEN_RE = re.compile(r"^([WB]):W([^:]*):B([^:]*)$")
MAX_SAMPLE = 100_000
MAX_ROWS_PER_FILE = 20_000_000
POSITION_TYPES = {"jnnw", "fen"}


def _digest_file(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def _path(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel.startswith("objects/") or ".." in Path(rel).parts:
        raise ValueError("unsafe object path")
    dest = root / rel
    if not dest.is_file() or any(part.is_symlink() for part in (dest, *dest.parents)):
        raise ValueError("missing, nonregular or symlinked source")
    if not dest.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise ValueError("path escapes snapshot root")
    return dest


def _parse_piece_list(text: str) -> tuple[int, int]:
    men = kings = 0
    if not text:
        return men, kings
    for token in text.split(","):
        if not re.fullmatch(r"K?(?:[1-9]|[1-4]\d|50)", token):
            raise ValueError("invalid FEN square")
        king = token.startswith("K")
        sq = int(token[1:] if king else token)
        bit = 1 << (sq - 1)
        if (men | kings) & bit:
            raise ValueError("repeated square")
        if king:
            kings |= bit
        else:
            men |= bit
    return men, kings


def fen_key(line: str) -> bytes:
    """Canonical 33-byte key; only strictly parseable FMJD-style position FEN."""
    s = line.split("#", 1)[0].strip()
    match = FEN_RE.fullmatch(s)
    if not match:
        raise ValueError("unrecognized FEN structure")
    stm, white, black = match.groups()
    wm, wk = _parse_piece_list(white)
    bm, bk = _parse_piece_list(black)
    if (wm | wk) & (bm | bk):
        raise ValueError("piece collision")
    return BOARD.pack(wm, wk, bm, bk, 0 if stm == "W" else 1)


def jnnw_key(raw: bytes) -> tuple[bytes, int]:
    wm, wk, bm, bk, stm, _score, wdl = RECORD.unpack(raw)
    if (wm | wk | bm | bk) & ~BOARD_MASK:
        raise ValueError("outside 50 squares")
    if sum(x.bit_count() for x in (wm, wk, bm, bk)) != (wm | wk | bm | bk).bit_count():
        raise ValueError("overlapping pieces")
    if stm not in (0, 1):
        raise ValueError("invalid side to move")
    if wdl not in (-1, 0, 1):
        raise ValueError("invalid WDL")
    return BOARD.pack(wm, wk, bm, bk, stm), wdl


def _samples(count: int, quota: int):
    if quota == 0:
        return iter(())
    return ((i * count) // quota for i in range(quota))


def _quota(counts: list[int], max_sampled: int) -> list[int]:
    """Proportional fixed-size quotas, deterministic largest-remainder tie breaks."""
    available = sum(counts)
    budget = min(max_sampled, available)
    if not available:
        return [0] * len(counts)
    base = [(budget * n) // available for n in counts]
    missing = budget - sum(base)
    order = sorted(range(len(counts)),
                   key=lambda i: (-((budget * counts[i]) % available), i))
    # Tie break is deterministic; never allocate above a file's row count.
    for i in order[:missing]:
        base[i] += 1
    return base


def _scan_jnnw(path: Path, obj: dict, quota: int, consume):
    digest = hashlib.sha256()
    total_bytes = 0
    inspected = 0
    with gzip.open(path, "rb") as fh:
        header = fh.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("truncated JNNW header")
        magic, count = HEADER.unpack(header)
        if magic != b"JNNW" or count != obj["record_count"]:
            raise ValueError("JNNW header/manifest mismatch")
        if count > MAX_ROWS_PER_FILE:
            raise ValueError("JNNW row safety ceiling exceeded")
        digest.update(header)
        total_bytes += len(header)
        picks = _samples(count, quota)
        target = next(picks, None)
        offset_records = 0
        while offset_records < count:
            n = min(65536, count - offset_records)
            chunk = fh.read(n * RECORD.size)
            if len(chunk) != n * RECORD.size:
                raise ValueError("truncated JNNW records")
            digest.update(chunk)
            total_bytes += len(chunk)
            while target is not None and target < offset_records + n:
                at = (target - offset_records) * RECORD.size
                try:
                    key, wdl = jnnw_key(chunk[at:at + RECORD.size])
                    consume(key, wdl, None)
                except ValueError as error:
                    consume(None, None, str(error))
                inspected += 1
                target = next(picks, None)
            offset_records += n
        if fh.read(1):
            raise ValueError("extra decompressed JNNW data")
    if total_bytes != obj["uncompressed_bytes"]:
        raise ValueError("JNNW uncompressed length mismatch")
    if digest.hexdigest() != obj["uncompressed_sha256"]:
        raise ValueError("JNNW uncompressed SHA-256 mismatch")
    return inspected


def _scan_fen(path: Path, obj: dict, quota: int, consume):
    rows = []
    with path.open("rb") as fh:
        raw = fh.read()
    if len(raw) != obj["uncompressed_bytes"]:
        raise ValueError("FEN source length mismatch")
    if hashlib.sha256(raw).hexdigest() != obj["uncompressed_sha256"]:
        raise ValueError("FEN uncompressed SHA-256 mismatch")
    for line in raw.decode("utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            rows.append(line)
    if len(rows) != obj["record_count"]:
        raise ValueError("FEN line count does not match manifest")
    for index in _samples(len(rows), quota):
        try:
            consume(fen_key(rows[index]), None, None)
        except ValueError as error:
            consume(None, None, str(error))
    return quota


def profile(snapshot_roots: list[Path], *, max_sampled: int = MAX_SAMPLE) -> dict:
    if not 0 < max_sampled <= MAX_SAMPLE:
        raise ValueError("pilot sample budget must be 1..100000")
    entries = []
    sources = []
    manifest_shas = {}
    format_counts = Counter()
    for label, root in (("r2", snapshot_roots[0]), ("historical", snapshot_roots[1])):
        raw = (root / "manifest.json").read_bytes()
        manifest = json.loads(raw)
        expected = {"r2": "dilf.r2_positions_snapshot.v1",
                    "historical": "dilf.recovered_positions_snapshot.v1"}[label]
        if manifest.get("schema") != expected:
            raise ValueError("unexpected snapshot manifest schema")
        manifest_shas[label] = hashlib.sha256(raw).hexdigest()
        objects = manifest["objects"]
        if len({x["path"] for x in objects}) != len(objects):
            raise ValueError("duplicate manifest object path")
        lookup = {x["path"]: x for x in objects}
        for src in manifest["sources"]:
            if src["object_path"] not in lookup:
                raise ValueError("missing referenced snapshot object")
        sources.append(len(manifest["sources"]))
        for obj in objects:
            fmt = obj["format"]
            format_counts[f"{label}/{fmt}"] += obj.get("record_count", 0)
            if fmt in POSITION_TYPES:
                if obj["record_count_unit"] != "positions":
                    raise ValueError("invalid unit for positional object")
                if not 0 <= obj["record_count"] <= MAX_ROWS_PER_FILE:
                    raise ValueError("invalid file row count")
                entries.append((label, root, obj))
    quotas = _quota([x[2]["record_count"] for x in entries], max_sampled)
    exact = {}
    errors = Counter()
    by_group = Counter()
    by_format = Counter()
    material = Counter()
    labels = Counter()
    results = []
    sampled = 0
    accepted = 0
    for (group, root, obj), quota in zip(entries, quotas):
        path = _path(root, obj["path"])
        if path.stat().st_size != obj["stored_bytes"]:
            raise ValueError("stored file byte size mismatch")
        if _digest_file(path) != obj["stored_sha256"]:
            raise ValueError("stored file SHA-256 mismatch")
        local_accepted = 0
        local_rejected = 0

        def consume(key, wdl, issue, *, name=obj["path"], origin=group):
            nonlocal sampled, accepted, local_accepted, local_rejected
            sampled += 1
            if issue:
                errors[issue] += 1
                local_rejected += 1
                return
            accepted += 1
            local_accepted += 1
            by_group[origin] += 1
            by_format[obj["format"]] += 1
            wm, wk, bm, bk, stm = BOARD.unpack(key)
            material[str((wm | wk | bm | bk).bit_count())] += 1
            if wdl is not None:
                labels[str(wdl)] += 1
            prior = exact.get(key)
            if prior is None:
                exact[key] = [1, {origin}, {name}, set() if wdl is None else {wdl}]
            else:
                prior[0] += 1
                prior[1].add(origin)
                prior[2].add(name)
                if wdl is not None:
                    prior[3].add(wdl)

        got = (_scan_jnnw(path, obj, quota, consume) if obj["format"] == "jnnw"
               else _scan_fen(path, obj, quota, consume))
        if got != quota:
            raise ValueError("sample count mismatch")
        results.append({"snapshot": group, "object": obj["path"],
                        "format": obj["format"], "declared_records": obj["record_count"],
                        "sampled": got, "accepted": local_accepted,
                        "rejected": local_rejected, "verified_file_sha256": True})
    return {
        "schema": "mtdp.r2_published_snapshots_pilot.v1",
        "method": "proportional_evenly_spaced_indices_per_file_v1",
        "sampling_bias": "Deterministic nonrandom convenience sample; no game-level independence or population inference.",
        "manifest_sha256": manifest_shas,
        "source_mapping_counts": {"r2": sources[0], "historical": sources[1]},
        "manifest_record_counts_including_metadata": dict(sorted(format_counts.items())),
        "expected_position_records": sum(x[2]["record_count"] for x in entries),
        "position_object_count": len(entries),
        "sampled_records": sampled,
        "accepted_sampled": accepted,
        "rejected_sampled": sampled - accepted,
        "sampled_reject_reasons": dict(sorted(errors.items())),
        "distinct_exact_sampled_positions": len(exact),
        "repeated_sample_observations": accepted - len(exact),
        "distinct_positions_sampled_from_both_snapshots":
            sum(len(v[1]) > 1 for v in exact.values()),
        "distinct_positions_sampled_from_multiple_objects":
            sum(len(v[2]) > 1 for v in exact.values()),
        "distinct_positions_with_divergent_raw_wdl":
            sum(len(v[3]) > 1 for v in exact.values()),
        "sampled_by_snapshot": dict(sorted(by_group.items())),
        "sampled_by_format": dict(sorted(by_format.items())),
        "sampled_by_material_count": dict(sorted(material.items(), key=lambda x: int(x[0]))),
        "sampled_by_raw_wdl": dict(sorted(labels.items())),
        "source_objects_verified": results,
        "r2_api_called": False,
        "raw_replay_legal_proof": False,
        "independent_game_cohort_qualified": False,
        "safe_decision_pruning_claim": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r2", type=Path, required=True, help="already-local 2026-11-21 root")
    parser.add_argument("--historical", type=Path, required=True,
                        help="already-local recovered-2026-06-20 root")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-sampled", type=int, default=MAX_SAMPLE)
    a = parser.parse_args()
    report = profile([a.r2, a.historical], max_sampled=a.max_sampled)
    with a.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({k: report[k] for k in (
        "expected_position_records", "sampled_records", "accepted_sampled",
        "distinct_exact_sampled_positions", "distinct_positions_sampled_from_both_snapshots")},
        sort_keys=True))


if __name__ == "__main__":
    main()
