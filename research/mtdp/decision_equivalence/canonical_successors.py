"""Canonical score-blind fingerprint of a complete action -> successor map.

Caller MUST supply canonical FMJD action identities and successor states,
including side-to-move and rule-relevant counters where applicable.
This module cannot certify completeness or legality of the supplied map.
"""
import hashlib
import json


def fingerprint(action_to_successor):
    """SHA-256 digest invariant to dictionary order, not a minimax certificate."""
    if not isinstance(action_to_successor, dict) or not action_to_successor:
        raise ValueError("expected nonempty action-to-successor mapping")
    for action, successor in action_to_successor.items():
        if (not isinstance(action, str) or not action.strip()
                or not isinstance(successor, str) or not successor.strip()
                or action != action.strip() or successor != successor.strip()):
            raise ValueError("invalid canonical action or successor identity")
    payload = json.dumps(sorted(action_to_successor.items()),
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
