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
