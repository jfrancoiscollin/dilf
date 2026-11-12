import pytest

from research.mtdp.jass_benchmark.run import read_run, summarize_target_games


def test_jass_receipt_requires_exact_consumed_nodes():
    fen = "W:W31:B20"
    move = {"action": [[31, 26], [], False], "jass_key": "31-26"}
    target = {"target_fen": fen, "legal_moves": [move]}
    scores = {((31, 26), (), False): 14}
    fields = [fen, "10000", "10000", "5", "budget", "31-26", "20", "8", "", "31-26", "31-26"]
    receipt, _ = read_run("\t".join(fields), target, 10000, [], scores)
    assert receipt["nodes"] == 10000
    fields[2] = "9999"
    with pytest.raises(ValueError, match="Unexpected Jass receipt"):
        read_run("\t".join(fields), target, 10000, [], scores)


def test_target_game_summary_weights_games_equally_and_assigns_shared_fen_once():
    def row(games, regret):
        return {
            "target_games": games,
            "nodes_at_common_depth": dict.fromkeys(("transfer", "canonical", "native"), 100),
            "arms": {
                arm: {
                    "best_move": "31-26", "ordinary_regret_centimen": value,
                    "scan_optimal": value == 0, "completed_depth": 3, "elapsed_us": 1,
                    "stop": "budget", "scan_best_category": "ordinary",
                    "scan_chosen_category": "ordinary",
                }
                for arm, value in (("transfer", regret), ("canonical", 20), ("native", 20))
            },
        }

    result = summarize_target_games([row(["b", "a"], 10), row(["a"], 10), row(["b"], 40)])
    assert result["games"] == 2
    assert result["targets_in_multiple_games"] == 1
    assert result["by_game"]["a"]["targets"] == 2
    assert result["by_game"]["b"]["targets"] == 1
    assert result["comparisons"]["canonical"] == {
        "ordinary_games": 2, "transfer_better_games": 1, "transfer_worse_games": 1,
        "mean_game_delta_centimen": 5, "median_game_delta_centimen": 5,
    }


def test_initial_only_receipt_requires_adaptive_order_fields():
    fen = "W:W31:B20"
    move = {"action": [[31, 26], [], False], "jass_key": "31-26"}
    target = {"target_fen": fen, "legal_moves": [move]}
    scores = {((31, 26), (), False): 14}
    fields = [fen, "10000", "10000", "5", "nodes", "31-26", "20", "8", "", "31-26", "31-26"]
    attempt = "1:1:1:1:14:31-26"
    with pytest.raises(ValueError, match="trace mode"):
        read_run("\t".join([*fields, attempt]), target, 10000, ["31-26"], scores, initial_only=True)

    raw = "\t".join([*fields, attempt + ":31-26:31-26"])
    _, trace = read_run(raw, target, 10000, ["31-26"], scores, initial_only=True)
    assert trace["verified_schedule_applications"] == 1
    assert trace["attempts"][0]["expected"] == ["31-26"]
    assert trace["attempts"][0]["best_move"] == "31-26"
