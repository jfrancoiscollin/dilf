"""One-ply successor congruence audit for MTDP quiet-man geometry.

A pair is compared only if its canonical FEN differs, both states share
the quiet-man signature, and exact square-indexed legal moves agree.
Successors are compared under identical actions; no minimax equivalence
is inferred.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from pedagogy.game import state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.pdn import PdnGame, read_games, validated_trajectory
from research.mtdp.signature_ablation import _quiet_man_key


def _quiet_signature(state: Any) -> tuple | None:
    if state.turn == "white":
        men, kings = state.white_men, state.white_kings
        opponents = state.black_men | state.black_kings
    else:
        men, kings = state.black_men, state.black_kings
        opponents = state.white_men | state.white_kings
    if kings:
        return None
    return _quiet_man_key(state.turn, men, opponents)


def _action_key(move: Any) -> tuple:
    return tuple(move.path), tuple(sorted(move.captures)), bool(move.promotion)


def audit_successors(games: list[PdnGame], engine: Any) -> dict[str, Any]:
    groups: dict[tuple, dict[str, Any]] = defaultdict(dict)
    observations = 0
    for game in games:
        trajectory = validated_trajectory(game, engine)
        observations += len(trajectory)
        for _, _, state in trajectory:
            key = _quiet_signature(state)
            if key is None:
                continue
            fen = state_to_fen(state)
            groups[key].setdefault(fen, state)

    pairs = 0
    unequal_actions = 0
    unequal_successor_fens = 0
    unequal_successor_quiet_keys = 0
    examples: list[dict[str, Any]] = []
    for states in groups.values():
        if len(states) < 2:
            continue
        for (fen_a, a), (fen_b, b) in combinations(sorted(states.items()), 2):
            pairs += 1
            moves_a = {_action_key(m): m for m in engine.legal_moves(a)}
            moves_b = {_action_key(m): m for m in engine.legal_moves(b)}
            if moves_a.keys() != moves_b.keys():
                unequal_actions += 1
                if len(examples) < 10:
                    examples.append({"fen_a": fen_a, "fen_b": fen_b,
                                     "failure": "different_legal_actions"})
                continue
            fen_disagree = False
            signature_disagree = False
            for action in sorted(moves_a):
                successor_a = engine.apply_move(a, moves_a[action])
                successor_b = engine.apply_move(b, moves_b[action])
                fen_disagree |= state_to_fen(successor_a) != state_to_fen(successor_b)
                signature_disagree |= (
                    _quiet_signature(successor_a) != _quiet_signature(successor_b)
                )
            unequal_successor_fens += int(fen_disagree)
            unequal_successor_quiet_keys += int(signature_disagree)
            if (fen_disagree or signature_disagree) and len(examples) < 10:
                examples.append({
                    "fen_a": fen_a, "fen_b": fen_b,
                    "different_successor_fen": fen_disagree,
                    "different_successor_quiet_signature": signature_disagree,
                })
    return {
        "schema_version": "mtdp-successor-audit-v1",
        "games": len(games),
        "observations": observations,
        "distinct_quiet_signatures": len(groups),
        "distinct_fen_pairs": pairs,
        "different_legal_action_pairs": unequal_actions,
        "different_successor_fen_pairs": unequal_successor_fens,
        "different_successor_quiet_signature_pairs": unequal_successor_quiet_keys,
        "examples": examples,
        "interpretation": (
            "One-ply descriptive test only; successor quiet signature may be "
            "undefined after captures or promotions. Equality is not "
            "strategic equivalence and does not justify pruning."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="MTDP one-ply successor congruence")
    parser.add_argument("--pdn", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_successors(read_games(args.pdn), create_engine())
    rendered = json.dumps(report, sort_keys=True, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
