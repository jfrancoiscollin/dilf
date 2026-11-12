"""Build a reproducible freeze for the next eligible finished 5+0 arena."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.depth_sensitivity import read_input
from research.mtdp.jass_benchmark.geometry_ablation import freeze, write_json
from research.mtdp.jass_cohort import ADAPTER_COMMIT

BASELINE = Path("data/exports/pcblues/pcblues_games.pdn")
SEVENTH = Path("research/mtdp/jass_benchmark/seventh-pRW2Ahpz/provenance.json")
PROTOCOL = "79e389aad3b7e58e110f19a38df6d5a58d83f5d3"
SPATIAL_JASS_CUTOFF = int(datetime.fromisoformat("2026-11-12T23:00:00+00:00").timestamp() * 1000)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def require_next_candidate(log, metadata, used, rejected, *, cutoff=0):
    outstanding = [row for row in log["candidate_log"]
                   if row["candidate_status"] in ("needs_pdn_and_replay", "pending_finish")
                   and row["id"] not in used and row["id"] not in rejected
                   and row["starts_at"] >= cutoff]
    if not outstanding or outstanding[0]["candidate_status"] != "needs_pdn_and_replay":
        raise ValueError("The next chronological candidate is not finished in the listing")
    candidate = outstanding[0]
    start = int(datetime.fromisoformat(metadata["startsAt"].replace("Z", "+00:00")).timestamp() * 1000)
    if (metadata["id"] != candidate["id"] or start != candidate["starts_at"]
            or not metadata.get("isFinished") or metadata["variant"] != "standard"
            or metadata["clock"] != {"limit": 300, "increment": 0}):
        raise ValueError("Detail metadata does not match the next finished standard 5+0 candidate")


def previous_inputs(provenances, pdn_dir, adapter):
    baseline = provenances[0]
    exclusions = [*baseline["inputs"]["exclusions"], *baseline["inputs"]["event"]]
    expected = {row["file"]: row["sha256"] for row in exclusions}
    manifest_hashes = dict(baseline["prior_manifests"])
    for index, provenance in enumerate(provenances):
        if index:
            old = {row["file"]: row["sha256"] for row in provenance["inputs"]["exclusions"]}
            if old != expected:
                raise ValueError("Earlier freeze has a different exclusion inventory")
            (event,) = provenance["inputs"]["event"]
            if event["file"] in expected or event["sha256"] in expected.values():
                raise ValueError("Reused earlier PDN")
            exclusions.append(event)
            expected[event["file"]] = event["sha256"]
        for shard in provenance["eligible_shards"]:
            read_input(shard)
            manifest_hashes[shard["path"]] = shard["stored_sha256"]
    (record,) = baseline["inputs"]["baseline"]
    if record["file"] != BASELINE.name or sha256(BASELINE.read_bytes()) != record["sha256"]:
        raise ValueError("PC Blues input digest changed")
    paths = []
    for record in exclusions:
        directory = pdn_dir if record["file"].startswith("mtdp-lidraughts-") else adapter / "docs/parties"
        path = directory / record["file"]
        if sha256(path.read_bytes()) != record["sha256"]:
            raise ValueError(f"Prior PDN digest changed: {path}")
        paths.append(path)
    fens = set()
    for name, digest in manifest_hashes.items():
        path = Path(name)
        raw = path.read_bytes()
        if sha256(raw) != digest:
            raise ValueError(f"Prior manifest digest changed: {path}")
        payload = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
        if isinstance(payload, list):
            fens.update(row["fen"] for row in payload)
        else:
            fens.update(row["target_fen"] for row in payload["targets"])
    return paths, fens, expected, manifest_hashes


def package(output, summary, rows, score_plan, game_audit, provenance):
    output.mkdir(parents=True, exist_ok=False)

    def archive(name, value):
        path = output / f"{name}.json.gz"
        raw = json_bytes(value)
        stored = gzip.compress(raw, compresslevel=9, mtime=0)
        path.write_bytes(stored)
        return {"path": str(path), "stored_sha256": sha256(stored), "content_sha256": sha256(raw)}

    report = {**summary, **provenance,
              "eligible_sha256": sha256(json_bytes(rows)),
              "eligible_shards": [archive(f"eligible-{start // 800:02d}", rows[start:start + 800])
                                  for start in range(0, len(rows), 800)],
              "score_plan": archive("score-plan", score_plan), "game_audit": archive("game-audit", game_audit)}
    write_json(output / "provenance.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate-log", "event-metadata", "pdn", "pdn-dir", "adapter", "scan", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--downloaded-at", required=True)
    parser.add_argument("--pdn-repeat", type=Path)
    parser.add_argument("--previous-freeze", action="append", default=[], type=Path)
    parser.add_argument("--spatial-jass", action="store_true", help="Freeze the prospective Jass arena")
    parser.add_argument("--rejections", type=Path, help="JSON mapping of earlier rejected event IDs to recorded reasons")
    args = parser.parse_args()
    later = [json.loads(path.read_text()) for path in args.previous_freeze]
    if args.spatial_jass:
        if [row["event"]["id"] for row in later] != ["xAnBIxHN", "MoXhmT9b", "MIDBy9dl"]:
            parser.error("Spatial Jass requires all three eighth-study freezes in order")
    elif len(later) > 2:
        parser.error("The protocol requires exactly three events")
    used = {row["event"]["id"] for row in later}
    raw_log, raw_meta = args.candidate_log.read_bytes(), args.event_metadata.read_bytes()
    metadata = json.loads(raw_meta)
    rejected = json.loads(args.rejections.read_text()) if args.rejections else {}
    if not isinstance(rejected, dict) or any(not isinstance(reason, str) or not reason.strip()
                                              for reason in rejected.values()):
        parser.error("Every rejected event needs a reason")
    require_next_candidate(json.loads(raw_log), metadata, used, rejected,
                           cutoff=SPATIAL_JASS_CUTOFF if args.spatial_jass else 0)
    revision = subprocess.check_output(["git", "-C", args.adapter, "rev-parse", "HEAD"], text=True).strip()
    if revision != ADAPTER_COMMIT:
        raise ValueError("draught-master is not at the pinned adapter revision")
    old = json.loads(SEVENTH.read_text())
    scan_dir = args.scan.resolve().parent
    hashes = {name: sha256(path.read_bytes()) for name, path in (
        ("scan_linux", args.scan), ("scan.ini", scan_dir / "scan.ini"), ("data/eval", scan_dir / "data/eval"),
    )}
    if hashes != old["scan_sha256"]:
        raise ValueError("Scan binary or configuration digest changed")
    exclusions, prior_fens, prior_pdns, manifest_hashes = previous_inputs([old, *later], args.pdn_dir, args.adapter)
    raw_pdn = args.pdn.read_bytes()
    event = metadata["id"]
    if args.pdn.name != f"mtdp-lidraughts-{event}.pdn" or not raw_pdn:
        raise ValueError("Expected a nonempty PDN for the finished candidate")
    if args.pdn_repeat and raw_pdn != args.pdn_repeat.read_bytes():
        raise ValueError("Repeat PDN download has different bytes")
    if sha256(raw_pdn) in {*prior_pdns.values(), sha256(BASELINE.read_bytes())}:
        raise ValueError("The event PDN duplicates an earlier export")
    summary, rows, plan, audit = freeze(BASELINE, exclusions, args.pdn, prior_fens, create_engine(),
                                       mover_occupancy=True)
    if not summary["inputs"]["event"][0]["accepted"]:
        raise ValueError("Event has no validated games")
    selection_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    package(args.output, summary, rows, plan, audit, {
        "event": {key: metadata[key] for key in ("id", "fullName", "startsAt", "variant", "clock", "isFinished")},
        "selection": {"protocol_commit": selection_commit if args.spatial_jass else PROTOCOL,
                      "code_commit": selection_commit,
                      "candidate_log_sha256": sha256(raw_log), "event_metadata_sha256": sha256(raw_meta),
                      "rejections": rejected, "source": "minimum (game ID, ply, FEN)",
                      "ownership": "first target game ID", "bootstrap_seed": 20261112},
        "export": {"url": f"https://lidraughts.org/api/tournament/{event}/games",
                   "downloaded_at": args.downloaded_at, "bytes": len(raw_pdn),
                   "sha256": sha256(raw_pdn), "terms": "https://lidraughts.org/terms-of-service"},
        "prior_manifests": manifest_hashes, "scan_sha256": hashes, "scan_version": "3.1",
        "depths": {"source": 12, "target": 16}, "score_policy": old["score_policy"],
    })


if __name__ == "__main__":
    main()
