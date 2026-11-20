"""Fail-closed proof of a PDN source/index/ply against an FMJD rules engine.

This module does not qualify independent D1 cohorts. The caller supplies the
pinned rules engine and must independently bind its own game_id to source/index.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from pedagogy.game import state_to_fen
from pedagogy.protocols import EngineProtocol
from research.mtdp.pdn import parse_games, validated_trajectory
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen


def prove_pdn_position(
    source: str | Path,
    expected_sha256: str,
    game_index: int,
    ply: int,
    expected_fen: str,
    engine: EngineProtocol,
) -> dict:
    """Authenticate and parse the same bytes, then legally replay the entire game.

    game_index is the 1-based index in the authenticated PDN, *not* a
    verified mapping from a manifest's arbitrary game_id. No score is read.
    """
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_sha256
    ):
        raise ValueError("invalid PDN SHA-256")
    if type(game_index) is not int or game_index < 1:
        raise ValueError("game_index must be a positive integer")
    if type(ply) is not int or ply < 0:
        raise ValueError("ply must be a nonnegative integer")
    raw = Path(source).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("PDN source bytes do not match digest")
    games = parse_games(raw.decode("utf-8-sig"))
    if game_index > len(games):
        raise ValueError("game index absent from authenticated PDN")
    game = games[game_index - 1]
    trajectory = validated_trajectory(game, engine)
    if ply >= len(trajectory):
        raise ValueError("ply absent from legally replayed game")
    actual_fen = canonical_fen(state_to_fen(trajectory[ply][2]))
    if actual_fen != canonical_fen(expected_fen):
        raise ValueError("FEN differs from legally replayed position")
    return {
        "source_pdn_sha256": digest,
        "source_game_index": game_index,
        "game_moves": len(game.moves),
        "verified_ply": ply,
        "canonical_fen": actual_fen,
        "pdn_bytes_verified": True,
        "source_index_membership_verified": True,
        "fmjd_legality_verified": True,
        "manifest_game_id_binding_verified": False,
        "independent_cohort_qualified": False,
    }
