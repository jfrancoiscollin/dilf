"""Named formations and the master :func:`compute_features` aggregator.

Formations are detected by exact square sets — a position "has" a formation
iff every square of its signature is occupied by the right side. The
signatures are kept small (3 squares) so detection is cheap and false
positives over a busy board are common; motif-layer logic refines the call
when needed.

:func:`determine_phase` mirrors spec §4 with two corrections noted in the
docstring; :func:`compute_features` is the entry point referenced by every
other layer of the pedagogy module.
"""

from __future__ import annotations

from typing import Final

from ..game import GameState
from ..protocols import EngineProtocol
from ..types import Features, Phase
from .geometry import (
    CENTER_EXTENDED,
    LEFT_WING,
    RIGHT_WING,
    min_promotion_distance,
)
from .material import count_material, total_pieces
from .mobility import count_legal_moves, hanging_pieces
from .structure import (
    find_backward_pawns,
    find_holes,
    find_isolated_pawns,
    find_outposts,
)

#: Known triple-square signatures, taken from spec §4. The detection is
#: purely set-based: a position is said to "have" formation X iff every
#: square of X is occupied by the right colour. To extend, add an entry to
#: this dict (no other code change is required).
KNOWN_FORMATIONS: Final[dict[str, frozenset[int]]] = {
    "classique_blancs": frozenset({32, 37, 41}),
    "classique_noirs": frozenset({10, 14, 19}),
    "roozenburg_blancs": frozenset({28, 32, 37}),
    "roozenburg_noirs": frozenset({14, 19, 23}),
    "ghestem_blancs": frozenset({27, 32, 38}),
}


def detect_formations(state: GameState) -> list[str]:
    """Return formation names whose every square is occupied by the right colour.

    "Blancs" signatures must be entirely covered by white pieces (men or
    kings) and analogously for "noirs". The result is sorted alphabetically
    for deterministic output.
    """
    white = state.pieces_of("white")
    black = state.pieces_of("black")
    out: list[str] = []
    for name, signature in KNOWN_FORMATIONS.items():
        if name.endswith("_blancs") and signature.issubset(white):
            out.append(name)
        elif name.endswith("_noirs") and signature.issubset(black):
            out.append(name)
    out.sort()
    return out


def determine_phase(state: GameState, half_move: int) -> Phase:
    """Game phase from move number and material.

    Two changes against the spec pseudo-code: ``sum(count_material.values())``
    would over-count by including the ``balance`` field, so we use
    :func:`total_pieces` instead; and ``state.white_kings`` is a frozenset,
    so its truthiness is tested via ``len(...) >= 1``.
    """
    if half_move <= 12:
        return Phase.OPENING
    has_king_each_side = len(state.white_kings) >= 1 and len(state.black_kings) >= 1
    if total_pieces(state) <= 8 or has_king_each_side:
        return Phase.ENDGAME
    return Phase.MIDDLEGAME


def compute_features(
    state: GameState,
    *,
    half_move: int = 13,
    engine: EngineProtocol | None = None,
) -> Features:
    """Compose every layer of features into one :class:`Features` snapshot.

    ``half_move`` defaults to 13 (just past the opening cut-off) so callers
    who don't track move history get a sensible non-opening phase by
    default. ``engine`` is needed only to populate the mobility fields; when
    omitted, both ``*_legal_moves`` counts are reported as 0 and motif-layer
    detectors should not infer mobility from them.
    """
    counts = count_material(state)
    white = state.pieces_of("white")
    black = state.pieces_of("black")
    return Features(
        white_men=counts["white_men"],
        white_kings=counts["white_kings"],
        black_men=counts["black_men"],
        black_kings=counts["black_kings"],
        material_balance=counts["balance"],
        center_count_white=len(white & CENTER_EXTENDED),
        center_count_black=len(black & CENTER_EXTENDED),
        left_wing_white=len(white & LEFT_WING),
        right_wing_white=len(white & RIGHT_WING),
        left_wing_black=len(black & LEFT_WING),
        right_wing_black=len(black & RIGHT_WING),
        isolated_pawns_white=find_isolated_pawns(state, "white"),
        isolated_pawns_black=find_isolated_pawns(state, "black"),
        backward_pawns_white=find_backward_pawns(state, "white"),
        backward_pawns_black=find_backward_pawns(state, "black"),
        holes_white=find_holes(state, "white"),
        holes_black=find_holes(state, "black"),
        outposts_white=find_outposts(state, "white"),
        outposts_black=find_outposts(state, "black"),
        white_legal_moves=count_legal_moves(state, "white", engine) if engine else 0,
        black_legal_moves=count_legal_moves(state, "black", engine) if engine else 0,
        hanging_pieces_white=hanging_pieces(state, "white", engine) if engine else [],
        hanging_pieces_black=hanging_pieces(state, "black", engine) if engine else [],
        white_promotion_distance=min_promotion_distance(state, "white"),
        black_promotion_distance=min_promotion_distance(state, "black"),
        formations=detect_formations(state),
        phase=determine_phase(state, half_move),
    )
