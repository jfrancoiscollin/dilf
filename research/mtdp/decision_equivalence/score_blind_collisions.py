"""Score-blind D1 signature collision audit.

Each record: game_id, position_id, signature, legal_actions (list of canonical
move strings). No evaluations are read. A collision is not decision equivalence.
"""
from collections import defaultdict


def audit(records):
    groups = defaultdict(list)
    seen = set()
    for r in records:
        if not isinstance(r, dict):
            raise ValueError("record must be an object")
        game, pos, sig, moves = (r.get(k) for k in
                                 ("game_id", "position_id", "signature", "legal_actions"))
        if any(not isinstance(x, str) or not x for x in (game, pos, sig)):
            raise ValueError("missing game, position or signature")
        if not isinstance(moves, list) or not moves or any(
            not isinstance(x, str) or not x for x in moves
        ) or len(set(moves)) != len(moves):
            raise ValueError("legal actions must be distinct nonempty strings")
        if (game, pos) in seen:
            raise ValueError("duplicate position identity")
        seen.add((game, pos))
        groups[sig].append((game, pos, frozenset(moves)))
    pairs = same_legal = different_legal = within_game = 0
    for items in groups.values():
        for i, (ga, _, la) in enumerate(items):
            for gb, _, lb in items[i + 1:]:
                pairs += 1
                same_legal += la == lb
                different_legal += la != lb
                within_game += ga == gb
    return {
        "schema": "mtdp-d1-score-blind-collisions-v1",
        "positions": len(seen),
        "distinct_signatures": len(groups),
        "compression_ratio": (len(seen) / len(groups)) if groups else None,
        "collision_pairs": pairs,
        "same_legal_action_pairs": same_legal,
        "different_legal_action_pairs": different_legal,
        "within_game_collision_pairs": within_game,
        "decision_equivalence_established": False,
        "minimax_equivalence_established": False,
    }
