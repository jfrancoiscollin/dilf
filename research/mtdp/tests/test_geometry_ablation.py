from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import geometry_ablation as ablation

A = ((31, 26), (), False)
B = ((32, 27), (), False)
C = ((33, 28), (), False)


def test_same_actions_different_geometry_and_lexicographic_selection():
    a, b, c = ("pc:1", 9, "A"), ("pc:1", 4, "B"), ("pc:2", 1, "C")
    index = {(A, B): [(a, "same"), (b, "other"), (c, "same")]}
    assert ablation.enumerate_matches(index, ((A, B), "same")) == {
        "L": [b, a, c], "LG": [a, c],
    }


def test_empty_geometry_arm_and_missing_legal_catalogue():
    source = ("pc:1", 9, "A")
    index = {(A, B): [(source, "other")]}
    assert ablation.enumerate_matches(index, ((A, B), "same")) == {"L": [source], "LG": []}
    assert ablation.enumerate_matches(index, ((A, C), "same")) == {"L": [], "LG": []}
    result = ablation.paired_summary([])
    assert result["paired"] == 0
    assert result["top3"]["coverage_delta"] is None
    assert result["top3"]["regret_ci"] == {"games": 0, "ci95": None}


def test_source_ties_break_by_canonical_action_and_target_cannot_select():
    source = {C: 1, B: 4, A: 4}
    target = {C: 100, B: 80, A: 0}
    result = ablation.outcomes(source, target, 3)
    assert result["prefix"] == [A, B, C]
    assert result["disjoint_optima"]
    assert result["top1"]["ordinary_regret_centimen"] == 100
    assert result["top3"]["covered"]
    with pytest.raises(ValueError, match="catalogues differ"):
        ablation.outcomes(source, {A: 0, B: 80}, 3)


def test_quiet_catalogue_fails_on_ambiguous_or_capturing_actions(monkeypatch):
    monkeypatch.setattr(ablation, "_quiet_signature", lambda _: "quiet")
    quiet = SimpleNamespace(path=(31, 26), captures=(), promotion=False)
    capture = SimpleNamespace(path=(31, 22), captures=(27,), promotion=False)
    for moves in ([quiet, quiet], [capture, quiet]):
        engine = SimpleNamespace(legal_moves=lambda _: moves)
        with pytest.raises(ValueError, match="Ambiguous or capturing"):
            ablation.quiet_catalogue(None, engine)


def test_target_leakage_excludes_pcblues_and_all_prior_sources_and_manifests():
    held = dict.fromkeys(("pc", "earlier-pdn", "earlier-manifest", "novel"))
    assert ablation.novel_targets(held, {"pc": None}, {"earlier-pdn": None},
                                  {"earlier-manifest"}) == ["novel"]


def test_occupancy_arms_hold_turn_fixed_and_nest_blockers_and_count():
    identity = [("pc", i, str(i)) for i in range(6)]
    actions = (A, B)
    key = ("white", frozenset((31, 32, 40)), frozenset((24,)))
    index = {
        ("white", actions): [
            (identity[3], key),
            (identity[2], ("white", key[1], frozenset((25,)))),
            (identity[1], ("white", frozenset((31, 32, 41)), key[2])),
            (identity[0], ("white", frozenset((31, 32)), key[2])),
        ],
        ("black", actions): [(identity[4], ("black", key[1], key[2]))],
        ("white", (A, C)): [(identity[5], key)],
    }
    assert ablation.enumerate_occupancy_matches(index, (actions, key)) == {
        "L": identity[:4], "LM": [identity[2], identity[3]],
        "LCB": [identity[1], identity[3]], "LMB": [identity[3]],
    }


def test_repeated_public_game_id_is_rejected(monkeypatch):
    games = {"new": ["abcdef12"], "old": ["abcdef12", "abcdef34"]}
    monkeypatch.setattr(ablation, "read_games", lambda path: [
        SimpleNamespace(tags={"Site": f"https://lidraughts.org/{game_id}"}) for game_id in games[path]
    ])
    with pytest.raises(ValueError, match="overlaps earlier game IDs"):
        ablation.check_event_game_ids("new", ["old"])


def test_input_digest_detects_changed_frozen_bytes(tmp_path):
    import hashlib

    path = tmp_path / "reference.json"
    raw = b'{"frozen":true}'
    checksum = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="Input hash mismatch"):
        ablation.read_input({"path": str(path), "stored_sha256": checksum, "content_sha256": checksum})


def test_categorical_transition_is_counted_without_subtracting_score():
    result = ablation.outcomes({A: 9000, B: 0}, {A: -9000, B: 30}, 2)
    assert result["top1"]["best_category"] == "ordinary"
    assert result["top1"]["candidate_category"] == "loss"
    assert result["top1"]["ordinary_regret_centimen"] is None
    assert result["top3"]["ordinary_regret_centimen"] == 0


def test_missing_successor_score_is_rejected():
    fields = {"schema": "mtdp-jass-scan-reference-v1", "cohort_sha256": "frozen",
              "scan_binary_sha256": "binary", "scan_eval_sha256": "eval", "scan_successor_depth": 16}
    receipt = {**fields, "action_scores_centimen": {"target": [{"action": A, "score": 0}]}}
    with pytest.raises(ValueError, match="invalid action scores"):
        ablation.validate_reference(receipt, {"target": {A, B}}, {"scan_linux": "binary", "data/eval": "eval"},
                                    "frozen", 16)
