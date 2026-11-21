"""MTDP-D1 score-blind FMJD PDN exporter.

This is an engineering adapter, not an independent scientific cohort.
Every game is validated atomically; ambiguous capture paths fail closed.
No engine evaluation or target scores enter any signature.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pedagogy.game import state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.pdn import PdnGame, read_games, validated_trajectory
from research.mtdp.successor_audit import _quiet_signature
from research.mtdp.decision_equivalence.score_blind_audit import audit


def _action_key(move: Any) -> list[Any]:
    return [list(move.path), sorted(move.captures), bool(move.promotion)]


def _typed_board(state: Any) -> list[Any]:
    return [
        sorted(state.white_men), sorted(state.white_kings),
        sorted(state.black_men), sorted(state.black_kings),
    ]


def position_record(state: Any, game_id: str, engine: Any) -> dict[str, Any]:
    """Emit E/L/Q and published LCB count/blocker key; no Scan scores."""
    moves = list(engine.legal_moves(state))
    actions = [_action_key(move) for move in moves]
    if len({json.dumps(a) for a in actions}) != len(actions):
        raise ValueError("ambiguous/duplicate FMJD action identity")
    actions.sort(key=lambda a: json.dumps(a, separators=(",", ":")))
    board = _typed_board(state)
    quiet = _quiet_signature(state)
    # _quiet_signature is defined only for mover-men positions without
    # immediate captures; tactical and king positions fall back to exact E.
    if quiet is None:
        q = ["exact-fallback", state.turn, board]
        lcb = ["exact-fallback", state.turn, board]
    else:
        turn, men, blockers = quiet
        q = ["quiet-v1", turn, sorted(men), sorted(blockers)]
        # Published LCB matching rule (geometry_ablation.py): identical
        # turn and complete legal-action catalogue, same mover-men count,
        # and identical immediate opponent blockers. Do not substitute
        # mover occupancy for count or omit the legal-action fingerprint.
        lcb = ["quiet-lcb-v1", turn, actions, len(men), sorted(blockers)]
    return {
        "fen": state_to_fen(state),
        "game_id": game_id,
        "actions": actions,
        "signatures": {
            "E": [state.turn, board],
            "L": [state.turn, actions],
            "LCB": lcb,
            "Q": q,
        },
    }


def export_records(games: list[PdnGame], engine: Any) -> list[dict[str, Any]]:
    rows = []
    for game in games:
        # Do not retain even the initial position from an invalid game.
        trajectory = validated_trajectory(game, engine)
        game_id = str(game.tags.get("GameID") or game.tags.get("Site") or game.index)
        for _, _, state in trajectory:
            rows.append(position_record(state, game_id, engine))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdn", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    rows = export_records(read_games(args.pdn), create_engine())
    # Validate complete score-blind population before writing any file.
    report = audit(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                for row in rows), encoding="utf-8"
    )
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        args.audit_output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")


if __name__ == "__main__":
    main()

