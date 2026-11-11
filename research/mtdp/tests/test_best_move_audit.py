from research.mtdp.best_move_audit import compare_scores


A = ((31, 26), (), False)
B = ((32, 28), (), False)
C = ((33, 29), (), False)


def test_tied_picks_can_disagree_with_an_optimum_in_common():
    result = compare_scores({A: 30, B: 30, C: 25}, {A: 11, B: 20, C: 15})

    assert not result["same_pick"]
    assert result["optimal_sets_overlap"]
    assert result["a_to_b"]["ordinary_regret_centimen"] == 9
    assert result["b_to_a"]["ordinary_regret_centimen"] == 0


def test_disjoint_optima_have_directional_costs():
    result = compare_scores({A: 30, B: 10}, {A: -40, B: 20})

    assert not result["same_pick"]
    assert not result["optimal_sets_overlap"]
    assert result["a_to_b"]["ordinary_regret_centimen"] == 60
    assert result["b_to_a"]["ordinary_regret_centimen"] == 20


def test_forced_scores_are_separate_from_ordinary_cost():
    result = compare_scores({A: 30, B: 10}, {A: -9990, B: 9998})

    assert result["a_to_b"]["ordinary_regret_centimen"] is None
    assert result["a_to_b"]["best_category"] == "win"
    assert result["a_to_b"]["transferred_category"] == "loss"


def test_scan_depth_configuration_without_starting_engine(tmp_path):
    from research.mtdp.best_move_audit import Scan, DEFAULT_DEPTH

    binary = tmp_path / "scan_linux"
    assert Scan(binary).depth == DEFAULT_DEPTH == 8
    assert Scan(binary, depth=12).depth == 12


def test_scan_rejects_invalid_depth_without_starting_engine(tmp_path):
    import pytest
    from research.mtdp.best_move_audit import Scan

    with pytest.raises(ValueError, match="positive"):
        Scan(tmp_path / "scan_linux", depth=0)


def test_prior_holdout_fens_are_excluded_from_fresh_pairs(monkeypatch):
    from types import SimpleNamespace

    from pedagogy.game import parse_fen
    from research.mtdp import best_move_audit

    base, old, fresh = "W:W:B1", "W:W:B2", "W:W:B3"
    sources = {
        "base": [base], "prior": [old], "fresh": [base, old, fresh],
    }

    def load(paths, engine, seen):
        name, = paths
        if name == "fresh":
            assert seen == {"base", "prior"}
        seen.add(name)
        return (
            {fen: parse_fen(fen) for fen in sources[name]},
            {fen: {name} for fen in sources[name]},
            [{"file": name}],
        )

    monkeypatch.setattr(best_move_audit, "load_positions", load)
    engine = SimpleNamespace(legal_moves=lambda state: [])
    report = best_move_audit.audit("base", ["fresh"], engine, SimpleNamespace(depth=12), ["prior"])

    assert report["novel_holdout_fens"] == 1
    assert report["prior_holdout_only_overlap_fens"] == 1
    assert not report["holdout_pairs"]
    pair, = report["pcblues_transfer_pairs"]
    assert (pair["fen_a"], pair["fen_b"]) == (base, fresh)
