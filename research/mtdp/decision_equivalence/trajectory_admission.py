"""Score-blind D1 trajectory admission gate; IDs must be canonical upstream.

A trajectory ID identifies a complete game move sequence, not a source filename.
This gate does not derive or validate that identity and does not read scores.
"""
from .split_leakage_audit import audit_game_partitions


def audit_trajectory_admission(rows, *, reserved_game_ids=(), reserved_fens=(),
                               reserved_trajectory_ids=()):
    """Reject trajectory reuse across games/splits and reserved histories.

    Every row requires a nonblank canonical trajectory_id. A game must have
    exactly one trajectory_id and source_id, and a trajectory_id may belong
    to only one game. Callers must supply the *complete* historical exclusion
    set, including prospectively reserved games, before admitting a corpus.
    """
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("nonempty metadata rows required")
    reserved = set(reserved_trajectory_ids)
    if any(not isinstance(t, str) or not t.strip() for t in reserved):
        raise ValueError("invalid reserved trajectory")
    game_identity = {}
    trajectory_game = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid metadata row")
        game, trajectory, source = (row.get(k) for k in
                                    ("game_id", "trajectory_id", "source_id"))
        if any(not isinstance(x, str) or not x.strip()
               for x in (game, trajectory, source)):
            raise ValueError("missing canonical trajectory metadata")
        if trajectory in reserved:
            raise ValueError("reserved trajectory overlap")
        identity = (trajectory, source)
        if game in game_identity and game_identity[game] != identity:
            raise ValueError("game identity inconsistent")
        game_identity[game] = identity
        if trajectory in trajectory_game and trajectory_game[trajectory] != game:
            raise ValueError("trajectory reused across games")
        trajectory_game[trajectory] = game
    result = audit_game_partitions(rows, reserved_game_ids=reserved_game_ids,
                                   reserved_fens=reserved_fens)
    return {**result, "n_trajectories": len(trajectory_game),
            "canonical_ids_verified": False}
