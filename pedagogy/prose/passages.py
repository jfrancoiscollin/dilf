"""ProsePassage — a verbatim excerpt of a master's text.

A ProsePassage is the atomic unit of strategic truth in the dilf
pipeline. Per CADRAGE_STRATEGIE.md §4.S1, every strategic assertion
must reference one or more passages by their stable ``passage_id``.

Passages are produced by ``scripts/index_prose.py``; the emit step
writes a Python module that exposes ``ALL_PASSAGES`` as a frozen
tuple of ``ProsePassage`` instances.

Passage id format
-----------------
``<SOURCE>_<book>_p<page>_<para_idx>`` — uppercase source code (e.g.
``SIJBRANDS``), book slug, zero-padded page number, two-digit
paragraph index on the page (0-based). Stable as long as the source
PDF and the chunking heuristic don't change.

Examples::

    SIJBRANDS_classique_p042_03
    SPRINGER_milieu_p108_00
    ROOZENBURG_systeme_p015_07

Embeddings
----------
Optional. The ``embedding`` field holds a fixed-size vector of floats
when ``index_prose.py embed`` has been run (default model is
sentence-transformers all-MiniLM-L6-v2, 384 dims). Storage is by
reference: when present, the actual vector lives in the index file
and ``embedding=None`` here keeps the fixture module small. A
companion sidecar ``prose_passages.embeddings.npy`` carries the
matrix in the same row order as ``ALL_PASSAGES``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ProsePassage:
    """A verbatim excerpt of a single passage from the corpus."""

    # Stable identity (see module docstring for format)
    passage_id: str

    # The verbatim text. Whitespace is preserved as-extracted by
    # pdftotext -layout so that quoting is faithful. The chunker may
    # strip outer whitespace but never rewrite the body.
    text: str

    # Source pointer
    source: str         # uppercase code, e.g. "SIJBRANDS"
    book: str           # slug, e.g. "classique"
    page: int           # 1-based page number in the PDF
    char_offset: int    # 0-based char offset on the page (for re-locating)

    # Heuristic tags, set by the `tag` step. See CADRAGE_STRATEGIE.md §5.1.
    systems: tuple[str, ...] = field(default_factory=tuple)
    # ^ e.g. ("roozenburg",) or ("classique", "keller") when ambiguous
    phase: Optional[str] = None     # "ouverture" | "milieu" | "finale" | None
    nature: Optional[str] = None    # "principe" | "plan" | "avertissement" | None

    # Optional dense vector (see module docstring). Stored externally
    # in practice; this field is here to make the contract explicit.
    embedding: Optional[tuple[float, ...]] = None
