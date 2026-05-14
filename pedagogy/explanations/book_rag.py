"""BookRAG — retrieve pedagogical excerpts by motif name (spec §7).

Implements the v1 strategy described in the spec: build a TF-IDF index over
the corpus PDFs (one document per page) at first call, then answer queries
by cosine similarity. v1 has no embeddings — pure lexical retrieval is
sufficient for named motifs, which are rare enough in the corpus to stand
out.

The class supports two construction paths:

- ``BookRAG(books_dir=Path(...))`` — the production path. Walks the
  directory, runs ``pdftotext`` on every PDF, splits on form-feed, and
  keeps one ``(book, page, text)`` row per non-empty page.
- ``BookRAG.from_documents(...)`` — the test path. Lets a caller seed the
  index with synthetic ``(book, page, text)`` tuples and skip the I/O.

Dependencies on ``scikit-learn`` and ``pdftotext`` (poppler-utils) are
imported lazily so importing :mod:`pedagogy.explanations` doesn't pay the
cost on instances that never call :meth:`search`.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

#: Half-width of the excerpt returned for each hit, in characters.
EXCERPT_HALF_WIDTH = 100

#: Lowest cosine similarity accepted as a hit (filters numerical noise).
_MIN_SCORE = 1e-6


@dataclass(frozen=True)
class BookExcerpt:
    """One pedagogical excerpt returned by :meth:`BookRAG.search`."""

    book: str
    page: int
    excerpt: str
    score: float

    def as_dict(self) -> dict[str, Any]:
        return {"book": self.book, "page": self.page, "excerpt": self.excerpt, "score": self.score}


def _pdf_to_pages(pdf: Path) -> list[str]:
    """Run ``pdftotext`` on ``pdf`` and split on form-feed (page separator)."""
    out = subprocess.check_output(
        ["pdftotext", "-layout", str(pdf), "-"], text=True
    )
    return out.split("\f")


def _query_for(motif_name: str) -> str:
    """Normalise a motif name into a free-text query."""
    return motif_name.replace("_", " ").lower()


def _extract_excerpt(text: str, query: str, half_width: int = EXCERPT_HALF_WIDTH) -> str:
    """Return ``2 * half_width`` chars around the first query-token hit.

    Falls back to the first ``2 * half_width`` chars when no token matches —
    the caller still wants something readable to show in the UI.
    """
    text_compact = re.sub(r"\s+", " ", text).strip()
    if not text_compact:
        return ""
    tokens = [tok for tok in query.split() if tok]
    lower = text_compact.lower()
    hit = -1
    for tok in tokens:
        idx = lower.find(tok)
        if idx >= 0 and (hit < 0 or idx < hit):
            hit = idx
    if hit < 0:
        return text_compact[: 2 * half_width].strip()
    start = max(0, hit - half_width)
    end = min(len(text_compact), hit + half_width)
    return text_compact[start:end].strip()


class BookRAG:
    """Lexical retrieval over the corpus PDFs."""

    def __init__(self, books_dir: Path | None = None):
        self.books_dir = Path(books_dir) if books_dir is not None else None
        self._docs: list[tuple[str, int, str]] = []
        self._vectorizer: Any = None
        self._matrix: Any = None
        self._built: bool = False

    @classmethod
    def from_documents(cls, documents: Iterable[tuple[str, int, str]]) -> "BookRAG":
        """Construct a BookRAG from in-memory ``(book, page, text)`` tuples.

        Used by tests to bypass PDF I/O. The TF-IDF index is built eagerly
        so callers don't need to know about the lazy-load mechanism.
        """
        rag = cls(books_dir=None)
        rag._docs = [d for d in documents if d[2].strip()]
        rag._build_tfidf()
        return rag

    @classmethod
    def from_directory(cls, books_dir: str | Path) -> "BookRAG":
        """Construct a BookRAG pointed at a directory of PDFs.

        Convenience constructor used by draught-master's app startup
        hook (``backend/main.py``) to build the shared singleton. Same
        semantics as ``BookRAG(books_dir=...)``: the TF-IDF index is
        built lazily on the first ``search()`` call so app boot stays
        cheap even when the corpus has hundreds of PDFs.
        """
        return cls(books_dir=Path(books_dir))

    def _load_documents(self) -> list[tuple[str, int, str]]:
        if self.books_dir is None:
            return []
        rows: list[tuple[str, int, str]] = []
        for pdf in sorted(self.books_dir.glob("*.pdf")):
            try:
                pages = _pdf_to_pages(pdf)
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
            for page_index, text in enumerate(pages, start=1):
                if text.strip():
                    rows.append((pdf.name, page_index, text))
        return rows

    def _build_tfidf(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        if not self._docs:
            self._vectorizer = None
            self._matrix = None
            self._built = True
            return
        self._vectorizer = TfidfVectorizer(lowercase=True)
        self._matrix = self._vectorizer.fit_transform(text for _, _, text in self._docs)
        self._built = True

    def _ensure_built(self) -> None:
        if self._built:
            return
        self._docs = self._load_documents()
        self._build_tfidf()

    def search(self, motif_name: str, max_results: int = 1) -> list[BookExcerpt]:
        """Return up to ``max_results`` excerpts most relevant to ``motif_name``.

        ``motif_name`` is the canonical underscore-separated form
        (``"coup_royal"``, ``"envoi_a_dame"``, …). Underscores are converted
        to spaces before the TF-IDF query so the PDF tokenisation sees the
        same form as the printed text.

        Returns the empty list when nothing scores above the noise floor.
        """
        self._ensure_built()
        if self._vectorizer is None or self._matrix is None or not self._docs:
            return []
        if max_results <= 0:
            return []
        query = _query_for(motif_name)
        query_vec = self._vectorizer.transform([query])

        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(
            (
                (float(score), idx)
                for idx, score in enumerate(sims)
                if score > _MIN_SCORE
            ),
            reverse=True,
        )[:max_results]

        out: list[BookExcerpt] = []
        for score, idx in ranked:
            book, page, text = self._docs[idx]
            out.append(
                BookExcerpt(
                    book=book,
                    page=page,
                    excerpt=_extract_excerpt(text, query),
                    score=score,
                )
            )
        return out

    def documents(self) -> Sequence[tuple[str, int, str]]:
        """Expose the indexed documents (useful for tests / debugging)."""
        self._ensure_built()
        return tuple(self._docs)
