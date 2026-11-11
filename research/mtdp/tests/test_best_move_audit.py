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
