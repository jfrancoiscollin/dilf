"""Strict adapter for opt-in, hard-capped first-root Jass probe receipts.

This does not supply moves from Scan or archive, and never treats an
interrupted/failed-bound result as a completed exact-score verification.
The binary must be built from the pinned disposable Jass checkout patched
with research/mtdp/jass_preflight/first-root-action.patch.
"""

import os
import subprocess
from pathlib import Path
from collections.abc import Sequence

SCHEMA = "mtdp-probe-v1"
INF_SCORE = 31_000
MODES = ("preliminary", "probe")


def parse_receipt(raw: str, *, mode: str, fen: str, issued_limit: int,
                  requested_move: str | None = None,
                  expected_legal_order: Sequence[str] | None = None) -> dict:
    """Reject malformed, unmetered, illegal or inflated first-root receipts."""
    if mode not in MODES or type(issued_limit) is not int or issued_limit <= 0:
        raise ValueError("Invalid issued metered search")
    if mode == "probe" and (not isinstance(requested_move, str) or not requested_move):
        raise ValueError("Probe requires a requested move")
    if mode == "preliminary" and requested_move is not None:
        raise ValueError("Preliminary receipt must not supply one probe move")
    rows = raw.splitlines()
    if len(rows) != 1:
        raise ValueError("Expected exactly one metered Jass receipt")
    parts = rows[0].split("\t")
    if len(parts) != 15:
        raise ValueError("Malformed metered Jass receipt")
    (schema, got_mode, got_fen, got_limit, nodes_text, complete_text, move,
     score_text, alpha_text, beta_text, bound, stop, visited_text,
     legal_count_text, native_csv) = parts
    if (schema != SCHEMA or got_mode != mode or got_fen != fen):
        raise ValueError("Metered receipt identity mismatch")
    try:
        limit, nodes, score, alpha, beta, visited, legal_count = map(
            int, (got_limit, nodes_text, score_text, alpha_text, beta_text,
                  visited_text, legal_count_text))
    except ValueError as error:
        raise ValueError("Metered receipt has a noninteger field") from error
    if (limit != issued_limit or nodes < 0 or nodes > limit
            or visited < 0 or legal_count <= 0 or visited > legal_count):
        raise ValueError("Invalid metered node or action accounting")
    if complete_text not in ("0", "1") or bound not in ("exact", "lower", "upper", "none") \
            or stop not in ("nodes", "none"):
        raise ValueError("Invalid completion, stop or bound evidence")
    native = native_csv.split(",")
    if (len(native) != legal_count or any(not key for key in native)
            or len(set(native)) != len(native)):
        raise ValueError("Invalid live native legal catalogue")
    if expected_legal_order is not None and tuple(native) != tuple(expected_legal_order):
        raise ValueError("Live legal order differs from frozen current position")
    complete = complete_text == "1"
    if mode == "probe":
        if requested_move not in native or move != requested_move or visited > 1:
            raise ValueError("Probe action differs from requested legal action")
        if complete and visited != 1:
            raise ValueError("Completed probe must visit exactly one root action")
    elif complete and (visited != legal_count or move not in native):
        raise ValueError("Completed preliminary attempt did not cover legal actions")
    elif not complete and move != "-":
        raise ValueError("Incomplete preliminary attempt cannot certify a winner")
    if complete and (nodes == 0 or stop != "none" or bound != "exact"
                     or alpha != -INF_SCORE or beta != INF_SCORE
                     or not alpha < score < beta):
        raise ValueError("Completed root receipt lacks independent full-window exactness")

    receipt = {
        "nodes": nodes, "completed": complete,
        "score": score if complete else None,
        "alpha_before": alpha, "beta": beta,
        "native_order": native,
        "stop": stop, "bound": bound,
        "visited": visited, "legal_count": legal_count,
    }
    if mode == "probe":
        receipt["move"] = move
    else:
        receipt["winner"] = move if complete else None
    return receipt


def run_depth_one(binary: Path, fen: str, *, mode: str,
                  limit: int, prefix: Sequence[str] = (),
                  expected_legal_order: Sequence[str] | None = None) -> dict:
    """Perform one engine call with hard node cap and a fresh search table."""
    if (mode not in MODES or type(limit) is not int or limit <= 0
            or not fen or any(not isinstance(m, str) or not m for m in prefix)
            or (mode == "probe" and len(prefix) != 1)):
        raise ValueError("Invalid metered Jass invocation")
    # Never allow an archived retrospective intervention or external tablebase
    # configuration to influence this controlled research arm.
    env = {k: v for k, v in os.environ.items() if k not in
           ("MTDP_DEPTH_ONE_WINNER", "JASS_EGDB_PATH", "JASS_EGDB_MTC_PATH")}
    env["JASS_TRACE_ROOT"] = "0"
    payload = " ".join([mode, fen, str(limit), *prefix]) + "\n"
    result = subprocess.run([str(binary.resolve())], input=payload, text=True,
                            capture_output=True, check=True, env=env)
    return parse_receipt(result.stdout, mode=mode, fen=fen, issued_limit=limit,
                         requested_move=prefix[0] if mode == "probe" else None,
                         expected_legal_order=expected_legal_order)
