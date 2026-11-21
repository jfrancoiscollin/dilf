"""Pinned inputs for P1RUlfJc; neither mode freezes positions or runs a search."""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_benchmark.prospective_candidate_replay import (
    BASELINE, EXPECTED_PDN_SHA256, PREVIOUS, checked_history, digest,
    public_ids, validated_archive_fens,
)
from research.mtdp.jass_cohort import ADAPTER_COMMIT
from research.mtdp.pdn import PdnReplayError, _resolve, read_games

DIRECTORY = "research/mtdp/jass_benchmark/spatial-jass/replication/"
REGISTRATION = DIRECTORY + "P1RUlfJc-preregistration.json"
PROTOCOL = DIRECTORY + "NAMED_ARENA_TOTAL_BUDGET_PREREGISTRATION_2026-11-18.md"
REGISTRATION_SHA = "cb607155e3a6c38bb557d6a6d109734c0b733d681f4a6571f45e908c34da9637"
PROTOCOL_SHA = "bb058030cc547c9ef2ff9bbe7bd773cc2214947f0aeac851ed84feec79abf169"
PREVIOUS_SHA = "e8029eff15b30352db9e33857ba58444d093902bfd539800d30cb237829d131f"
EVENT = "P1RUlfJc"


def utc(text):
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Timestamp must contain a timezone")
    return value.astimezone(timezone.utc)


def registration(root):
    raw = (root / REGISTRATION).read_bytes()
    if digest(raw) != REGISTRATION_SHA or digest((root / PROTOCOL).read_bytes()) != PROTOCOL_SHA:
        raise ValueError("Preregistered selection or protocol changed")
    record = json.loads(raw)
    if record["event"]["id"] != EVENT or utc(record["registered_utc"]) >= utc(record["event"]["startsAt"]):
        raise ValueError("Selection was not fixed before the named event")
    return record


def final_metadata(reg, metadata, now):
    expected = reg["event"]
    finish = utc(expected["startsAt"]) + timedelta(minutes=expected["minutes"])
    if now.tzinfo is None or now < finish:
        raise ValueError("Final export gate is closed until the scheduled finish")
    if metadata.get("isFinished") is not True:
        raise ValueError("Named event is not confirmed finished")
    if metadata.get("secondsToStart", 0) != 0:
        raise ValueError("Finished metadata has an inconsistent countdown")
    for key in ("id", "createdBy", "system", "variant", "clock", "minutes"):
        if metadata.get(key) != expected[key]:
            raise ValueError(f"Named event metadata changed: {key}")
    if utc(metadata["startsAt"]) != utc(expected["startsAt"]):
        raise ValueError("Named event start changed")
    return finish


def check_final(root, metadata_path, first, repeat, log_path, *, now=None):
    reg = registration(root)
    now = now or datetime.now(timezone.utc)
    metadata_raw = metadata_path.read_bytes()
    finish = final_metadata(reg, json.loads(metadata_raw), now)
    if first.resolve() == repeat.resolve() or first.samefile(repeat):
        raise ValueError("Two distinct export files are required")
    raw = first.read_bytes()
    if not raw or raw != repeat.read_bytes():
        raise ValueError("Independent final exports differ or are empty")
    log_raw = log_path.read_bytes()
    log = json.loads(log_raw)["candidate"]
    receipts = [log["first"], log["independent_repeat"]]
    request_ids = set()
    for receipt in receipts:
        if (receipt["url"] != f"https://lidraughts.org/api/tournament/{EVENT}/games"
                or receipt["sha256"] != digest(raw) or receipt["bytes"] != len(raw)
                or not finish <= utc(receipt["retrieved_at_utc"]) <= now):
            raise ValueError("Final acquisition receipt disagrees with the selected inputs")
        identity = receipt["request_id"]
        if not isinstance(identity, str) or not identity or identity in request_ids:
            raise ValueError("Distinct acquisition request IDs are required")
        request_ids.add(identity)
    return {"schema": "mtdp-named-final-input-check-v1", "event": EVENT,
            "registration_sha256": REGISTRATION_SHA, "protocol_sha256": PROTOCOL_SHA,
            "metadata_sha256": digest(metadata_raw), "pdn_sha256": digest(raw),
            "bytes": len(raw), "download_log_sha256": digest(log_raw),
            "scope": "input_receipts_consistent_population_and_Jass_checks_still_required",
            "scientific_freeze": False}


def confirmed_prefixes(games, engine):
    """Keep only verified prefix states; never pick among ambiguous routes."""
    fens, quarantined = set(), []
    for game in games:
        state = parse_fen(game.tags["FEN"]) if "FEN" in game.tags else initial_state()
        fens.add(state_to_fen(state))
        for ply, token in enumerate(game.moves, 1):
            try:
                move = _resolve(state, token, engine)
            except PdnReplayError as error:
                quarantined.append({"game": game.index, "ply": ply, "error": str(error)})
                break
            state = engine.apply_move(state, move)
            fens.add(state_to_fen(state))
    return fens, quarantined


def prepare_registry(root, history, reserved, adapter):
    registration(root)
    previous_raw = (root / PREVIOUS).read_bytes()
    if digest(previous_raw) != PREVIOUS_SHA:
        raise ValueError("Historical provenance changed")
    previous = json.loads(previous_raw)
    archived, archive_receipt = validated_archive_fens(root, previous)
    checked_history(root, history, previous, set())
    pinned_checkout(adapter, ADAPTER_COMMIT)
    engine = create_engine()
    if Path(engine._rules.__file__).resolve() != (adapter / "backend/game_engine.py").resolve():
        raise ValueError("Imported FMJD engine differs from pinned checkout")
    if reserved.name != "mtdp-lidraughts-fFgE7oED.pdn" or digest(reserved.read_bytes()) != EXPECTED_PDN_SHA256:
        raise ValueError("Reserved fFgE7oED export changed")
    records = [*previous["inputs"]["baseline"], *previous["inputs"]["exclusions"],
               *previous["inputs"]["event"]]
    files = []
    for row in records:
        name = row["file"]
        if Path(name).name != name:
            raise ValueError("Unsafe historical source name")
        path = (root / BASELINE if name == "pcblues_games.pdn" else
                history / name if name.startswith("mtdp-lidraughts-") else adapter / "docs/parties" / name)
        if digest(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"Historical source digest changed: {name}")
        files.append((path, row["games"]))
    files.append((reserved, 157))
    public, token_sequences, provenance = set(), set(), []
    other_quarantines = []
    reserved_fens, quarantined = confirmed_prefixes(read_games(reserved), engine)
    extra_fens = set(reserved_fens)
    for path, expected_games in files:
        games = read_games(path)
        if len(games) != expected_games:
            raise ValueError("Historical source game count changed")
        if path.name.startswith("mtdp-lidraughts-"):
            ids = set(public_ids(path))
            if public & ids:
                raise ValueError("Duplicate public IDs between historical sources")
            public.update(ids)
        else:
            fens, rejected = confirmed_prefixes(games, engine)
            other_quarantines.extend({"file": path.name, **row} for row in rejected)
            extra_fens.update(fens)
        for game in games:
            start = state_to_fen(parse_fen(game.tags["FEN"])) if "FEN" in game.tags else state_to_fen(initial_state())
            payload = json.dumps([start, [token.lower() for token in game.moves]], separators=(",", ":")).encode()
            token_sequences.add(digest(payload))
        provenance.append({"file": path.name, "sha256": digest(path.read_bytes()), "games": len(games)})
    return {"schema": "mtdp-named-exclusion-inputs-v1", "event": EVENT,
            "registration_sha256": REGISTRATION_SHA, "protocol_sha256": PROTOCOL_SHA,
            "previous_provenance_sha256": PREVIOUS_SHA, "adapter_commit": ADAPTER_COMMIT,
            "archive": archive_receipt, "sources": sorted(provenance, key=lambda r: r["file"]),
            "public_game_ids": sorted(public), "normalized_token_sequence_sha256": sorted(token_sequences),
            "confirmed_fens": sorted(archived | extra_fens),
            "reserved_confirmed_prefix_fens": len(reserved_fens),
            "reserved_whole_game_quarantines": quarantined,
            "other_confirmed_prefix_quarantines": other_quarantines,
            "scientific_freeze": False,
            "limitations": ["Token-sequence equality is not canonical board-trajectory equality.",
                            "No state beyond the first ambiguous ply is inferred.",
                            "Future population, complete trajectory guard and Jass mappings remain required."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("registry", "check-final"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for name in ("history", "reserved", "adapter", "metadata", "first", "repeat", "download-log"):
        parser.add_argument(f"--{name}", type=Path)
    args = parser.parse_args()
    required = ("history", "reserved", "adapter") if args.mode == "registry" else ("metadata", "first", "repeat", "download_log")
    if any(getattr(args, name) is None for name in required):
        parser.error(f"Mode {args.mode} requires {required}")
    report = (prepare_registry(args.root, args.history, args.reserved, args.adapter) if args.mode == "registry"
              else check_final(args.root, args.metadata, args.first, args.repeat, args.download_log))
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    summary = {k: v for k, v in report.items() if k not in (
        "public_game_ids", "normalized_token_sequence_sha256", "confirmed_fens")}
    for key in ("public_game_ids", "normalized_token_sequence_sha256", "confirmed_fens"):
        if key in report:
            summary[key + "_count"] = len(report[key])
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
