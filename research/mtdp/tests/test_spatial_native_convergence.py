from research.mtdp.jass_benchmark.spatial_native_convergence import compare, summarize


def test_comparison_uses_both_arms_and_ignores_interrupted_aspiration_retry():
    receipt = {
        "target_fen": "position",
        "common_completed_depth": 1,
        "arms": {
            "LCB": {"completed_depth": 2, "best_move": "a"},
            "native": {"completed_depth": 2, "best_move": "a"},
        },
    }
    traces = {}
    for arm, first_move, order in (("LCB", "a", ["a", "b"]), ("native", "b", ["b", "a"])):
        traces[arm] = {"root_order": order, "attempts": [
            {"depth": 1, "completed": True, "best_move": first_move},
            {"depth": 2, "completed": True, "best_move": "b"},
            {"depth": 2, "completed": True, "best_move": "a"},
            {"depth": 3, "completed": True, "best_move": "b"},
            {"depth": 3, "completed": False, "best_move": "a"},
        ]}
    result = compare(receipt, traces)
    assert not result["same_initial_order"]
    assert result["common_completed_depth"] == 2
    assert result["common_depths_with_different_best_move"] == [1]
    assert result["agreement_after_last_disagreement"] == 2
    assert summarize([result])["positions_with_later_common_depth_agreement"] == 1
