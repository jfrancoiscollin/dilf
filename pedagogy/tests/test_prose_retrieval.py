"""Tests for ``pedagogy.prose.retrieval``.

Sandbox-safe: tests use precomputed vectors (taken from the index
itself) rather than re-encoding text, so they pass without
``sentence-transformers`` installed.
"""
from __future__ import annotations

import numpy as np
import pytest

from pedagogy.prose import retrieval
from pedagogy.prose.passages import ProsePassage


def test_self_retrieval_returns_top_score_for_every_source():
    """Querying with a passage's own vector ranks it at score ≈ 1.0.

    Duplicates exist in the corpus (same text on different pages), so
    several passages may tie at 1.0. We only assert that the queried
    passage is among the top-tied hits, not that it's strictly first.
    """
    shards = retrieval._discover_shards()
    assert shards, "no shards discovered"
    for shard in shards:
        # Sample first/middle/last — full sweep bloats CI time.
        for idx in {0, shard.matrix.shape[0] // 2, shard.matrix.shape[0] - 1}:
            qvec = shard.matrix[idx]
            hits = retrieval.search_with_vector(qvec, k=5, sources=(shard.source,))
            assert hits, f"{shard.source}[{idx}]: no hit"
            top_score = hits[0][0]
            assert top_score == pytest.approx(1.0, abs=1e-3), (
                f"{shard.source}[{idx}]: top score {top_score:.4f} ≠ 1.0"
            )
            wanted = shard.passages[idx].passage_id
            tied = [p.passage_id for s, p in hits if s == pytest.approx(top_score, abs=1e-3)]
            assert wanted in tied, (
                f"{shard.source}[{idx}]: wanted {wanted} not in tied top hits {tied}"
            )


def test_scores_are_monotonic_descending():
    shards = retrieval._discover_shards()
    qvec = shards[0].matrix[0]
    hits = retrieval.search_with_vector(qvec, k=20)
    scores = [s for s, _ in hits]
    assert scores == sorted(scores, reverse=True), "results not sorted by score desc"


def test_source_filter_restricts_results():
    shards_by_src = {s.source: s for s in retrieval._discover_shards()}
    target = "KELLER"
    assert target in shards_by_src, f"{target} not in index"
    qvec = shards_by_src[target].matrix[0]
    hits = retrieval.search_with_vector(qvec, k=10, sources=(target,))
    assert hits, "filtered search returned nothing"
    assert all(p.source == target for _, p in hits), (
        "source filter leaked: got sources " f"{{{p.source for _, p in hits}}}"
    )


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        retrieval.search_with_vector(
            np.ones(retrieval.EMBED_DIM, dtype=np.float32),
            sources=("NOT_A_REAL_SOURCE",),
        )


def test_bad_query_shape_raises():
    with pytest.raises(ValueError, match="shape"):
        retrieval.search_with_vector(np.ones(10, dtype=np.float32))


def test_zero_vector_raises():
    with pytest.raises(ValueError, match="zero"):
        retrieval.search_with_vector(np.zeros(retrieval.EMBED_DIM, dtype=np.float32))


def test_k_caps_at_corpus_size():
    """Asking for more than N results returns N, not crashes."""
    shards = retrieval._discover_shards()
    small = min(shards, key=lambda s: s.matrix.shape[0])
    n = small.matrix.shape[0]
    qvec = small.matrix[0]
    hits = retrieval.search_with_vector(qvec, k=n + 100, sources=(small.source,))
    assert len(hits) == n


def test_hits_carry_passage_metadata():
    """The returned ProsePassage has the same fields as the fixture."""
    shards = retrieval._discover_shards()
    shard = shards[0]
    hits = retrieval.search_with_vector(shard.matrix[0], k=1, sources=(shard.source,))
    _, p = hits[0]
    assert isinstance(p, ProsePassage)
    assert p.source == shard.source
    assert p.book == shard.book
    assert p.passage_id.startswith(shard.source)
