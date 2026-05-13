"""Tests for ``pedagogy.explanations.book_rag`` — PR 11.

The production path needs scikit-learn + poppler-utils + real PDFs; we
exercise it via :meth:`BookRAG.from_documents` instead, which injects
synthetic ``(book, page, text)`` rows and bypasses every I/O step.

The TF-IDF retrieval itself is exercised end-to-end with scikit-learn —
no mocking; if scikit-learn isn't installed the whole module is skipped.
"""

from __future__ import annotations

import pytest

pytest.importorskip("sklearn")

from pedagogy.explanations.book_rag import (
    BookExcerpt,
    BookRAG,
    _extract_excerpt,
    _query_for,
)


# ---------------------------------------------------------------------------
# _query_for — query normalisation
# ---------------------------------------------------------------------------


def test_query_for_replaces_underscores_with_spaces() -> None:
    assert _query_for("coup_royal") == "coup royal"


def test_query_for_lowercases_input() -> None:
    assert _query_for("Coup_Royal") == "coup royal"


def test_query_for_passes_simple_motif_unchanged_apart_from_case() -> None:
    assert _query_for("sacrifice") == "sacrifice"


# ---------------------------------------------------------------------------
# _extract_excerpt
# ---------------------------------------------------------------------------


def test_extract_excerpt_returns_window_around_query_term() -> None:
    text = (
        "Avant tout, parlons de la défense centrale. "
        "Puis le coup royal, ce mécanisme classique, "
        "ramasse jusqu'à sept pions sur l'axe central."
    )
    excerpt = _extract_excerpt(text, "coup royal", half_width=30)
    assert "coup royal" in excerpt.lower()
    assert len(excerpt) <= 80


def test_extract_excerpt_compacts_whitespace() -> None:
    text = "  multiple\n\n  spaces\tand\t\ttabs  here  "
    excerpt = _extract_excerpt(text, "spaces")
    assert "  " not in excerpt  # no double spaces
    assert "\n" not in excerpt
    assert "\t" not in excerpt


def test_extract_excerpt_falls_back_to_start_when_no_match() -> None:
    text = "Aucune mention de la chose recherchée dans ce paragraphe."
    excerpt = _extract_excerpt(text, "coup royal", half_width=20)
    assert excerpt.startswith("Aucune mention")


def test_extract_excerpt_returns_empty_for_whitespace_only_input() -> None:
    assert _extract_excerpt("   \n\n  ", "coup royal") == ""


# ---------------------------------------------------------------------------
# BookRAG.from_documents — empty / degenerate cases
# ---------------------------------------------------------------------------


def test_from_documents_empty_rag_returns_no_results() -> None:
    rag = BookRAG.from_documents([])
    assert rag.search("coup_royal") == []


def test_from_documents_skips_blank_pages() -> None:
    rag = BookRAG.from_documents(
        [
            ("dubois.pdf", 1, ""),
            ("dubois.pdf", 2, "   \n\n"),
            ("dubois.pdf", 3, "Le coup royal mène la rafle au centre."),
        ]
    )
    assert len(rag.documents()) == 1
    assert rag.documents()[0][1] == 3


def test_search_returns_empty_when_max_results_is_zero_or_negative() -> None:
    rag = BookRAG.from_documents([("a.pdf", 1, "coup royal central")])
    assert rag.search("coup_royal", max_results=0) == []
    assert rag.search("coup_royal", max_results=-3) == []


# ---------------------------------------------------------------------------
# BookRAG.from_documents — retrieval quality
# ---------------------------------------------------------------------------


@pytest.fixture
def dubois_corpus() -> BookRAG:
    """A tiny three-page synthetic corpus that mimics Dubois prose."""
    return BookRAG.from_documents(
        [
            (
                "dubois_perf.pdf", 7,
                "Le coup royal est une rafle longue qui exploite l'empilement "
                "central. On le rencontre quand l'adversaire surcharge les "
                "cases 22, 23, 27, 28.",
            ),
            (
                "dubois_perf.pdf", 12,
                "Le coup turc désigne une trajectoire qui repasse par la même "
                "case, créant l'illusion d'une double prise.",
            ),
            (
                "dubois_perf.pdf", 21,
                "L'envoi à dame est un sacrifice qui force la promotion en "
                "deux demi-coups, typique en finale.",
            ),
        ]
    )


def test_search_returns_a_hit_for_a_known_motif(dubois_corpus: BookRAG) -> None:
    hits = dubois_corpus.search("coup_royal")
    assert len(hits) == 1
    assert isinstance(hits[0], BookExcerpt)
    assert hits[0].book == "dubois_perf.pdf"
    assert hits[0].page == 7
    assert "coup royal" in hits[0].excerpt.lower()
    assert hits[0].score > 0.0


def test_search_picks_the_most_relevant_page(dubois_corpus: BookRAG) -> None:
    hits = dubois_corpus.search("envoi_a_dame")
    assert len(hits) == 1
    assert hits[0].page == 21


def test_search_max_results_caps_the_output(dubois_corpus: BookRAG) -> None:
    hits = dubois_corpus.search("coup", max_results=5)
    # Only the two coup-prefixed pages should hit; the envoi page contains
    # no occurrence of "coup".
    assert len(hits) == 2
    pages = {h.page for h in hits}
    assert pages == {7, 12}


def test_search_returns_empty_when_no_token_matches(dubois_corpus: BookRAG) -> None:
    assert dubois_corpus.search("not_a_motif") == []


def test_search_is_case_insensitive(dubois_corpus: BookRAG) -> None:
    hits_lower = dubois_corpus.search("coup_royal")
    hits_upper = dubois_corpus.search("COUP_ROYAL")
    assert hits_lower[0].page == hits_upper[0].page


def test_search_ranks_by_descending_score(dubois_corpus: BookRAG) -> None:
    rag = BookRAG.from_documents(
        [
            ("a.pdf", 1, "coup royal coup royal coup royal — page très orientée"),
            ("a.pdf", 2, "Une seule mention du coup royal ici."),
        ]
    )
    hits = rag.search("coup_royal", max_results=2)
    assert len(hits) == 2
    assert hits[0].score >= hits[1].score
    assert hits[0].page == 1  # the denser page wins


def test_book_excerpt_as_dict_returns_expected_keys() -> None:
    rag = BookRAG.from_documents([("x.pdf", 4, "coup royal en plein centre")])
    hit = rag.search("coup_royal")[0]
    payload = hit.as_dict()
    assert set(payload.keys()) == {"book", "page", "excerpt", "score"}
    assert payload["book"] == "x.pdf"
    assert payload["page"] == 4
