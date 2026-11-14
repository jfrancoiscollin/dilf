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


def test_partial_frozen_cohort_rejected():
    with pytest.raises(ValueError, match="Incomplete frozen cohort"):
        audit({"positions": [receipt("a", "one", 100, 200)]},
              50_000, expected_positions=473)


def test_complete_frozen_cohort_accepted():
    result = audit({"positions": [receipt("a", str(i), 100, 200)
                                   for i in range(473)]},
                   50_000, expected_positions=473)
    assert result["depth_one_probe_lower_bound"]["positions"] == 473


@pytest.mark.parametrize("expected", [0, -1, True, 1.5])
def test_invalid_frozen_cohort_size_rejected(expected):
    with pytest.raises(ValueError, match="Expected cohort size"):
        audit({"positions": [receipt("a", "one", 100, 200)]},
              50_000, expected_positions=expected)


@pytest.mark.parametrize("probe", [True, 1.5, "4", None, -1])
def test_invalid_probe_cost_rejected_with_clear_error(probe):
    with pytest.raises(ValueError, match="Invalid depth-one probe node cost"):
        audit({"positions": [receipt("a", "one", probe, 10)]},
              50_000, expected_positions=1)


def test_per_arena_costs_are_separate_and_sum_to_cohort():
    result = audit({"positions": [
        receipt("west", "one", 5_100, 6_000),
        receipt("east", "two", 100, 5_500),
        receipt("east", "three", 200, 300),
    ]}, 50_000, expected_positions=3)
    by_arena = result["by_arena"]
    assert list(by_arena) == ["east", "west"]
    assert by_arena["west"]["depth_one_probe_lower_bound"]["positions_over_cap"] == 1
    assert by_arena["east"]["depth_one_probe_lower_bound"]["positions_over_cap"] == 0
    assert by_arena["east"]["full_historical_auxiliary_cost"]["positions_over_cap"] == 1
    assert sum(item["depth_one_probe_lower_bound"]["measured_verification_nodes"]
               for item in by_arena.values()) == result["depth_one_probe_lower_bound"]["measured_verification_nodes"]
