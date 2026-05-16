"""``sacrifice`` — material loss compensated by a still-acceptable Scan score.

Two detection paths :

1. **Immediate sacrifice** (spec pseudo-code §5). The played move itself
   shows a negative material delta (engine *allowed* sub-maximal play or
   engine doesn't enforce the FMJD prise-maximale rule). The score after
   the move must remain above ``SACRIFICE_FAILED_SCORE`` for the moving
   side.

2. **Forced-reply sacrifice** (FMJD-strict gameplay). When the engine
   enforces the prise-maximale rule, the player cannot lose material on
   their own move — the loss materialises on the opponent's *forced*
   capture reply. Path 1 stays silent on those games.

   We detect this case by checking that the opponent has at least one
   capture available in ``state_after`` and projecting one ply via
   ``engine.apply_move``. If the projected material is negative for the
   player AND ``scan_score_after`` (from the player's POV) remains above
   the failure threshold, we flag a sacrifice. Severity follows the same
   formula based on projected material loss.

Kings are weighted as 3 men in the balance — see
:func:`pedagogy.features.material.count_material`.
"""

from __future__ import annotations

from ..features.material import material_balance
from ..game import GameState, Move
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

#: Player's Scan-score threshold below which the sacrifice is considered to
#: have failed (in pawn units, from the moving player's POV).
SACRIFICE_FAILED_SCORE = -0.3


def _side_sign(side: str) -> int:
    return 1 if side == "white" else -1


def _project_forced_capture(
    state_after: GameState,
    engine: EngineProtocol | None,
) -> GameState | None:
    """Apply any one of the opponent's max-capture legal moves to
    ``state_after``. Returns ``None`` when no capture is available or
    when the engine is missing. Used to project the board state after
    the forced reply so we can measure the true material change of a
    sacrifice on FMJD-strict gameplay.
    """
    if engine is None:
        return None
    opp_moves = engine.legal_moves(state_after)
    captures = [m for m in opp_moves if m.is_capture]
    if not captures:
        return None
    # Under FMJD strict, every move in ``captures`` shares the same
    # (maximal) capture count, so any element is equivalent for the
    # material balance check.
    return engine.apply_move(state_after, captures[0])


class SacrificeDetector(MotifDetector):
    """Detector for the ``sacrifice`` motif."""

    name = "sacrifice"

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

        # Path 1 — material change visible on ``state_after`` already.
        delta = sign * (material_balance(state_after) - material_balance(state_before))
        if delta < 0:
            if sign * scan_score_after < SACRIFICE_FAILED_SCORE:
                return None
            loss = abs(delta)
            return MotifMatch(
                motif="sacrifice",
                role="played",
                squares=list(move.path),
                pv=list(pv) if pv else [],
                severity=min(1.0, loss / 3.0),
                metadata={
                    "material_loss": loss,
                    "score_after": scan_score_after,
                    "path": "immediate",
                },
            )

        # Path 2 — FMJD-strict: the loss appears after the opponent's
        # forced capture reply. Only fires on non-capturing moves —
        # capturing moves that net zero are exchanges, not sacrifices.
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
        if sign * scan_score_after < SACRIFICE_FAILED_SCORE:
            return None
        loss = abs(projected_delta)
        return MotifMatch(
            motif="sacrifice",
            role="played",
            squares=list(move.path),
            pv=list(pv) if pv else [],
            severity=min(1.0, loss / 3.0),
            metadata={
                "material_loss": loss,
                "score_after": scan_score_after,
                "path": "forced_reply",
            },
        )
