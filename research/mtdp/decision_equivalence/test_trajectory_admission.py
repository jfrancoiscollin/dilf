"""Synthetic score-blind tests, not an independent FMJD cohort."""
import pytest
from research.mtdp.decision_equivalence.trajectory_admission import audit_trajectory_admission


def rows():
    return [
        dict(game_id="g1", trajectory_id="sha-A", split="train", fen="F-A", source_id="s1"),
        dict(game_id="g1", trajectory_id="sha-A", split="train", fen="F-B", source_id="s1"),
        dict(game_id="g2", trajectory_id="sha-B", split="test", fen="F-C", source_id="s2"),
    ]


def test_clean_metadata_and_no_canonicalization_claim():
    result = audit_trajectory_admission(rows())
    assert result["n_trajectories"] == 2
    assert result["n_games"] == 2
    assert result["score_blind"] is True
    assert result["canonical_ids_verified"] is False


@pytest.mark.parametrize("index,key,value,pattern", [
    (2, "trajectory_id", "sha-A", "trajectory reused"),
    (1, "trajectory_id", "sha-C", "game identity inconsistent"),
    (1, "source_id", "s3", "game identity inconsistent"),
    (2, "trajectory_id", "", "missing canonical"),
    (2, "fen", "F-A", "position reused"),
])
def test_collision_fail_closed(index, key, value, pattern):
    data = rows()
    data[index][key] = value
    with pytest.raises(ValueError, match=pattern):
        audit_trajectory_admission(data)


def test_reserved_trajectory_rejected():
    with pytest.raises(ValueError, match="reserved trajectory"):
        audit_trajectory_admission(rows(), reserved_trajectory_ids={"sha-B"})


def test_invalid_reserved_identifier_rejected():
    with pytest.raises(ValueError, match="invalid reserved"):
        audit_trajectory_admission(rows(), reserved_trajectory_ids={" "})


def test_original_split_guard_still_applies():
    data = rows()
    data[2]["split"] = "train"
    with pytest.raises(ValueError, match="both train and test"):
        audit_trajectory_admission(data)
