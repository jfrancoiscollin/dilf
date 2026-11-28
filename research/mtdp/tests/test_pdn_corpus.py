"""Repository corpus smoke test: parsing needs no FMJD engine."""
from __future__ import annotations

from pathlib import Path

from research.mtdp.pdn import read_games


def test_pcblues_mainlines_parse() -> None:
    source = Path(__file__).resolve().parents[3] / "data/exports/pcblues/pcblues_games.pdn"
    games = read_games(source)
    assert len(games) == 26
    assert all(game.moves for game in games)
    assert all(game.tags.get("Event") is not None for game in games)
    assert all(game.tags.get("Result") for game in games)
    assert games[0].moves[:2] == ("32-28", "17-22")
