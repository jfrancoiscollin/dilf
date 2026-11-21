"""Conservative score-blind eligibility gate for cross-game D1 action transfer.

Eligibility is not evidence of best-move or minimax equivalence. No scores read.
Inputs must already be admitted from pinned legal FMJD replay and leakage checks.
"""
from collections import defaultdict


def eligible_cross_game_pairs(rows):
    """Diagnostic only; not a cohort admission gate or independent split."""
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        game, pos = row["game_id"], row["position_id"]
        signature, fen, moves = row["signature"], row["fen"], row["legal_moves"]
        if not isinstance(game, str) or not game or not isinstance(pos, (str, int)) or isinstance(pos, bool):
            raise ValueError("invalid identity")
        normalized_pos = str(pos)
        if (game, normalized_pos) in seen:
            raise ValueError("duplicate identity after position-id normalization")
        seen.add((game, normalized_pos))
        if not isinstance(signature, str) or not signature or not isinstance(fen, str) or not fen:
            raise ValueError("invalid signature/FEN")
        if not isinstance(moves, list) or not moves or any(not isinstance(m, str) or not m for m in moves) or len(set(moves)) != len(moves):
            raise ValueError("invalid legal actions")
        groups[signature].append((game, str(pos), fen, frozenset(moves)))
    eligible = []
    rejected = {"same_game": 0, "different_legal_actions": 0, "identical_fen": 0}
    for signature, group in sorted(groups.items()):
        for i, a in enumerate(group):
            for b in group[i+1:]:
                if a[0] == b[0]:
                    rejected["same_game"] += 1
                elif a[3] != b[3]:
                    rejected["different_legal_actions"] += 1
                elif a[2] == b[2]:
                    rejected["identical_fen"] += 1
                else:
                    eligible.append(((a[0], a[1]), (b[0], b[1])))
    return {"eligible_pairs": eligible, "eligible_count": len(eligible),
            "rejected": rejected, "best_move_equivalence_proven": False,
            "minimax_equivalence_proven": False, "independent_cohort_proven": False}
