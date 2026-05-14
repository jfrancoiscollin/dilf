"""Notation utilities — parse/reconstruct draughts move notations.

The :mod:`pedagogy.notation.dubois` submodule deals specifically with the
abbreviated capture notation used in Dubois pedagogical books (``aXb`` =
start square and landing square only, with the capture trajectory left
implicit and reconstructed geometrically).
"""

from pedagogy.notation.dubois import (
    AmbiguousRafleError,
    NoSuchRafleError,
    NotAManError,
    enumerate_pawn_captures,
    reconstruct_pawn_capture,
)

__all__ = [
    "AmbiguousRafleError",
    "NoSuchRafleError",
    "NotAManError",
    "enumerate_pawn_captures",
    "reconstruct_pawn_capture",
]
