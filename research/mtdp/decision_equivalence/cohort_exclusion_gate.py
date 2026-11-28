"""Fail-closed score-blind D1 cohort exclusion gate.

Inputs are JSONL records. Each candidate must provide game_id, trajectory_sha256,
fen_sha256, source, tournament, ply. Forbidden records may contain any subset
of these keys; missing registries or malformed rows abort. No Scan scores read.
"""
import argparse
import hashlib
import json
from pathlib import Path

KEYS = ("game_id", "trajectory_sha256", "fen_sha256")
REQUIRED = (*KEYS, "source", "tournament", "ply")
SCORE_KEYS = {"score", "scan_score", "eval", "best_move", "rank", "wdl"}


def read_jsonl(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        raise ValueError(f"missing or empty registry: {path}")
    rows = []
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"blank registry row: {path}:{line_no}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {path}:{line_no}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"not an object: {path}:{line_no}")
        rows.append(row)
    return rows


def validate(candidates, registries):
    if not registries:
        raise ValueError("at least one complete forbidden registry required")
    forbidden = {key: set() for key in KEYS}
    for registry in registries:
        for row in registry:
            if not any(isinstance(row.get(k), str) and row[k] for k in KEYS):
                raise ValueError("forbidden row without identity")
            for key in KEYS:
                if key in row:
                    if not isinstance(row[key], str) or not row[key]:
                        raise ValueError(f"invalid forbidden {key}")
                    forbidden[key].add(row[key])
    seen_games = {}
    seen_trajectories = {}
    seen_fens = set()
    accepted = []
    for row in candidates:
        if any(k in row for k in SCORE_KEYS):
            raise ValueError("candidate contains target-score/rank fields")
        if any(k not in row or row[k] in (None, "") for k in REQUIRED):
            raise ValueError("incomplete candidate provenance")
        if not all(isinstance(row[k], str) for k in REQUIRED if k != "ply"):
            raise ValueError("invalid candidate identity type")
        if type(row["ply"]) is not int or row["ply"] < 0:
            raise ValueError("invalid ply")
        for key in ("trajectory_sha256", "fen_sha256"):
            if len(row[key]) != 64 or any(c not in "0123456789abcdef" for c in row[key]):
                raise ValueError(f"invalid {key}")
        if any(row[k] in forbidden[k] for k in KEYS):
            raise ValueError("candidate overlaps forbidden registry")
        game = row["game_id"]
        identity = (row["source"], row["tournament"], row["trajectory_sha256"])
        if game in seen_games and seen_games[game] != identity:
            raise ValueError("game id reused for different trajectory")
        if row["trajectory_sha256"] in seen_trajectories and seen_trajectories[row["trajectory_sha256"]] != game:
            raise ValueError("trajectory duplicated across games")
        seen_games[game] = identity
        seen_trajectories[row["trajectory_sha256"]] = game
        if row["fen_sha256"] in seen_fens:
            raise ValueError("duplicate FEN; requires explicit quarantine")
        seen_fens.add(row["fen_sha256"])
        accepted.append(row)
    if not accepted:
        raise ValueError("empty candidate cohort")
    per_game = {}
    for row in accepted:
        per_game.setdefault(row["game_id"], []).append(row["ply"])
    if any(plies != sorted(plies) or len(plies) != len(set(plies)) for plies in per_game.values()):
        raise ValueError("nonchronological or repeated ply")
    return accepted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--forbidden", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise ValueError("refuse overwrite of an existing manifest")
    rows = validate(read_jsonl(args.candidates), [read_jsonl(p) for p in args.forbidden])
    payload = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows)
    Path(args.output).write_text(payload, encoding="utf-8")
    print(json.dumps({"rows": len(rows), "sha256": hashlib.sha256(payload.encode()).hexdigest(),
                      "status": "engineering_gate_only_not_independence_certification"}, sort_keys=True))


if __name__ == "__main__":
    main()
