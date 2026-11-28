"""Score-blind legal-action identity diagnostic for D1 signature collisions.

Not a legal FMJD parser, corpus admission gate, or minimax equivalence test.
Inputs must be sourced from a pinned legal replay engine.
"""
from collections import Counter, defaultdict
from math import comb


def audit_action_sets(rows):
    groups = defaultdict(Counter)
    seen = set()
    for row in rows:
        pid = (row["game_id"], row["position_id"])
        if pid in seen:
            raise ValueError("duplicate game-position identity")
        seen.add(pid)
        signature = row["signature"]
        moves = row["legal_moves"]
        if not isinstance(signature, str) or not signature:
            raise ValueError("invalid signature")
        if not isinstance(moves, list) or not moves:
            raise ValueError("nonterminal legal action list required")
        if any(not isinstance(m, str) or not m for m in moves) or len(moves) != len(set(moves)):
            raise ValueError("invalid or duplicate legal action")
        groups[signature][frozenset(moves)] += 1
    collision_pairs = sum(comb(sum(counts.values()), 2) for counts in groups.values())
    same_action_pairs = sum(comb(n, 2) for counts in groups.values() for n in counts.values())
    return {
        "positions": len(seen),
        "distinct_signatures": len(groups),
        "compression_ratio": len(seen) / len(groups) if groups else None,
        "collision_pairs": collision_pairs,
        "same_legal_action_set_pairs": same_action_pairs,
        "different_legal_action_set_pairs": collision_pairs - same_action_pairs,
        "best_move_equivalence_proven": False,
        "minimax_equivalence_proven": False,
    }
