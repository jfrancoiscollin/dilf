"""Verdict layer — classify each half-move into a :class:`Verdict`.

Two pieces of public API live here:

- :func:`classify_move` (in :mod:`pedagogy.verdicts.classifier`) maps a pair
  of Scan scores + the played move's context into a single :class:`Verdict`.
- :func:`assemble_verdict` (in :mod:`pedagogy.verdicts.assembler`) builds the
  full :class:`MoveVerdict` by composing the motif registry, the classifier,
  and the features layer.

No I/O lives in this layer. The Scan scores are passed in by the caller —
nothing in :mod:`pedagogy.verdicts` ever touches a Scan binary, a database,
or a network.
"""

from __future__ import annotations

from .assembler import assemble_verdict
from .classifier import classify_move, win_chance

__all__ = [
    "assemble_verdict",
    "classify_move",
    "win_chance",
]
