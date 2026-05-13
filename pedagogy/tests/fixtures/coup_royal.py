"""Synthetic Move fixtures for the coup_royal detector.

These are *not* tied to specific Dubois diagrams — the detector reasons on
the **signature** of the move (capture count, center mass, rows touched,
promotion / great-diagonal landing) and trusts the engine to have produced
a physically-legal rafle. Each fixture is therefore a hand-built ``Move``
that exercises one branch of the signature predicate.

Naming convention: ``ROYAL_*`` is a positive case, ``NOT_ROYAL_*`` is a
negative case.
"""

from __future__ import annotations

from pedagogy.game import Move

# ---------------------------------------------------------------------------
# Positive cases -- signature must match.
# ---------------------------------------------------------------------------

#: 6-capture rafle ending on white's promotion row, also crossing the great
#: diagonal (passes through 23 and captures 28).
ROYAL_CLASSIC_SIX_PROMO: Move = Move(
    path=(40, 29, 23, 18, 12, 7, 3),
    captures=(33, 28, 22, 17, 13, 9),
)

#: 7-capture rafle, severity 0.7.
ROYAL_SEVEN_PROMO: Move = Move(
    path=(40, 29, 23, 18, 12, 7, 3, 14),
    captures=(33, 28, 22, 17, 13, 9, 8),
)

#: 8-capture rafle.
ROYAL_EIGHT_PROMO: Move = Move(
    path=(45, 34, 23, 18, 12, 7, 3, 14, 25),
    captures=(40, 28, 22, 17, 13, 9, 8, 19),
)

#: 10-capture rafle, severity capped at 1.0.
ROYAL_TEN_PROMO: Move = Move(
    path=(45, 34, 23, 12, 7, 3, 13, 18, 24, 29, 5),
    captures=(40, 33, 28, 22, 17, 11, 8, 9, 19, 14),
)

#: 12-capture rafle (improbable in practice, used to test severity capping).
ROYAL_TWELVE_PROMO: Move = Move(
    path=(45, 34, 23, 12, 7, 3, 14, 25, 36, 47, 41, 32, 21),
    captures=(40, 28, 17, 8, 4, 9, 20, 31, 42, 46, 37, 26),
)

#: 6-capture rafle that ends OFF a promotion row but its path passes
#: through 23, which is on the great diagonal.
ROYAL_SIX_VIA_MAIN_DIAGONAL: Move = Move(
    path=(40, 29, 23, 18, 12, 7, 16),  # 16 is row 4, not a promotion row
    captures=(33, 28, 22, 17, 13, 6),
)

#: Mirror version for black: 6 captures going from row 4 down to row 10.
ROYAL_BLACK_SIX_PROMO: Move = Move(
    path=(12, 17, 23, 28, 33, 39, 49),
    captures=(16, 22, 27, 32, 38, 43),
)


# ---------------------------------------------------------------------------
# Negative cases -- signature must NOT match.
# ---------------------------------------------------------------------------

#: Quiet move, no captures.
NOT_ROYAL_QUIET: Move = Move(path=(32, 28))

#: Single capture.
NOT_ROYAL_SINGLE_CAPTURE: Move = Move(path=(32, 21), captures=(27,))

#: 5-capture rafle (one short of the minimum).
NOT_ROYAL_FIVE_CAPTURES: Move = Move(
    path=(40, 29, 23, 18, 12, 7),
    captures=(33, 28, 22, 17, 13),
)

#: 6 captures but only 3 of them are in CENTER_EXTENDED.
NOT_ROYAL_FEW_CENTER: Move = Move(
    path=(40, 29, 18, 13, 4, 5, 14),
    captures=(33, 22, 17, 45, 35, 25),
)

#: 6 captures spread on only 3 rows.
NOT_ROYAL_THREE_ROWS: Move = Move(
    path=(40, 29, 18, 7, 16),
    captures=(34, 33, 22, 23, 12, 11),  # rows {7, 7, 5, 5, 3, 3}
)

#: 6 captures, 4+ in center, 4 rows -- but the path neither ends on a
#: promotion row nor touches the great diagonal.
NOT_ROYAL_NO_PROMO_NO_DIAG: Move = Move(
    path=(44, 35, 24, 18, 12, 6, 16),
    captures=(33, 27, 22, 17, 11, 38),
)
