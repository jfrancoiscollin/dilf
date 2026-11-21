"""Fail-closed lexical admission for D1 trajectory fingerprints.

This is NOT FMJD legality, canonicalization, or independent-cohort approval.
Callers must still replay the entire game with pinned FMJD rules, canonicalize
FEN/move paths and reconcile historical/reserved trajectory exclusions.
"""
from research.mtdp.decision_equivalence.fmjd_move_tokens import validate_move_token
from research.mtdp.decision_equivalence.trajectory_fingerprint import trajectory_fingerprint


def lexical_trajectory_fingerprint(initial_fen, moves):
    """Hash a trajectory only if every supplied move has accepted FMJD syntax.

    No token is silently rewritten. The full ordered capture path is retained,
    even if two notations have the same endpoints. Input remains score-blind.
    """
    if not isinstance(moves, (list, tuple)):
        raise ValueError('ordered move sequence required')
    for token in moves:
        validate_move_token(token)
    return trajectory_fingerprint(initial_fen, moves)
