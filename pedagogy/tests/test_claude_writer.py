"""Tests for ``pedagogy.explanations.claude_writer`` (PR 10).

Coverage targets the spec's zero-tolerance hallucination policy
(§14.7) and the prompt-shape invariants. The Anthropic SDK is never
actually called — we inject a fake client that records the request
and returns canned text.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from pedagogy.explanations.claude_writer import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    KNOWN_MOTIFS_FR,
    SYSTEM_PROMPT,
    build_user_prompt,
    detect_invented_motifs,
    write_commentary,
)
from pedagogy.types import (
    Features,
    MotifMatch,
    MoveVerdict,
    Phase,
    Verdict,
)


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _features(**over: Any) -> Features:
    defaults: dict[str, Any] = dict(
        white_men=15, white_kings=0, black_men=15, black_kings=0,
        material_balance=0,
        center_count_white=3, center_count_black=2,
        left_wing_white=2, right_wing_white=2,
        left_wing_black=2, right_wing_black=3,
        isolated_pawns_white=[], isolated_pawns_black=[],
        backward_pawns_white=[], backward_pawns_black=[],
        holes_white=[], holes_black=[],
        outposts_white=[], outposts_black=[],
        white_legal_moves=7, black_legal_moves=8,
        white_promotion_distance=5, black_promotion_distance=4,
        formations=[],
        phase=Phase.MIDDLEGAME,
    )
    defaults.update(over)
    return Features(**defaults)


def _verdict(
    *,
    motifs: Optional[list[MotifMatch]] = None,
    side: str = "white",
    move_notation: str = "32-28",
    verdict: Verdict = Verdict.GOOD,
    score_before: float = 0.5,
    score_after: float = 0.4,
    features_before: Optional[Features] = None,
    phase: Phase = Phase.MIDDLEGAME,
) -> MoveVerdict:
    return MoveVerdict(
        move_number=10,
        side=side,
        move_notation=move_notation,
        fen_before="W:Wb:Bb",
        fen_after="B:Wb:Bb",
        score_before=score_before,
        score_after=score_after,
        delta_winchance=0.05,
        verdict=verdict,
        is_forced=False,
        motifs=motifs or [],
        features_before=features_before or _features(),
        features_after=None,
        phase=phase,
    )


class FakeAsyncClient:
    """In-process stand-in for ``anthropic.AsyncAnthropic``."""

    def __init__(self, response_text: str = "Bon coup central.") -> None:
        self.response_text = response_text
        self.calls: list[dict[str, Any]] = []
        self.messages = self  # mimic ``client.messages.create(...)``

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self.response_text)])


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT — shape invariants the production prompt must keep
# ---------------------------------------------------------------------------


def test_system_prompt_lists_the_strict_constraints() -> None:
    assert "CONTRAINTES STRICTES" in SYSTEM_PROMPT
    assert "AUCUN motif tactique" in SYSTEM_PROMPT
    assert "inventer de variante" in SYSTEM_PROMPT


def test_system_prompt_asks_for_french_one_to_three_sentences() -> None:
    assert "français" in SYSTEM_PROMPT
    assert "1 à 3 phrases" in SYSTEM_PROMPT


def test_system_prompt_requires_no_preamble() -> None:
    assert "UNIQUEMENT par le commentaire" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# build_user_prompt
# ---------------------------------------------------------------------------


def test_build_user_prompt_contains_required_sections() -> None:
    prompt = build_user_prompt(_verdict())
    for header in (
        "COUP JOUÉ:", "VERDICT:", "SCORES SCAN:",
        "MOTIFS DÉTECTÉS:", "POSITION:", "EXTRAITS PÉDAGOGIQUES PERTINENTS:",
        "Rédige le commentaire.",
    ):
        assert header in prompt


def test_build_user_prompt_lists_each_motif() -> None:
    motifs = [
        MotifMatch(
            motif="coup_royal", role="played", squares=[40, 34, 24],
            pv=["40x29x18x3"], severity=0.7,
            metadata={"captures_count": 6},
        ),
        MotifMatch(
            motif="sacrifice", role="played", squares=[27],
            pv=[], severity=0.5,
            metadata={"material_loss": 1, "score_after": 0.4},
        ),
    ]
    prompt = build_user_prompt(_verdict(motifs=motifs))
    assert "coup_royal" in prompt
    assert "sacrifice" in prompt
    assert "captures_count" in prompt


def test_build_user_prompt_handles_empty_motifs_with_a_marker() -> None:
    prompt = build_user_prompt(_verdict(motifs=[]))
    assert "(aucun motif détecté)" in prompt


def test_build_user_prompt_handles_empty_excerpts() -> None:
    prompt = build_user_prompt(_verdict(), book_excerpts=[])
    assert "(aucun extrait)" in prompt


def test_build_user_prompt_renders_excerpts_with_a_marker() -> None:
    prompt = build_user_prompt(
        _verdict(),
        book_excerpts=["Le coup royal traverse le centre."],
    )
    assert "> Le coup royal traverse le centre." in prompt


def test_build_user_prompt_includes_features_when_present() -> None:
    features = _features(
        center_count_white=4, center_count_black=2,
        material_balance=+1,
        formations=["classique_blancs"],
    )
    prompt = build_user_prompt(_verdict(features_before=features))
    assert "Centre blancs/noirs: 4/2" in prompt
    assert "Matériel: +1" in prompt
    assert "classique_blancs" in prompt


def test_build_user_prompt_survives_missing_features() -> None:
    v = _verdict()
    v.features_before = None
    prompt = build_user_prompt(v)
    assert "POSITION:" in prompt
    assert "Phase:" in prompt


# ---------------------------------------------------------------------------
# detect_invented_motifs — the post-hoc anti-hallucination guard
# ---------------------------------------------------------------------------


def test_detect_invented_returns_empty_list_on_clean_text() -> None:
    text = "Un bon coup central qui améliore la mobilité du camp blanc."
    assert detect_invented_motifs(text, _verdict()) == []


def test_detect_invented_flags_motif_mentioned_without_detection() -> None:
    text = "Vous avez raté un coup royal éclatant dans cette position."
    assert detect_invented_motifs(text, _verdict()) == ["coup royal"]


def test_detect_invented_allows_motif_mentioned_when_detected() -> None:
    motifs = [MotifMatch(
        motif="coup_royal", role="missed",
        squares=[], pv=[], severity=1.0, metadata={"captures_count": 6},
    )]
    text = "Vous avez raté un coup royal éclatant."
    assert detect_invented_motifs(text, _verdict(motifs=motifs)) == []


def test_detect_invented_is_case_insensitive() -> None:
    text = "COUP ROYAL en plein milieu."
    assert detect_invented_motifs(text, _verdict()) == ["coup royal"]


def test_detect_invented_catches_motifs_with_accents() -> None:
    text = "Cette position mène à un envoi à dame inéluctable."
    assert detect_invented_motifs(text, _verdict()) == ["envoi à dame"]


def test_detect_invented_catches_multiple_invented_motifs() -> None:
    text = "Le coup turc enchaîne avec un coup de talon spectaculaire."
    invented = detect_invented_motifs(text, _verdict())
    assert set(invented) == {"coup turc", "coup de talon"}


def test_known_motifs_fr_canonical_keys_are_snake_case() -> None:
    for canonical in KNOWN_MOTIFS_FR.values():
        assert canonical.islower()
        assert " " not in canonical


# ---------------------------------------------------------------------------
# write_commentary — happy path with injected client
# ---------------------------------------------------------------------------


def test_write_commentary_returns_claude_text_when_clean() -> None:
    client = FakeAsyncClient(response_text="Bon coup, vous gardez le centre.")
    text = asyncio.run(write_commentary(_verdict(), client=client))
    assert text == "Bon coup, vous gardez le centre."


def test_write_commentary_sends_system_and_user_prompts_to_claude() -> None:
    client = FakeAsyncClient(response_text="OK.")
    asyncio.run(write_commentary(_verdict(), client=client))
    call = client.calls[-1]
    assert call["system"] == SYSTEM_PROMPT
    assert call["model"] == DEFAULT_MODEL
    assert call["max_tokens"] == DEFAULT_MAX_TOKENS
    assert call["messages"][0]["role"] == "user"
    assert "COUP JOUÉ:" in call["messages"][0]["content"]


def test_write_commentary_falls_back_when_response_invents_a_motif() -> None:
    client = FakeAsyncClient(
        response_text="Vous avez raté un coup royal magistral !",
    )
    fallback_text = "Coup correct, sans plus."
    text = asyncio.run(write_commentary(
        _verdict(),  # no detected motifs
        client=client,
        fallback=lambda _v: fallback_text,
    ))
    assert text == fallback_text


def test_write_commentary_falls_back_on_empty_response() -> None:
    client = FakeAsyncClient(response_text="")
    text = asyncio.run(write_commentary(
        _verdict(),
        client=client,
        fallback=lambda _v: "fallback OK",
    ))
    assert text == "fallback OK"


def test_write_commentary_returns_empty_string_when_no_fallback_provided() -> None:
    client = FakeAsyncClient(response_text="Vous avez raté un coup royal éclatant.")
    text = asyncio.run(write_commentary(_verdict(), client=client, fallback=None))
    assert text == ""


def test_write_commentary_keeps_text_when_motif_mentioned_was_detected() -> None:
    motifs = [MotifMatch(
        motif="coup_royal", role="missed",
        squares=[], pv=[], severity=1.0, metadata={"captures_count": 6},
    )]
    client = FakeAsyncClient(response_text="Vous avez raté un coup royal éclatant.")
    text = asyncio.run(write_commentary(
        _verdict(motifs=motifs),
        client=client,
        fallback=lambda _v: "should not fire",
    ))
    assert "coup royal" in text.lower()
