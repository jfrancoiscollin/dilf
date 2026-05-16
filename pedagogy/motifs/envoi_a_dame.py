"""``envoi_a_dame`` — sacrifice that leads to a promotion within 2 half-moves.

Two detection paths (mirror those of :class:`SacrificeDetector`) :

1. **Immediate sacrifice** — the played move shows a negative material
   delta on its own ``state_after``. Original spec behaviour ; fires on
   engines that do not enforce the FMJD prise-maximale rule.

2. **Forced-reply sacrifice (FMJD-strict)** — the player makes a quiet
   move, the opponent has a forced capture reply, and the player's PV
   second move (the post-capture move) lands on the promotion row.
   The material loss is measured after applying the opponent's forced
   capture.

Both paths additionally require :

* the played move is not itself a promotion (otherwise it is a plain
  promotion, not a "sending to king" sacrifice) ;
* the first or second half-move of the Scan PV lands on the moving
  player's promotion row (white → rows 1–5, black → rows 46–50) ;
* the Scan score after the played move remains above
  ``SACRIFICE_FAILED_SCORE`` for the moving side.
"""

from __future__ import annotations

from ..features.geometry import BLACK_PROMOTION_ROW, WHITE_PROMOTION_ROW
from ..features.material import material_balance
from ..game import GameState, Move
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector
from .sacrifices import SACRIFICE_FAILED_SCORE, _project_forced_capture

#: Maximum half-move depth (within the PV) at which the promotion must occur.
ENVOI_PROMO_PLY_LIMIT = 2


def _last_square_of_notation(text: str) -> int | None:
    """Return the landing square of a PDN-like move string, or None if malformed."""
    if not text:
        return None
    tokens = text.replace("-", "x").split("x")
    try:
        return int(tokens[-1])
    except ValueError:
        return None


def _promotion_row_for(side: str) -> frozenset[int]:
    return WHITE_PROMOTION_ROW if side == "white" else BLACK_PROMOTION_ROW


def _side_sign(side: str) -> int:
    return 1 if side == "white" else -1


class EnvoiADameDetector(MotifDetector):
    """Detector for the ``envoi_a_dame`` motif."""

    name = "envoi_a_dame"

    def detect(
        self,
        state_before: GameState,
        move: Move,
        state_after: GameState,
        *,
        pv: list[str] | None = None,
        scan_score_before: float = 0.0,
        scan_score_after: float = 0.0,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        sign = _side_sign(state_before.turn)
        promo_row = _promotion_row_for(state_before.turn)
        if move.path[-1] in promo_row:
            return None  # played move is itself the promotion
        if not pv:
            return None
        if sign * scan_score_after < SACRIFICE_FAILED_SCORE:
            return None  # position collapsed

        # Locate the promotion landing within the PV (up to ENVOI_PROMO_PLY_LIMIT).
        promotion_square: int | None = None
        for ply, notation_str in enumerate(pv[:ENVOI_PROMO_PLY_LIMIT], start=1):
            landing = _last_square_of_notation(notation_str)
            if landing is not None and landing in promo_row:
                promotion_square = landing
                break
        if promotion_square is None:
            return None

        # Path 1 — immediate material loss visible on state_after.
        immediate_delta = sign * (
            material_balance(state_after) - material_balance(state_before)
        )
        if immediate_delta < 0:
            loss = abs(immediate_delta)
            return MotifMatch(
                motif="envoi_a_dame",
                role="played",
                squares=[*move.path, promotion_square],
                pv=list(pv[:ENVOI_PROMO_PLY_LIMIT]),
                severity=min(1.0, 0.5 + loss / 4.0),
                metadata={
                    "material_loss": loss,
                    "promotion_square": promotion_square,
                    "score_after": scan_score_after,
                    "path": "immediate",
                },
            )

        # Path 2 — FMJD-strict: loss materialises after the opponent's
        # forced capture reply. Requires non-capturing player move.
        if move.is_capture:
            return None
        projected = _project_forced_capture(state_after, engine)
        if projected is None:
            return None
        projected_delta = sign * (
            material_balance(projected) - material_balance(state_before)
        )
        if projected_delta >= 0:
            return None
        loss = abs(projected_delta)
        return MotifMatch(
            motif="envoi_a_dame",
            role="played",
            squares=[*move.path, promotion_square],
            pv=list(pv[:ENVOI_PROMO_PLY_LIMIT]),
            severity=min(1.0, 0.5 + loss / 4.0),
            metadata={
                "material_loss": loss,
                "promotion_square": promotion_square,
                "score_after": scan_score_after,
                "path": "forced_reply",
            },
        )
