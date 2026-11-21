"""Strict PDN mainline replay through an externally supplied FMJD rules engine.

No internal rules are guessed. Every ply is matched against engine.legal_moves,
and applied using engine.apply_move. The adapter fails closed on ambiguity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from pedagogy.game import GameState, Move, initial_state, parse_fen
from pedagogy.protocols import EngineProtocol

_TAG = re.compile(r'^\s*\[([A-Za-z][A-Za-z0-9_]*)\s+"((?:\\.|[^"\\])*)"\s*\]\s*$', re.M)
_MOVE = re.compile(r"^(\d{1,2})([-xX])(\d{1,2})(?:[xX](\d{1,2}))*$")
_MOVE_NUM = re.compile(r"^\d+\.(?:\.\.)?$")
_RESULTS = {"1-0", "0-1", "1/2-1/2", "2-0", "0-2", "1-1", "*"}
_TOKEN = re.compile(r"\d{1,2}(?:[-xX]\d{1,2})+|\d+\.{1,3}|1/2-1/2|2-0|0-2|1-1|1-0|0-1|\*|\S+")


@dataclass(frozen=True)
class PdnGame:
    index: int
    tags: dict[str, str]
    moves: tuple[str, ...]


class PdnReplayError(ValueError):
    pass


def _strip_comments_and_variations(text: str) -> str:
    """Strip comments and nested parenthesized sidelines; reject malformed input."""
    out: list[str] = []
    depth = 0
    brace = False
    line_comment = False
    for char in text:
        if line_comment:
            if char == "\n":
                line_comment = False
            continue
        if brace:
            if char == "}":
                brace = False
            continue
        if char == ";" and depth == 0:
            line_comment = True
        elif char == "{" and depth == 0:
            brace = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise PdnReplayError("Unexpected closing variation")
        elif depth == 0:
            out.append(char)
    if depth or brace:
        raise PdnReplayError("Unclosed variation or comment")
    return "".join(out)


def parse_games(pdn: str) -> list[PdnGame]:
    """Parse header-separated PDN mainlines; do not trust Result tags as labels."""
    chunks = re.split(r"(?=^\s*\[Event\s+)", pdn, flags=re.M | re.I)
    games: list[PdnGame] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        tags = {match.group(1): match.group(2) for match in _TAG.finditer(chunk)}
        movetext = _TAG.sub("", chunk)
        movetext = _strip_comments_and_variations(movetext)
        moves: list[str] = []
        for raw in _TOKEN.findall(movetext):
            if raw in _RESULTS:
                break
            if _MOVE_NUM.fullmatch(raw) or raw.startswith("$"):
                continue
            if re.fullmatch(r"\d+\.{1,3}", raw):
                continue
            if not _MOVE.fullmatch(raw):
                raise PdnReplayError(f"Unsupported PDN token: {raw!r}")
            moves.append(raw)
        if tags or moves:
            games.append(PdnGame(len(games) + 1, tags, tuple(moves)))
    return games


def _resolve(state: GameState, token: str, engine: EngineProtocol) -> Move:
    squares = [int(s) for s in re.findall(r"\d+", token)]
    capture = "x" in token.lower()
    if len(squares) < 2 or any(not 1 <= sq <= 50 for sq in squares):
        raise PdnReplayError(f"Invalid PDN move: {token!r}")
    candidates = [
        move for move in engine.legal_moves(state)
        if move.from_square == squares[0]
        and move.to_square == squares[-1]
        and move.is_capture == capture
    ]
    # Explicit multi-landing notation must match the whole path.
    if len(squares) > 2:
        candidates = [move for move in candidates if move.path == tuple(squares)]
    if len(candidates) != 1:
        raise PdnReplayError(
            f"{token!r}: expected exactly one legal matching move, found {len(candidates)}"
        )
    return candidates[0]


def replay_game(game: PdnGame, engine: EngineProtocol) -> Iterator[tuple[int, str, GameState]]:
    """Yield (ply, original_move_token, position), including initial ply 0.

    An invalid or ambiguous move raises PdnReplayError; callers must quarantine
    the entire game, not use a partially reconstructed trajectory.
    """
    state = parse_fen(game.tags["FEN"]) if "FEN" in game.tags else initial_state()
    yield 0, "", state
    for ply, token in enumerate(game.moves, 1):
        try:
            move = _resolve(state, token, engine)
            state = engine.apply_move(state, move)
        except (ValueError, AssertionError, IndexError) as exc:
            raise PdnReplayError(f"Game {game.index}, ply {ply}, {token}: {exc}") from exc
        yield ply, token, state


def validated_trajectory(game: PdnGame, engine: EngineProtocol) -> list[tuple[int, str, GameState]]:
    """Atomic validation: no partial trajectory is returned on error."""
    return list(replay_game(game, engine))


def read_games(path: Path) -> list[PdnGame]:
    return parse_games(path.read_text(encoding="utf-8-sig"))
