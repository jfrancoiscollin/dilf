"""Explanation layer — render :class:`MoveVerdict` into prose.

PR 6 of the spec lands only the French templates and their renderer.
Subsequent PRs will add:

- English templates + i18n (PR 12)
- BookRAG with TF-IDF retrieval over ``docs/corpus/`` (PR 11)
- Claude writer with anti-hallucination verification (PR 10)

No I/O lives here; every function is pure given its inputs.
"""

from __future__ import annotations

from .book_rag import BookExcerpt, BookRAG
from .claude_writer import (
    KNOWN_MOTIFS_FR,
    SYSTEM_PROMPT,
    build_user_prompt,
    detect_invented_motifs,
    write_commentary,
)
from .pipeline import explain_verdict, render_from_templates
from .templates_fr import (
    TEMPLATES_FR,
    VERDICT_FALLBACKS_FR,
    render_template,
    render_verdict_fallback,
)

__all__ = [
    "BookExcerpt",
    "BookRAG",
    "KNOWN_MOTIFS_FR",
    "SYSTEM_PROMPT",
    "TEMPLATES_FR",
    "VERDICT_FALLBACKS_FR",
    "build_user_prompt",
    "detect_invented_motifs",
    "explain_verdict",
    "render_from_templates",
    "render_template",
    "render_verdict_fallback",
    "write_commentary",
]
