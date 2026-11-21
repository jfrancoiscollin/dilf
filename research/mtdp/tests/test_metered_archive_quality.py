"""Engineering-only retrospective quality controls for frozen MTDP receipts."""

import json
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark import metered_archive_quality as quality


def test_bootstrap_whole_game_clusters_is_deterministic():
    observations = [
        ("a", "game-1", 1.0), ("a", "game-1", 3.0),
        ("a", "game-2", 0.0), ("b", "game-3", -1.0),
        ("b", "game-4", 5.0),
    ]
    first = quality.game_cluster_interval(observations)
    assert first == quality.game_cluster_interval(observations)
    assert first["games"] == 4
    assert len(first["ci95"]) == 2
    assert first["ci95"][0] <= first["ci95"][1]


def test_bootstrap_handles_single_game_without_fake_uncertainty():
    assert quality.game_cluster_interval([]) == {"games": 0, "ci95": None}
    assert quality.game_cluster_interval([("a", "one", 0.0)]) == {
        "games": 1, "ci95": None,
    }


def test_reject_missing_or_modified_frozen_catalogue(tmp_path: Path):
    root = tmp_path / "replication"
    root.mkdir()
    (root / "frozen-cohort.json").write_text(
        json.dumps({"arenas": [{"event": "unknown", "matched": 473}]}),
    )
    with pytest.raises(ValueError, match="frozen cohort"):
        quality.analyze(tmp_path / "receipts", root)


def test_all_retrospective_reports_marked_unfit_for_prospective_claims():
    assert quality.SCHEMA.endswith("retrospective-quality-v1")
    assert sum(quality.EVENTS.values()) == 473
    assert quality.JASS_COMMIT == "cfe07fce6385b980553a898e9651d53419589ebc"
