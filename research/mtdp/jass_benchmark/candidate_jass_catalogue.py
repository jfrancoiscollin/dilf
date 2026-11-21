"""Score-blind Jass/FMJD action check for the reserved, unfrozen candidate."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_cohort import ADAPTER_COMMIT, JASS_COMMIT
from research.mtdp.jass_move_mapping import map_root_moves, read_jass_catalogues

REPLAY_SHA256 = "e9de3a4cfdf44e6f33e77681290fc0ccbc23e5b9e2e02992b9d30229d118a16b"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compare(rows, engine, catalogues):
    """Require every target and both selected sources to share a full bijection."""
    fens = sorted({row["fen"] for row in rows} | {
        fen for row in rows for fen in row["source_fens"].values()
    })
    if len(catalogues) != len(fens):
        raise ValueError("Incomplete Jass catalogue")
    mappings = {
        fen: map_root_moves(engine.legal_moves(parse_fen(fen)), catalogue)
        for fen, catalogue in zip(fens, catalogues, strict=True)
    }
    for row in rows:
        expected = {(tuple(route), tuple(captures), bool(promotion))
                    for route, captures, promotion in row["legal"]}
        mapping = mappings[row["fen"]]
        if set(mapping) != expected or len(expected) != len(row["legal"]):
            raise ValueError("Candidate target differs from its replay action list")
        if set(row["source_fens"]) != {"L", "LCB"}:
            raise ValueError("Candidate needs both preselected source arms")
        if any(mappings[fen] != mapping for fen in row["source_fens"].values()):
            raise ValueError("Source and target action mappings differ")
    positions = []
    for fen in fens:
        serialized = [[list(action[0]), list(action[1]), action[2], key]
                      for action, key in sorted(mappings[fen].items())]
        payload = json.dumps(serialized, separators=(",", ":")).encode()
        positions.append({"fen": fen, "actions": len(serialized),
                          "mapping_sha256": digest(payload)})
    return {"targets": len(rows), "distinct_sources": len({
        f for row in rows for f in row["source_fens"].values()
    }), "distinct_positions": len(fens),
        "target_action_occurrences": sum(len(row["legal"]) for row in rows),
        "positions": positions}


def pinned_checkout(path, revision):
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    if head != revision or subprocess.check_output(["git", "-C", str(path), "diff", "HEAD"]):
        raise ValueError("Expected a clean pinned engine checkout")


def audit(replay, executable, jass, adapter):
    raw = replay.read_bytes()
    if digest(raw) != REPLAY_SHA256:
        raise ValueError("Replay differs from the verified pre-score candidate report")
    pinned_checkout(jass, JASS_COMMIT)
    pinned_checkout(adapter, ADAPTER_COMMIT)
    engine = create_engine()
    if Path(engine._rules.__file__).resolve() != (adapter / "backend/game_engine.py").resolve():
        raise ValueError("Imported FMJD engine differs from checked adapter")
    rows = json.loads(raw)["candidate_targets"]
    fens = sorted({row["fen"] for row in rows} | {
        f for row in rows for f in row["source_fens"].values()
    })
    result = compare(rows, engine, read_jass_catalogues(executable, map(parse_fen, fens)))
    return {"schema": "mtdp-candidate-jass-catalogue-v1", "candidate": "fFgE7oED",
            "scope": "legal_action_bijections_only_no_scores_no_scientific_freeze",
            "replay_sha256": digest(raw), "jass_commit": JASS_COMMIT,
            "adapter_commit": ADAPTER_COMMIT, "executable_sha256": digest(executable.read_bytes()),
            **result, "next_gate": "chronological_selection_before_scoring_freeze"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("replay", "executable", "jass", "adapter", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.replay, args.executable, args.jass, args.adapter)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "positions"}, sort_keys=True))


if __name__ == "__main__":
    main()
