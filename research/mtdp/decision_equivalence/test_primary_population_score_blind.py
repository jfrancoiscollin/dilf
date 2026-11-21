"""D1 synthetic invariance of the *primary* top-3 sampling frame.

Changing reference scores must not change admission to the primary n>=4
population. This is not an FMJD cohort or a Scan result.
"""
from research.mtdp.decision_equivalence.paired_cluster_report import paired_cluster_report


def _row(game, scores):
    legal = ["a", "b", "c", "d"]
    return {"game_id": game, "legal": legal, "scores": dict(zip(legal, scores)),
            "candidate": legal, "baseline": list(reversed(legal))}


def test_primary_top3_sampling_frame_is_score_blind():
    distinct = [_row("game1", [4, 3, 2, 1]),
                _row("game2", [8, 5, 2, 0])]
    tied = [_row("game1", [4, 4, 4, 4]),
            _row("game2", [8, 8, 8, 8])]
    reports = [paired_cluster_report(rows, metric="recall_at_3",
                                      top3_population="fixed_n_ge_4",
                                      repetitions=100, seed=19)
               for rows in (distinct, tied)]
    for report in reports:
        assert report["n_input_observations"] == 2
        assert report["n_observations"] == 2
        assert report["n_clusters"] == 2
        assert report["excluded"]["noninformative_top3"] == 0
        assert report["top3_population_is_primary_fixed"] is True


def test_secondary_top3_population_is_explicitly_score_conditional():
    distinct = [_row("game1", [4, 3, 2, 1]),
                _row("game2", [8, 5, 2, 0])]
    report = paired_cluster_report(distinct, metric="recall_at_3",
                                   top3_population="conditional_informative",
                                   repetitions=100, seed=19)
    assert report["n_observations"] == 2
    assert report["top3_population_is_primary_fixed"] is False
