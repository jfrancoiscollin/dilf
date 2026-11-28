from copy import deepcopy

import pytest

from research.mtdp.jass_benchmark.depth_sensitivity import compare_event, summarize


@pytest.fixture
def experiment():
    a, b = [[31, 26], [], False], [[32, 28], [], False]
    row = {
        "source_fen": "source", "target_fen": "target", "target_games": ["game:1"],
        "source_game": "baseline:1", "legal_moves": [
            {"action": a, "jass_key": "31-26"}, {"action": b, "jass_key": "32-28"},
        ],
    }
    manifest = {"schema": "mtdp-jass-cohort-v1", "targets": [row],
                "engine": {"jass_node_budgets": [200_000]}}
    hashes = {"scan_linux": "engine", "data/eval": "eval"}
    shared = {"schema": "mtdp-jass-scan-reference-v1", "cohort_sha256": "cohort",
              "scan_binary_sha256": "engine", "scan_eval_sha256": "eval"}

    def reference(depth, target):
        return {**shared, "scan_successor_depth": depth, "action_scores_centimen": {
            fen: [{"action": action, "score": score} for action, score in zip((a, b), values, strict=True)]
            for fen, values in (("source", (9, 1)), ("target", target))
        }}

    receipts = [{**row, "budget": 200_000, "arms": {
        "transfer": {"best_move": "31-26", "nodes": 200_000, "ordinary_regret_centimen": 55,
                     "scan_centimen": 5},
        **{arm: {"best_move": "32-28", "nodes": 200_000, "ordinary_regret_centimen": 0,
                 "scan_centimen": 60} for arm in ("native", "canonical")},
    }}]
    return manifest, reference(12, (5, 60)), reference(16, (70, 5)), receipts, hashes, "cohort"


def test_compare_preserves_jass_choices_and_detects_reversal(experiment):
    summary = summarize({"event": compare_event(*experiment)})
    assert summary["scan"]["disjoint_12"] == 1
    assert summary["scan"]["disjoint_16"] == 0
    delta = summary["jass"][200_000]["paired_deltas"]["transfer_minus_canonical"]
    assert delta["12"]["mean_centimen"] == 55
    assert delta["16"]["mean_centimen"] == -65
    assert delta["opposite_signs"] == 1


def test_rejects_duplicate_scores_even_when_action_sets_match(experiment):
    changed = deepcopy(experiment)
    scores = changed[2]["action_scores_centimen"]["target"]
    scores.append(scores[0])
    with pytest.raises(ValueError, match="invalid action scores"):
        compare_event(*changed)


def test_rejects_receipt_that_disagrees_with_shallow_scan(experiment):
    changed = deepcopy(experiment)
    changed[3][0]["arms"]["transfer"]["scan_centimen"] = 4
    with pytest.raises(ValueError, match="receipt disagrees"):
        compare_event(*changed)
