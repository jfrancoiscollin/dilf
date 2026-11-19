"""Score-blind D1 historical corpus guard; no target engine scores."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen

RESERVED_EVENTS = frozenset({"fFgE7oED", "P1RUlfJc", "s7ahYqL4", "D9PF2OSW"})
SPLITS = frozenset({"train", "test"})
# Reject target-engine outcomes before freezing any score-blind manifest.
# Metadata may be extended, but score-derived fields must never enter this stage.
TARGET_FIELDS = frozenset({"score", "scores", "eval", "evaluation", "cp", "centipawns",
                           "regret", "top1", "top3", "wdl", "best_move", "bestmove",
                           "pv", "principal_variation", "scan_score", "jass_score"})


def _reject_target_fields(value, location="row"):
    """Fail closed for target-derived keys at any nesting depth."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in TARGET_FIELDS:
                raise ValueError(f"{location}.{key}: target-derived field in score-blind manifest")
            _reject_target_fields(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_target_fields(child, f"{location}[{index}]")


def audit(rows, *, reserved_events=RESERVED_EVENTS):
    """Reject reserved events, game/FEN leakage, duplicate game/ply."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty JSONL rows required")
    game_split, game_event, event_split, tournament_split, last_ply, fen_owner, seen = {}, {}, {}, {}, {}, {}, set()
    split_games = defaultdict(set)
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {i}: object required")
        _reject_target_fields(row, f"row {i}")
        for field in ("game_id", "tournament_id", "event_id", "fen", "split"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"row {i}: missing {field}")
        gid, event, split = row["game_id"], row["event_id"], row["split"]
        if split not in SPLITS:
            raise ValueError(f"row {i}: invalid split")
        if event in reserved_events or row["tournament_id"] in reserved_events:
            raise ValueError(f"row {i}: reserved event/tournament identifier")
        ply = row.get("ply")
        if type(ply) is not int or ply < 0:
            raise ValueError(f"row {i}: invalid ply")
        if gid in game_split and game_split[gid] != split:
            raise ValueError(f"row {i}: game crosses splits")
        if gid in game_event and game_event[gid] != (event, row["tournament_id"]):
            raise ValueError(f"row {i}: inconsistent game provenance")
        game_split[gid] = split
        game_event[gid] = (event, row["tournament_id"])
        if event in event_split and event_split[event] != split:
            raise ValueError(f"row {i}: event crosses splits")
        event_split[event] = split
        tournament = row["tournament_id"]
        if tournament in tournament_split and tournament_split[tournament] != split:
            raise ValueError(f"row {i}: tournament crosses splits")
        tournament_split[tournament] = split
        key = (gid, ply)
        if key in seen:
            raise ValueError(f"row {i}: duplicate game/ply")
        seen.add(key)
        if gid in last_ply and ply <= last_ply[gid]:
            raise ValueError(f"row {i}: nonchronological ply for game")
        last_ply[gid] = ply
        fen_hash = hashlib.sha256(canonical_fen(row["fen"]).encode("utf-8")).hexdigest()
        if fen_hash in fen_owner and fen_owner[fen_hash] != split:
            raise ValueError(f"row {i}: FEN crosses splits")
        fen_owner[fen_hash] = split
        split_games[split].add(gid)
    # Input order retained: no sorting before hashing.
    payload = "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
                      for row in rows)
    return {"rows": len(rows), "games_by_split": {s: len(split_games[s]) for s in sorted(SPLITS)},
            "unique_fens": len(fen_owner), "canonical_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "score_blind": True}


def audit_jsonl(path):
    return audit([json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
                  if line.strip()])
