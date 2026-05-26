"""Top-k retrieval over the prose-passage corpus.

Given a query — either a free-text string or a precomputed embedding
vector — return the most semantically similar
:class:`~pedagogy.prose.passages.ProsePassage` instances from one or
more fixture modules. This is the runtime counterpart to
``scripts/index_prose.py``: that script builds the index, this module
queries it.

Two entry points
----------------
- :func:`search_with_vector` — pure numpy, no ML dependency. Takes a
  unit-norm 384-dim query vector and runs cosine similarity against
  the loaded sidecars. Use this in tests and when the query vector
  comes from an external encoder.
- :func:`search` — wraps the above. Encodes the text query with
  sentence-transformers ``all-MiniLM-L6-v2`` (the same model used at
  index time, see ``CADRAGE_STRATEGIE.md §5.1``) and forwards. Imports
  sentence-transformers lazily so this module stays importable in
  sandboxes that can't reach huggingface.co.

Both return ``list[tuple[float, ProsePassage]]`` sorted by score
descending. Scores are cosine similarities in ``[-1, 1]``; since the
index vectors are L2-normalized to unit length, the dot product is
the cosine.

Source filtering
----------------
Pass ``sources=("SIJBRANDS", "SPRINGER")`` to restrict the search to
specific corpora. The default is to search every sidecar found under
``pedagogy/prose/fixtures/``.

CLI
---
::

    python -m pedagogy.prose.retrieval "le coup turc" --k 5
    python -m pedagogy.prose.retrieval "envoi à dame" --k 3 --source SIJBRANDS

Requires sentence-transformers for the text-query CLI; the
``--vector`` flag accepts a JSON list of 384 floats instead.
"""
from __future__ import annotations

import argparse
import functools
import importlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import numpy as np

from pedagogy.prose.passages import ProsePassage

log = logging.getLogger(__name__)

EMBED_DIM = 384
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@dataclass(frozen=True)
class _Shard:
    """One fixture module + its sidecar, loaded once and reused."""

    source: str             # uppercase code, e.g. "SIJBRANDS"
    book: str               # slug, e.g. "course"
    passages: tuple[ProsePassage, ...]
    matrix: np.ndarray      # shape (N, 384), float32, row-normalized


@functools.lru_cache(maxsize=1)
def _discover_shards() -> tuple[_Shard, ...]:
    """Find and load every ``prose_passages_<src>_<book>.py`` + sidecar.

    Sidecar absence (no ``.embeddings.npy`` next to the module) is a
    hard error: a fixture without embeddings can't be searched.
    """
    shards: list[_Shard] = []
    for npy_path in sorted(FIXTURES_DIR.glob("prose_passages_*.embeddings.npy")):
        stem = npy_path.stem.removesuffix(".embeddings")
        module_name = f"pedagogy.prose.fixtures.{stem}"
        module = importlib.import_module(module_name)
        passages: tuple[ProsePassage, ...] = module.ALL_PASSAGES
        matrix = np.load(npy_path).astype(np.float32, copy=False)
        if matrix.shape[0] != len(passages):
            raise RuntimeError(
                f"{npy_path.name}: matrix has {matrix.shape[0]} rows but "
                f"ALL_PASSAGES has {len(passages)} — fixture and sidecar drifted"
            )
        if matrix.shape[1] != EMBED_DIM:
            raise RuntimeError(
                f"{npy_path.name}: matrix dim is {matrix.shape[1]}, expected {EMBED_DIM}"
            )
        # `prose_passages_<src>_<book>` → strip prefix, split on first underscore
        rest = stem.removeprefix("prose_passages_")
        src, _, book = rest.partition("_")
        shards.append(_Shard(source=src.upper(), book=book, passages=passages, matrix=matrix))
    if not shards:
        raise RuntimeError(
            f"No prose-passage sidecars found under {FIXTURES_DIR}. "
            "Run `python scripts/index_prose.py all --pdf <path> --source <SRC> --book <slug>`."
        )
    return tuple(shards)


def _filter_shards(sources: Optional[Sequence[str]]) -> tuple[_Shard, ...]:
    if sources is None:
        return _discover_shards()
    wanted = {s.upper() for s in sources}
    kept = tuple(s for s in _discover_shards() if s.source in wanted)
    missing = wanted - {s.source for s in kept}
    if missing:
        raise ValueError(
            f"Unknown source(s): {sorted(missing)}. "
            f"Available: {sorted({s.source for s in _discover_shards()})}"
        )
    return kept


def search_with_vector(
    query_vector: np.ndarray,
    k: int = 5,
    sources: Optional[Sequence[str]] = None,
) -> list[tuple[float, ProsePassage]]:
    """Return the top-k passages most similar to ``query_vector``.

    ``query_vector`` must have shape ``(384,)`` and is L2-normalized
    in-place before scoring. ``k`` is capped at the total number of
    indexed passages (after source filtering). The result is sorted by
    score descending.
    """
    if query_vector.ndim != 1 or query_vector.shape[0] != EMBED_DIM:
        raise ValueError(
            f"query_vector must have shape ({EMBED_DIM},), got {query_vector.shape}"
        )
    q = query_vector.astype(np.float32, copy=True)
    norm = float(np.linalg.norm(q))
    if norm == 0.0:
        raise ValueError("query_vector is zero — cannot compute cosine similarity")
    q /= norm

    shards = _filter_shards(sources)
    # Score per shard, collect (score, passage) pairs, then global top-k.
    scored: list[tuple[float, ProsePassage]] = []
    for shard in shards:
        # Vectors in the sidecar are already unit-norm, so the dot
        # product is the cosine similarity directly.
        scores = shard.matrix @ q
        for idx in range(scores.shape[0]):
            scored.append((float(scores[idx]), shard.passages[idx]))

    if not scored:
        return []
    k = min(k, len(scored))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:k]


@functools.lru_cache(maxsize=1)
def _encoder() -> "Any":
    """Lazy import + load of sentence-transformers. Cached for reuse."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "Text-query retrieval requires `sentence-transformers`. "
            "Install with `pip install sentence-transformers`, or use "
            "`search_with_vector` with a precomputed vector."
        ) from exc
    return SentenceTransformer(EMBED_MODEL)


def search(
    query: str,
    k: int = 5,
    sources: Optional[Sequence[str]] = None,
) -> list[tuple[float, ProsePassage]]:
    """Encode ``query`` then return the top-k matching passages.

    Uses ``sentence-transformers/all-MiniLM-L6-v2`` to match the model
    used at index time. The first call loads the model (~80 MB); later
    calls reuse it.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")
    vec = _encoder().encode([query], normalize_embeddings=True)[0]
    return search_with_vector(np.asarray(vec, dtype=np.float32), k=k, sources=sources)


def _cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", help="Free-text query (or '-' to read --vector JSON)")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--source",
        action="append",
        default=None,
        help="Restrict to this source (uppercase code, e.g. SIJBRANDS). Repeatable.",
    )
    parser.add_argument(
        "--vector",
        help="Path to a JSON file containing a 384-float query vector. "
        "When set, the positional `query` argument is used only as a label.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.vector:
        data = json.loads(Path(args.vector).read_text())
        hits = search_with_vector(np.asarray(data, dtype=np.float32), k=args.k, sources=args.source)
    else:
        hits = search(args.query, k=args.k, sources=args.source)

    for score, p in hits:
        snippet = " ".join(p.text.split())[:160]
        print(f"{score:6.3f}  {p.passage_id}  p.{p.page}")
        print(f"        {snippet}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
