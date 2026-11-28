"""Explain quarantined candidate moves without resolving or accepting them."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.prospective_candidate_replay import EXPECTED_PDN_SHA256
from research.mtdp.jass_cohort import ADAPTER_COMMIT
from research.mtdp.pdn import PdnReplayError, _resolve, read_games


def explain(game, engine):
    state = parse_fen(game.tags["FEN"]) if "FEN" in game.tags else initial_state()
    for ply, token in enumerate(game.moves, 1):
        try:
            move = _resolve(state, token, engine)
        except PdnReplayError as error:
            squares = tuple(map(int, re.findall(r"\d+", token)))
            candidates = [
                move for move in engine.legal_moves(state)
                if move.from_square == squares[0] and move.to_square == squares[-1]
                and move.is_capture == ("x" in token.lower())
                and (len(squares) == 2 or move.path == squares)
            ]
            rows = sorted([
                {"path": list(move.path), "captures": sorted(move.captures),
                 "promotion": move.promotion,
                 "successor_fen": state_to_fen(engine.apply_move(state, move))}
                for move in candidates
            ], key=lambda row: (row["path"], row["captures"], row["promotion"]))
            return {
                "game_index": game.index, "site": game.tags.get("Site"), "ply": ply,
                "token": token, "fen_before": state_to_fen(state), "error": str(error),
                "legal_candidates": rows,
                "distinct_successors": len({row["successor_fen"] for row in rows}),
                "disposition": "whole_game_remains_quarantined",
            }
        state = engine.apply_move(state, move)
    return None


def audit(pdn, adapter):
    raw = pdn.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_PDN_SHA256:
        raise ValueError("Candidate PDN digest differs from the reserved export")
    revision = subprocess.check_output(
        ["git", "-C", str(adapter), "rev-parse", "HEAD"], text=True,
    ).strip()
    if revision != ADAPTER_COMMIT:
        raise ValueError("FMJD adapter revision differs from the pinned engine")
    engine = create_engine()
    actual_source = Path(engine._rules.__file__).resolve()
    expected_source = (adapter / "backend/game_engine.py").resolve()
    if actual_source != expected_source:
        raise ValueError("Imported FMJD engine differs from the checked adapter")
    if subprocess.check_output(
        ["git", "-C", str(adapter), "diff", "HEAD", "--", "backend/game_engine.py"],
    ):
        raise ValueError("Pinned FMJD engine has local modifications")
    games = read_games(pdn)
    cases = [case for game in games if (case := explain(game, engine)) is not None]
    return {
        "candidate": "fFgE7oED", "pdn_sha256": digest, "adapter_commit": revision,
        "games": len(games), "quarantined_cases": cases,
        "scope": "diagnostic_only_no_scoring_no_chronological_freeze",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pdn", "adapter", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.pdn, args.adapter)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"games": report["games"], "cases": [
        {key: case[key] for key in ("game_index", "ply", "token", "distinct_successors")}
        for case in report["quarantined_cases"]
    ]}, sort_keys=True))


if __name__ == "__main__":
    main()
