"""``coup_enfilade`` — rafle that takes 3+ men aligned on a single diagonal.

An *enfilade* is the simplest of the long rafles: the captured pieces
sit in a row along **one** diagonal, with the moving piece travelling
straight without ever reversing direction. The path therefore has a
constant ``(row_delta_sign, col_delta_sign)`` between every consecutive
pair of squares, and the captured pieces are spaced one diagonal step
apart.

Distinguished from :class:`pedagogy.motifs.coup_de_talon.CoupDeTalonDetector`
by the absence of any direction change. Distinguished from
:class:`pedagogy.motifs.coup_express.CoupExpressDetector` by the capture
range it covers: ``coup_enfilade`` is the club-level 3- or 4-capture
straight rafle, ``coup_express`` takes over from 5 captures upward. The
two are intentionally disjoint so each played rafle produces at most one
of these two motifs.
"""

from __future__ import annotations

from ..features.geometry import square_to_coords
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

#: Minimum capture count to even consider the motif. Below this we let
#: :class:`CoupDeTalonDetector` / :class:`SacrificeDetector` carry the
#: signal alone — a 2-capture straight rafle is too generic to teach.
ENFILADE_MIN_CAPTURES = 3

#: Maximum capture count. From 5 onwards :class:`CoupExpressDetector`
#: takes over with its own template (the spectacular long rafle).
ENFILADE_MAX_CAPTURES = 4


def _step_signs(a: int, b: int) -> tuple[int, int]:
    """Return ``(sign(row_b - row_a), sign(col_b - col_a))``."""
    ra, ca = square_to_coords(a)
    rb, cb = square_to_coords(b)
    return (1 if rb > ra else -1 if rb < ra else 0, 1 if cb > ca else -1 if cb < ca else 0)


def _path_is_single_diagonal(path: tuple[int, ...]) -> bool:
    """``True`` iff every consecutive pair shares the same diagonal step.

    A path of length 2 is trivially single-diagonal (one direction).
    """
    if len(path) < 2:
        return False
    steps = [_step_signs(a, b) for a, b in zip(path, path[1:])]
    return all(s == steps[0] for s in steps[1:])


class CoupEnfiladeDetector(MotifDetector):
    """Detector for the ``coup_enfilade`` motif."""

    name = "coup_enfilade"
    requires_pv = False

    def _detect_on(self, move: Move, role: str, severity_floor: float) -> MotifMatch | None:
        if not move.is_capture:
            return None
        cnt = len(move.captures)
        if cnt < ENFILADE_MIN_CAPTURES or cnt > ENFILADE_MAX_CAPTURES:
            return None
        if not _path_is_single_diagonal(move.path):
            return None
        return MotifMatch(
            motif=self.name,
            role=role,
            squares=[*move.path],
            pv=[notation(move)],
            severity=max(severity_floor, min(1.0, len(move.captures) / 5.0)),
            metadata={
                "captures_count": len(move.captures),
                "path_length": len(move.path),
            },
        )

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
        return self._detect_on(move, role="played", severity_floor=0.0)

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
        return self._detect_on(best_move, role="missed", severity_floor=1.0)
