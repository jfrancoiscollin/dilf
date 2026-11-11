"""Minimal, engine-free spatial descriptors for FMJD positions.

These are descriptive statistics, not estimates of winning chances or
strategic value. All calculations use dilf's canonical GameState and geometry.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from pedagogy.game import GameState, state_to_fen
from pedagogy.features.geometry import CENTER_CORE, CENTER_EXTENDED, diagonal_neighbors
from pedagogy.features.material import count_material


@dataclass(frozen=True)
class SpatialMetrics:
    fen: str
    turn: str
    white_pieces: int
    black_pieces: int
    material_balance: int
    center_core_white: int
    center_core_black: int
    center_extended_white: int
    center_extended_black: int
    adjacency_edges_white: int
    adjacency_edges_black: int
    occupied_squares: int
    occupied_fraction: float

    def as_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


def _adjacency_edges(squares: frozenset[int]) -> int:
    """Number of undirected diagonal-neighbour pairs occupied by one side."""
    return sum(1 for sq in squares for neighbor in diagonal_neighbors(sq)
               if neighbor in squares and sq < neighbor)


def compute_spatial_metrics(state: GameState) -> SpatialMetrics:
    """Compute reproducible geometric descriptors, with no engine evaluation."""
    white = state.pieces_of("white")
    black = state.pieces_of("black")
    material = count_material(state)
    occupied = len(state.all_pieces)
    return SpatialMetrics(
        fen=state_to_fen(state),
        turn=state.turn,
        white_pieces=len(white),
        black_pieces=len(black),
        material_balance=material["balance"],
        center_core_white=len(white & CENTER_CORE),
        center_core_black=len(black & CENTER_CORE),
        center_extended_white=len(white & CENTER_EXTENDED),
        center_extended_black=len(black & CENTER_EXTENDED),
        adjacency_edges_white=_adjacency_edges(white),
        adjacency_edges_black=_adjacency_edges(black),
        occupied_squares=occupied,
        occupied_fraction=occupied / 50,
    )
