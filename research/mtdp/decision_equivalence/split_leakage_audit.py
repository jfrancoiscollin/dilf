"""D1 fail-closed game-level split and reservation audit (score-blind).

Input rows are metadata only; do not include Scan scores. This module never
selects games or computes evidence of decision equivalence.
"""
from collections import defaultdict


def audit_game_partitions(rows, reserved_game_ids=(), reserved_fens=()):
    """Return counts only after checking split leakage and duplicate positions.

    Required per-row: game_id, split ('train'/'test'), fen (canonical FMJD
    position representation), source_id. Every game belongs to exactly one
    split, every FEN to one game and split, and no reserved game/FEN is used.
    Conservative: even a repeated FEN in different games is rejected.
    """
    if not isinstance(rows, (tuple, list)) or not rows:
        raise ValueError("nonempty metadata rows required")
    reserved_games = set(reserved_game_ids)
    reserved_positions = set(reserved_fens)
    if any(not isinstance(v, str) or not v for v in reserved_games | reserved_positions):
        raise ValueError("invalid reservation identifiers")
    games = {}
    positions = {}
    seen = set()
    sources = defaultdict(set)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid metadata row")
        game, split, fen, source = (row.get(k) for k in
                                    ("game_id", "split", "fen", "source_id"))
        if any(not isinstance(v, str) or not v.strip()
               for v in (game, split, fen, source)):
            raise ValueError("missing metadata")
        if split not in ("train", "test"):
            raise ValueError("unknown split")
        if game in reserved_games or fen in reserved_positions:
            raise ValueError("reserved cohort overlap")
        if game in games and games[game] != split:
            raise ValueError("game crosses splits")
        games[game] = split
        if fen in positions and positions[fen] != game:
            raise ValueError("position reused across games")
        positions[fen] = game
        if (game, fen) in seen:
            raise ValueError("duplicate game position")
        seen.add((game, fen))
        sources[split].add(source)
    if not {"train", "test"}.issubset(set(games.values())):
        raise ValueError("both train and test required")
    if sources["train"] & sources["test"]:
        raise ValueError("source overlap between splits")
    return {"n_games": len(games), "n_positions": len(positions),
            "n_train_games": sum(s == "train" for s in games.values()),
            "n_test_games": sum(s == "test" for s in games.values()),
            "score_blind": True}
