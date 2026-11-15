"""Engineering smoke orchestration tests; no Scan or Jass strength claims."""
import pytest

from research.mtdp.jass_benchmark import metered_engine_smoke


def fake_engine(monkeypatch, *, incomplete=False):
    calls = []
    native = ["a", "b", "c"]

    def replay(_binary, _fen, *, mode, limit, prefix, expected_legal_order=None):
        calls.append((mode, limit, list(prefix)))
        if mode == "preliminary":
            assert limit == 1000
            return {"nodes": 1000 if incomplete else 100, "completed": not incomplete,
                    "winner": None if incomplete else "b",
                    "score": None if incomplete else 8,
                    "alpha_before": -31000, "beta": 31000,
                    "native_order": native}
        if incomplete:
            pytest.fail("Incomplete preliminary must not trigger probes")
        assert list(prefix) == [prefix[0]]
        assert list(expected_legal_order) == native
        return {"nodes": 120, "completed": True, "move": prefix[0],
                "score": 8 if prefix[0] in ("a", "b") else 3,
                "alpha_before": -31000, "beta": 31000, "native_order": native}

    def main(_binary, _fen, _prefix, forced, limit, live):
        calls.append(("main", limit, forced))
        assert live == native
        assert limit == (9000 if incomplete else 9540)
        assert forced == (None if incomplete else "a")
        return {"nodes": limit, "depth_ceiling": False}

    monkeypatch.setattr(metered_engine_smoke, "run_depth_one", replay)
    monkeypatch.setattr(metered_engine_smoke, "main_search", main)
    return calls


def test_real_callback_contract_accounts_for_verification_exactly_once(monkeypatch):
    calls = fake_engine(monkeypatch)
    result = metered_engine_smoke.technical_smoke(
        None, None, "fen", total_nodes=10_000, prefix=["b"])
    assert result["decision_reason"] == "verified_tie"
    assert result["intervention"] == "a"
    assert result["verification_nodes"] == 460
    assert result["main_nodes"] == 9540
    assert result["complete_budget"] is True
    assert [entry[0] for entry in calls].count("preliminary") == 1
    assert [entry[0] for entry in calls].count("probe") == 3


def test_incomplete_preflight_falls_back_and_spends_full_remaining_nodes(monkeypatch):
    calls = fake_engine(monkeypatch, incomplete=True)
    result = metered_engine_smoke.technical_smoke(
        None, None, "fen", total_nodes=10_000, prefix=["b"])
    assert result["decision_reason"] == "preliminary_incomplete_or_bounded"
    assert result["intervention"] is None
    assert result["verification_nodes"] + result["main_nodes"] == 10_000
    assert not any(entry[0] == "probe" for entry in calls)


def test_invalid_prefix_rejected_before_main(monkeypatch):
    calls = fake_engine(monkeypatch)
    with pytest.raises(ValueError, match="Prefix differs"):
        metered_engine_smoke.technical_smoke(
            None, None, "fen", total_nodes=10_000, prefix=["illegal"])
    assert not any(entry[0] == "main" for entry in calls)
