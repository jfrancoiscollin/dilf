"""Necessary FMJD 10x10 diagonal geometry for D1, NOT move legality.

This deliberately remains separate from the lexical trajectory admission gate:
no corpus may be admitted on geometric validation alone.
"""
from research.mtdp.decision_equivalence.fmjd_move_tokens import validate_move_token


def square_coordinates(square):
    """FMJD 1..50 -> zero-based row/column, top row dark squares at odd columns."""
    if type(square) is not int or not 1 <= square <= 50:
        raise ValueError("FMJD square must be integer 1..50")
    row, index = divmod(square - 1, 5)
    return row, 2 * index + (1 if row % 2 == 0 else 0)


def validate_diagonal_path(token):
    """Check only necessary diagonal geometry for each supplied path leg.

    Captures must span at least two rows. This does not validate piece type,
    side to move, victims, obstructions, maximal capture, promotion or legality.
    """
    validate_move_token(token)
    separator = "x" if "x" in token else "-"
    points = [square_coordinates(int(s)) for s in token.split(separator)]
    for (r1, c1), (r2, c2) in zip(points, points[1:]):
        if abs(r2 - r1) != abs(c2 - c1):
            raise ValueError("non-diagonal FMJD move-path leg")
        if separator == "x" and abs(r2 - r1) < 2:
            raise ValueError("capture leg cannot span fewer than two rows")
    return token
