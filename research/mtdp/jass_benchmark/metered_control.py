"""Outcome-blind node-metered protocol for the MTDP tie-break experiment.

This is a runner-independent execution contract, not a Jass integration.
Callbacks must use fresh transposition tables, independent full-window
first-root probes, and genuine node counts. No archived winner or Scan
score is accepted by this interface. It does not claim playing-strength gain.
"""

from collections.abc import Callable, Sequence
from typing import Any

from research.mtdp.jass_benchmark.total_budget import (
    next_probe_limit, record_probe_nodes, verify_receipt,
)
from research.mtdp.jass_benchmark.prospective_tiebreak import choose_native_order_tie


def _integer(value: Any) -> bool:
    return type(value) is int


def _window_exact(receipt: dict, move: str, window: tuple[int, int]) -> bool:
    """Treat only a completed, first-root, in-window score as exact."""
    a, b = window
    return (
        receipt.get("move") == move
        and type(receipt.get("completed")) is bool
        and receipt["completed"]
        and _integer(receipt.get("score"))
        and receipt.get("alpha_before") == a
        and receipt.get("beta") == b
        and a < receipt["score"] < b
    )


def execute(
    *, total_nodes: int, native_order: Sequence[str],
    preliminary: Callable[[int], dict],
    probe: Callable[[str, int], dict],
    main: Callable[[str | None, int], dict],
) -> dict:
    """Meter verification and use all unspent nodes in the final replay.

    The None intervention means retain the native LCB winner. ``preliminary``
    and ``probe`` receive a hard per-call node limit. ``main`` receives the
    exact remaining node limit, including on every verification fallback.
    The callbacks own their engine search and fresh-table guarantees.
    """
    order = tuple(native_order)
    if (not order or any(not isinstance(key, str) or not key for key in order)
            or len(set(order)) != len(order)):
        raise ValueError("Native legal order must contain unique nonempty keys")

    spent, reason, chosen, receipts = 0, "verification_budget_exhausted", None, []
    limit = next_probe_limit(total_nodes, spent)
    if limit:
        first = preliminary(limit)
        if not isinstance(first, dict):
            raise ValueError("Invalid preliminary receipt")
        spent = record_probe_nodes(total_nodes, spent, limit, first.get("nodes"))
        receipts.append({"phase": "preliminary", "issued_limit": limit, "nodes": first["nodes"]})
        if first.get("completed") is True and first["nodes"] == 0:
            raise ValueError("Completed preliminary search cannot have zero metered nodes")
        if first.get("completed") is not True:
            # A capped preliminary call may stop before identifying any winner.
            reason = "preliminary_incomplete_or_bounded"
        else:
            winner, best_score = first.get("winner"), first.get("score")
            a, b = first.get("alpha_before"), first.get("beta")
            if (winner not in order or not _integer(best_score)
                    or not _integer(a) or not _integer(b) or a >= b):
                raise ValueError("Invalid completed preliminary winner or window")
            window = a, b
            if not a < best_score < b:
                reason = "preliminary_incomplete_or_bounded"
            else:
                scores = {}
                reason = "verification_budget_exhausted"
                for move in order:
                    limit = next_probe_limit(total_nodes, spent)
                    if not limit:
                        break
                    result = probe(move, limit)
                    if not isinstance(result, dict):
                        raise ValueError("Invalid probe receipt")
                    spent = record_probe_nodes(total_nodes, spent, limit, result.get("nodes"))
                    receipts.append({"phase": "probe", "move": move, "issued_limit": limit,
                                     "nodes": result["nodes"]})
                    if result.get("completed") is True and result["nodes"] == 0:
                        raise ValueError("Completed probe cannot have zero metered nodes")
                    if not _window_exact(result, move, window):
                        reason = "probe_incomplete_or_bounded"
                        break
                    scores[move] = result["score"]
                else:
                    if max(scores.values()) != best_score or scores[winner] != best_score:
                        reason = "inconsistent_exact_scores"
                    else:
                        selected = choose_native_order_tie(
                            order, scores, completed={m: True for m in order},
                            exact={m: True for m in order}, lcb_winner=winner,
                        )
                        chosen = selected if selected != winner else None
                        ties = sum(value == best_score for value in scores.values()) > 1
                        reason = ("verified_tie" if chosen else
                                  "verified_tie_same_winner" if ties else "verified_unique_best")
    # No verification after the first missing, incomplete, or bounded receipt.
    final_limit = total_nodes - spent
    result = main(chosen, final_limit)
    if not isinstance(result, dict):
        raise ValueError("Invalid main receipt")
    depth_ceiling = result.get("depth_ceiling")
    complete = verify_receipt(total_nodes, spent, result.get("nodes"),
                              depth_ceiling=depth_ceiling)
    if depth_ceiling and result["nodes"] == final_limit:
        raise ValueError("Depth ceiling cannot claim an exhausted node budget")
    return {
        "total_nodes": total_nodes, "verification_nodes": spent,
        "main_nodes": result["nodes"], "main_limit": final_limit,
        "complete_budget": complete, "fallback_reason": None if reason.startswith("verified_") else reason,
        "decision_reason": reason, "intervention": chosen, "verification_receipts": receipts,
    }
