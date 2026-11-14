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
    if not depth_ceiling and main_nodes != main_limit:
        raise ValueError("Non-ceiling replay did not exhaust its allocated budget")
    if type(depth_ceiling) is not bool:
        raise ValueError("Depth-ceiling flag must be boolean")
    return not depth_ceiling
