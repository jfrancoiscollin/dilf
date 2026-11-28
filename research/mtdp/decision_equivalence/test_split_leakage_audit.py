"""Synthetic metadata-only D1 leakage audit tests; no prospective targets used."""
import pytest
from research.mtdp.decision_equivalence.split_leakage_audit import audit_game_partitions


def rows():
    return [
        {"game_id": "g1", "split": "train", "fen": "FEN-A", "source_id": "tournament-a"},
        {"game_id": "g1", "split": "train", "fen": "FEN-B", "source_id": "tournament-a"},
        {"game_id": "g2", "split": "test", "fen": "FEN-C", "source_id": "tournament-b"},
    ]


def test_clean_partition_counts_are_score_blind():
    assert audit_game_partitions(rows()) == {
        "n_games": 2, "n_positions": 3, "n_train_games": 1,
        "n_test_games": 1, "score_blind": True
    }


@pytest.mark.parametrize("mutation,pattern", [
    (lambda r: r[1].update(split="test"), "game crosses"),
    (lambda r: r[2].update(fen="FEN-A"), "position reused"),
    (lambda r: r[2].update(source_id="tournament-a"), "source overlap"),
    (lambda r: r[2].update(split="train"), "both train and test"),
    (lambda r: r[2].update(split="validation"), "unknown split"),
    (lambda r: r[2].update(game_id=""), "missing metadata"),
])
def test_partition_violations_fail_closed(mutation, pattern):
    data = rows()
    mutation(data)
    with pytest.raises(ValueError, match=pattern):
        audit_game_partitions(data)


def test_reserved_game_and_fen_rejected():
    with pytest.raises(ValueError, match="reserved"):
        audit_game_partitions(rows(), reserved_game_ids={"g2"})
    with pytest.raises(ValueError, match="reserved"):
        audit_game_partitions(rows(), reserved_fens={"FEN-B"})


def test_duplicate_position_in_same_game_rejected():
    data = rows()
    data.append(dict(data[0]))
    with pytest.raises(ValueError, match="duplicate"):
        audit_game_partitions(data)
