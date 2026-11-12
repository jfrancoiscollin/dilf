from copy import deepcopy

import pytest

from research.mtdp.jass_benchmark.fourth_cohort_cross_depth import analyze
from research.mtdp.jass_scan_reference import score_manifest


@pytest.fixture
def experiment():
    moves = [{"jass_key": f"{sq}-15", "action": [[sq, 15], [], False]} for sq in (9, 1, 2, 3)]
    row = {"source_fen": "s", "target_fen": "t", "target_games": ["game:1", "game:2"], "legal_moves": moves}
    manifest = {"schema": "mtdp-jass-cohort-v1", "targets": [row], "counts": {"covered": 1},
                "engine": {}, "mapping_errors": {}, "mapping_rejected_pairs": []}
    fields = {"schema": "mtdp-jass-scan-reference-v1", "scan_binary_sha256": "binary",
              "scan_eval_sha256": "eval", "cohort_sha256": "manifest"}
    source = {**fields, "role": "source", "scan_successor_depth": 12, "action_scores_centimen": {
        "s": [{**move, "score": score} for move, score in zip(moves, (10, 3, 2, 1), strict=True)],
    }}
    target = {**fields, "role": "target", "scan_successor_depth": 16, "action_scores_centimen": {
        "t": [{**move, "score": score} for move, score in zip(moves, (100, 3, 2, 1), strict=True)],
    }}
    provenance = {"event": {"id": "event"}, "depths": {"source": 12, "target": 16}, "engines": {},
                  "manifest": {"content_sha256": "manifest"},
                  "scan_sha256": {"scan_linux": "binary", "data/eval": "eval"}}
    return manifest, source, target, provenance


def test_scores_only_fixed_source_ranking_and_retains_multi_game_targets(experiment):
    result = analyze(*experiment)
    assert result["summary"]["coverage_table"]["transfer_only"] == 1
    assert result["summary"]["regret_delta_mean_centimen"] == -97
    assert result["first_transfer"]["covered"] == 1
    assert result["multi_game_targets"] == 1
    assert result["single_game_sensitivity"] is None


def test_rejects_reference_with_wrong_depth_or_mixed_position_roles(experiment):
    changed = deepcopy(experiment)
    changed[1]["scan_successor_depth"] = 16
    with pytest.raises(ValueError, match="depth-12 reference field"):
        analyze(*changed)
    changed = deepcopy(experiment)
    changed[1]["action_scores_centimen"].update(changed[2]["action_scores_centimen"])
    with pytest.raises(ValueError, match="different scored positions"):
        analyze(*changed)


def test_scoring_role_excludes_other_side_before_replay(monkeypatch, experiment):
    from types import SimpleNamespace

    manifest = deepcopy(experiment[0])
    manifest["targets"][0]["legal_moves"].sort(key=lambda move: move["action"])
    monkeypatch.setattr("research.mtdp.jass_scan_reference.parse_fen", lambda fen: fen)
    actions = [row["action"] for row in manifest["targets"][0]["legal_moves"]]
    moves = [SimpleNamespace(path=action[0], captures=(), promotion=False) for action in actions]
    seen = []

    def legal(state):
        seen.append(state)
        return moves if state == "s" else []

    engine = SimpleNamespace(legal_moves=legal, apply_move=lambda _state, _move: "after")
    result = score_manifest(manifest, engine, None, role="source")
    assert set(result["action_scores_centimen"]) == {"s"}
    assert result["role"] == "source"
    assert "t" not in seen


def test_freeze_keeps_forced_quiet_match_when_requested(monkeypatch):
    from types import SimpleNamespace
    from research.mtdp import jass_cohort

    source, target = "source", "target"
    state = object()
    move = SimpleNamespace(path=(31, 26), captures=(), promotion=False)
    key = ((31, 26), (), False)

    def load(paths, *_args, **_kwargs):
        states = {fen: state for fen in paths}
        return states, {fen: {f"{fen}:1"} for fen in paths}, []

    monkeypatch.setattr(jass_cohort, "load_positions", load)
    monkeypatch.setattr(jass_cohort, "group_positions", lambda states: {"quiet": list(states)})
    monkeypatch.setattr(jass_cohort, "map_root_moves", lambda *_: {key: "31-26"})
    monkeypatch.setattr(jass_cohort, "typed_radius_two", lambda _: None)
    engine = SimpleNamespace(legal_moves=lambda _: [move])
    catalogue = lambda states: (None for _ in states)

    default = jass_cohort.freeze_cohort(source, [], target, engine, catalogue)
    included = jass_cohort.freeze_cohort(source, [], target, engine, catalogue, include_forced=True)
    assert default["counts"]["forced_move"] == 1
    assert default["targets"] == []
    assert included["counts"]["covered"] == 1
    assert included["targets"][0]["legal_moves"] == [{"action": key, "jass_key": "31-26"}]
