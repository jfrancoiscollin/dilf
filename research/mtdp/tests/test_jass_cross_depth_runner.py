from pathlib import Path
from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import run


def test_cross_depth_requests_use_only_source_scores_and_bytewise_keys(monkeypatch):
    moves = [{"jass_key": f"{sq}-20", "action": [[sq, 20], [], False]} for sq in (1, 2, 3, 10)]
    target = {"source_fen": "source", "target_fen": "target", "target_games": ["g1"],
              "source_game": "pc:1", "legal_moves": moves}
    manifest = {"targets": [target], "selection": {"arm_order_seed": 0},
                "engine": {"jass_node_budgets": [10_000]}}
    source = {"action_scores_centimen": {
        "source": [{**move, "score": score} for move, score in zip(moves, (0, 0, 20, 20), strict=True)],
    }}
    captured = []

    def subprocess_run(command, *, input, **kwargs):
        assert command[-1] == "--initial-only"
        captured.append(set(input.splitlines()))
        return SimpleNamespace(returncode=0, stdout="receipt\n" * 3)

    def read_run(_raw, _target, budget, prefix, _scores, *, initial_only, record_depth_ceiling):
        assert initial_only and not record_depth_ceiling
        return {"completed_depth": 1}, {"attempts": [{"depth": 1, "completed": True, "nodes_after": budget}]}

    monkeypatch.setattr(run.subprocess, "run", subprocess_run)
    monkeypatch.setattr(run, "read_run", read_run)
    for sign in (1, -1):
        judge = {"action_scores_centimen": {
            "target": [{**move, "score": sign * i} for i, move in enumerate(moves)],
        }}
        run.run_benchmark(manifest, judge, Path("runner"), initial_only=True, source_reference=source)
    assert captured[0] == captured[1] == {
        "target 10000", "target 10000 1-20 10-20 2-20", "target 10000 10-20 3-20 1-20",
    }


def test_spatial_arms_use_their_own_source_and_same_budget(monkeypatch):
    moves = [{"jass_key": f"{sq}-20", "action": [[sq, 20], [], False]} for sq in (1, 2, 3, 10)]
    target = {
        "source_fen": "control", "source_fens": {"L": "control", "LCB": "spatial"},
        "target_fen": "target", "target_games": ["g1"], "source_game": "pc:1",
        "legal_moves": moves,
    }
    manifest = {"targets": [target], "selection": {"arm_order_seed": 20261113},
                "engine": {"jass_node_budgets": [10_000]}}

    def scores(values):
        return [{**move, "score": score} for move, score in zip(moves, values, strict=True)]

    source = {"action_scores_centimen": {
        "control": scores((0, 0, 20, 20)), "spatial": scores((30, 40, 0, 0)),
    }}
    captured = []

    def subprocess_run(command, *, input, **kwargs):
        assert command[-2:] == ["--initial-only", "--record-depth-ceiling"]
        captured.append(input)
        return SimpleNamespace(returncode=0, stdout="receipt\n" * 3)

    def read_run(_raw, _target, budget, prefix, _scores, *, initial_only, record_depth_ceiling):
        assert initial_only and record_depth_ceiling
        return {"completed_depth": 1}, {"attempts": [{"depth": 1, "completed": True, "nodes_after": budget}]}

    monkeypatch.setattr(run.subprocess, "run", subprocess_run)
    monkeypatch.setattr(run, "read_run", read_run)
    with pytest.raises(ValueError, match="initial-only"):
        run.run_benchmark(manifest, {}, Path("runner"), compare_spatial_sources=True)
    for sign in (1, -1):
        judge = {"action_scores_centimen": {"target": scores((sign, 0, 0, -sign))}}
        pairs, _ = run.run_benchmark(manifest, judge, Path("runner"), initial_only=True,
                                     source_reference=source, compare_spatial_sources=True)
        assert pairs[0]["prefixes"] == {
            "native": [], "L": ["10-20", "3-20", "1-20"], "LCB": ["2-20", "1-20", "10-20"],
        }
    assert captured[0] == captured[1]
    assert set(captured[0].splitlines()) == {
        "target 10000", "target 10000 10-20 3-20 1-20", "target 10000 2-20 1-20 10-20",
    }
