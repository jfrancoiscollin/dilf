"""``prise_max_ratee`` — the player took, but not the longest sequence.

Under FMJD rules the engine must enforce maximum capture, so this detector
should normally return ``None``. Its actual use case (per spec §5) is PDN
imports from sites that play looser rules: the captured sequence is then
shorter than the longest one our FMJD engine reports as legal.

The detector requires an engine because it has to enumerate the legal
moves available *in the position before the play*. When no engine is
supplied, the detector silently returns ``None`` rather than crashing the
orchestrator.
"""

from __future__ import annotations

from ..game import GameState, Move
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector


class PriseMaxRateeDetector(MotifDetector):
    """Detector for the ``prise_max_ratee`` motif."""

    name = "prise_max_ratee"
    requires_pv = False

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
        if not move.is_capture or engine is None:
            return None
        legal = engine.legal_moves(state_before)
        max_captures = max((len(m.captures) for m in legal), default=0)
        if len(move.captures) >= max_captures:
            return None
        return MotifMatch(
            motif=self.name,
            role="played",
            squares=list(move.path),
            pv=[],
            severity=1.0,
            metadata={
                "captures_played": len(move.captures),
                "captures_possible": max_captures,
            },
        )
