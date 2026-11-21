"""Check the native disagreements covered by Scan's six-piece bitbases."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from pedagogy.game import notation, parse_fen, state_to_fen
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


def verify_scan(engine):
    if sha256(engine) != SCAN_SHA256 or sha256(engine.parent / "data/eval") != SCAN_EVAL_SHA256:
        raise ValueError(f"Scan binary or evaluation file does not match the pinned build: {engine}")


def verify_archive(archive):
    with archive.open("rb") as stream:
        archive_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_digest != TABLE_SHA256:
        raise ValueError("Bitbase archive differs from the recorded download")
    return archive_digest


def legal_successors(rules, root):
    moves = rules.legal_moves(root)
    successors = {notation(move): rules.apply_move(root, move) for move in moves}
    if len(successors) != len(moves) or any(move.is_capture for move in moves):
        raise ValueError("Expected unambiguous quiet root moves")
    return successors


def probe(table_binary, states):
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
    return [result for _, result in probes]


def analyze(binary, table_binary, archive):
    binary, table_binary = binary.resolve(), table_binary.resolve()
    for engine in (binary, table_binary):
        verify_scan(engine)
    archive_digest = verify_archive(archive)
    root = parse_fen(FEN)
    successors = legal_successors(create_engine(), root)
    root_result, *probes = probe(table_binary, [root, *successors.values()])
    with Scan(binary, depth=18) as scan:
        moves = {
            move: {"successor": state_to_fen(state), "result_for_black": INVERT[result],
                   "scan_depth18": load_position_scores(scan, state)}
            for (move, state), result in zip(successors.items(), probes, strict=True)
        }
    if root_result != max((row["result_for_black"] for row in moves.values()),
                          key=("loss", "draw", "win").index):
        raise ValueError("Root bitbase result differs from its best legal successor")
    return {"fen": FEN, "result_for_black": root_result, "moves": moves,
            "scan_binary_sha256": SCAN_SHA256, "bitbase_url": TABLE_URL,
            "bitbase_archive_sha256": archive_digest,
            "bitbase_ini_sha256": sha256(table_binary.parent / "scan.ini")}


def audit_disagreements(reference, table_binary, archive):
    table_binary = table_binary.resolve()
    verify_scan(table_binary)
    archive_digest = verify_archive(archive)
    summary = json.loads(reference.read_bytes())
    if summary["budget"] != 50_000:
        raise ValueError("Expected the 50,000-node disagreement receipt")
    rules = create_engine()
    positions, states = [], []
    for row in summary["positions"]:
        root = parse_fen(row["fen"])
        pieces = sum(map(len, (root.white_men, root.black_men, root.white_kings, root.black_kings)))
        if pieces > 6:
            continue
        successors = legal_successors(rules, root)
        choices = {arm: row["arms"][arm]["move"] for arm in ("LCB", "native")}
        if choices["LCB"] == choices["native"]:
            raise ValueError(f"Expected different archived choices: {row['fen']}")
        positions.append((row, root, pieces, successors, choices))
        states.extend((root, *successors.values()))

    results = iter(probe(table_binary, states))
    output = []
    for row, root, pieces, successors, choices in positions:
        root_result = next(results)
        moves = {move: {"successor": state_to_fen(state), "result_for_mover": INVERT[next(results)]}
                 for move, state in successors.items()}
        if root_result != max((move["result_for_mover"] for move in moves.values()),
                              key=("loss", "draw", "win").index):
            raise ValueError(f"Root result differs from its best successor: {row['fen']}")
        output.append({
            "arena": row["arena"], "fen": row["fen"], "pieces": pieces, "mover": root.turn,
            "result_for_mover": root_result, "legal_moves": moves, "choices": choices,
            "different_theoretical_outcome": (
                moves[choices["LCB"]]["result_for_mover"] != moves[choices["native"]]["result_for_mover"]
            ),
        })
    return {"reference_sha256": sha256(reference), "budget": summary["budget"],
            "total_disagreements": len(summary["positions"]), "positions": output,
            "scan_binary_sha256": SCAN_SHA256, "bitbase_url": TABLE_URL,
            "bitbase_archive_sha256": archive_digest,
            "bitbase_ini_sha256": sha256(table_binary.parent / "scan.ini")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--scan", type=Path)
    sources.add_argument("--disagreements", type=Path)
    for name in ("table-scan", "archive", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if args.disagreements:
        report = audit_disagreements(args.disagreements, args.table_scan, args.archive)
    else:
        report = analyze(args.scan, args.table_scan, args.archive)
    write_json(args.output, report)


if __name__ == "__main__":
    main()
