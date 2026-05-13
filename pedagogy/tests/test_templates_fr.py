"""Tests for the French templates (spec §7, PR 6).

Coverage targets the spec's acceptance criterion: every ``(motif, role)``
combination our P1 detectors can emit must resolve via the registry, and
every :class:`Verdict` must have a fallback.
"""

from __future__ import annotations

import pytest

from pedagogy.explanations.templates_fr import (
    TEMPLATES_FR,
    VERDICT_FALLBACKS_FR,
    render_template,
    render_verdict_fallback,
)
from pedagogy.motifs import ALL_DETECTORS
from pedagogy.types import MotifMatch, Verdict


# ---------------------------------------------------------------------------
# Resolution priority
# ---------------------------------------------------------------------------


def _coup_royal_match(*, role: str = "played", captures: int = 7) -> MotifMatch:
    return MotifMatch(
        motif="coup_royal",
        role=role,
        squares=[40, 34, 24, 14, 3],
        pv=["40x29x18x12x3"],
        severity=0.7,
        metadata={"captures_count": captures},
    )


def test_render_template_uses_specific_triple_when_available() -> None:
    text = render_template(_coup_royal_match(), Verdict.BRILLIANT)
    assert text is not None
    assert "Magnifique coup royal" in text


def test_render_template_falls_back_to_motif_role_generic() -> None:
    # Verdict.GOOD has no specific (coup_royal, played, GOOD) entry, so we
    # must land in the (coup_royal, played, None) generic row.
    text = render_template(_coup_royal_match(), Verdict.GOOD)
    assert text is not None
    assert text.startswith("Coup royal —")


def test_render_template_returns_none_when_no_match() -> None:
    # An unknown motif name has no entry at any level.
    bogus = MotifMatch(motif="not_a_motif", role="played", squares=[], pv=[], severity=0.0)
    assert render_template(bogus, Verdict.BLUNDER) is None


def test_render_template_returns_none_for_unmapped_role() -> None:
    # "suffered" is in the spec but not produced by any P1 detector and
    # therefore not registered — we expect None.
    suffered = MotifMatch(
        motif="coup_royal", role="suffered", squares=[], pv=[], severity=0.5,
        metadata={"captures_count": 6},
    )
    assert render_template(suffered, Verdict.BLUNDER) is None


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------


def test_render_template_substitutes_metadata_keys() -> None:
    text = render_template(_coup_royal_match(captures=9), Verdict.BRILLIANT)
    assert text is not None
    assert "9 prises" in text


def test_render_template_joins_pv_when_referenced() -> None:
    match = MotifMatch(
        motif="coup_royal", role="missed",
        squares=[40, 34, 24, 14, 3],
        pv=["40x29", "29x18", "18x3"],
        severity=1.0,
        metadata={"captures_count": 6},
    )
    text = render_template(match, Verdict.BLUNDER)
    assert text is not None
    assert "40x29 29x18 18x3" in text


def test_render_template_handles_empty_pv_gracefully() -> None:
    match = _coup_royal_match(role="missed")
    match.pv.clear()
    text = render_template(match, Verdict.BLUNDER)
    assert text is not None
    # Empty PV substituted; template format must not blow up.
    assert "{pv}" not in text


def test_render_template_ctx_overrides_metadata_keys() -> None:
    # captures_count is in metadata; ctx.captures_count must win.
    text = render_template(
        _coup_royal_match(captures=6),
        Verdict.BRILLIANT,
        ctx={"captures_count": 99},
    )
    assert text is not None
    assert "99 prises" in text
    assert "6 prises" not in text


def test_render_template_works_without_ctx() -> None:
    text = render_template(_coup_royal_match(), Verdict.BEST)
    assert text is not None
    assert "Coup royal joué proprement" in text


# ---------------------------------------------------------------------------
# Per-motif smoke (every motif we ship has a played-generic entry)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "motif_name,metadata",
    [
        ("coup_royal", {"captures_count": 6}),
        ("coup_turc", {"captures_count": 4, "path_length": 5}),
        ("coup_de_talon", {"captures_count": 3, "path_length": 4}),
        ("envoi_a_dame", {"material_loss": 1, "promotion_square": 3, "score_after": 0.4}),
        ("sacrifice", {"material_loss": 2, "score_after": 0.2}),
        ("prise_max_ratee", {"captures_played": 1, "captures_possible": 3}),
    ],
)
def test_every_p1_motif_has_played_generic(motif_name: str, metadata: dict) -> None:
    match = MotifMatch(
        motif=motif_name, role="played",
        squares=[], pv=[], severity=0.5, metadata=metadata,
    )
    # GOOD has no specific (motif, played, GOOD) entry for any of these,
    # so the generic (motif, played, None) row catches it.
    text = render_template(match, Verdict.GOOD)
    assert text is not None, f"{motif_name} is missing a (played, None) generic"
    assert text.strip()


def test_coup_royal_is_the_only_missed_motif_for_now() -> None:
    """The current P1 set only emits ``missed`` for coup_royal.

    If another detector starts emitting ``missed`` later (PR 14 motifs P2),
    add a (motif, "missed", None) generic to keep this invariant true.
    """
    missed_keys = {
        (motif, role) for (motif, role, _) in TEMPLATES_FR if role == "missed"
    }
    assert missed_keys == {("coup_royal", "missed")}


def test_motif_registry_matches_template_coverage() -> None:
    """Every detector currently in ALL_DETECTORS has at least one template."""
    motif_names_in_registry = {cls().name for cls in ALL_DETECTORS}
    motif_names_in_templates = {motif for (motif, _, _) in TEMPLATES_FR}
    missing = motif_names_in_registry - motif_names_in_templates
    assert not missing, f"detectors without any template: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Verdict fallbacks
# ---------------------------------------------------------------------------


def test_render_verdict_fallback_covers_every_verdict() -> None:
    for v in Verdict:
        text = render_verdict_fallback(v)
        assert text and isinstance(text, str)


def test_verdict_fallback_dict_keys_match_enum() -> None:
    assert set(VERDICT_FALLBACKS_FR.keys()) == set(Verdict)


def test_verdict_fallback_strings_are_non_empty() -> None:
    assert all(v.strip() for v in VERDICT_FALLBACKS_FR.values())
