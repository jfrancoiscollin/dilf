"""``coup_bonnard`` — sacrifice that forces opponent promotion, then captures the new king.

Spec §1: "Sacrifice qui force promotion adverse puis dame capturée". The
played move is the sacrifice; the rest of the sequence happens in the
next two half-moves. We rely on the Scan principal variation:

1. The played move loses material in the immediate after-state.
2. The PV contains the opponent's response **landing on the opponent's
   promotion row**.
3. The PV contains a follow-up player move whose path **passes through
   or lands on** the same promotion row, i.e. captures the new king.

When no PV is available the motif cannot be confirmed — the detector
returns ``None`` rather than guess.
"""

from __future__ import annotations

import re

from ..features.formations import compute_features
from ..features.geometry import BLACK_PROMOTION_ROW, WHITE_PROMOTION_ROW
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

_SQUARE_TOKEN = re.compile(r"\d+")


def _squares_in_notation(s: str) -> list[int]:
    return [int(tok) for tok in _SQUARE_TOKEN.findall(s)]


def _move_destination(s: str) -> int | None:
    squares = _squares_in_notation(s)
    return squares[-1] if squares else None


def _move_touches(s: str, target: frozenset[int]) -> bool:
    return any(sq in target for sq in _squares_in_notation(s))


def _material_loss(state_before: GameState, state_after: GameState, side: str) -> int:
    bal_before = compute_features(state_before).material_balance
    bal_after = compute_features(state_after).material_balance
    sign = 1 if side == "white" else -1
    return -sign * (bal_after - bal_before)


def _is_bonnard_setup(
    state_before: GameState,
    state_after: GameState,
    side: str,
    pv: list[str] | None,
) -> bool:
    if not pv or len(pv) < 3:
        return False
    if _material_loss(state_before, state_after, side) < 1:
        return False
    opponent_promotion_row = (
        BLACK_PROMOTION_ROW if side == "white" else WHITE_PROMOTION_ROW
    )
    opp_response = pv[1]
    dest = _move_destination(opp_response)
    if dest is None or dest not in opponent_promotion_row:
        return False
    follow_up = pv[2]
    return _move_touches(follow_up, opponent_promotion_row)


def _build_match(move: Move, side: str, role: str, pv: list[str]) -> MotifMatch:
    return MotifMatch(
        motif="coup_bonnard",
        role=role,
        squares=list(move.path),
        pv=list(pv),
        severity=0.8 if role == "played" else 1.0,
        metadata={"side": side},
    )


class CoupBonnardDetector(MotifDetector):
    """Detector for the ``coup_bonnard`` motif."""

    name = "coup_bonnard"

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
        if not _is_bonnard_setup(state_before, state_after, side, pv):
            return None
        assert pv is not None
        return _build_match(move, side, "played", pv)

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
        except Exception:  # noqa: BLE001 — a missing apply_move shouldn't break the registry
            return None
        if not _is_bonnard_setup(state_before, state_after_best, side, best_pv):
            return None
        return _build_match(best_move, side, "missed", best_pv)
