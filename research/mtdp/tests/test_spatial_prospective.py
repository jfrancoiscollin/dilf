import json

import pytest

from research.mtdp.jass_benchmark.spatial_prospective import combine, select


def test_live_scores_with_a_bound_do_not_trigger_intervention(monkeypatch):
    target = {"legal_moves": [{"action": [[31, 26], [], False], "jass_key": "31-26"},
                              {"action": [[32, 27], [], False], "jass_key": "32-27"}]}
    order = ["31-26", "32-27"]

    def replay(_runner, _target, _scores, prefix, *, budget):
        assert budget == 10_000
        move = prefix[0]
        alpha = 4 if prefix == ["31-26"] else -100
        log = {"winner": "32-27", "score": 4,
               "moves": [{"move": move, "score": 4, "alpha_before": alpha, "beta": 100}]}
        return log, {"nodes": budget}, {"legal": order, "attempts": [{"completed": True, "nodes_after": 5}]}

    monkeypatch.setattr("research.mtdp.jass_benchmark.spatial_prospective.replay", replay)
    winner, kind, _, probe_nodes, auxiliary_nodes, _ = select(None, target, ["32-27", "31-26"])
    assert (winner, kind, probe_nodes, auxiliary_nodes) == ("32-27", "unresolved", 10, 30_000)


@pytest.mark.parametrize("duplicate", [False, True])
def test_aggregation_rejects_missing_or_duplicate_receipts(tmp_path, duplicate):
    root = {"event": {"id": "arena"}}
    packets = [(root, [], {}, [{"target_fen": "position", "budget": 50_000}])]
    row = {"event": "arena", "fen": "position", "budget": 50_000}
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps({"freeze_sha256": "freeze", "runner_sha256": "runner",
                                "positions": [row, row] if duplicate else []}))
    with pytest.raises(ValueError, match="Missing, duplicate"):
        combine([path], packets, "freeze")


def test_pinned_runner_exact_tie_and_unique_winner():
    import os
    from pathlib import Path

    runner = os.environ.get("MTDP_TIE_RUNNER")
    if not runner:
        pytest.skip("Set MTDP_TIE_RUNNER to the patched benchmark executable")
    arena = Path("research/mtdp/jass_benchmark/spatial-jass/replication/uG0fGZzB")
    from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
    from research.mtdp.jass_benchmark.spatial_replication import read_freeze, read_scan_scores

    provenance, _, manifest = read_freeze(arena)
    _, scores = read_scan_scores(arena, provenance, manifest)
    cases = {
        "B:W26,29,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49:B1,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,20,22,23":
            ("22-28", "16-21", "verified_tie"),
        "B:W25,26,27,32,33,35,36,37,38,39,40,41,42,43,45,46,48,49,50:B1,2,3,4,6,7,8,9,10,11,12,13,14,16,17,18,19,23,24":
            ("23-28", "23-28", "no_tie"),
    }
    for target in manifest["benchmark_targets"]:
        fen = target["target_fen"]
        if fen not in cases:
            continue
        original, expected, kind = cases.pop(fen)
        _, lists = candidate_lists(target["legal_moves"], scores["source"][target["source_fens"]["LCB"]])
        chosen, status, exact_scores, _, _, log = select(Path(runner), target, lists["transfer"])
        assert (log["winner"], chosen, status) == (original, expected, kind)
        assert exact_scores[original] == exact_scores[chosen] == max(exact_scores.values())
    assert not cases


@pytest.mark.parametrize("live_order", [
    ["31-26", "31-26"],
    ["31-26", "32-27", "33-28"],
    ["31-26"],
    ["31-26", "33-28"],
])
def test_prospective_rejects_mismatched_live_legal_catalogue(monkeypatch, live_order):
    target = {"legal_moves": [{"action": [[31, 26], [], False], "jass_key": "31-26"},
                              {"action": [[32, 27], [], False], "jass_key": "32-27"}]}
    def replay(_runner, _target, _scores, _prefix, *, budget):
        return ({"winner": "31-26", "score": 1, "moves": []},
                {"nodes": budget}, {"legal": live_order, "attempts": []})
    monkeypatch.setattr("research.mtdp.jass_benchmark.spatial_prospective.replay", replay)
    with pytest.raises(ValueError, match="legal order"):
        select(None, target, ["31-26", "32-27"])


@pytest.mark.parametrize("auxiliary,probe", [
    (-1, 0), (10, -1), (5, 6), (True, 0), (10, "5"),
])
def test_aggregation_rejects_invalid_verification_cost(tmp_path, auxiliary, probe):
    root = {"event": {"id": "arena"}}
    packets = [(root, [], {}, [{"target_fen": "position", "budget": 50_000}])]
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps({
        "freeze_sha256": "freeze", "runner_sha256": "runner",
        "positions": [{"event": "arena", "fen": "position", "budget": 50_000,
                       "auxiliary_nodes": auxiliary, "probe_depth_one_nodes": probe}],
    }))
    with pytest.raises(ValueError, match="auxiliary verification node accounting"):
        combine([path], packets, "freeze")
