"""Pure positional features (no engine, no Scan calls).

Each function takes a :class:`pedagogy.game.GameState` and returns scalars or
lists, with the exception of :mod:`pedagogy.features.mobility` which needs an
engine to enumerate legal moves.
"""

from .geometry import (
    BLACK_PROMOTION_ROW,
    CENTER_CORE,
    CENTER_EXTENDED,
    LEFT_WING,
    MAIN_DIAGONAL,
    NO_MAN_DISTANCE,
    RIGHT_WING,
    WHITE_PROMOTION_ROW,
    coords_to_square,
    diagonal_neighbors,
    min_promotion_distance,
    promotion_distance,
    row_of,
    square_to_coords,
    squares_between,
)
from .material import count_material, material_balance
from .mobility import count_legal_moves, hanging_pieces, threatened_captures

__all__ = [
    # geometry
    "BLACK_PROMOTION_ROW",
    "CENTER_CORE",
    "CENTER_EXTENDED",
    "LEFT_WING",
    "MAIN_DIAGONAL",
    "NO_MAN_DISTANCE",
    "RIGHT_WING",
    "WHITE_PROMOTION_ROW",
    "coords_to_square",
    "diagonal_neighbors",
    "min_promotion_distance",
    "promotion_distance",
    "row_of",
    "square_to_coords",
    "squares_between",
    # material
    "count_material",
    "material_balance",
    # mobility
    "count_legal_moves",
    "hanging_pieces",
    "threatened_captures",
]
