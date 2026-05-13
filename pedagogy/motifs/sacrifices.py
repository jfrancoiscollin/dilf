"""``sacrifice`` — material loss compensated by a still-acceptable Scan score.

Follows the spec pseudo-code (§5):

* let ``side_sign = +1`` for white, ``-1`` for black
* ``material_loss = side_sign × (balance_after − balance_before)``
  is negative when the player just *lost* material
* if it is non-negative, no sacrifice was played
* if the Scan score from the player's POV is too negative
  (``< −0.3`` pawn units), the sacrifice failed and we do not flag it
* severity = ``min(1, |material_loss| / 3)``

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
        delta = sign * (material_balance(state_after) - material_balance(state_before))
        if delta >= 0:
            return None
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
            },
        )
