"""StrategicConcept — a chunk of strategic teaching with sourced assertions.

Mirrors the spec in CADRAGE_STRATEGIE.md §6. Each ``Assertion`` is
either a CITED reformulation of one or more passages, a SYNTHESIS
(decomposable into CITED) or an ENGINE quantitative claim from Scan.
The invariant ``verified=True`` is documented under
:class:`StrategicConcept`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pedagogy.game import GameState


class AssertionType(Enum):
    CITED = "cited"          # Reformulation of one or more corpus passages
    SYNTHESIS = "synthesis"  # Articulation of several CITED by Claude (capped, §4.S5)
    ENGINE = "engine"        # Quantitative claim produced by Scan


@dataclass(frozen=True)
class Assertion:
    """A single statement in a strategic concept, with provenance.

    Per §4.S1, the ``kind`` is always explicit. Per §4.S5, a
    SYNTHESIS must list the ``passage_ids`` of every CITED it relies
    on. Per §4.S7, ``claude_notes`` is the place to record when a
    cited statement is dated (e.g. a Roozenburg judgement from the
    1950s that modern engine analysis nuances).
    """

    text: str
    kind: AssertionType

    # CITED / SYNTHESIS provenance
    passage_ids: tuple[str, ...] = field(default_factory=tuple)

    # ENGINE provenance
    engine_fen: str = ""
    engine_eval: Optional[float] = None

    # Calibration
    confidence: str = "medium"   # "high" | "medium" | "low"
    claude_notes: str = ""


@dataclass(frozen=True)
class IllustrativePosition:
    """A position attached to a StrategicConcept to anchor the claim
    on the board. ``scan_eval`` is filled by ``validate_strategic.py``
    via the Scan engine; until then, ``verified=False``."""

    state: GameState
    caption: str
    scan_eval: Optional[float] = None
    crop_id: str = ""           # Set when extracted from the corpus
    verified: bool = False


@dataclass(frozen=True)
class StrategicConcept:
    """A traceable unit of strategic teaching.

    Invariant for ``verified=True`` (cf §4.S6, validated by the
    upcoming ``scripts/validate_strategic.py``):

    - every CITED / SYNTHESIS assertion has at least one resolvable
      ``passage_id`` in ``ALL_PASSAGES``;
    - every ENGINE assertion has a non-None ``engine_eval``;
    - every illustration has a non-None ``scan_eval``.

    Concepts ship ``verified=False`` by default. The validator is the
    only writer that flips this to ``True`` — never Claude in-conversation.
    """

    # Identity
    id: str             # e.g. "SYS_ROOZENBURG_001"
    system: str         # "classique" | "roozenburg" | "keller" | ...
    title: str
    phase: str          # "ouverture" | "milieu" | "finale"

    # Body
    assertions: tuple[Assertion, ...] = field(default_factory=tuple)
    illustrations: tuple[IllustrativePosition, ...] = field(default_factory=tuple)

    # Meta
    verified: bool = False
    claude_notes: str = ""
