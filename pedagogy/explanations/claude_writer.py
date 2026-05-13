"""Claude commentary writer with anti-hallucination guard (spec §7 / PR 10).

The function :func:`write_commentary` calls Claude to produce one to three
sentences of French commentary on a :class:`MoveVerdict`. The model is given
a **closed list** of motifs (the ones our deterministic detectors flagged)
and the system prompt explicitly forbids it from mentioning any other
tactical motif. We verify this post-hoc by scanning the response for
known French motif names and falling back to the template renderer when a
violation is detected (spec §14.7 — zero-tolerance hallucination policy).

The Anthropic SDK is imported lazily so that importing this module on a
process that never calls Claude doesn't pay the dependency cost.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

from ..types import Features, MotifMatch, MoveVerdict
from .book_rag import BookExcerpt, BookRAG

#: System prompt sent to Claude. The constraints block mirrors spec §7
#: line-for-line and is the contract that ``detect_invented_motifs``
#: enforces post-hoc.
SYSTEM_PROMPT = """Tu es un commentateur pédagogique pour le jeu de dames international.

Tu reçois pour un coup donné :
1. La notation du coup joué (ex: "32-28")
2. Le verdict ("blunder", "mistake", "brilliant", etc.)
3. Une LISTE FERMÉE de motifs détectés par un système déterministe
4. Des features positionnelles (centre, formations, etc.)
5. Optionnellement, des extraits de livres pédagogiques

Tu dois rédiger un commentaire en français de 1 à 3 phrases, au ton bienveillant.

CONTRAINTES STRICTES :
- Tu ne dois mentionner AUCUN motif tactique qui n'est pas dans la liste fournie.
- Tu ne dois pas inventer de variante (séquence de coups). Si tu cites une variante, \
tu ne peux le faire qu'en recopiant exactement la PV fournie.
- Tu ne dois pas évaluer la position avec un score différent de celui fourni par Scan.
- Tu ne dois pas faire de prédiction sur ce que jouera l'adversaire après.
- Si la liste de motifs est vide, contente-toi de commenter le verdict en termes \
généraux (centre, mobilité) sans nommer de motif tactique.

Tu réponds UNIQUEMENT par le commentaire, sans préambule ni signature."""

#: Default Claude model used when the caller doesn't override it. The
#: spec calls for ``claude-opus-4-7``; older or newer aliases are
#: handled by the caller passing ``model=...``.
DEFAULT_MODEL = "claude-opus-4-7"

#: Maximum tokens of output we ask Claude to produce. 300 is comfortable
#: for the 1-3 sentences the prompt requests.
DEFAULT_MAX_TOKENS = 300

#: French motif names the verifier looks for. Each maps to the canonical
#: snake-case form stored in :attr:`MotifMatch.motif`. Mentioning any of
#: these in the response is allowed only when the matching canonical key
#: is present in ``verdict.motifs``.
KNOWN_MOTIFS_FR: dict[str, str] = {
    "coup royal": "coup_royal",
    "coup turc": "coup_turc",
    "coup de talon": "coup_de_talon",
    "envoi à dame": "envoi_a_dame",
    "coup philippe": "coup_philippe",
    "coup raphaël": "coup_raphael",
    "coup de l'express": "coup_de_l_express",
    "coup bonnard": "coup_bonnard",
    "sacrifice": "sacrifice",
    "enchaînement": "enchainement",
    "percée": "percee",
    "opposition": "opposition",
    "prise maximale": "prise_max_ratee",
}


def _format_motif(m: MotifMatch) -> str:
    return (
        f"- {m.motif} ({m.role}) — sévérité {m.severity:.2f} "
        f"— métadonnées {m.metadata}"
    )


def _format_features(features: Optional[Features], phase: object) -> str:
    if features is None:
        return f"Phase: {phase}"
    return (
        f"Centre blancs/noirs: {features.center_count_white}"
        f"/{features.center_count_black}, "
        f"Matériel: {features.material_balance:+d}, "
        f"Formations: {', '.join(features.formations) or 'aucune'}, "
        f"Phase: {phase}"
    )


def build_user_prompt(
    verdict: MoveVerdict,
    book_excerpts: Optional[Sequence[str]] = None,
) -> str:
    """Compose the structured user prompt for ``write_commentary``."""
    motifs_block = (
        "\n".join(_format_motif(m) for m in verdict.motifs)
        if verdict.motifs
        else "(aucun motif détecté)"
    )
    features_block = _format_features(verdict.features_before, verdict.phase)
    excerpts = list(book_excerpts or [])
    excerpts_block = (
        "\n".join(f"> {e}" for e in excerpts) if excerpts else "(aucun extrait)"
    )
    return (
        f"COUP JOUÉ: {verdict.move_notation} ({verdict.side})\n"
        f"VERDICT: {verdict.verdict.value}\n"
        f"SCORES SCAN: {verdict.score_before:+.2f} -> {verdict.score_after:+.2f}\n\n"
        f"MOTIFS DÉTECTÉS:\n{motifs_block}\n\n"
        f"POSITION:\n{features_block}\n\n"
        f"EXTRAITS PÉDAGOGIQUES PERTINENTS:\n{excerpts_block}\n\n"
        "Rédige le commentaire."
    )


def detect_invented_motifs(text: str, verdict: MoveVerdict) -> list[str]:
    """Return the French motif names mentioned in ``text`` but absent from the verdict.

    Returns an empty list when the response is clean. Caller is expected
    to fall back to the template renderer when this list is non-empty
    (spec §14.7).
    """
    detected = {m.motif for m in verdict.motifs}
    lower = text.lower()
    invented: list[str] = []
    for fr_name, canonical in KNOWN_MOTIFS_FR.items():
        if fr_name in lower and canonical not in detected:
            invented.append(fr_name)
    return invented


def _gather_book_excerpts(
    verdict: MoveVerdict, book_rag: Optional[BookRAG]
) -> list[str]:
    if book_rag is None or not verdict.motifs:
        return []
    out: list[str] = []
    for motif in verdict.motifs:
        try:
            hits: Iterable[BookExcerpt] = book_rag.search(motif.motif, max_results=1)
        except Exception:  # noqa: BLE001 — the book layer must never break commentary
            continue
        for hit in hits:
            out.append(hit.excerpt)
    return out


async def _call_claude(
    verdict: MoveVerdict,
    book_excerpts: Sequence[str],
    model: str,
    max_tokens: int,
    client: Any,
) -> str:
    if client is None:
        import anthropic

        client = anthropic.AsyncAnthropic()
    user_prompt = build_user_prompt(verdict, book_excerpts)
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    blocks = getattr(response, "content", None) or []
    for block in blocks:
        text = getattr(block, "text", None)
        if text:
            return str(text).strip()
    return ""


async def write_commentary(
    verdict: MoveVerdict,
    book_rag: Optional[BookRAG] = None,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    client: Any = None,
    fallback: Any = None,
) -> str:
    """Generate Claude commentary with an anti-hallucination fallback.

    ``client`` lets the caller (typically tests) inject an
    :class:`anthropic.AsyncAnthropic`-shaped object. When ``None``, the
    real SDK is lazy-imported and instantiated.

    ``fallback`` is the function called when Claude's reply mentions a
    non-detected motif (or when it comes back empty). It must accept a
    :class:`MoveVerdict` and return ``str``. The caller is expected to
    pass the pipeline's template renderer here; we accept it as a
    parameter to keep this module decoupled from the pipeline.
    """
    excerpts = _gather_book_excerpts(verdict, book_rag)
    text = await _call_claude(verdict, excerpts, model, max_tokens, client)
    if not text or detect_invented_motifs(text, verdict):
        if fallback is None:
            return ""
        result = fallback(verdict)
        return str(result) if result is not None else ""
    return text
