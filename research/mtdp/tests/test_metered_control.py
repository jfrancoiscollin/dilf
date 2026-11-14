"""Simulated-engine contract tests; not evidence of real Jass integration."""
import pytest
from research.mtdp.jass_benchmark.metered_control import execute


def preliminary(limit):
    assert limit == 1000
    return {"nodes": 100, "winner": "b", "score": 8,
            "alpha_before": -100, "beta": 100, "completed": True}


def probe(move, limit):
    assert limit <= 900
    return {"nodes": 120, "move": move, "score": 8 if move in ("a", "b") else 3,
            "alpha_before": -100, "beta": 100, "completed": True}


def test_meters_every_call_selects_native_tie_and_preserves_total_budget():
    main_calls = []
    def main(intervention, limit):
        main_calls.append((intervention, limit))
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=10_000, native_order=["a", "b", "c"],
                     preliminary=preliminary, probe=probe, main=main)
    assert report["intervention"] == "a"
    assert report["decision_reason"] == "verified_tie"
    assert report["verification_nodes"] == 460
    assert report["main_nodes"] == 9540
    assert main_calls == [("a", 9540)]
    assert sum(x["nodes"] for x in report["verification_receipts"]) == 460
    assert report["complete_budget"] is True


def test_cap_exhaustion_skips_probe_and_spends_remainder_on_fallback():
    calls = []
    def expensive(_move, limit):
        calls.append(limit)
        return {"nodes": limit, "move": "a", "score": 8,
                "alpha_before": -100, "beta": 100, "completed": True}
    def main(intervention, limit):
        assert intervention is None
        assert limit == 9000
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=10_000, native_order=["a", "b"],
                     preliminary=preliminary, probe=expensive, main=main)
    assert calls == [900]
    assert report["decision_reason"] == "verification_budget_exhausted"
    assert report["verification_nodes"] == 1000
    assert report["complete_budget"] is True


def test_bounded_probe_causes_fallback_without_peeking_later():
    calls = []
    def bounded(move, _limit):
        calls.append(move)
        return {"nodes": 40, "move": move, "score": 8,
                "alpha_before": 8, "beta": 100, "completed": True}
    def main(chosen, limit):
        assert chosen is None and limit == 9860
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=10_000, native_order=["a", "b"],
                     preliminary=preliminary, probe=bounded, main=main)
    assert calls == ["a"]
    assert report["fallback_reason"] == "probe_incomplete_or_bounded"


def test_inconsistent_exact_scores_fall_back_to_lcb():
    def bad(move, limit):
        return {**probe(move, limit), "score": 7}
    def main(chosen, limit):
        assert chosen is None
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=10_000, native_order=["a", "b"],
                     preliminary=preliminary, probe=bad, main=main)
    assert report["decision_reason"] == "inconsistent_exact_scores"


@pytest.mark.parametrize("bad_nodes", [901, -1, True, None, 1.2])
def test_overrun_or_invalid_probe_receipt_fails_closed(bad_nodes):
    def bad(move, limit):
        return {**probe(move, limit), "nodes": bad_nodes}
    with pytest.raises(ValueError, match="Probe receipt"):
        execute(total_nodes=10_000, native_order=["a", "b"],
                preliminary=preliminary, probe=bad,
                main=lambda *_: pytest.fail("Main must not run after invalid accounting"))


def test_depth_ceiling_explicit_exception_excluded_from_complete_budget():
    def main(chosen, limit):
        assert chosen == "a"
        return {"nodes": limit - 1, "depth_ceiling": True}
    result = execute(total_nodes=10_000, native_order=["a", "b"],
                     preliminary=preliminary, probe=probe, main=main)
    assert result["complete_budget"] is False


def test_underfilled_main_without_depth_ceiling_is_rejected():
    with pytest.raises(ValueError, match="did not exhaust"):
        execute(total_nodes=10_000, native_order=["a", "b"],
                preliminary=preliminary, probe=probe,
                main=lambda _choice, limit: {"nodes": limit-1, "depth_ceiling": False})


def test_tiny_budget_skips_all_verification_and_uses_full_budget():
    def main(intervention, limit):
        assert intervention is None and limit == 9
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=9, native_order=["a", "b"],
                     preliminary=lambda _limit: pytest.fail("No preliminary call"),
                     probe=lambda *_: pytest.fail("No probe"), main=main)
    assert report["verification_nodes"] == 0
    assert report["decision_reason"] == "verification_budget_exhausted"


@pytest.mark.parametrize("order", [["a", "a"], [], ["a", 1], [""]])
def test_invalid_live_legal_order_rejected_before_spending(order):
    with pytest.raises(ValueError, match="Native legal order"):
        execute(total_nodes=10_000, native_order=order,
                preliminary=lambda _: pytest.fail("No calls"),
                probe=lambda *_: pytest.fail("No calls"),
                main=lambda *_: pytest.fail("No calls"))


def test_incomplete_preliminary_without_winner_falls_back_and_meters_cost():
    def incomplete(limit):
        return {"nodes": 32, "completed": False}
    def main(chosen, limit):
        assert chosen is None and limit == 9968
        return {"nodes": limit, "depth_ceiling": False}
    report = execute(total_nodes=10_000, native_order=["a", "b"],
                     preliminary=incomplete,
                     probe=lambda *_: pytest.fail("No verification after incomplete receipt"), main=main)
    assert report["fallback_reason"] == "preliminary_incomplete_or_bounded"
    assert report["verification_nodes"] == 32
