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


def render_from_templates(verdict: MoveVerdict, lang: str = "fr") -> str:
    """Compose the template-only commentary.

    Iterates :attr:`MoveVerdict.motifs` and concatenates the non-None
    template strings. Falls back to :func:`render_verdict_fallback`
    when none of the motifs produced a template.

    ``lang`` is accepted for forward compatibility with PR 12 (Templates
    EN). For now anything other than ``"fr"`` falls back to French.
    """
    del lang  # PR 12 will fan out the per-language registries.
    parts = [
        text
        for motif in verdict.motifs
        if (text := render_template(motif, verdict.verdict)) is not None
    ]
    if parts:
        return " ".join(parts)
    return render_verdict_fallback(verdict.verdict)


def _append_book_pointer(base: str, verdict: MoveVerdict, book_rag: BookRAG) -> str:
    for motif in verdict.motifs:
        hits = book_rag.search(motif.motif, max_results=1)
        if hits:
            top = hits[0]
            return f"{base}\n\nPour approfondir : {top.book} p.{top.page}"
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
    ``"claude"``. ``client`` is forwarded to :func:`write_commentary`
    in claude mode (so tests can inject a fake). The book reference
    line in ``template+book`` mode only appears when ``book_rag`` is
    supplied and produces at least one hit.
    """
    if mode == "template":
        return render_from_templates(verdict, lang=lang)
    if mode == "template+book":
        base = render_from_templates(verdict, lang=lang)
        if book_rag is None:
            return base
        return _append_book_pointer(base, verdict, book_rag)
    if mode == "claude":
        return await write_commentary(
            verdict,
            book_rag=book_rag,
            client=client,
            fallback=lambda v: render_from_templates(v, lang=lang),
        )
    raise ValueError(f"Unknown explanation mode: {mode!r}")
