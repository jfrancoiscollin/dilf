"""Score-blind D1 signature collision audit.

Each record: game_id, position_id, signature, legal_actions (canonical move
strings). Collision counts are exact combinatorial counts, not independent
samples, and cannot establish decision or minimax equivalence.
"""
from collections import Counter, defaultdict


def _pairs(n):
    return n * (n - 1) // 2


def audit(records):
    by_signature = defaultdict(lambda: {"total": 0, "legal": Counter(), "game": Counter()})
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
        g = by_signature[sig]
        g["total"] += 1
        g["legal"][frozenset(moves)] += 1
        g["game"][game] += 1
    pairs = sum(_pairs(g["total"]) for g in by_signature.values())
    same_legal = sum(_pairs(n) for g in by_signature.values()
                     for n in g["legal"].values())
    within_game = sum(_pairs(n) for g in by_signature.values()
                      for n in g["game"].values())
    return {
        "schema": "mtdp-d1-score-blind-collisions-v1",
        "positions": len(seen),
        "distinct_signatures": len(by_signature),
        "compression_ratio": (len(seen) / len(by_signature)) if by_signature else None,
        "collision_pairs": pairs,
        "same_legal_action_pairs": same_legal,
        "different_legal_action_pairs": pairs - same_legal,
        "within_game_collision_pairs": within_game,
        "decision_equivalence_established": False,
        "minimax_equivalence_established": False,
    }
