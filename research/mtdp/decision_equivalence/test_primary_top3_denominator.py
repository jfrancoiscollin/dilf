"""D1: primary top-3 denominator must be fixed by legal-action count only.

Synthetic data; no Scan labels, no independent FMJD cohort.
"""
from research.mtdp.decision_equivalence.paired_cluster_report import paired_cluster_report


def _row(game_id, n, scores):
    legal = [f"m{i}" for i in range(n)]
    return {
        "game_id": game_id,
        "legal": legal,
        "candidate": legal,
        "baseline": list(reversed(legal)),
        "scores": dict(zip(legal, scores)),
    }


def test_primary_top3_excludes_small_branching_without_score_selection():
    # Same legal-action counts and provenance; adversarially replace all scores.
    distinct = [
        _row("g1", 3, [9, 5, 0]),
        _row("g1", 4, [9, 5, 2, 0]),
        _row("g2", 5, [9, 7, 5, 3, 0]),
    ]
    all_tied = [
        _row("g1", 3, [0, 0, 0]),
        _row("g1", 4, [0, 0, 0, 0]),
        _row("g2", 5, [0, 0, 0, 0, 0]),
    ]
    for rows in (distinct, all_tied):
        report = paired_cluster_report(
            rows, metric="recall_at_3", top3_population="fixed_n_ge_4",
            repetitions=100, seed=17,
        )
        assert report["n_input_observations"] == 3
        assert report["n_observations"] == 2
        assert report["n_clusters"] == 2
        assert report["excluded"]["noninformative_top3"] == 1
        assert report["excluded"]["all_score_ties"] == 0
        assert report["top3_population_is_primary_fixed"] is True


def test_primary_top3_retains_all_tied_scores_with_repeated_game():
    rows = [
        _row("g1", 4, [1, 1, 1, 1]),
        _row("g1", 4, [2, 2, 2, 2]),
        _row("g2", 4, [3, 3, 3, 3]),
    ]
    report = paired_cluster_report(
        rows, metric="recall_at_3", top3_population="fixed_n_ge_4",
        repetitions=100, seed=17,
    )
    assert report["n_observations"] == 3
    assert report["n_clusters"] == 2
    assert report["excluded"]["noninformative_top3"] == 0
    assert report["excluded"]["all_score_ties"] == 0
