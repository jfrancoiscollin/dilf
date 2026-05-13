"""Tests for the English templates + the lang dispatcher (PR 12)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from pedagogy.explanations import (
    KNOWN_MOTIFS_EN,
    KNOWN_MOTIFS_FR,
    SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_FR,
    TEMPLATES_EN,
    VERDICT_FALLBACKS_EN,
    detect_invented_motifs,
    explain_verdict,
    render_from_templates,
    render_template,
    render_verdict_fallback,
    write_commentary,
)
from pedagogy.motifs import ALL_DETECTORS
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


def _coup_royal_match(role: str = "played", captures: int = 7) -> MotifMatch:
    return MotifMatch(
        motif="coup_royal", role=role,
        squares=[40, 34, 24, 14, 3], pv=["40x29x18x12x3"],
        severity=0.7, metadata={"captures_count": captures},
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
# TEMPLATES_EN coverage parity with TEMPLATES_FR
# ---------------------------------------------------------------------------


def test_every_motif_in_registry_has_an_english_template() -> None:
    motifs = {cls().name for cls in ALL_DETECTORS}
    en_motifs = {motif for (motif, _, _) in TEMPLATES_EN}
    missing = motifs - en_motifs
    assert not missing, f"motifs without EN template: {sorted(missing)}"


def test_english_verdict_fallbacks_cover_every_verdict() -> None:
    assert set(VERDICT_FALLBACKS_EN.keys()) == set(Verdict)
    assert all(v.strip() for v in VERDICT_FALLBACKS_EN.values())


def test_every_motif_emitting_missed_has_english_missed_generic() -> None:
    motifs_with_missed = {
        motif for (motif, role, _) in TEMPLATES_EN if role == "missed"
    }
    motifs_with_missed_generic = {
        motif for (motif, role, verdict) in TEMPLATES_EN
        if role == "missed" and verdict is None
    }
    missing = motifs_with_missed - motifs_with_missed_generic
    assert not missing, f"EN motifs without missed-generic: {sorted(missing)}"


# ---------------------------------------------------------------------------
# render_template — language dispatch
# ---------------------------------------------------------------------------


def test_render_template_returns_english_when_lang_en() -> None:
    text = render_template(_coup_royal_match(), Verdict.BRILLIANT, lang="en")
    assert text is not None
    assert "royal coup" in text.lower()
    assert "magnifique" not in text.lower()


def test_render_template_returns_french_when_lang_fr() -> None:
    text = render_template(_coup_royal_match(), Verdict.BRILLIANT, lang="fr")
    assert text is not None
    assert "magnifique coup royal" in text.lower()


def test_render_template_defaults_to_french_when_lang_omitted() -> None:
    text = render_template(_coup_royal_match(), Verdict.BRILLIANT)
    assert text is not None
    assert "magnifique" in text.lower()


def test_render_template_unknown_lang_falls_back_to_french() -> None:
    text = render_template(_coup_royal_match(), Verdict.BRILLIANT, lang="zz")
    assert text is not None
    assert "magnifique" in text.lower()


def test_render_template_substitutes_metadata_under_lang_en() -> None:
    text = render_template(
        _coup_royal_match(captures=9), Verdict.BRILLIANT, lang="en"
    )
    assert text is not None
    assert "9-piece rafle" in text


# ---------------------------------------------------------------------------
# render_verdict_fallback — language dispatch
# ---------------------------------------------------------------------------


def test_render_verdict_fallback_returns_english_when_lang_en() -> None:
    text = render_verdict_fallback(Verdict.GOOD, lang="en")
    assert "Good move" in text


def test_render_verdict_fallback_returns_french_when_lang_fr() -> None:
    text = render_verdict_fallback(Verdict.GOOD, lang="fr")
    assert "Bon coup" in text


def test_render_verdict_fallback_unknown_lang_falls_back_to_french() -> None:
    assert render_verdict_fallback(Verdict.GOOD, lang="zz") == render_verdict_fallback(
        Verdict.GOOD, lang="fr"
    )


# ---------------------------------------------------------------------------
# render_from_templates — language dispatch
# ---------------------------------------------------------------------------


def test_render_from_templates_propagates_lang_to_motifs() -> None:
    out = render_from_templates(_verdict(motifs=[_coup_royal_match()]), lang="en")
    assert "royal coup" in out.lower()
    assert "magnifique" not in out.lower()


def test_render_from_templates_propagates_lang_to_verdict_fallback() -> None:
    out = render_from_templates(
        _verdict(verdict=Verdict.GOOD, motifs=[]), lang="en"
    )
    assert "Good move" in out


# ---------------------------------------------------------------------------
# detect_invented_motifs — language dispatch
# ---------------------------------------------------------------------------


def test_detect_invented_motifs_catches_english_motif_names() -> None:
    text = "You missed a royal coup here."
    assert detect_invented_motifs(text, _verdict(), lang="en") == ["royal coup"]


def test_detect_invented_motifs_does_not_catch_english_when_lang_fr() -> None:
    text = "You missed a royal coup here."
    # In FR mode the registry doesn't have "royal coup"; the verifier
    # should not flag it.
    assert detect_invented_motifs(text, _verdict(), lang="fr") == []


def test_detect_invented_motifs_allows_english_motif_when_detected() -> None:
    motifs = [_coup_royal_match(role="missed")]
    text = "Royal coup was on the board."
    assert detect_invented_motifs(text, _verdict(motifs=motifs), lang="en") == []


def test_known_motifs_en_canonical_keys_match_fr_canonical_keys() -> None:
    fr_canonicals = set(KNOWN_MOTIFS_FR.values())
    en_canonicals = set(KNOWN_MOTIFS_EN.values())
    assert en_canonicals == fr_canonicals


# ---------------------------------------------------------------------------
# write_commentary — system prompt selection
# ---------------------------------------------------------------------------


def test_write_commentary_uses_english_system_prompt_when_lang_en() -> None:
    client = FakeAsyncClient("Nice central move.")
    asyncio.run(write_commentary(_verdict(), client=client, lang="en"))
    call = client.calls[-1]
    assert call["system"] == SYSTEM_PROMPT_EN
    assert "français" not in call["system"]


def test_write_commentary_uses_french_system_prompt_when_lang_fr() -> None:
    client = FakeAsyncClient("Bon coup central.")
    asyncio.run(write_commentary(_verdict(), client=client, lang="fr"))
    call = client.calls[-1]
    assert call["system"] == SYSTEM_PROMPT_FR


def test_write_commentary_verifier_uses_english_registry_when_lang_en() -> None:
    # Response invents "royal coup" — should fall back.
    client = FakeAsyncClient("You missed a royal coup here.")
    out = asyncio.run(write_commentary(
        _verdict(),
        client=client,
        fallback=lambda _v: "fallback OK",
        lang="en",
    ))
    assert out == "fallback OK"


# ---------------------------------------------------------------------------
# explain_verdict — language propagation
# ---------------------------------------------------------------------------


def test_explain_verdict_template_mode_in_english() -> None:
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_match()]),
        mode="template",
        lang="en",
    ))
    assert "royal coup" in out.lower()


def test_explain_verdict_template_plus_book_uses_english_preamble() -> None:
    from pedagogy.explanations import BookRAG

    rag = BookRAG.from_documents(
        [("dubois_perf.pdf", 7, "The royal coup runs through the centre.")]
    )
    out = asyncio.run(explain_verdict(
        _verdict(motifs=[_coup_royal_match()]),
        mode="template+book",
        book_rag=rag,
        lang="en",
    ))
    assert "Read more" in out
    assert "Pour approfondir" not in out


def test_explain_verdict_claude_mode_in_english() -> None:
    client = FakeAsyncClient("Good central move, well played.")
    out = asyncio.run(explain_verdict(
        _verdict(),
        mode="claude",
        client=client,
        lang="en",
    ))
    assert out == "Good central move, well played."
    assert client.calls[-1]["system"] == SYSTEM_PROMPT_EN
