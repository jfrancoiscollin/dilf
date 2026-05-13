"""Tests for ``pedagogy.explanations.pipeline.explain_verdict`` (PR 10).

The pipeline composes the templates, BookRAG and ``write_commentary``;
this file exercises the three explanation modes plus the failure path
(unknown mode).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from pedagogy.explanations import (
    BookRAG,
    explain_verdict,
    render_from_templates,
)
from pedagogy.types import MotifMatch, MoveVerdict, Phase, Verdict


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _verdict(
    *,
    verdict: Verdict = Verdict.BRILLIANT,
    motifs: list[MotifMatch] | None = None,
) -> MoveVerdict:
    return MoveVerdict(
        move_number=15,
        side="white",
        move_notation="40x29",
        fen_before="W:Wb:Bb",
        fen_after="B:Wb:Bb",
        score_before=1.0,
        score_after=1.0,
        delta_winchance=0.0,
        verdict=verdict,
        is_forced=False,
        motifs=motifs or [],
        phase=Phase.MIDDLEGAME,
    )


def _coup_royal_motif(role: str = "played") -> MotifMatch:
    return MotifMatch(
        motif="coup_royal", role=role,
        squares=[40, 34, 24, 14, 3], pv=["40x29x18x12x3"],
        severity=0.7, metadata={"captures_count": 6},
    )


class FakeAsyncClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, Any]] = []
        self.messages = self

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self.response_text)])


# ---------------------------------------------------------------------------
# render_from_templates
# ---------------------------------------------------------------------------


def test_render_from_templates_uses_motif_templates_when_available() -> None:
    out = render_from_templates(_verdict(motifs=[_coup_royal_motif()]))
    assert "Magnifique coup royal" in out


def test_render_from_templates_falls_back_to_verdict_phrase_when_no_motif() -> None:
    out = render_from_templates(_verdict(verdict=Verdict.GOOD, motifs=[]))
    # Comes from VERDICT_FALLBACKS_FR
    assert "Bon coup" in out


def test_render_from_templates_joins_multiple_motif_strings() -> None:
    motifs = [
        _coup_royal_motif("played"),
        MotifMatch(
            motif="sacrifice", role="played",
            squares=[], pv=[], severity=0.5,
            metadata={"material_loss": 1, "score_after": 0.5},
        ),
    ]
    out = render_from_templates(_verdict(motifs=motifs))
    assert "coup royal" in out.lower()
    assert "sacrifice" in out.lower()


# ---------------------------------------------------------------------------
# explain_verdict — mode="template"
# ---------------------------------------------------------------------------


def test_explain_verdict_template_mode_runs_templates_only() -> None:
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_motif()]),
        mode="template",
    ))
    assert "Magnifique coup royal" in out


# ---------------------------------------------------------------------------
# explain_verdict — mode="template+book"
# ---------------------------------------------------------------------------


def test_explain_verdict_template_plus_book_appends_book_pointer() -> None:
    rag = BookRAG.from_documents(
        [("dubois_perf.pdf", 7, "Le coup royal traverse le centre. ")]
    )
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_motif()]),
        mode="template+book",
        book_rag=rag,
    ))
    assert "Magnifique coup royal" in out
    assert "Pour approfondir" in out
    assert "dubois_perf.pdf" in out
    assert "p.7" in out


def test_explain_verdict_template_plus_book_skips_pointer_when_no_hits() -> None:
    rag = BookRAG.from_documents(
        [("other.pdf", 1, "Texte sans rapport avec la position.")]
    )
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_motif()]),
        mode="template+book",
        book_rag=rag,
    ))
    assert "Pour approfondir" not in out


def test_explain_verdict_template_plus_book_returns_template_only_when_no_rag() -> None:
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_motif()]),
        mode="template+book",
        book_rag=None,
    ))
    assert "Pour approfondir" not in out
    assert "coup royal" in out.lower()


# ---------------------------------------------------------------------------
# explain_verdict — mode="claude"
# ---------------------------------------------------------------------------


def test_explain_verdict_claude_mode_returns_claude_text_when_clean() -> None:
    client = FakeAsyncClient("Bon coup au centre, bien joué.")
    out = asyncio.run(explain_verdict(
        _verdict(),  # no motifs, so any tactical name would be hallucinated
        mode="claude",
        client=client,
    ))
    assert out == "Bon coup au centre, bien joué."


def test_explain_verdict_claude_mode_falls_back_to_templates_on_hallucination() -> None:
    client = FakeAsyncClient("Magnifique coup royal qui change la partie.")
    out = asyncio.run(explain_verdict(
        _verdict(verdict=Verdict.GOOD),  # no motifs detected
        mode="claude",
        client=client,
    ))
    # Verifier flagged "coup royal" as invented -> we should have landed
    # on the generic verdict fallback (FR phrase for GOOD).
    assert "Bon coup" in out


# ---------------------------------------------------------------------------
# explain_verdict — error handling
# ---------------------------------------------------------------------------


def test_explain_verdict_raises_value_error_on_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unknown explanation mode"):
        asyncio.run(explain_verdict(_verdict(), mode="not-a-mode"))
