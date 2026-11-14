"""PDN parsing and fail-closed replay with a minimal deterministic rules mock."""
from __future__ import annotations

import pytest

from pedagogy.game import GameState, Move, state_from_pieces
from research.mtdp.pdn import PdnReplayError, parse_games, validated_trajectory


class MockRules:
    def legal_moves(self, state: GameState) -> list[Move]:
        if state.turn == "white" and 32 in state.white_men:
            return [Move((32, 28))]
        if state.turn == "black" and 17 in state.black_men:
            return [Move((17, 22))]
        return []

    def apply_move(self, state: GameState, move: Move) -> GameState:
        if state.turn == "white":
            return state_from_pieces(
                white_men=(state.white_men - {32}) | {28},
                black_men=state.black_men,
                turn="black",
            )
        return state_from_pieces(
            white_men=state.white_men,
            black_men=(state.black_men - {17}) | {22},
            turn="white",
        )


def test_parse_two_games_and_headers() -> None:
    pdn = ('[Event "A"]\n[Result "2-0"]\n1. 32-28 17-22 2-0\n\n'
           '[Event "B"]\n[Result "1-1"]\n1. 32-28 {note} (1. 31-27) 17-22 1-1')
    games = parse_games(pdn)
    assert len(games) == 2
    assert games[0].moves == ("32-28", "17-22")
    assert games[1].moves == ("32-28", "17-22")


def test_replay_validated_trajectory() -> None:
    game = parse_games('[Event "A"]\n1. 32-28 17-22 *')[0]
    result = validated_trajectory(game, MockRules())
    assert [ply for ply, _, _ in result] == [0, 1, 2]
    assert 28 in result[1][2].white_men
    assert 22 in result[2][2].black_men


def test_invalid_move_rejects_entire_game() -> None:
    game = parse_games('[Event "A"]\n1. 32-28 18-23 *')[0]
    with pytest.raises(PdnReplayError):
        validated_trajectory(game, MockRules())


def test_ambiguous_endpoint_capture_is_rejected() -> None:
    class Ambiguous(MockRules):
        def legal_moves(self, state: GameState) -> list[Move]:
            return [Move((32, 21, 12), (27, 17)), Move((32, 23, 12), (28, 18))]

    game = parse_games('[Event "A"]\n1. 32x12 *')[0]
    with pytest.raises(PdnReplayError, match="exactly one"):
        validated_trajectory(game, Ambiguous())


def test_unsupported_notation_fails_closed() -> None:
    with pytest.raises(PdnReplayError, match="Unsupported"):
        parse_games('[Event "A"]\n1. 32-28 ?! *')
