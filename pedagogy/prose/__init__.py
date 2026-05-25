"""Prose layer: corpus passages + strategic concepts.

This package is the strategic counterpart to ``pedagogy/tests/fixtures/``
which hosts tactical positions. It hosts:

- :class:`~pedagogy.prose.passages.ProsePassage` — a verbatim excerpt of
  a master's text, identified by a stable ``passage_id``. Produced by
  ``scripts/index_prose.py``.
- :class:`~pedagogy.prose.concepts.StrategicConcept` — a chunk of
  strategic teaching whose every assertion is anchored to either a
  ``passage_id`` (CITED / SYNTHESIS) or a Scan evaluation (ENGINE).

The contract is documented in ``docs/pre_process_corpus/CADRAGE_STRATEGIE.md``
§4 (anti-hallucination rules) and §6 (fixture format).
"""

from pedagogy.prose.concepts import (
    Assertion,
    AssertionType,
    IllustrativePosition,
    StrategicConcept,
)
from pedagogy.prose.passages import ProsePassage

__all__ = [
    "Assertion",
    "AssertionType",
    "IllustrativePosition",
    "ProsePassage",
    "StrategicConcept",
]
