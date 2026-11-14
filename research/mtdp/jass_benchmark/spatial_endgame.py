"""Check the largest native disagreement against Scan's six-piece bitbases."""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from pedagogy.game import parse_fen, state_to_fen
from research.mtdp.best_move_audit import Scan
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_benchmark.geometry_ablation import write_json
from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_cohort import SCAN_SHA256
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256

FEN = "B:WK3,16,19,24:B15,37"
TABLE_URL = "https://hjetten.home.xs4all.nl/scan/bb.zip"
TABLE_SHA256 = "1c3bdb50edb2903da76763010e58aeb24e00d1705f8e118fac881deba1efc43c"
INVERT = {"win": "loss", "loss": "win", "draw": "draw"}


def load_position_scores(scan, state):
    board = ["e"] * 50
    for piece, squares in (("w", state.white_men), ("W", state.white_kings),
                           ("b", state.black_men), ("B", state.black_kings)):
        for square in squares:
            board[square - 1] = piece
    scan.send("new-game", f"pos pos={state.turn[0].upper()}{''.join(board)}",
              f"level depth={scan.depth}", "go analyze")
    lines = list(scan.until("done"))
    pattern = re.compile(r'^info depth=18\b.*?\bscore=(-?\d+\.\d+)\b.*?\bpv="([^"]+)"')
    matches = [match.groups() for line in lines if (match := pattern.search(line))]
    if not matches:
        raise ValueError(f"Missing depth-18 principal variation for {state_to_fen(state)}")
    score, pv = matches[-1]
    return {"score_for_side_to_move": score, "pv": pv.split()}


def analyze(binary, table_binary, archive):
    binary, table_binary = binary.resolve(), table_binary.resolve()
    for engine in (binary, table_binary):
        if sha256(engine) != SCAN_SHA256 or sha256(engine.parent / "data/eval") != SCAN_EVAL_SHA256:
            raise ValueError(f"Scan binary or evaluation file does not match the pinned build: {engine}")
    with archive.open("rb") as stream:
        archive_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_digest != TABLE_SHA256:
        raise ValueError("Bitbase archive differs from the recorded download")
    rules = create_engine()
    root = parse_fen(FEN)
    successors = {
        f"{move.path[0]}-{move.path[-1]}": rules.apply_move(root, move)
        for move in rules.legal_moves(root)
    }
    states = [root, *successors.values()]
    fens = [state_to_fen(state) for state in states]
    commands = ["0"]
    for fen in fens:
        commands.extend((f"fen {fen}", "fen"))
    commands.append("q")
    run = subprocess.run([str(table_binary)], cwd=table_binary.parent,
                         input="\n".join(commands) + "\n", text=True,
                         capture_output=True, check=True, timeout=150)
    probes = re.findall(r"(?m)^(white|black) to play, bitbase (win|draw|loss)$", run.stdout)
    echoed = re.findall(r"(?m)^[WB]:W[^\n]*:B[^\n]*$", run.stdout)
    if ([side for side, _ in probes] != [state.turn for state in states]
            or echoed != fens):
        raise ValueError(f"Incomplete or misordered bitbase probes: {probes}")
    with Scan(binary, depth=18) as scan:
        moves = {
            move: {"successor": state_to_fen(state), "result_for_black": INVERT[result],
                   "scan_depth18": load_position_scores(scan, state)}
            for (move, state), (_, result) in zip(successors.items(), probes[1:], strict=True)
        }
    root_result = probes[0][1]
    if root_result != max((row["result_for_black"] for row in moves.values()),
                          key=("loss", "draw", "win").index):
        raise ValueError("Root bitbase result differs from its best legal successor")
    return {"fen": FEN, "result_for_black": root_result, "moves": moves,
            "scan_binary_sha256": SCAN_SHA256, "bitbase_url": TABLE_URL,
            "bitbase_archive_sha256": archive_digest,
            "bitbase_ini_sha256": sha256(table_binary.parent / "scan.ini")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("scan", "table-scan", "archive", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.scan, args.table_scan, args.archive))


if __name__ == "__main__":
    main()
