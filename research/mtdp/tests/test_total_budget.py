"""Unit tests for total-budget verification and main-search accounting."""

import pytest

from research.mtdp.jass_benchmark.total_budget import (
    main_search_limit, next_probe_limit, verification_cap, verify_receipt,
)


@pytest.mark.parametrize("budget,cap", [(10_000, 1_000), (50_000, 5_000),
                                        (200_000, 20_000), (9, 0)])
def test_verification_cap(budget, cap):
    assert verification_cap(budget) == cap


def test_main_search_uses_all_unspent_nodes_even_on_fallback():
    assert next_probe_limit(50_000, 1_500) == 3_500
    assert main_search_limit(50_000, 1_500) == 48_500
    assert verify_receipt(50_000, 1_500, 48_500)


@pytest.mark.parametrize("spent", [-1, 5_001, 1.5, True])
def test_invalid_verification_accounting_rejected(spent):
    with pytest.raises(ValueError):
        next_probe_limit(50_000, spent)


@pytest.mark.parametrize("budget", [0, -1, 1.0, True])
def test_invalid_total_budget_rejected(budget):
    with pytest.raises(ValueError):
        verification_cap(budget)


def test_incomplete_main_search_requires_ceiling_exception():
    with pytest.raises(ValueError, match="did not exhaust"):
        verify_receipt(10_000, 500, 9_499)
    assert not verify_receipt(10_000, 500, 9_499, depth_ceiling=True)


@pytest.mark.parametrize("main", [-1, 9_501, 3.2, True])
def test_invalid_main_nodes_rejected(main):
    with pytest.raises(ValueError):
        verify_receipt(10_000, 500, main)


def test_over_cap_probe_does_not_get_to_steal_main_nodes():
    with pytest.raises(ValueError):
        main_search_limit(10_000, 1_001)


def test_aggregate_feasibility_cannot_pool_unused_per_position_budget():
    from research.mtdp.jass_benchmark.total_budget import aggregate_feasibility
    report = aggregate_feasibility(50_000, [0, 6_000])
    assert report == {
        "positions": 2, "per_position_cap": 5_000,
        "aggregate_cap": 10_000, "measured_verification_nodes": 6_000,
        "positions_over_cap": 1, "all_positions_fit": False,
    }


def test_aggregate_feasibility_valid_cohort():
    from research.mtdp.jass_benchmark.total_budget import aggregate_feasibility
    report = aggregate_feasibility(50_000, [1_000, 5_000])
    assert report["all_positions_fit"] is True
    assert report["positions_over_cap"] == 0


@pytest.mark.parametrize("invalid", [[-1], [True], [1.2]])
def test_aggregate_feasibility_rejects_invalid_nodes(invalid):
    from research.mtdp.jass_benchmark.total_budget import aggregate_feasibility
    with pytest.raises(ValueError, match="Invalid metered"):
        aggregate_feasibility(50_000, invalid)


def test_empty_cohort_cannot_be_declared_feasible():
    from research.mtdp.jass_benchmark.total_budget import aggregate_feasibility
    with pytest.raises(ValueError, match="empty cohort"):
        aggregate_feasibility(50_000, [])


@pytest.mark.parametrize("flag", [1, 0, "yes", None])
def test_depth_ceiling_requires_explicit_boolean(flag):
    with pytest.raises(ValueError, match="Depth-ceiling flag must be boolean"):
        verify_receipt(10_000, 500, 9_500, depth_ceiling=flag)


def test_capped_probe_limit_and_actual_receipts():
    from research.mtdp.jass_benchmark.total_budget import (
        capped_probe_limit, record_probe_nodes,
    )
    assert capped_probe_limit(10_000, 900, 500) == 100
    assert record_probe_nodes(10_000, 900, 100, 80) == 980
    assert capped_probe_limit(10_000, 980, 100) == 20
    assert record_probe_nodes(10_000, 980, 20, 20) == 1_000
    assert capped_probe_limit(10_000, 1_000, 500) == 0


@pytest.mark.parametrize("requested", [-1, True, 1.5, None])
def test_capped_probe_rejects_invalid_requested_limit(requested):
    from research.mtdp.jass_benchmark.total_budget import capped_probe_limit
    with pytest.raises(ValueError, match="Requested probe nodes"):
        capped_probe_limit(10_000, 0, requested)


@pytest.mark.parametrize("measured", [-1, True, 1.5, None, 101])
def test_probe_receipt_must_be_measured_and_within_issued_limit(measured):
    from research.mtdp.jass_benchmark.total_budget import record_probe_nodes
    with pytest.raises(ValueError, match="Probe receipt"):
        record_probe_nodes(10_000, 900, 100, measured)


def test_probe_receipt_cannot_spend_after_cap_exhaustion():
    from research.mtdp.jass_benchmark.total_budget import record_probe_nodes
    with pytest.raises(ValueError, match="Issued probe limit exceeds remaining verification allowance"):
        record_probe_nodes(10_000, 1_000, 100, 1)


def test_ordered_probe_audit_accounts_for_actual_nodes():
    from research.mtdp.jass_benchmark.total_budget import audit_probe_sequence
    assert audit_probe_sequence(10_000, [(600, 450), (550, 500), (50, 50)]) == {
        "probe_count": 3,
        "verification_nodes": 1_000,
        "verification_remaining": 0,
        "main_search_limit": 9_000,
    }


def test_ordered_probe_audit_does_not_pool_caps_or_reuse_spent_budget():
    from research.mtdp.jass_benchmark.total_budget import audit_probe_sequence
    with pytest.raises(ValueError, match="Issued probe limit"):
        audit_probe_sequence(10_000, [(1_000, 900), (200, 101)])


@pytest.mark.parametrize("bad", [None, (), [(100,)], [[100, 50]], [(True, 0)],
                                     [(100, True)], [(100, 101)]])
def test_ordered_probe_audit_rejects_malformed_receipts(bad):
    from research.mtdp.jass_benchmark.total_budget import audit_probe_sequence
    with pytest.raises(ValueError):
        audit_probe_sequence(10_000, bad)


def test_empty_probe_sequence_preserves_main_budget():
    from research.mtdp.jass_benchmark.total_budget import audit_probe_sequence
    assert audit_probe_sequence(50_000, []) == {
        "probe_count": 0, "verification_nodes": 0,
        "verification_remaining": 5_000, "main_search_limit": 50_000,
    }


def test_issued_probe_limit_must_be_capped_before_engine_call():
    from research.mtdp.jass_benchmark.total_budget import record_probe_nodes
    with pytest.raises(ValueError, match="Issued probe limit"):
        record_probe_nodes(10_000, 900, 200, 50)


def test_exhausted_verification_cap_rejects_even_zero_node_probe():
    from research.mtdp.jass_benchmark.total_budget import record_probe_nodes
    with pytest.raises(ValueError, match="Issued probe limit"):
        record_probe_nodes(10_000, 1_000, 1, 0)


def test_zero_limit_is_skip_not_a_measured_probe():
    from research.mtdp.jass_benchmark.total_budget import (
        audit_probe_sequence, record_probe_nodes,
    )
    with pytest.raises(ValueError, match="Zero-node probe"):
        record_probe_nodes(10_000, 0, 0, 0)
    with pytest.raises(ValueError, match="Zero-node probe"):
        audit_probe_sequence(10_000, [(0, 0)])
    with pytest.raises(ValueError, match="Zero-node probe"):
        audit_probe_sequence(9, [(0, 0)])
    # Skipping a probe is represented by an empty receipt sequence.
    assert audit_probe_sequence(9, [])["main_search_limit"] == 9


def test_complete_position_receipt_is_comparable_at_equal_total_budget():
    from research.mtdp.jass_benchmark.total_budget import audit_complete_search
    result = audit_complete_search(10_000, [(600, 450), (550, 500), (50, 50)], 9_000)
    assert result == {
        "probe_count": 3, "verification_nodes": 1_000,
        "verification_remaining": 0, "main_search_limit": 9_000,
        "main_nodes": 9_000, "total_measured_nodes": 10_000,
        "comparable": True,
    }


def test_complete_position_receipt_rejects_unexplained_shortfall():
    from research.mtdp.jass_benchmark.total_budget import audit_complete_search
    with pytest.raises(ValueError, match="did not exhaust"):
        audit_complete_search(10_000, [(100, 80)], 9_919)


def test_complete_position_receipt_marks_depth_ceiling_noncomparable():
    from research.mtdp.jass_benchmark.total_budget import audit_complete_search
    result = audit_complete_search(10_000, [(100, 80)], 9_000, depth_ceiling=True)
    assert result["total_measured_nodes"] == 9_080
    assert result["comparable"] is False


def test_complete_position_receipt_rejects_overspend():
    from research.mtdp.jass_benchmark.total_budget import audit_complete_search
    with pytest.raises(ValueError, match="Invalid metered main-search"):
        audit_complete_search(10_000, [(100, 80)], 9_921)


def test_paired_cohort_requires_equal_ids_and_full_budget():
    from research.mtdp.jass_benchmark.total_budget import audit_paired_searches
    full = {"total_measured_nodes": 10_000, "comparable": True}
    ceiling = {"total_measured_nodes": 9_000, "comparable": False}
    report = audit_paired_searches(
        10_000, {"arena:a": full, "arena:b": full},
        {"arena:a": full, "arena:b": ceiling},
    )
    assert report == {
        "positions": 2, "paired_comparable": 1,
        "paired_excluded": 1, "all_pairs_comparable": False,
    }
    with pytest.raises(ValueError, match="identical nonempty"):
        audit_paired_searches(10_000, {"a": full}, {"b": full})
    with pytest.raises(ValueError, match="exhaust"):
        audit_paired_searches(
            10_000, {"a": {"total_measured_nodes": 9_999, "comparable": True}},
            {"a": full},
        )


@pytest.mark.parametrize("invalid", [
    {"total_measured_nodes": True, "comparable": True},
    {"total_measured_nodes": 10_001, "comparable": True},
    {"total_measured_nodes": 10_000, "comparable": 1},
    {"total_measured_nodes": 10_000},
])
def test_paired_cohort_rejects_malformed_receipts(invalid):
    from research.mtdp.jass_benchmark.total_budget import audit_paired_searches
    with pytest.raises(ValueError, match="Invalid search receipt"):
        audit_paired_searches(
            10_000, {"a": invalid},
            {"a": {"total_measured_nodes": 10_000, "comparable": True}},
        )
