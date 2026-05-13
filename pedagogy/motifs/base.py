"""Abstract base class for motif detectors.

A *motif* is a named pattern in the position or in the played move that the
pedagogy framework can talk about. Every concrete detector inherits from
:class:`MotifDetector` and implements :meth:`detect`; :meth:`detect_missed`
defaults to "no opinion" and is overridden when relevant.

Detector instances are stateless. They are constructed once per call site
and may be safely reused across positions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from ..game import GameState, Move
from ..protocols import EngineProtocol
from ..types import MotifMatch


class MotifDetector(ABC):
    """Base class for every motif detector.

    Class attributes:
        name: stable identifier used in :class:`MotifMatch.motif` and as
            the lookup key in template tables.
        requires_pv: hint to orchestrators that ``detect`` benefits from a
            principal variation. Detectors that look only at the played
            move set this to ``False`` so the orchestrator can call them
            even when no PV is available.
    """

    name: ClassVar[str]
    requires_pv: ClassVar[bool] = True

    @abstractmethod
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
        """Return a :class:`MotifMatch` if the played move exhibits the motif."""

    def detect_missed(
        self,
        state_before: GameState,
        best_move: Move,
        best_pv: list[str],
        played_move: Move,
        *,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        """Return a :class:`MotifMatch` if the *best* move (not played) is the motif.

        Default implementation returns ``None``: detectors that have no
        meaningful "missed" semantics (e.g. ``prise_max_ratee``) inherit
        this safely.
        """
        return None
