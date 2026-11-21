"""Frozen-archive technical gate contracts; none establish MTDP Elo gain."""

from pathlib import Path
import pytest

from research.mtdp.jass_benchmark import metered_archive_gate as gate


ROOT = Path("research/mtdp/jass_benchmark/spatial-jass/replication")


@pytest.mark.parametrize("event,expected", [
    ("uG0fGZzB", 25), ("l45uk39x", 12), ("GYEtKzUg", 55),
    ("MtDQWBNR", 33), ("CARZrQpl", 348),
])
def test_frozen_sources_and_LCB_prefixes_only(event, expected):
    entry, positions, digests = gate.read_frozen_arena(ROOT, event)
    assert entry["matched"] == len(positions) == expected
    assert len({x["target_fen"] for x in positions}) == expected
    assert all(0 < len(x["prefix"]) <= 3
               and x["legal_count"] >= len(x["prefix"]) for x in positions)
    assert all(len(digests[x]) == 64 for x in
               ("manifest_sha256", "source_sha256", "provenance_sha256"))


def test_gate_counts_actual_main_winner_not_inferred_from_tie(monkeypatch):
    def frozen(_root, _event):
        return ({"matched": 2}, [
            {"target_fen": "fen1", "target_games": ["one"], "prefix": ["a"],
             "legal_count": 2},
            {"target_fen": "fen2", "target_games": ["two"], "prefix": ["b"],
             "legal_count": 2},
        ], {"manifest_sha256": "archived"})
    calls = []
    def live(_probe, _main, fen, *, total_nodes, prefix):
        calls.append((fen, total_nodes, prefix))
        control = "b" if fen == "fen1" else "a"
        return {
            "native_legal_actions": 2, "paired_comparable": True,
            "verification_nodes": 10, "main_nodes": total_nodes - 10,
            "decision_reason": "verified_tie", "intervention": "a",
            "control_main": {"best_move": control},
            "native_baseline": {"best_move": "b"},
            "lcb_baseline": {"best_move": "a"},
        }
    monkeypatch.setattr(gate, "read_frozen_arena", frozen)
    monkeypatch.setattr(gate, "technical_smoke", live)
    result = gate.run(ROOT, "mock", 10_000, None, None)
    assert calls == [("fen1", 10_000, ["a"]), ("fen2", 10_000, ["b"])]
    assert result["full_arena"] and result["examined_positions"] == 2
    assert result["summary"]["control_matches_native"] == 1
    assert result["summary"]["control_matches_lcb"] == 1
    assert result["summary"]["all_paired_comparable"] is True


def test_gate_rejects_node_count_mismatch(monkeypatch):
    monkeypatch.setattr(gate, "read_frozen_arena", lambda *_: (
        {"matched": 1}, [{"target_fen": "fen", "target_games": ["one"],
                          "prefix": ["a"], "legal_count": 1}], {}))
    monkeypatch.setattr(gate, "technical_smoke", lambda *_args, **_kwargs: {
        "native_legal_actions": 1, "paired_comparable": True,
        "verification_nodes": 10, "main_nodes": 9_989,
    })
    with pytest.raises(ValueError, match="total budget mismatch"):
        gate.run(ROOT, "mock", 10_000, None, None)


@pytest.mark.parametrize("bad", [0, -1, 5.5, True])
def test_gate_rejects_invalid_diagnostic_limit(monkeypatch, bad):
    monkeypatch.setattr(gate, "read_frozen_arena", lambda *_: (
        {"matched": 1}, [{"target_fen": "fen", "target_games": [],
                          "prefix": [], "legal_count": 1}], {}))
    with pytest.raises(ValueError, match="Invalid diagnostic"):
        gate.run(ROOT, "mock", 10_000, None, None, diagnostic_limit=bad)


def test_budget_not_frozen_rejected_without_engine_calls():
    with pytest.raises(ValueError, match="three frozen"):
        gate.run(ROOT, "uG0fGZzB", 12_345, None, None)
