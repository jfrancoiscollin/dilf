"""Atomic, provenance-preserving trajectory export using an injected rules engine.

Never emits partial games: all positions are validated before any game rows
are written. An optional quarantine report records failures without leaking
partial trajectories into the research dataset.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from pedagogy.protocols import EngineProtocol
from research.mtdp.dataset import record, write_jsonl
from research.mtdp.pdn import PdnGame, PdnReplayError, read_games, validated_trajectory


def trajectory_records(game: PdnGame, engine: EngineProtocol) -> list[dict[str, Any]]:
    """Validate the whole game before constructing any export records."""
    trajectory = validated_trajectory(game, engine)
    rows: list[dict[str, Any]] = []
    for ply, token, state in trajectory:
        rows.append(record(
            state,
            source="pcblues_game_pdn",
            source_id=f"game-{game.index}",
            metadata={
                "game_index": game.index,
                "ply": ply,
                "move": token,
                "source_deel": game.tags.get("Deel"),
                "source_page": game.tags.get("Page"),
                "source_event": game.tags.get("Event"),
                "result_is_provenance_only": True,
                "kings_present": bool(state.white_kings or state.black_kings),
                "king_detection_verified": True,
            },
        ))
    return rows


def export_games(
    games: list[PdnGame], engine: EngineProtocol, output: Path,
    quarantine_output: Path,
) -> dict[str, int]:
    """Replay, quarantine and write only fully validated games.

    Quarantine is keyed by game index and error, never by a partial position.
    Both output files are overwritten on each invocation.
    """
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str | int]] = []
    for game in games:
        try:
            accepted.extend(trajectory_records(game, engine))
        except (PdnReplayError, ValueError, AssertionError) as exc:
            rejected.append({"game_index": game.index, "reason": str(exc)})
    write_jsonl(accepted, output)
    write_jsonl(rejected, quarantine_output)
    return {
        "games_total": len(games),
        "games_accepted": len(games) - len(rejected),
        "games_quarantined": len(rejected),
        "positions_exported": len(accepted),
    }


def _load_engine(spec: str) -> EngineProtocol:
    """Import a user-supplied zero-argument adapter factory, module:function."""
    if ":" not in spec:
        raise ValueError("Engine factory must be module:function")
    module, name = spec.split(":", 1)
    factory = getattr(importlib.import_module(module), name)
    engine = factory()
    if not isinstance(engine, EngineProtocol):
        raise TypeError("Factory must return an EngineProtocol implementation")
    return engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and export MTDP game trajectories")
    parser.add_argument("--pdn", type=Path, default=Path("data/exports/pcblues/pcblues_games.pdn"))
    parser.add_argument("--engine-factory", required=True, help="Trusted import path module:function")
    parser.add_argument("--output", type=Path, default=Path(".cache/mtdp/trajectories.jsonl"))
    parser.add_argument("--quarantine", type=Path, default=Path(".cache/mtdp/quarantine.jsonl"))
    args = parser.parse_args()
    result = export_games(read_games(args.pdn), _load_engine(args.engine_factory),
                          args.output, args.quarantine)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
