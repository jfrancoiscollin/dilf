"""French templates for the explanations layer (spec §7).

Each entry of :data:`TEMPLATES_FR` is keyed by ``(motif, role, verdict | None)``.
The renderer first tries the specific triple, then falls back to
``(motif, role, None)`` — a documented per-motif/role generic. When neither
is registered, :func:`render_template` returns ``None`` and the caller is
expected to substitute :data:`VERDICT_FALLBACKS_FR` to keep the explanation
non-empty.

Placeholders available inside a template string:

* every key of the matched :attr:`MotifMatch.metadata` dict;
* ``pv`` — the motif's principal variation, joined into a single string;
* anything the caller passes via the ``ctx`` argument (it wins over the
  metadata keys on collision).
"""

from __future__ import annotations

from typing import Mapping, Optional

from ..types import MotifMatch, Verdict

#: Per-motif/role/verdict template registry. Verdicts deliberately not
#: enumerated for every band — the generic ``(motif, role, None)`` row
#: catches the rest.
TEMPLATES_FR: dict[tuple[str, str, Optional[Verdict]], str] = {
    # ===================================================================
    # coup_royal — rafle longue passant par le centre / la grande diagonale
    # ===================================================================
    ("coup_royal", "played", Verdict.BRILLIANT): (
        "Magnifique coup royal ! Vous avez exécuté une rafle de "
        "{captures_count} prises au centre, le mécanisme classique qui "
        "exploite un adversaire ayant empilé ses pions sur les cases "
        "centrales."
    ),
    ("coup_royal", "played", Verdict.BEST): (
        "Coup royal joué proprement : {captures_count} prises sur l'axe "
        "central. C'est une rafle qui se prépare en amenant l'adversaire "
        "à surcharger le centre."
    ),
    ("coup_royal", "played", None): (
        "Coup royal — rafle de {captures_count} prises traversant le centre."
    ),
    ("coup_royal", "missed", Verdict.BLUNDER): (
        "Coup royal manqué : la séquence {pv} capturait {captures_count} "
        "pièces et changeait probablement le sort de la partie. Quand "
        "votre adversaire empile au centre, cherchez systématiquement la "
        "rafle qui passe par la grande diagonale."
    ),
    ("coup_royal", "missed", Verdict.MISTAKE): (
        "Vous aviez un coup royal disponible ({pv}, {captures_count} prises). "
        "À chercher dès que la configuration centrale se prête à une rafle "
        "longue."
    ),
    ("coup_royal", "missed", None): (
        "Un coup royal était possible : {pv}."
    ),

    # ===================================================================
    # coup_turc — la trajectoire repasse par une même case
    # ===================================================================
    ("coup_turc", "played", Verdict.BRILLIANT): (
        "Très joli coup turc ! Votre rafle de {captures_count} prises est "
        "passée deux fois par la même case ({path_length} étapes au total) "
        "— un schéma que peu de joueurs voient à l'avance."
    ),
    ("coup_turc", "played", None): (
        "Coup turc — la trajectoire de la rafle ({captures_count} prises) "
        "repasse par une case intermédiaire."
    ),

    # ===================================================================
    # coup_de_talon — la rafle inverse sa direction en cours de route
    # ===================================================================
    ("coup_de_talon", "played", Verdict.BRILLIANT): (
        "Coup de talon élégant : votre rafle ({captures_count} prises) "
        "inverse sa direction au milieu du parcours, ce qui prend "
        "l'adversaire à contre-pied."
    ),
    ("coup_de_talon", "played", None): (
        "Coup de talon — la rafle ({captures_count} prises) renverse sa "
        "direction en cours de route."
    ),

    # ===================================================================
    # envoi_a_dame — sacrifice qui force une promotion
    # ===================================================================
    ("envoi_a_dame", "played", Verdict.BRILLIANT): (
        "Bel envoi à dame ! Vous sacrifiez {material_loss} pion(s) pour "
        "forcer la promotion en {promotion_square} et Scan évalue toujours "
        "votre position à {score_after:+.1f}."
    ),
    ("envoi_a_dame", "played", None): (
        "Envoi à dame — sacrifice de {material_loss} pion(s) menant à une "
        "promotion forcée en {promotion_square}."
    ),

    # ===================================================================
    # sacrifice — sacrifice tactique sans perte d'évaluation
    # ===================================================================
    ("sacrifice", "played", Verdict.BRILLIANT): (
        "Beau sacrifice ! Vous offrez {material_loss} pion(s), mais Scan "
        "évalue toujours la position à {score_after:+.1f}. C'est exactement "
        "le genre d'investissement matériel que paie le calcul."
    ),
    ("sacrifice", "played", Verdict.BEST): (
        "Sacrifice justifié : {material_loss} pion(s) cédé(s) pour conserver "
        "une évaluation de {score_after:+.1f}."
    ),
    ("sacrifice", "played", None): (
        "Sacrifice de {material_loss} pion(s) — évaluation après : "
        "{score_after:+.1f}."
    ),

    # ===================================================================
    # prise_max_ratee — la règle de prise maximale a été violée
    # ===================================================================
    ("prise_max_ratee", "played", Verdict.MISTAKE): (
        "Attention : vous avez joué une prise de {captures_played} pion(s), "
        "mais une prise de {captures_possible} était disponible. En FMJD, "
        "la règle de prise maximale est obligatoire."
    ),
    ("prise_max_ratee", "played", Verdict.BLUNDER): (
        "Erreur de règle : vous avez pris {captures_played} pièce(s) alors "
        "que {captures_possible} étaient obligatoires. En jeu de dames "
        "international, la séquence la plus longue prime."
    ),
    ("prise_max_ratee", "played", None): (
        "Prise non maximale : {captures_played} prises jouées, "
        "{captures_possible} possibles."
    ),

    # ===================================================================
    # coup_philippe — rafle exploitant un sacrifice sur l'aile (P2)
    # ===================================================================
    ("coup_philippe", "played", Verdict.BRILLIANT): (
        "Joli coup Philippe ! Votre rafle de {captures_count} prises démarre "
        "sur l'aile en {first_capture} : la pièce sacrifiée par l'adversaire "
        "vous a ouvert la trajectoire."
    ),
    ("coup_philippe", "played", None): (
        "Coup Philippe — rafle de {captures_count} prises lancée sur l'aile "
        "(case {first_capture})."
    ),
    ("coup_philippe", "missed", None): (
        "Un coup Philippe était possible : {pv}, démarrant sur l'aile en "
        "{first_capture}."
    ),

    # ===================================================================
    # coup_raphael — rafle spécifique 28x6 / 23x5 (ou son miroir) (P2)
    # ===================================================================
    ("coup_raphael", "played", Verdict.BRILLIANT): (
        "Magnifique coup Raphaël ! Votre rafle {start_square}x{land_square} "
        "ramasse {captures_count} pièces sur la diagonale du fond — un "
        "schéma nommé d'après son auteur."
    ),
    ("coup_raphael", "played", None): (
        "Coup Raphaël — rafle {start_square}x{land_square} ({captures_count} "
        "prises) côté {side}."
    ),
    ("coup_raphael", "missed", None): (
        "Un coup Raphaël était disponible : {pv}."
    ),

    # ===================================================================
    # coup_express — rafle longue (5+) en ligne droite (P2)
    # ===================================================================
    ("coup_express", "played", Verdict.BRILLIANT): (
        "Coup de l'express ! Une rafle rectiligne de {captures_count} pions, "
        "sans changer de diagonale — l'adversaire n'a rien vu venir."
    ),
    ("coup_express", "played", None): (
        "Coup de l'express — rafle rectiligne de {captures_count} prises."
    ),
    ("coup_express", "missed", None): (
        "Un coup de l'express en ligne droite était disponible : {pv} "
        "({captures_count} prises)."
    ),

    # ===================================================================
    # coup_bonnard — sacrifice qui force la promotion adverse puis la
    # dame est capturée (P2)
    # ===================================================================
    ("coup_bonnard", "played", Verdict.BRILLIANT): (
        "Beau coup Bonnard : votre sacrifice force la promotion adverse, "
        "et la nouvelle dame tombe au coup suivant. Le calcul à trois "
        "demi-coups est sec."
    ),
    ("coup_bonnard", "played", None): (
        "Coup Bonnard — sacrifice forçant une promotion adverse aussitôt "
        "rattrapée."
    ),
    ("coup_bonnard", "missed", None): (
        "Un coup Bonnard était possible : {pv}."
    ),
}

#: Generic verdict commentary used when no motif template matched. Always
#: defined for every :class:`Verdict` value — :func:`render_verdict_fallback`
#: never raises.
VERDICT_FALLBACKS_FR: dict[Verdict, str] = {
    Verdict.BRILLIANT: (
        "Coup brillant — sacrifice juste qui ne perd rien à l'évaluation."
    ),
    Verdict.BEST: "Meilleur coup selon l'évaluation moteur.",
    Verdict.EXCELLENT: "Coup excellent, très proche du meilleur.",
    Verdict.GOOD: "Bon coup, qui conserve l'essentiel de votre position.",
    Verdict.INACCURACY: (
        "Imprécision : vous concédez un peu d'évaluation, sans drame."
    ),
    Verdict.MISTAKE: (
        "Erreur : votre coup dégrade significativement la position."
    ),
    Verdict.BLUNDER: (
        "Gaffe : ce coup fait basculer l'évaluation contre vous."
    ),
    Verdict.FORCED: "Coup forcé — il n'y avait pas d'alternative légale.",
    Verdict.BOOK: "Coup d'ouverture issu du répertoire théorique.",
}


def render_template(
    motif: MotifMatch,
    verdict: Verdict,
    ctx: Optional[Mapping[str, object]] = None,
) -> Optional[str]:
    """Render the French commentary for a (motif, verdict), or return None.

    Resolution order:

    1. ``(motif.motif, motif.role, verdict)`` — fully specific.
    2. ``(motif.motif, motif.role, None)`` — motif/role generic.
    3. ``None`` — caller falls back to :func:`render_verdict_fallback`.
    """
    key_specific = (motif.motif, motif.role, verdict)
    key_generic: tuple[str, str, Optional[Verdict]] = (motif.motif, motif.role, None)
    template = TEMPLATES_FR.get(key_specific) or TEMPLATES_FR.get(key_generic)
    if template is None:
        return None
    merged: dict[str, object] = dict(motif.metadata)
    merged["pv"] = " ".join(motif.pv) if motif.pv else ""
    if ctx:
        merged.update(ctx)
    return template.format(**merged)


def render_verdict_fallback(verdict: Verdict) -> str:
    """Return the generic French phrase for ``verdict``. Never raises."""
    return VERDICT_FALLBACKS_FR[verdict]
