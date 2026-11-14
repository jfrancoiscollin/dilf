"""Tests for retrospective probe-cost feasibility reporting."""

import pytest

from research.mtdp.jass_benchmark.prospective_cost_audit import audit


def receipt(event, fen, probe, auxiliary, budget=50_000):
    return {"event": event, "fen": fen, "budget": budget,
            "probe_depth_one_nodes": probe, "auxiliary_nodes": auxiliary}


def test_costs_are_not_pooled_across_positions():
    result = audit({"positions": [
        receipt("a", "one", 100, 5_100),
        receipt("a", "two", 5_001, 5_001),
    ]}, 50_000)
    assert result["depth_one_probe_lower_bound"]["positions_over_cap"] == 1
    assert result["full_historical_auxiliary_cost"]["positions_over_cap"] == 2
    assert result["depth_one_probe_lower_bound"]["measured_verification_nodes"] == 5_101


@pytest.mark.parametrize("rows", [
    [], [receipt("a", "x", 1, 2), receipt("a", "x", 1, 2)],
    [receipt("a", "x", 5, 4)], [receipt("a", "x", -1, 4)],
    [receipt("a", "x", 1, True)],
])
def test_missing_duplicate_or_invalid_receipts_rejected(rows):
    with pytest.raises(ValueError):
        audit({"positions": rows}, 50_000)


def test_only_requested_budget_is_used():
    result = audit({"positions": [
        receipt("a", "one", 100, 200),
        receipt("a", "one", 200, 300, budget=10_000),
    ]}, 10_000)
    assert result["depth_one_probe_lower_bound"]["positions"] == 1
    assert result["depth_one_probe_lower_bound"]["measured_verification_nodes"] == 200
