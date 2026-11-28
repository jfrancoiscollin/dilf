"""Fail-closed score-blind validation of complete FMJD successor exports.

The independent legal-action oracle must be separately pinned and validated.
Equality of action sets does not establish successor correctness or minimax equivalence.
"""
from research.mtdp.decision_equivalence.canonical_successors import fingerprint


def verified_fingerprint(action_to_successor, legal_actions):
    """Reject missing/extra legal actions before fingerprinting transitions."""
    if not isinstance(legal_actions, (list, tuple)) or not legal_actions:
        raise ValueError("legal actions must be a nonempty ordered collection")
    if any(not isinstance(a, str) or not a.strip() or a != a.strip()
           for a in legal_actions):
        raise ValueError("invalid legal action identity")
    if len(set(legal_actions)) != len(legal_actions):
        raise ValueError("duplicate legal action identity")
    if not isinstance(action_to_successor, dict):
        raise ValueError("expected successor map")
    if set(action_to_successor) != set(legal_actions):
        raise ValueError("successor map differs from independently generated legal actions")
    return fingerprint(action_to_successor)
