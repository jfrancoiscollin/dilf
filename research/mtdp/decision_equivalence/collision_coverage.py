"""Score-blind position-level collision coverage; never a decision-equivalence test."""
from collections import defaultdict


def coverage(records):
    """Count affected *positions* (not pairs) by signature and game.

    Identical FEN across games must be handled by upstream split-integrity audit.
    """
    groups = defaultdict(list)
    seen = set()
    for r in records:
        if not isinstance(r, dict):
            raise ValueError("record must be an object")
        game, pos, sig, moves = (r.get(k) for k in
                                 ("game_id", "position_id", "signature", "legal_actions"))
        if any(not isinstance(x, str) or not x for x in (game, pos, sig)):
            raise ValueError("invalid identity or signature")
        if not isinstance(moves, list) or not moves or any(
            not isinstance(m, str) or not m for m in moves
        ) or len(moves) != len(set(moves)):
            raise ValueError("invalid legal actions")
        if (game, pos) in seen:
            raise ValueError("duplicate game-position identity")
        seen.add((game, pos))
        groups[sig].append((game, frozenset(moves)))
    collided = cross_game = cross_game_discordant = 0
    for entries in groups.values():
        if len(entries) < 2:
            continue
        collided += len(entries)
        games = {game for game, _ in entries}
        if len(games) < 2:
            continue
        cross_game += len(entries)
        # An entry has a cross-game discordance iff a different game
        # contains a different legal-action set. Avoid quadratic pair scans.
        per_game = defaultdict(set)
        for game, moves in entries:
            per_game[game].add(moves)
        for game, moves in entries:
            if any(other != game and (len(sets) > 1 or moves not in sets)
                   for other, sets in per_game.items()):
                cross_game_discordant += 1
    n = len(seen)
    return {
        "schema": "mtdp-d1-collision-position-coverage-v1",
        "positions": n,
        "positions_in_signature_collision": collided,
        "positions_in_cross_game_collision": cross_game,
        "positions_in_cross_game_different_legal_collision": cross_game_discordant,
        "cross_game_different_legal_coverage": cross_game_discordant / n if n else None,
        "decision_equivalence_established": False,
        "minimax_equivalence_established": False,
    }
