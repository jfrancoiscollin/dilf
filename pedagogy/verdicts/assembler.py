"""Compose features + motifs + classifier into a complete :class:`MoveVerdict`.

The assembler is the only place in :mod:`pedagogy.verdicts` that touches the
features layer and the motif registry — the classifier itself stays a pure
score-to-verdict function. ``assemble_verdict`` mirrors the pseudo-code in
spec §6 line-for-line.
"""

from __future__ import annotations

from typing import Optional

from ..features.formations import compute_features, determine_phase
from ..game import GameState, Move, notation, state_to_fen
from ..motifs import detect_all, detect_all_missed
from ..protocols import EngineProtocol
from ..types import MoveVerdict, Verdict
from .classifier import classify_move, win_chance


def _signed_delta(score_before: float, score_after: float, side: str) -> float:
    """Win-chance loss for the moving side. Positive => the move hurt."""
    sign = 1.0 if side == "white" else -1.0
    return sign * win_chance(score_before) - sign * win_chance(score_after)


def assemble_verdict(
    state_before: GameState,
    move: Move,
    state_after: GameState,
    *,
    score_before: float,
    score_after: float,
    best_move: Optional[Move] = None,
    best_pv: Optional[list[str]] = None,
    half_move_number: int,
    is_book: bool = False,
    engine: Optional[EngineProtocol] = None,
) -> MoveVerdict:
    """Build the :class:`MoveVerdict` for one played half-move.

    ``is_forced`` is derived from the engine: a move is forced iff exactly
    one legal move was available in ``state_before``. When ``engine`` is
    ``None`` we fall back to ``False`` — the caller is expected to wire an
    engine in for end-to-end analysis, but tests can omit it.

    The motif list is built in two passes:

    1. ``detect_all`` runs every detector against the **played** move.
    2. If a non-equivalent ``best_move`` is supplied, ``detect_all_missed``
       runs every detector against the **unplayed** best move and appends
       any matches (these carry ``role="missed"``).
    """
    is_forced = False
    if engine is not None:
        is_forced = len(engine.legal_moves(state_before)) == 1

    motifs = detect_all(
        state_before,
        move,
        state_after,
        pv=best_pv,
        scan_score_before=score_before,
        scan_score_after=score_after,
        engine=engine,
    )

    if best_move is not None and best_move.path != move.path:
        missed = detect_all_missed(
            state_before,
            best_move,
            best_pv or [],
            move,
            engine=engine,
        )
        motifs.extend(missed)

    verdict: Verdict = classify_move(
        score_before=score_before,
        score_after=score_after,
        side=state_before.turn,
        is_forced=is_forced,
        is_book=is_book,
        motifs=motifs,
    )

    features_before = compute_features(state_before, half_move=half_move_number, engine=engine)
    features_after = compute_features(state_after, half_move=half_move_number + 1, engine=engine)
    phase = determine_phase(state_before, half_move_number)

    return MoveVerdict(
        move_number=half_move_number,
        side=state_before.turn,
        move_notation=notation(move),
        fen_before=state_to_fen(state_before),
        fen_after=state_to_fen(state_after),
        score_before=score_before,
        score_after=score_after,
        delta_winchance=_signed_delta(score_before, score_after, state_before.turn),
        verdict=verdict,
        is_forced=is_forced,
        motifs=motifs,
        features_before=features_before,
        features_after=features_after,
        phase=phase,
    )
