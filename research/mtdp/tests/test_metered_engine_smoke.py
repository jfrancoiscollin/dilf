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
        if limit == 10_000:
            assert forced is None
        else:
            assert limit == (9000 if incomplete else 9540)
            assert forced == (None if incomplete else "a")
        return {"nodes": limit, "depth_ceiling": False, "best_move": "a", "stop": "nodes"}

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
    assert result["paired_comparable"] is True
    assert result["native_baseline"]["nodes"] == 10_000
    assert result["lcb_baseline"]["nodes"] == 10_000
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
    assert result["paired_comparable"] is True


def test_invalid_prefix_rejected_before_main(monkeypatch):
    calls = fake_engine(monkeypatch)
    with pytest.raises(ValueError, match="Prefix differs"):
        metered_engine_smoke.technical_smoke(
            None, None, "fen", total_nodes=10_000, prefix=["illegal"])
    assert not any(entry[0] == "main" for entry in calls)


def test_king_first_archived_fen_matches_jass_men_first_canonicalization():
    from research.mtdp.jass_benchmark.metered_engine_smoke import _position_identity
    archive = "B:WK2,25,35,40,48:B15,37"
    canonical = "B:W25,35,40,48,K2:B15,37"
    assert _position_identity(archive) == _position_identity(canonical)


@pytest.mark.parametrize("altered", [
    "W:W25,35,40,48,K2:B15,37",  # changed side to move
    "B:W2,25,35,40,48:B15,37",  # king demoted
    "B:W25,35,40,48,K3:B15,37",  # king moved
    "B:W25,35,40,48,K2:B15,38",  # opponent moved
])
def test_fen_identity_rejects_semantic_changes(altered):
    from research.mtdp.jass_benchmark.metered_engine_smoke import _position_identity
    assert _position_identity(altered) != _position_identity("B:WK2,25,35,40,48:B15,37")


@pytest.mark.parametrize("malformed", [
    "B:W25,25:B15", "B:WK51,25:B15", "B:W0:B15",
    "B:W25:BK25", "B:W25:B15,15", "B:W25:B1x",
])
def test_fen_identity_rejects_duplicate_or_invalid_squares(malformed):
    from research.mtdp.jass_benchmark.metered_engine_smoke import _position_identity
    with pytest.raises(ValueError):
        _position_identity(malformed)
