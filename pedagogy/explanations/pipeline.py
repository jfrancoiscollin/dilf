"""Pipeline orchestrator for the explanations layer (spec §7).

Three stackable modes:

- ``template``: deterministic, no LLM, no book lookup. Uses
  :func:`render_template` per detected motif and falls back to the
  generic verdict phrase from :data:`VERDICT_FALLBACKS_FR` when no
  motif template matched.
- ``template+book``: template output, plus one ``BookRAG`` excerpt
  appended as a *"Pour approfondir"* line when the corpus has a hit.
- ``claude``: hands the verdict to :func:`write_commentary`, which
  calls Claude and falls back to the template renderer on any
  hallucination.
"""

from __future__ import annotations

from typing import Optional

from ..types import MoveVerdict
from .book_rag import BookRAG
from .claude_writer import write_commentary
from .templates_fr import render_template, render_verdict_fallback


#: Localised "to dig deeper" preamble used by template+book mode.
_BOOK_POINTER_PREFIX = {"fr": "Pour approfondir", "en": "Read more"}


def render_from_templates(verdict: MoveVerdict, lang: str = "fr") -> str:
    """Compose the template-only commentary in the requested language.

    Iterates :attr:`MoveVerdict.motifs` and concatenates the non-None
    template strings. Falls back to :func:`render_verdict_fallback`
    when none of the motifs produced a template. Unknown ``lang`` values
    silently degrade to French.
    """
    parts = [
        text
        for motif in verdict.motifs
        if (text := render_template(motif, verdict.verdict, lang=lang)) is not None
    ]
    if parts:
        return " ".join(parts)
    return render_verdict_fallback(verdict.verdict, lang=lang)


def _append_book_pointer(
    base: str, verdict: MoveVerdict, book_rag: BookRAG, lang: str = "fr"
) -> str:
    for motif in verdict.motifs:
        hits = book_rag.search(motif.motif, max_results=1)
        if hits:
            top = hits[0]
            preamble = _BOOK_POINTER_PREFIX.get(lang, _BOOK_POINTER_PREFIX["fr"])
            return f"{base}\n\n{preamble} : {top.book} p.{top.page}"
    return base


async def explain_verdict(
    verdict: MoveVerdict,
    *,
    mode: str = "template",
    book_rag: Optional[BookRAG] = None,
    lang: str = "fr",
    client: object = None,
) -> str:
    """Top-level entry point used by the API layer.

    ``mode`` is one of ``"template"``, ``"template+book"`` or
    ``"claude"``. ``lang`` is propagated to every layer: the template
    registry, the verdict fallback, the book-pointer preamble in
    ``template+book``, and the Claude system prompt + verifier in
    ``claude`` mode.
    """
    if mode == "template":
        return render_from_templates(verdict, lang=lang)
    if mode == "template+book":
        base = render_from_templates(verdict, lang=lang)
        if book_rag is None:
            return base
        return _append_book_pointer(base, verdict, book_rag, lang=lang)
    if mode == "claude":
        return await write_commentary(
            verdict,
            book_rag=book_rag,
            client=client,
            fallback=lambda v: render_from_templates(v, lang=lang),
            lang=lang,
        )
    raise ValueError(f"Unknown explanation mode: {mode!r}")
