"""English templates for the explanations layer (spec §7, PR 12).

Mirror of :mod:`pedagogy.explanations.templates_fr`. The keys match the
French registry one-for-one so callers can switch language without
changing motif coverage. The dispatch function lives in
:mod:`pedagogy.explanations.templates_fr`'s ``render_template`` — pass
``lang="en"`` and it reads this dict instead of ``TEMPLATES_FR``.
"""

from __future__ import annotations

from typing import Optional

from ..types import Verdict

#: Per-motif/role/verdict English templates. Same key shape as TEMPLATES_FR.
TEMPLATES_EN: dict[tuple[str, str, Optional[Verdict]], str] = {
    # ===================================================================
    # coup_royal — royal coup (long rafle through the centre)
    # ===================================================================
    ("coup_royal", "played", Verdict.BRILLIANT): (
        "Beautiful royal coup! You ran a {captures_count}-piece rafle through "
        "the centre — the textbook way to punish an opponent who has piled "
        "up on the central squares."
    ),
    ("coup_royal", "played", Verdict.BEST): (
        "Clean royal coup: {captures_count} captures on the central axis. "
        "This rafle sets up by drawing your opponent into overloading the "
        "centre."
    ),
    ("coup_royal", "played", None): (
        "Royal coup — {captures_count}-piece rafle through the centre."
    ),
    ("coup_royal", "missed", Verdict.BLUNDER): (
        "Missed a royal coup: the sequence {pv} would have captured "
        "{captures_count} pieces and likely won the game. Whenever your "
        "opponent stacks up the centre, scan for the long rafle through "
        "the great diagonal."
    ),
    ("coup_royal", "missed", Verdict.MISTAKE): (
        "A royal coup was on the board ({pv}, {captures_count} captures). "
        "Worth looking for any time the central configuration invites a "
        "long rafle."
    ),
    ("coup_royal", "missed", None): (
        "A royal coup was available: {pv}."
    ),

    # ===================================================================
    # coup_turc — turkish stroke (trajectory revisits a square)
    # ===================================================================
    ("coup_turc", "played", Verdict.BRILLIANT): (
        "Nice turkish stroke! Your {captures_count}-capture rafle passed "
        "through the same square twice ({path_length} steps total) — a "
        "pattern few players see coming."
    ),
    ("coup_turc", "played", None): (
        "Turkish stroke — the {captures_count}-capture rafle's trajectory "
        "revisits an intermediate square."
    ),

    # ===================================================================
    # coup_de_talon — heel stroke (rafle reverses direction)
    # ===================================================================
    ("coup_de_talon", "played", Verdict.BRILLIANT): (
        "Elegant heel stroke: your {captures_count}-capture rafle reverses "
        "direction mid-way, catching the opponent on the wrong foot."
    ),
    ("coup_de_talon", "played", None): (
        "Heel stroke — the {captures_count}-capture rafle reverses direction "
        "in flight."
    ),

    # ===================================================================
    # envoi_a_dame — promotion sacrifice
    # ===================================================================
    ("envoi_a_dame", "played", Verdict.BRILLIANT): (
        "Beautiful promotion sacrifice! You give up {material_loss} man/men "
        "to force promotion on {promotion_square}, and Scan still rates your "
        "position at {score_after:+.1f}."
    ),
    ("envoi_a_dame", "played", None): (
        "Promotion sacrifice — {material_loss} man/men given up to force "
        "promotion on {promotion_square}."
    ),

    # ===================================================================
    # sacrifice — tactical sacrifice that doesn't lose evaluation
    # ===================================================================
    ("sacrifice", "played", Verdict.BRILLIANT): (
        "Strong sacrifice! You give up {material_loss} man/men, but Scan "
        "still rates the position at {score_after:+.1f}. Exactly the kind "
        "of material investment that calculation pays for."
    ),
    ("sacrifice", "played", Verdict.BEST): (
        "Justified sacrifice: {material_loss} man/men conceded to keep the "
        "evaluation at {score_after:+.1f}."
    ),
    ("sacrifice", "played", None): (
        "Sacrifice of {material_loss} man/men — evaluation after: "
        "{score_after:+.1f}."
    ),

    # ===================================================================
    # prise_max_ratee — maximum capture rule violated
    # ===================================================================
    ("prise_max_ratee", "played", Verdict.MISTAKE): (
        "Careful: you played a {captures_played}-piece capture, but a "
        "{captures_possible}-piece capture was available. In FMJD, the "
        "maximum capture rule is mandatory."
    ),
    ("prise_max_ratee", "played", Verdict.BLUNDER): (
        "Rules error: you took {captures_played} piece(s) when "
        "{captures_possible} were obligatory. In international draughts, "
        "the longest capture sequence has priority."
    ),
    ("prise_max_ratee", "played", None): (
        "Non-maximum capture: {captures_played} played, "
        "{captures_possible} available."
    ),

    # ===================================================================
    # coup_philippe — wing-anchored rafle (P2)
    # ===================================================================
    ("coup_philippe", "played", Verdict.BRILLIANT): (
        "Nice Philippe stroke! Your {captures_count}-capture rafle starts "
        "on the wing ({first_capture}): the piece your opponent sacrificed "
        "opened the trajectory."
    ),
    ("coup_philippe", "played", None): (
        "Philippe stroke — {captures_count}-capture rafle launched from the "
        "wing (square {first_capture})."
    ),
    ("coup_philippe", "missed", None): (
        "A Philippe stroke was possible: {pv}, starting on the wing at "
        "{first_capture}."
    ),

    # ===================================================================
    # coup_raphael — specific 28x6 / 23x5 pattern (P2)
    # ===================================================================
    ("coup_raphael", "played", Verdict.BRILLIANT): (
        "Beautiful Raphaël stroke! Your {start_square}x{land_square} rafle "
        "sweeps {captures_count} pieces along the back diagonal — a named "
        "pattern from the Raphaël tradition."
    ),
    ("coup_raphael", "played", None): (
        "Raphaël stroke — {start_square}x{land_square} rafle "
        "({captures_count} captures) on the {side} side."
    ),
    ("coup_raphael", "missed", None): (
        "A Raphaël stroke was available: {pv}."
    ),

    # ===================================================================
    # coup_express — straight-line long rafle (P2)
    # ===================================================================
    ("coup_express", "played", Verdict.BRILLIANT): (
        "Express stroke! A straight rafle of {captures_count} pieces — no "
        "direction change — your opponent never saw it coming."
    ),
    ("coup_express", "played", None): (
        "Express stroke — straight-line rafle of {captures_count} captures."
    ),
    ("coup_express", "missed", None): (
        "A straight-line express stroke was available: {pv} "
        "({captures_count} captures)."
    ),

    # ===================================================================
    # coup_bonnard — sacrifice forcing opponent promotion, then king
    # captured (P2)
    # ===================================================================
    ("coup_bonnard", "played", Verdict.BRILLIANT): (
        "Beautiful Bonnard stroke: your sacrifice forces the opponent to "
        "promote, and the new king falls on the next move. Three-ply "
        "calculation, no margin for error."
    ),
    ("coup_bonnard", "played", None): (
        "Bonnard stroke — sacrifice forcing an opponent promotion that is "
        "immediately captured."
    ),
    ("coup_bonnard", "missed", None): (
        "A Bonnard stroke was possible: {pv}."
    ),

    # ===================================================================
    # coup_napoleon — sacrifice + opponent deflection + promotion (P3)
    # ===================================================================
    ("coup_napoleon", "played", Verdict.BRILLIANT): (
        "Beautiful Napoléon stroke! Your sacrifice forces the opponent to "
        "capture, clearing the diagonal, and you queen via {pv}."
    ),
    ("coup_napoleon", "played", None): (
        "Napoléon stroke — deflection sacrifice followed by a promotion "
        "on square {promotion_square}."
    ),
    ("coup_napoleon", "missed", None): (
        "A Napoléon stroke was available: {pv} (promotion on "
        "{promotion_square})."
    ),

    # ===================================================================
    # coup_manoury — sacrifice setting up a 4+ capture rafle (P3)
    # ===================================================================
    ("coup_manoury", "played", Verdict.BRILLIANT): (
        "Beautiful Manoury stroke: your sacrifice sets up the long rafle "
        "of {followup_captures} captures ({followup_notation}). The "
        "textbook profitable combination."
    ),
    ("coup_manoury", "played", None): (
        "Manoury stroke — sacrifice leading to a rafle of "
        "{followup_captures} captures."
    ),
    ("coup_manoury", "missed", None): (
        "A Manoury stroke was possible: {pv} (final rafle of "
        "{followup_captures} captures)."
    ),

    # ===================================================================
    # coup_enfilade — straight-line rafle, 3 or 4 captures (P3)
    # ===================================================================
    ("coup_enfilade", "played", Verdict.BRILLIANT): (
        "Nice enfilade! Your {captures_count}-capture rafle takes three "
        "or four men aligned on a single diagonal."
    ),
    ("coup_enfilade", "played", None): (
        "Enfilade — straight-line rafle of {captures_count} captures."
    ),
    ("coup_enfilade", "missed", None): (
        "An enfilade was possible: {pv} ({captures_count} captures)."
    ),

    # ===================================================================
    # coup_du_bruleur — quiet move that locks 2+ opponent men (P3)
    # ===================================================================
    ("coup_du_bruleur", "played", Verdict.BRILLIANT): (
        "Burner stroke: your quiet push locks {burned_count} opponent men "
        "that can no longer advance without external help."
    ),
    ("coup_du_bruleur", "played", None): (
        "Burner stroke — {burned_count} opponent men now blocked on both "
        "forward diagonals."
    ),

    # ===================================================================
    # combinaison_N_temps — generic forcing combinations (unnamed)
    # ===================================================================
    ("combinaison_2_temps", "played", None): (
        "Two-move combination: forced chain that nets you "
        "{material_gain} pawn(s)."
    ),
    ("combinaison_2_temps", "missed", None): (
        "You missed a two-move combination worth {material_gain} pawn(s)."
    ),
    ("combinaison_3_temps", "played", None): (
        "Three-move combination: forced chain that nets you "
        "{material_gain} pawn(s)."
    ),
    ("combinaison_3_temps", "missed", None): (
        "You missed a three-move combination worth {material_gain} pawn(s)."
    ),
    ("combinaison_4_temps", "played", None): (
        "Four-move combination: forced chain that nets you "
        "{material_gain} pawn(s) — nice calculation."
    ),
    ("combinaison_4_temps", "missed", None): (
        "You missed a four-move combination worth {material_gain} pawn(s)."
    ),
    ("combinaison_5_temps", "played", None): (
        "Combination in {depth_temps} moves: forced chain that nets you "
        "{material_gain} pawn(s) — outstanding calculation."
    ),
    ("combinaison_5_temps", "missed", None): (
        "You missed a {depth_temps}-move combination worth "
        "{material_gain} pawn(s)."
    ),
}

#: Generic verdict commentary used when no motif template matched. Always
#: defined for every :class:`Verdict` value.
VERDICT_FALLBACKS_EN: dict[Verdict, str] = {
    Verdict.BRILLIANT: (
        "Brilliant move — a correct sacrifice that costs no evaluation."
    ),
    Verdict.BEST: "Best move according to the engine.",
    Verdict.EXCELLENT: "Excellent move, very close to best.",
    Verdict.GOOD: "Good move that keeps the essentials of your position.",
    Verdict.INACCURACY: (
        "Inaccuracy: you give up a bit of evaluation, nothing dramatic."
    ),
    Verdict.MISTAKE: (
        "Mistake: this move significantly degrades the position."
    ),
    Verdict.BLUNDER: (
        "Blunder: this move swings the evaluation against you."
    ),
    Verdict.FORCED: "Forced move — there was no legal alternative.",
    Verdict.BOOK: "Opening book move from theory.",
}
