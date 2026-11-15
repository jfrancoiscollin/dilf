"""End-to-end *engineering smoke* for the metered MTDP Jass control.

Two disposable binaries based on the SAME pinned Jass revision are required:
- the first-root research probe (first-root-action.patch);
- the initial-only search with retrospective winner intervention patches.
No Scan reference or archived winner enters the selector. A standard opening
position is diagnostic only, never a substitute for prospective cohort scoring.
"""

import argparse
import os
import subprocess
from pathlib import Path
from collections.abc import Sequence

from research.mtdp.jass_benchmark.metered_control import execute
from research.mtdp.jass_benchmark.metered_probe_adapter import run_depth_one
from research.mtdp.jass_benchmark.total_budget import verification_cap


def _position_identity(fen: str) -> tuple:
    """Canonical FMJD piece identity, independent of king/list ordering.

    Jass serializes men before kings, whereas frozen PDNs may put a king
    first. This accepts formatting differences ONLY when every exact side,
    occupied square and man/king identity matches.
    """
    fields = fen.split(":")
    if len(fields) != 3 or fields[0] not in ("W", "B"):
        raise ValueError("Invalid metered position FEN")
    pieces = []
    occupied = set()
    for tag, field in zip(("W", "B"), fields[1:], strict=True):
        if not field.startswith(tag):
            raise ValueError("Invalid metered FEN colour order")
        parsed = []
        for token in (field[1:].split(",") if len(field) > 1 else []):
            king = token.startswith("K")
            square_text = token[1:] if king else token
            if (not square_text.isdigit() or str(int(square_text)) != square_text):
                raise ValueError("Invalid metered FEN square")
            square = int(square_text)
            if square < 1 or square > 50 or square in occupied:
                raise ValueError("Duplicate or out-of-range metered FEN square")
            occupied.add(square)
            parsed.append((square, king))
        pieces.append(tuple(sorted(parsed)))
    return fields[0], *pieces


def main_search(binary: Path, fen: str, prefix: Sequence[str],
                forced: str | None, limit: int, native_order: Sequence[str]) -> dict:
    if type(limit) is not int or limit <= 0:
        raise ValueError("Main search requires a positive residual limit")
    env = {k: v for k, v in os.environ.items() if k not in (
        "MTDP_DEPTH_ONE_WINNER", "JASS_EGDB_PATH", "JASS_EGDB_MTC_PATH",
    )}
    env["JASS_TRACE_ROOT"] = "0"
    if forced is not None:
        if forced not in native_order:
            raise ValueError("Forced winner is not a live legal action")
        env["MTDP_DEPTH_ONE_WINNER"] = forced
    line = " ".join([fen, str(limit), *prefix]) + "\n"
    run = subprocess.run([str(binary.resolve()), "--initial-only", "--record-depth-ceiling"],
                         input=line, text=True, capture_output=True, check=True, env=env)
    rows = run.stdout.splitlines()
    if len(rows) != 1:
        raise ValueError("Main Jass runner returned multiple or missing receipts")
    values = rows[0].split("\t")
    if len(values) < 12 or _position_identity(values[0]) != _position_identity(fen):
        observed = values[0] if values else None
        raise ValueError(
            f"Malformed main Jass root receipt: requested={fen!r} "
            f"observed={observed!r} fields={len(values)} "
            f"raw_prefix={rows[0][:150]!r}"
        )
    try:
        issued, nodes, completed_depth = map(int, values[1:4])
    except ValueError as error:
        raise ValueError("Noninteger main Jass receipt") from error
    reason = values[4]
    legal = values[9].split(",")
    order = values[10].split(",")
    if issued != limit or nodes < 0 or nodes > limit or reason not in (
        "nodes", "depth_ceiling",
    ):
        raise ValueError("Invalid Jass main search budget or stop reason")
    if (legal != list(native_order) or set(order) != set(legal)
            or len(order) != len(set(order)) or order[:len(prefix)] != list(prefix)):
        raise ValueError("Main Jass root catalogue or LCB prefix differs")
    if not values[11].startswith("1:") or completed_depth < 1:
        raise ValueError("Main Jass search did not complete the first depth")
    if forced is not None and forced not in legal:
        raise ValueError("Main Jass forced an illegal move")
    if values[5] not in legal:
        raise ValueError("Main Jass returned a best move outside the legal catalogue")
    return {"nodes": nodes, "depth_ceiling": reason == "depth_ceiling",
            "best_move": values[5], "score": int(values[6]),
            "completed_depth": completed_depth, "stop": reason}


def technical_smoke(probe_binary: Path, main_binary: Path,
                    fen: str, *, total_nodes: int, prefix: Sequence[str]) -> dict:
    """Meter one current-position verification and actual remaining-budget search."""
    cap = verification_cap(total_nodes)
    if cap == 0:
        raise ValueError("Technical smoke requires positive verification allowance")
    initial = run_depth_one(probe_binary, fen, mode="preliminary", limit=cap,
                            prefix=prefix)
    native = initial["native_order"]
    if any(key not in native for key in prefix) or len(set(prefix)) != len(prefix):
        raise ValueError("Prefix differs from the live legal order")
    def preliminary(limit):
        if limit != cap:
            raise ValueError("Preliminary receipt issued for different cap")
        # This is the fresh, actual preliminary execution above; no replay and
        # no archived receipt. execute charges its measured nodes exactly once.
        return initial
    def probe(move, limit):
        return run_depth_one(probe_binary, fen, mode="probe", limit=limit,
                             prefix=[move], expected_legal_order=native)
    controlled_main_receipt = {}
    def main(forced, limit):
        receipt = main_search(main_binary, fen, prefix, forced, limit, native)
        controlled_main_receipt.update(receipt)
        return receipt
    report = execute(total_nodes=total_nodes, native_order=native,
                     preliminary=preliminary, probe=probe, main=main)
    # Paired equal-total-node controls: fresh independent searches, not
    # another intervention or additional nodes charged to the treatment.
    baseline_native = main_search(main_binary, fen, [], None, total_nodes, native)
    baseline_lcb = main_search(main_binary, fen, prefix, None, total_nodes, native)
    complete_controls = (
        not baseline_native["depth_ceiling"] and baseline_native["nodes"] == total_nodes
        and not baseline_lcb["depth_ceiling"] and baseline_lcb["nodes"] == total_nodes
    )
    return {**report, "native_legal_actions": len(native),
            "preliminary_nodes": initial["nodes"],
            "control_main": controlled_main_receipt,
            "native_baseline": baseline_native, "lcb_baseline": baseline_lcb,
            "paired_comparable": report["complete_budget"] and complete_controls,
            "scope": "technical_engineering_smoke_not_strength_evidence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-runner", type=Path, required=True)
    parser.add_argument("--main-runner", type=Path, required=True)
    parser.add_argument("--fen", required=True)
    parser.add_argument("--total-nodes", type=int, required=True)
    parser.add_argument("--prefix", nargs="*", default=[])
    args = parser.parse_args()
    import json
    print(json.dumps(technical_smoke(args.probe_runner, args.main_runner,
                    args.fen, total_nodes=args.total_nodes, prefix=args.prefix),
                    sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
