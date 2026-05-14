"""``coup_manoury`` — sacrifice that sets up a 4+ capture rafle two plies later.

The Manoury pattern, taught as the canonical "combinaison à profit" in
French clubs, is:

1. the player gives up material (a single piece sacrifice, sometimes
   two) on a square that is *not* itself a rafle;
2. the opponent's best reply is forced into a configuration where the
   diagonals align;
3. the player's follow-up is a long rafle that captures at least four
   opponent men in a single move.

Detection relies on the Scan principal variation rather than on a
geometric pattern: the third PV entry (``pv[2]``) is the player's
follow-up; we require it to be a capture sequence with at least four
``x`` separators (i.e. four pieces taken).

We deliberately do **not** require the sacrifice's immediate material
delta to be exactly −1: champion-level Manoury variants sometimes give
up two pieces before the rafle. We do require a *non-positive* delta
and a Scan score that stays acceptable after the dust settles.
"""

from __future__ import annotations

from ..features.material import material_balance
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector
from .sacrifices import SACRIFICE_FAILED_SCORE

#: Minimum captures in the follow-up rafle for the motif to fire.
MANOURY_MIN_FOLLOWUP_CAPTURES = 4


def _side_sign(side: str) -> int:
    return 1 if side == "white" else -1


def _capture_count(notation_str: str) -> int:
    """Number of pieces taken in a PDN-like capture string.

    ``"40x29x18"`` represents 2 captures; in general the count is
    ``notation.count("x")``. Quiet moves return 0.
    """
    return notation_str.count("x")


def _followup_capture_count(pv: list[str] | None) -> int:
    if not pv or len(pv) < 3:
        return 0
    return _capture_count(pv[2])


def _build_match(
    move: Move,
    *,
    side: str,
    role: str,
    pv: list[str],
    material_loss: int,
    followup_captures: int,
    score_after: float,
) -> MotifMatch:
    return MotifMatch(
        motif="coup_manoury",
        role=role,
        squares=list(move.path),
        pv=list(pv[:3]),
        severity=min(1.0, followup_captures / 6.0),
        metadata={
            "side": side,
            "material_loss": material_loss,
            "followup_captures": followup_captures,
            "score_after": score_after,
            "followup_notation": pv[2],
        },
    )


class CoupManouryDetector(MotifDetector):
    """Detector for the ``coup_manoury`` motif."""

    name = "coup_manoury"

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
        side = state_before.turn
        sign = _side_sign(side)
        delta = sign * (material_balance(state_after) - material_balance(state_before))
        if delta >= 0:
            return None
        if sign * scan_score_after < SACRIFICE_FAILED_SCORE:
            return None
        followup = _followup_capture_count(pv)
        if followup < MANOURY_MIN_FOLLOWUP_CAPTURES:
            return None
        assert pv is not None
        return _build_match(
            move,
            side=side,
            role="played",
            pv=pv,
            material_loss=abs(delta),
            followup_captures=followup,
            score_after=scan_score_after,
        )

    def detect_missed(
        self,
        state_before: GameState,
        best_move: Move,
        best_pv: list[str],
        played_move: Move,
        *,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        if played_move.path == best_move.path:
            return None
        if engine is None:
            return None
        side = state_before.turn
        try:
            state_after_best = engine.apply_move(state_before, best_move)
        except Exception:  # noqa: BLE001 — keep registry resilient
            return None
        sign = _side_sign(side)
        delta = sign * (
            material_balance(state_after_best) - material_balance(state_before)
        )
        if delta >= 0:
            return None
        followup = _followup_capture_count(best_pv)
        if followup < MANOURY_MIN_FOLLOWUP_CAPTURES:
            return None
        return _build_match(
            best_move,
            side=side,
            role="missed",
            pv=best_pv,
            material_loss=abs(delta),
            followup_captures=followup,
            score_after=0.0,
        )
