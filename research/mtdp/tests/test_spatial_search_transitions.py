from research.mtdp.jass_benchmark.spatial_search_transitions import compare, summarize


def test_search_transition_counts_tied_optima_and_categorical_costs():
    candidate = {
        "L": {"prefix": ["20-24"], "top1": {"covered": True, "ordinary_regret_centimen": 0}},
        "LCB": {"prefix": ["14-19"], "top1": {"covered": False, "ordinary_regret_centimen": None}},
    }
    receipt = {"arms": {
        arm: {"scan_optimal": True, "best_move": "19-23", "ordinary_regret_centimen": 0}
        for arm in ("L", "LCB")
    }}
    arms = compare(candidate, receipt)
    assert arms["L"]["transition"] == "retained"
    assert arms["L"]["first_move"] != arms["L"]["final_move"]
    assert arms["L"]["regret_change_centimen"] == 0
    assert arms["LCB"]["transition"] == "recovered"
    assert arms["LCB"]["regret_change_centimen"] is None
    totals = summarize([{"arms": arms}])
    assert totals["different_final_moves"] == 0
    assert totals["arms"]["LCB"] == {
        "retained": 0, "recovered": 1, "displaced": 0, "missed_both": 0,
    }
