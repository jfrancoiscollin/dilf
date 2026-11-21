"""Check canonical DILF actions against the generated Jass root catalogue."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

from pedagogy.game import GameState, Move, parse_fen, state_to_fen
from research.mtdp.successor_audit import _action_key

Action = tuple[tuple[int, ...], tuple[int, ...], bool]
Catalogue = list[tuple[str, bool]]


class MoveMappingError(ValueError):
    """A position cannot be used for a one-to-one comparison of root moves."""


def map_root_moves(moves: Iterable[Move], jass_moves: Catalogue) -> dict[Action, str]:
    """Return a complete bijection or reject the entire position."""
    mapping: dict[Action, str] = {}
    expected: dict[str, bool] = {}
    for move in moves:
        action = _action_key(move)
        if action in mapping:
            raise MoveMappingError(f"Duplicate DILF canonical action: {action}")
        separator = "x" if move.is_capture else "-"
        key = f"{move.from_square}{separator}{move.to_square}"
        if move.is_capture:
            key += "".join(f"x{square}" for square in action[1])
        if key in expected:
            raise MoveMappingError(f"Ambiguous DILF root key: {key}")
        expected[key] = move.promotion
        mapping[action] = key

    actual = dict(jass_moves)
    if len(actual) != len(jass_moves):
        raise MoveMappingError("Duplicate Jass root key")
    if expected != actual:
        missing = sorted(expected.items() - actual.items())
        extra = sorted(actual.items() - expected.items())
        raise MoveMappingError(f"Root catalogue mismatch: missing={missing}, extra={extra}")
    return mapping


def read_jass_catalogues(executable: Path, states: Iterable[GameState]) -> list[Catalogue]:
    """Query the pinned Jass exporter and verify the echoed board for every row."""
    positions = list(states)
    process = subprocess.run(
        [str(executable.resolve())],
        input="".join(f"{state_to_fen(state)}\n" for state in positions),
        capture_output=True,
        text=True,
        check=True,
    )
    rows = process.stdout.splitlines()
    if len(rows) != len(positions):
        raise ValueError(f"Expected {len(positions)} Jass rows, got {len(rows)}")
    catalogues = []
    for state, row in zip(positions, rows, strict=True):
        fen, *fields = row.split("\t")
        if parse_fen(fen) != state:
            raise ValueError(f"Jass echoed a different position for {state_to_fen(state)}")
        catalogue = []
        for field in fields:
            key, separator, promotion = field.partition("=")
            if not key or not separator or promotion not in {"0", "1"}:
                raise ValueError(f"Malformed Jass move entry: {field!r}")
            catalogue.append((key, promotion == "1"))
        catalogues.append(catalogue)
    return catalogues
