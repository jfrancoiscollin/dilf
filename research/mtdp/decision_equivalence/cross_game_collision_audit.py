"""Score-blind decomposition of signature collisions across games.

Descriptive only: neither independent samples nor best-move/minimax equivalence.
Rows must already come from a pinned legal FMJD replay.
"""
from collections import Counter, defaultdict
from math import comb


def cross_game_collision_audit(rows):
    groups = defaultdict(lambda: defaultdict(Counter))
    identities = set()
    for row in rows:
        game = row["game_id"]
        position = row["position_id"]
        signature = row["signature"]
        moves = row["legal_moves"]
        if not isinstance(game, str) or not game or not isinstance(position, (str, int)):
            raise ValueError("invalid game/position identity")
        if not isinstance(signature, str) or not signature:
            raise ValueError("invalid signature")
        if not isinstance(moves, list) or not moves or any(not isinstance(m, str) or not m for m in moves) or len(moves) != len(set(moves)):
            raise ValueError("invalid legal action list")
        identity = (game, position)
        if identity in identities:
            raise ValueError("duplicate game-position identity")
        identities.add(identity)
        groups[signature][game][frozenset(moves)] += 1

    total = within = same_total = same_within = 0
    for games in groups.values():
        all_actions = Counter()
        for action_counts in games.values():
            n = sum(action_counts.values())
            within += comb(n, 2)
            same_within += sum(comb(v, 2) for v in action_counts.values())
            all_actions.update(action_counts)
        total += comb(sum(all_actions.values()), 2)
        same_total += sum(comb(v, 2) for v in all_actions.values())
    cross = total - within
    same_cross = same_total - same_within
    return {
        "positions": len(identities),
        "signature_collision_pairs": total,
        "within_game_pairs": within,
        "cross_game_pairs": cross,
        "cross_game_same_legal_actions": same_cross,
        "cross_game_different_legal_actions": cross - same_cross,
        "independent_cohort_proven": False,
        "best_move_equivalence_proven": False,
        "minimax_equivalence_proven": False,
    }
