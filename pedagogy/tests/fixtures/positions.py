"""Reference positions used across feature/motif tests.

Each entry carries a unique ``name``, an FEN string and the *subset* of
features that PR 1 verifies (material, geometry and mobility-related
quantities). Structure and formation features will be added in PR 2.

Square numbering follows the FMJD/PDN convention used everywhere else in the
project: square 1 is the top-left dark square (Black's POV).
"""

from __future__ import annotations

from typing import TypedDict

from pedagogy.game import GameState, parse_fen


class ReferencePosition(TypedDict):
    name: str
    fen: str
    # Material
    white_men: int
    white_kings: int
    black_men: int
    black_kings: int
    balance: int
    # Geometry
    center_count_white: int
    center_count_black: int
    left_wing_white: int
    right_wing_white: int
    left_wing_black: int
    right_wing_black: int
    white_promotion_distance: int
    black_promotion_distance: int


# Initial FMJD position: White to move, 20 men each, square 31..50 vs 1..20.
INITIAL: ReferencePosition = {
    "name": "initial_position",
    "fen": (
        "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50"
        ":B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
    ),
    "white_men": 20,
    "white_kings": 0,
    "black_men": 20,
    "black_kings": 0,
    "balance": 0,
    # 31..34 sit in CENTER_EXTENDED (column-wise core of row 7).
    "center_count_white": 4,
    "center_count_black": 4,
    # White covers LEFT_WING = {31, 36, 41, 46}.
    "left_wing_white": 4,
    "right_wing_white": 4,
    # Square 1 is excluded from LEFT_WING by the spec glossary.
    "left_wing_black": 3,
    "right_wing_black": 4,
    # Closest white men are on row 7 -> 6 rows from row 1.
    "white_promotion_distance": 6,
    "black_promotion_distance": 6,
}


# A classic middlegame mock-up: tip of the white classical wedge on 32/37/41,
# black mirrors on 10/14/19, scattered support elsewhere.
CLASSICAL: ReferencePosition = {
    "name": "classical_formation",
    "fen": "W:W26,27,32,33,37,38,41,42,46,47:B14,15,19,20,10,4,5,11,12,13",
    "white_men": 10,
    "white_kings": 0,
    "black_men": 10,
    "black_kings": 0,
    "balance": 0,
    # White CENTER_EXTENDED ∩ white = {26, 27, 32, 33} -> 4.
    "center_count_white": 4,
    # Black CENTER_EXTENDED ∩ black = {19} -> 1 (14 is not in CENTER_EXTENDED).
    "center_count_black": 1,
    # White LEFT_WING ∩ white = {26, 41, 46}.
    "left_wing_white": 3,
    # White RIGHT_WING ∩ white = {} -> 0.
    "right_wing_white": 0,
    # Black LEFT_WING ∩ black = {11}.
    "left_wing_black": 1,
    # Black RIGHT_WING ∩ black = {5, 10, 15, 20}.
    "right_wing_black": 4,
    # Closest white man to row 1: square 26 on row 6 -> distance 5.
    "white_promotion_distance": 5,
    # Closest black man to row 10: square 20 on row 4 -> distance 6.
    "black_promotion_distance": 6,
}


# Endgame: one white king vs three black men, white to move.
KING_VS_THREE_MEN: ReferencePosition = {
    "name": "endgame_king_vs_three_men",
    "fen": "W:WK28:B6,16,26",
    "white_men": 0,
    "white_kings": 1,
    "black_men": 3,
    "black_kings": 0,
    "balance": 0,  # 3 - 3
    # The white king sits on 28 (in CENTER_EXTENDED).
    "center_count_white": 1,
    # Black pieces in CENTER_EXTENDED = {16, 26} -> 2.
    "center_count_black": 2,
    "left_wing_white": 0,
    "right_wing_white": 0,
    "left_wing_black": 3,  # 6, 16, 26 all in LEFT_WING
    "right_wing_black": 0,
    # White has no men -> NO_MAN_DISTANCE (11).
    "white_promotion_distance": 11,
    # Black men {6, 16, 26}: rows 2, 4, 6 -> 10 - 6 = 4.
    "black_promotion_distance": 4,
}


# Two-piece sparring position: white king on 23, black king on 28. Drawish.
TWO_KINGS: ReferencePosition = {
    "name": "two_kings_only",
    "fen": "W:WK23:BK28",
    "white_men": 0,
    "white_kings": 1,
    "black_men": 0,
    "black_kings": 1,
    "balance": 0,
    "center_count_white": 1,
    "center_count_black": 1,
    "left_wing_white": 0,
    "right_wing_white": 0,
    "left_wing_black": 0,
    "right_wing_black": 0,
    # Neither side has any men; sentinel value applies.
    "white_promotion_distance": 11,
    "black_promotion_distance": 11,
}


# Material imbalance, opening-ish position, used to test balance signs.
WHITE_PLUS_ONE: ReferencePosition = {
    "name": "white_plus_one_pawn",
    "fen": "B:W31,32,33,34,35,36,37,38,39,40,41:B1,2,3,4,5,6,7,8,9,10",
    "white_men": 11,
    "white_kings": 0,
    "black_men": 10,
    "black_kings": 0,
    "balance": 1,
    "center_count_white": 4,  # 31..34
    "center_count_black": 0,
    "left_wing_white": 3,  # 31, 36, 41
    "right_wing_white": 2,  # 35, 40
    "left_wing_black": 1,  # 6
    "right_wing_black": 2,  # 5, 10
    "white_promotion_distance": 6,  # row 7
    "black_promotion_distance": 8,  # row 2
}


ALL_POSITIONS: list[ReferencePosition] = [
    INITIAL,
    CLASSICAL,
    KING_VS_THREE_MEN,
    TWO_KINGS,
    WHITE_PLUS_ONE,
]


def state_for(position: ReferencePosition) -> GameState:
    """Convenience: parse the FEN of a reference position."""
    return parse_fen(position["fen"])
