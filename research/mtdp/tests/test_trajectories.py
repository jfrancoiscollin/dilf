"""Export is atomic per game; no invalid intermediate positions are emitted."""
from __future__ import annotations

import json

from pedagogy.game import GameState, Move, state_from_pieces
from research.mtdp.pdn import parse_games
from research.mtdp.trajectories import export_games, trajectory_records


class TwoPlyRules:
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


def test_export_quarantines_invalid_game_atomically(tmp_path) -> None:
    games = parse_games(
        '[Event "A"]\n1. 32-28 17-22 *\n'
        '[Event "B"]\n1. 32-28 18-23 *\n'
    )
    output = tmp_path / "valid.jsonl"
    quarantine = tmp_path / "quarantine.jsonl"
    summary = export_games(games, TwoPlyRules(), output, quarantine)
    assert summary == {
        "games_total": 2, "games_accepted": 1,
        "games_quarantined": 1, "positions_exported": 3,
    }
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    failures = [json.loads(line) for line in quarantine.read_text().splitlines()]
    assert [r["metadata"]["ply"] for r in rows] == [0, 1, 2]
    assert {r["source_id"] for r in rows} == {"game-1"}
    assert failures[0]["game_index"] == 2
    assert rows[0]["metadata"]["result_is_provenance_only"] is True


def test_trajectory_contains_initial_state() -> None:
    game = parse_games('[Event "A"]\n1. 32-28 *')[0]
    rows = trajectory_records(game, TwoPlyRules())
    assert len(rows) == 2
    assert rows[0]["metrics"]["occupied_squares"] == 40
