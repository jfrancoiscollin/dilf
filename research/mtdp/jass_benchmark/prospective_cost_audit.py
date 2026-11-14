"""Retrospective verification-cost audit; never claims an equal-compute run."""

import argparse
import gzip
import json
from pathlib import Path

from research.mtdp.jass_benchmark.total_budget import aggregate_feasibility


def audit(report: dict, budget: int, *, expected_positions: int | None = None) -> dict:
    """Audit independently metered depth-one probe costs on frozen positions.

    These costs are a *lower bound* on the old auxiliary verification work,
    not a measurement of a future capped or short-circuited runner.
    """
    if type(budget) is not int or budget <= 0:
        raise ValueError("Budget must be a positive integer")
    rows = report["positions"]
    if any(type(row["budget"]) is not int or row["budget"] <= 0 for row in rows):
        raise ValueError("Invalid receipt budget")
    selected = [row for row in rows if row["budget"] == budget]
    if any(not isinstance(row["event"], str) or not row["event"]
           or not isinstance(row["fen"], str) or not row["fen"]
           for row in selected):
        raise ValueError("Invalid receipt position identity")
    keys = [(row["event"], row["fen"]) for row in selected]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate position receipts")
    if not selected:
        raise ValueError("No receipts for requested budget")
    if expected_positions is not None:
        if type(expected_positions) is not int or expected_positions <= 0:
            raise ValueError("Expected cohort size must be a positive integer")
        if len(selected) != expected_positions:
            raise ValueError("Incomplete frozen cohort for requested budget")
    costs = [row["probe_depth_one_nodes"] for row in selected]
    auxiliary = [row["auxiliary_nodes"] for row in selected]
    if any(type(n) is not int or n < 0 for n in costs):
        raise ValueError("Invalid depth-one probe node cost")
    if any(type(n) is not int or n < 0 for n in auxiliary):
        raise ValueError("Invalid auxiliary node cost")
    if any(probe > total for probe, total in zip(costs, auxiliary, strict=True)):
        raise ValueError("Depth-one probes exceed metered auxiliary cost")
    lower = aggregate_feasibility(budget, costs)
    full = aggregate_feasibility(budget, auxiliary)
    # A probe-only overrun proves the historical full-probe method cannot fit.
    # A probe-only fit does NOT establish that a future capped runner will fit.
    proven_over_cap = lower["positions_over_cap"]
    arenas = {}
    for event in sorted({row["event"] for row in selected}):
        group = [row for row in selected if row["event"] == event]
        arenas[event] = {
            "depth_one_probe_lower_bound": aggregate_feasibility(
                budget, [row["probe_depth_one_nodes"] for row in group]),
            "full_historical_auxiliary_cost": aggregate_feasibility(
                budget, [row["auxiliary_nodes"] for row in group]),
        }
    return {
        "budget": budget,
        "depth_one_probe_lower_bound": lower,
        "full_historical_auxiliary_cost": full,
        "by_arena": arenas,
        "historical_full_probe_method": {
            "provably_over_cap_from_depth_one": proven_over_cap,
            "not_ruled_out_by_depth_one": len(selected) - proven_over_cap,
            "equal_compute_success_established": False,
        },
        "interpretation": (
            "Retrospective audit only: depth-one probe nodes are a lower bound; "
            "historical full-search auxiliary nodes are not a capped-run measurement; "
            "positions below the depth-one lower-bound cap remain inconclusive."
        ),
    }



def audit_cohort_alignment(report: dict, budgets: tuple[int, ...] = (10_000, 50_000, 200_000),
                           *, expected_positions: int = 473) -> dict:
    """Require identical frozen (event, FEN) identities at every budget.

    This is an archive-integrity check, not an equal-compute comparison.
    """
    if not budgets or any(type(b) is not int or b <= 0 for b in budgets):
        raise ValueError("Invalid comparison budgets")
    if len(set(budgets)) != len(budgets):
        raise ValueError("Duplicate comparison budgets")
    cohorts = {}
    for budget in budgets:
        audit(report, budget, expected_positions=expected_positions)
        cohorts[budget] = {(row["event"], row["fen"])
                           for row in report["positions"] if row["budget"] == budget}
    reference = cohorts[budgets[0]]
    for budget in budgets[1:]:
        if cohorts[budget] != reference:
            raise ValueError("Frozen cohort identities differ between budgets")
    return {"budgets": list(budgets), "aligned_positions": len(reference),
            "identical_frozen_cohorts": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--budget", required=True, type=int)
    parser.add_argument("--expected-positions", required=True, type=int,
                        help="Frozen cohort size; reject partial archives")
    parser.add_argument("--check-alignment", action="store_true",
                        help="Require identical frozen cohorts across the three standard budgets")
    args = parser.parse_args()
    with gzip.open(args.report, "rt", encoding="utf-8") as stream:
        report = json.load(stream)
    result = audit(report, args.budget, expected_positions=args.expected_positions)
    if args.check_alignment:
        result["cohort_alignment"] = audit_cohort_alignment(
            report, expected_positions=args.expected_positions)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
