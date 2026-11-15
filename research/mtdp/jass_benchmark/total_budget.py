"""Fail-closed node accounting for the preregistered equal-compute control.

This module does not run Jass; callers must meter actual nodes returned by
each invocation and never substitute requested limits for measured usage.
"""


def verification_cap(total_nodes: int) -> int:
    """Maximum nodes available to preliminary search and exact-score probes."""
    if type(total_nodes) is not int or total_nodes <= 0:
        raise ValueError("Total node budget must be a positive integer")
    return total_nodes // 10


def next_probe_limit(total_nodes: int, spent_verification: int) -> int:
    """Remaining verification allowance; zero means fail closed to LCB."""
    cap = verification_cap(total_nodes)
    if (type(spent_verification) is not int or spent_verification < 0
            or spent_verification > cap):
        raise ValueError("Invalid metered verification node count")
    return cap - spent_verification


def main_search_limit(total_nodes: int, spent_verification: int) -> int:
    """Node budget for a fresh-table main search, including fallback."""
    next_probe_limit(total_nodes, spent_verification)
    return total_nodes - spent_verification


def verify_receipt(total_nodes: int, verification_nodes: int,
                   main_nodes: int, *, depth_ceiling: bool = False) -> bool:
    """Check metered accounting; False means a documented ceiling exception."""
    main_limit = main_search_limit(total_nodes, verification_nodes)
    if type(main_nodes) is not int or main_nodes < 0 or main_nodes > main_limit:
        raise ValueError("Invalid metered main-search node count")
    if type(depth_ceiling) is not bool:
        raise ValueError("Depth-ceiling flag must be boolean")
    if not depth_ceiling and main_nodes != main_limit:
        raise ValueError("Non-ceiling replay did not exhaust its allocated budget")
    return not depth_ceiling


def aggregate_feasibility(total_nodes: int, verification_nodes: list[int]) -> dict[str, int | bool]:
    """Audit a frozen cohort's metered verification cost, without rerunning Jass.

    Aggregate feasibility is necessary but not sufficient: each position must
    independently fit its own cap; surplus from another position is not pooled.
    """
    cap = verification_cap(total_nodes)
    if not verification_nodes:
        raise ValueError("Cannot establish cohort feasibility from an empty cohort")
    if any(type(nodes) is not int or nodes < 0 for nodes in verification_nodes):
        raise ValueError("Invalid metered verification nodes")
    over_cap = sum(nodes > cap for nodes in verification_nodes)
    return {
        "positions": len(verification_nodes),
        "per_position_cap": cap,
        "aggregate_cap": cap * len(verification_nodes),
        "measured_verification_nodes": sum(verification_nodes),
        "positions_over_cap": over_cap,
        "all_positions_fit": over_cap == 0,
    }


def capped_probe_limit(total_nodes: int, spent_verification: int,
                       requested_nodes: int) -> int:
    """Bound a proposed probe by the remaining verification allowance.

    Zero means the caller must skip the probe and use the preregistered
    fallback. This is a *request* limit, not a measured-node receipt.
    """
    remaining = next_probe_limit(total_nodes, spent_verification)
    if type(requested_nodes) is not int or requested_nodes < 0:
        raise ValueError("Requested probe nodes must be a nonnegative integer")
    return min(remaining, requested_nodes)


def record_probe_nodes(total_nodes: int, spent_verification: int,
                       requested_limit: int, measured_nodes: int) -> int:
    """Accept only an actual metered receipt within the issued probe limit.

    Never substitute the requested limit for measured usage. Fail closed if
    the engine reports more nodes than permitted by either bound.
    """
    allowed = capped_probe_limit(total_nodes, spent_verification, requested_limit)
    # Zero is a skip/fallback sentinel, never a valid engine invocation.
    # Otherwise a fabricated (0, 0) receipt could count as a probe.
    if requested_limit == 0:
        raise ValueError("Zero-node probe must be skipped, not recorded")
    # An issued engine limit must already be capped by the caller. Silently
    # clipping it here would validate a receipt from an over-budget invocation.
    if requested_limit > allowed:
        raise ValueError("Issued probe limit exceeds remaining verification allowance")
    if (type(measured_nodes) is not int or measured_nodes < 0
            or measured_nodes > allowed):
        raise ValueError("Probe receipt exceeds issued limit or is invalid")
    return spent_verification + measured_nodes


def audit_probe_sequence(total_nodes: int,
                         probes: list[tuple[int, int]]) -> dict[str, int]:
    """Replay ordered (issued_limit, measured_nodes) receipts without Jass.

    Each receipt is checked against the *remaining* 10% allowance, so a
    previously valid standalone probe cannot be reused after the cap is spent.
    The result is an accounting audit, not evidence of engine execution.
    """
    spent = 0
    if type(probes) is not list:
        raise ValueError("Probe sequence must be a list")
    for receipt in probes:
        if (type(receipt) is not tuple or len(receipt) != 2):
            raise ValueError("Each probe receipt must be a (limit, nodes) tuple")
        issued, measured = receipt
        spent = record_probe_nodes(total_nodes, spent, issued, measured)
    return {
        "probe_count": len(probes),
        "verification_nodes": spent,
        "verification_remaining": next_probe_limit(total_nodes, spent),
        "main_search_limit": main_search_limit(total_nodes, spent),
    }


def audit_complete_search(total_nodes: int, probes: list[tuple[int, int]],
                          main_nodes: int, *,
                          depth_ceiling: bool = False) -> dict[str, int | bool]:
    """Reconcile ordered verification receipts with a metered main search.

    This is a post-run audit only; it does not invoke an engine. A complete
    non-ceiling replay must consume the full position budget. Ceiling-limited
    replays are explicitly marked non-comparable rather than silently passed.
    """
    verification = audit_probe_sequence(total_nodes, probes)
    comparable = verify_receipt(
        total_nodes, verification["verification_nodes"], main_nodes,
        depth_ceiling=depth_ceiling,
    )
    return {
        **verification,
        "main_nodes": main_nodes,
        "total_measured_nodes": verification["verification_nodes"] + main_nodes,
        "comparable": comparable,
    }


def audit_paired_searches(
    total_nodes: int,
    baseline: dict[str, dict[str, int | bool]],
    treatment: dict[str, dict[str, int | bool]],
) -> dict[str, int | bool]:
    """Check paired, equal-compute receipts without inferring playing strength.

    Keys are frozen position identifiers (for example arena plus FEN).
    Each arm must contain exactly the same unique positions, and every receipt
    must have been independently audited with audit_complete_search.
    """
    verification_cap(total_nodes)
    if (type(baseline) is not dict or type(treatment) is not dict
            or not baseline or baseline.keys() != treatment.keys()):
        raise ValueError("Paired cohorts must have identical nonempty position IDs")
    if any(type(key) is not str or not key for key in baseline):
        raise ValueError("Position IDs must be nonempty strings")
    for arm in (baseline, treatment):
        for receipt in arm.values():
            if type(receipt) is not dict:
                raise ValueError("Invalid search receipt")
            nodes = receipt.get("total_measured_nodes")
            comparable = receipt.get("comparable")
            if (type(nodes) is not int or nodes < 0 or nodes > total_nodes
                    or type(comparable) is not bool):
                raise ValueError("Invalid search receipt")
            if comparable and nodes != total_nodes:
                raise ValueError("Comparable receipt must exhaust position budget")
    paired = sum(baseline[key]["comparable"] and treatment[key]["comparable"]
                 for key in baseline)
    return {
        "positions": len(baseline),
        "paired_comparable": paired,
        "paired_excluded": len(baseline) - paired,
        "all_pairs_comparable": paired == len(baseline),
    }
