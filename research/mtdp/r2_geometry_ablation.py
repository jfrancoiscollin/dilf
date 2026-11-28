"""Read-only H13 geometry ablation on the *same* pinned 100k snapshot sample.

Counts candidate coarse equivalence classes; never assumes that same material/
spatial occupancy implies legal, tactical, or decision equivalence. No engine
and no leakage-sensitive independent-cohort admission.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from research.mtdp.r2_snapshot_diversity import (
    BOARD, POSITION_TYPES, MAX_ROWS_PER_FILE, _quota,
    _path, _digest_file, _scan_jnnw, _scan_fen,
)

# These are verified manifest payloads from the first two byte-identical pilots.
MANIFEST_SHA256 = {
    "r2": "e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c",
    "historical": "e3ed9e2945dd3ff058868968d05343f85cf14ac6565f2180671cc44141768b19",
}
SCHEMAS = {
    "r2": "dilf.r2_positions_snapshot.v1",
    "historical": "dilf.recovered_positions_snapshot.v1",
}
COARSENINGS = (10, 5, 2, 1)  # rows per zone. 10=material-only; 1=row counts.


def occupancy_signature(key: bytes, *, rows_per_zone: int) -> tuple[int, ...]:
    """Count each of W-men, W-kings, B-men, B-kings in contiguous row bands."""
    if rows_per_zone not in COARSENINGS or len(key) != BOARD.size:
        raise ValueError("invalid spatial grouping or board")
    wm, wk, bm, bk, stm = BOARD.unpack(key)
    mask = (1 << 50) - 1
    if stm not in (0, 1) or any(x & ~mask for x in (wm, wk, bm, bk)):
        raise ValueError("bad board encoding")
    if sum(x.bit_count() for x in (wm, wk, bm, bk)) != (wm | wk | bm | bk).bit_count():
        raise ValueError("overlapping pieces")
    values = [stm]
    for bb in (wm, wk, bm, bk):
        for start in range(0, 10, rows_per_zone):
            width = min(rows_per_zone, 10 - start) * 5
            zone = ((1 << width) - 1) << (start * 5)
            values.append((bb & zone).bit_count())
    return tuple(values)


def _classes(positions: dict[bytes, tuple[set[str], set[int]]], rows: int) -> dict:
    groups: dict[tuple[int, ...], list[bytes]] = defaultdict(list)
    for key in positions:
        groups[occupancy_signature(key, rows_per_zone=rows)].append(key)
    size_histogram = Counter()
    multi_label_classes = 0
    cross_snapshot_classes = 0
    ambiguous = 0
    largest = 0
    for keys in groups.values():
        n = len(keys)
        largest = max(largest, n)
        if n == 1:
            size_histogram["1"] += 1
            continue
        ambiguous += n
        size_histogram["2"] += int(n == 2)
        size_histogram["3-9"] += int(3 <= n < 10)
        size_histogram["10-99"] += int(10 <= n < 100)
        size_histogram["100+"] += int(n >= 100)
        origin = set()
        labels = set()
        for key in keys:
            origin.update(positions[key][0])
            labels.update(positions[key][1])
        if len(origin) >= 2:
            cross_snapshot_classes += 1
        if len(labels) > 1:
            multi_label_classes += 1
    n = len(positions)
    return {
        "rows_per_zone": rows,
        "zones_per_side_piece_type": (10 + rows - 1) // rows,
        "distinct_positions": n,
        "signature_classes": len(groups),
        "classes_with_multiple_distinct_positions": sum(len(v) > 1 for v in groups.values()),
        "distinct_positions_in_multi_position_classes": ambiguous,
        "largest_class_distinct_positions": largest,
        "upper_bound_representatives_removed_if_collapse_all": n - len(groups),
        "classes_with_multiple_raw_wdl_labels": multi_label_classes,
        "multi_position_classes_with_both_snapshots": cross_snapshot_classes,
        "class_size_histogram": dict(sorted(size_histogram.items())),
    }


def profile(r2: Path, historical: Path, *, sample_budget: int = 100_000,
            expected_sha256: dict[str, str] | None = None) -> dict:
    if not 0 < sample_budget <= 100_000:
        raise ValueError("sample budget outside bounded preregistered limit")
    allowed = MANIFEST_SHA256 if expected_sha256 is None else expected_sha256
    entries = []
    manifest_sha = {}
    for label, root in (("r2", r2), ("historical", historical)):
        payload = (root / "manifest.json").read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != allowed[label]:
            raise ValueError("manifest SHA-256 mismatch: " + label)
        manifest_sha[label] = digest
        manifest = json.loads(payload)
        if manifest.get("schema") != SCHEMAS[label]:
            raise ValueError("wrong snapshot schema")
        objects = manifest["objects"]
        if len({obj["path"] for obj in objects}) != len(objects):
            raise ValueError("repeated object path")
        known_paths = {obj["path"] for obj in objects}
        if any(src["object_path"] not in known_paths for src in manifest["sources"]):
            raise ValueError("dangling object mapping")
        for obj in objects:
            if obj["format"] in POSITION_TYPES:
                if obj.get("record_count_unit") != "positions":
                    raise ValueError("position unit mismatch")
                if not 0 <= obj["record_count"] <= MAX_ROWS_PER_FILE:
                    raise ValueError("invalid declared row count")
                entries.append((label, root, obj))
    counts = [obj["record_count"] for _, _, obj in entries]
    quotas = _quota(counts, sample_budget)
    # Exact keys are NOT exported. Source snapshot identity and raw labels are
    # attributes of a sampled position, never features in its spatial signature.
    positions: dict[bytes, tuple[set[str], set[int]]] = {}
    rejects = Counter()
    accepted = 0
    sampled = 0
    for (label, root, obj), quota in zip(entries, quotas):
        f = _path(root, obj["path"])
        if f.stat().st_size != obj["stored_bytes"] or _digest_file(f) != obj["stored_sha256"]:
            raise ValueError("stored object digest/size mismatch")
        def consume(key, wdl, issue):
            nonlocal accepted, sampled
            sampled += 1
            if issue is not None:
                rejects[issue] += 1
                return
            accepted += 1
            record = positions.get(key)
            if record is None:
                record = (set(), set())
                positions[key] = record
            record[0].add(label)
            if wdl is not None:
                record[1].add(wdl)
        got = (_scan_jnnw(f, obj, quota, consume)
               if obj["format"] == "jnnw" else _scan_fen(f, obj, quota, consume))
        if got != quota:
            raise ValueError("sample selection mismatch")
    if sampled != min(sum(counts), sample_budget):
        raise ValueError("sample total mismatch")
    # Same committed inputs, selection, parser, sample; disallow accidental
    # drift from the twice-replicated 100k descriptive baseline.
    if expected_sha256 is None and sample_budget == 100_000:
        if (sampled, accepted, len(positions)) != (100_000, 100_000, 98_306):
            raise ValueError("snapshot baseline reconciliation failed")
    classes = {
        ("material_only" if rows == 10 else f"rows_per_zone_{rows}"): _classes(positions, rows)
        for rows in COARSENINGS
    }
    return {
        "schema": "mtdp.h13_geometry_coarsening_v1",
        "method": "same-pinned-proportional-evenly-spaced-100k-v1",
        "source_manifest_sha256": manifest_sha,
        "gross_manifest_position_records": sum(counts),
        "sampled_records": sampled,
        "accepted_sampled_records": accepted,
        "rejected_sampled_records": sampled - accepted,
        "sample_rejections": dict(sorted(rejects.items())),
        "exact_distinct_positions": len(positions),
        "identity_includes_side_to_move_and_king_type": True,
        "classes": classes,
        "scope": "descriptive feature collisions; class merging never performed",
        "position_legality_verified": False,
        "independent_games_proven": False,
        "decisional_equivalence_proven": False,
        "measured_search_nodes_saved": False,
        "raw_wdl_is_not_independent_reference": True,
        "representative_population_inference": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--r2", required=True, type=Path)
    p.add_argument("--historical", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    report = profile(a.r2, a.historical)
    with a.output.open("x", encoding="utf-8") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"sampled": report["sampled_records"],
                      "exact_distinct": report["exact_distinct_positions"],
                      "classes": {k: v["signature_classes"] for k, v in report["classes"].items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
