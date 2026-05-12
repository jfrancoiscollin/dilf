"""Shared dataclasses and enums for the pedagogy module.

These types are the contract between layers (features -> motifs -> verdicts ->
explanations -> profile -> api). They are intentionally framework-free: no DB,
no FastAPI, no Anthropic SDK imports here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Verdict(str, Enum):
    """Pedagogical verdict for a half-move."""

    BRILLIANT = "brilliant"      # Correct AND non-obvious sacrifice
    BEST = "best"                # Best move
    EXCELLENT = "excellent"      # Near-best (delta < 0.03)
    GOOD = "good"                # Good (delta < 0.075)
    INACCURACY = "inaccuracy"    # Inaccuracy (0.075 <= delta < 0.15)
    MISTAKE = "mistake"          # Mistake (0.15 <= delta < 0.30)
    BLUNDER = "blunder"          # Blunder (delta >= 0.30)
    FORCED = "forced"            # Forced move (single legal move)
    BOOK = "book"                # Opening book move


class Phase(str, Enum):
    """Phase of the game."""

    OPENING = "opening"          # <= 12 half-moves
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"          # <= 8 total pieces OR kings on both sides


@dataclass
class Features:
    """Purely geometric snapshot of a position. No Scan call involved."""

    # Material
    white_men: int
    white_kings: int
    black_men: int
    black_kings: int
    material_balance: int        # white - black, king = 3 men

    # Center / wings
    center_count_white: int
    center_count_black: int
    left_wing_white: int
    right_wing_white: int
    left_wing_black: int
    right_wing_black: int

    # Structure
    isolated_pawns_white: list[int]
    isolated_pawns_black: list[int]
    backward_pawns_white: list[int]
    backward_pawns_black: list[int]
    holes_white: list[int]
    holes_black: list[int]
    outposts_white: list[int]
    outposts_black: list[int]

    # Mobility
    white_legal_moves: int
    black_legal_moves: int

    # Promotion
    white_promotion_distance: int   # min(distance from a white piece to row 1)
    black_promotion_distance: int

    # Formations
    formations: list[str] = field(default_factory=list)

    # Phase
    phase: Phase = Phase.MIDDLEGAME


@dataclass
class MotifMatch:
    """A motif detected in the position or in the played move."""

    motif: str                              # e.g. "coup_royal"
    role: str                               # "played" | "missed" | "suffered" | "threatened"
    squares: list[int]                      # Squares involved (for UI highlighting)
    pv: list[str]                           # Principal variation that executes the motif
    severity: float                         # 0..1 — pedagogical severity
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MoveVerdict:
    """Complete verdict of a half-move."""

    move_number: int
    side: str                               # "white" | "black"
    move_notation: str                      # e.g. "32-28"
    fen_before: str
    fen_after: str
    score_before: float                     # Scan score, units = pawns
    score_after: float
    delta_winchance: float
    verdict: Verdict
    is_forced: bool
    motifs: list[MotifMatch] = field(default_factory=list)
    features_before: Optional[Features] = None
    features_after: Optional[Features] = None
    phase: Phase = Phase.MIDDLEGAME


@dataclass
class GameAnalysis:
    """Complete pedagogical analysis of a game."""

    game_id: int
    user_id: Optional[int]
    user_side: Optional[str]
    opening_name: Optional[str]
    verdicts: list[MoveVerdict]
    summary: dict[str, Any]


@dataclass
class UserProfile:
    """Aggregated player profile."""

    user_id: int
    games_count: int
    average_accuracy: float
    strengths: list[dict[str, Any]]         # [{"motif": ..., "frequency": ..., "score": ...}]
    weaknesses: list[dict[str, Any]]
    weakest_phase: Phase
    recommended_exercise_tags: list[str]
