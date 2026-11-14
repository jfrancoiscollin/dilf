"""Outcome-blind tie selection for the prospective Jass depth-one control.

This pure decision helper does not execute Jass or claim FMJD equivalence.
The caller must independently establish that each score is exact and comparable.
"""
from collections.abc import Mapping, Sequence


def choose_native_order_tie(
    native_order: Sequence[str],
    scores: Mapping[str, int],
    *,
    completed: Mapping[str, bool],
    exact: Mapping[str, bool],
    lcb_winner: str,
) -> str:
    """Choose first native-ordered exact maximizer; fail closed to LCB.

    Incomplete, bounded, missing or non-comparable scores cannot establish a tie.
    All legal candidates must have an exact completed score before intervention.
    """
    if not native_order or len(set(native_order)) != len(native_order):
        raise ValueError("Native legal move order must be nonempty and unique")
    legal = set(native_order)
    if lcb_winner not in legal:
        raise ValueError("LCB winner is not a legal move")
    if set(scores) != legal or set(completed) != legal or set(exact) != legal:
        return lcb_winner
    if not all(completed.values()) or not all(exact.values()):
        return lcb_winner
    if any(type(value) is not int for value in scores.values()):
        raise ValueError("Scores must be exact integer values")
    maximum = max(scores.values())
    if scores[lcb_winner] != maximum:
        raise ValueError("LCB winner disagrees with verified maximum")
    tied = [move for move in native_order if scores[move] == maximum]
    return tied[0] if len(tied) > 1 else lcb_winner
