"""Fail-closed D1 corpus split guard; no target engine scores accepted.

This is an engineering gate, not a proof that two different game IDs
represent independent games. Source provenance must be audited separately.
"""
import hashlib
import json


FORBIDDEN = frozenset({"score", "scores", "scan_score", "eval", "evaluation",
                       "best_move", "best_action", "rank", "ranking", "wdl"})


def validate_partition(rows, reserved_game_ids=(), reserved_position_ids=()):
    """Validate chronological, game-disjoint score-blind train/test rows.

    Required fields: game_id, position_id, ply, split ('train' or 'test').
    Reject reserved identities, duplicate positions, game leakage and
    non-increasing ply within each game in source order.
    Return deterministic SHA-256 of the accepted ordered manifest.
    """
    reserved_games = set(reserved_game_ids)
    reserved_positions = set(reserved_position_ids)
    if not all(isinstance(x, str) and x for x in reserved_games | reserved_positions):
        raise ValueError("invalid reserved identity")
    seen_positions, game_split, last_ply = set(), {}, {}
    manifest = []
    for row in rows:
        if not isinstance(row, dict) or FORBIDDEN.intersection(row):
            raise ValueError("non-score-blind or invalid record")
        g, p, ply, split = (row.get(k) for k in ("game_id", "position_id", "ply", "split"))
        if not isinstance(g, str) or not g or not isinstance(p, str) or not p:
            raise ValueError("missing identity")
        if type(ply) is not int or ply < 0 or split not in ("train", "test"):
            raise ValueError("invalid ply or split")
        if g in reserved_games or p in reserved_positions:
            raise ValueError("reserved prospective identity")
        if p in seen_positions:
            raise ValueError("duplicate position identity")
        if g in game_split and game_split[g] != split:
            raise ValueError("game crosses partitions")
        if g in last_ply and ply <= last_ply[g]:
            raise ValueError("nonchronological or duplicate ply")
        seen_positions.add(p)
        game_split[g] = split
        last_ply[g] = ply
        manifest.append({"game_id": g, "position_id": p, "ply": ply, "split": split})
    if not manifest:
        raise ValueError("empty manifest")
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "positions": len(manifest), "games": len(game_split),
            "train_games": sum(s == "train" for s in game_split.values()),
            "test_games": sum(s == "test" for s in game_split.values())}
