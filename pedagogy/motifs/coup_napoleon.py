"""``coup_napoleon`` — sacrifice + opponent deflection + promotion follow-up.

The Napoléon pattern, as taught in classical French manuals (Dubois,
Bizot), is a three-ply sequence:

1. the player plays a sacrifice (loses material in the immediate
   after-state from their POV);
2. the opponent's forced — or simply best — response is a *capture*,
   which **deflects** an opponent piece away from a diagonal that was
   guarding the player's path to promotion;
3. the player's next move lands on their own promotion row.

What distinguishes the Napoléon from a plain :class:`EnvoiADameDetector`
is the explicit deflection step: ``pv[1]`` must be a capture move. A
``envoi_a_dame`` accepts any opponent response; Napoléon requires the
opponent to actively take something on the deflection square.

The detector requires a Scan principal variation of length ≥ 3. Without
a PV the motif cannot be confirmed and the detector returns ``None``.
"""

from __future__ import annotations

from ..features.geometry import BLACK_PROMOTION_ROW, WHITE_PROMOTION_ROW
from ..features.material import material_balance
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector
from .sacrifices import SACRIFICE_FAILED_SCORE


def _side_sign(side: str) -> int:
    return 1 if side == "white" else -1


def _promotion_row_for(side: str) -> frozenset[int]:
    return WHITE_PROMOTION_ROW if side == "white" else BLACK_PROMOTION_ROW


def _is_capture_notation(text: str) -> bool:
    """``True`` if ``text`` represents a capture (contains 'x') rather than a slide."""
    return "x" in text


def _last_square_of_notation(text: str) -> int | None:
    if not text:
        return None
    tokens = text.replace("-", "x").split("x")
    try:
        return int(tokens[-1])
    except ValueError:
        return None


def _matches_napoleon_pv(
    side: str,
    pv: list[str] | None,
) -> int | None:
    """Return the landing square of the promotion follow-up, or ``None``.

    ``pv[0]`` is the played move (ignored here, the caller already has the
    ``Move`` object), ``pv[1]`` is the opponent response, ``pv[2]`` is the
    player's follow-up.
    """
    if not pv or len(pv) < 3:
        return None
    opp_response = pv[1]
    if not _is_capture_notation(opp_response):
        return None
    follow_up = pv[2]
    landing = _last_square_of_notation(follow_up)
    if landing is None:
        return None
    if landing not in _promotion_row_for(side):
        return None
    return landing


def _build_match(
    move: Move,
    *,
    side: str,
    role: str,
    pv: list[str],
    promotion_square: int,
    material_loss: int,
    score_after: float,
) -> MotifMatch:
    return MotifMatch(
        motif="coup_napoleon",
        role=role,
        squares=[*move.path, promotion_square],
        pv=list(pv[:3]),
        severity=min(1.0, 0.5 + material_loss / 4.0),
        metadata={
            "side": side,
            "material_loss": material_loss,
            "promotion_square": promotion_square,
            "score_after": score_after,
        },
    )


class CoupNapoleonDetector(MotifDetector):
    """Detector for the ``coup_napoleon`` motif."""

    name = "coup_napoleon"

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
        if move.path[-1] in _promotion_row_for(side):
            return None
        promotion_square = _matches_napoleon_pv(side, pv)
        if promotion_square is None:
            return None
        assert pv is not None
        return _build_match(
            move,
            side=side,
            role="played",
            pv=pv,
            promotion_square=promotion_square,
            material_loss=abs(delta),
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
        except Exception:  # noqa: BLE001 — keep registry resilient to engine bugs
            return None
        sign = _side_sign(side)
        delta = sign * (
            material_balance(state_after_best) - material_balance(state_before)
        )
        if delta >= 0:
            return None
        if best_move.path[-1] in _promotion_row_for(side):
            return None
        promotion_square = _matches_napoleon_pv(side, best_pv)
        if promotion_square is None:
            return None
        return _build_match(
            best_move,
            side=side,
            role="missed",
            pv=best_pv,
            promotion_square=promotion_square,
            material_loss=abs(delta),
            score_after=0.0,
        )
