"""D1-B pairwise collision accounting, using synthetic score-blind records."""
from research.mtdp.decision_equivalence.signature_collision_audit import audit


def test_pairwise_collision_counts_distinguish_game_and_successor():
    rows = [
        {"game_id": "g1", "position_id": "p1", "signatures": {"L": "same"}, "successor_fingerprint": "A"},
        {"game_id": "g1", "position_id": "p2", "signatures": {"L": "same"}, "successor_fingerprint": "B"},
        {"game_id": "g2", "position_id": "p3", "signatures": {"L": "same"}, "successor_fingerprint": "A"},
        {"game_id": "g3", "position_id": "p4", "signatures": {"L": "other"}, "successor_fingerprint": "C"},
    ]
    metrics = audit(rows)["families"]["L"]
    assert metrics["collision_pairs"] == 3
    assert metrics["cross_game_collision_pairs"] == 2
    assert metrics["successor_divergent_collision_pairs"] == 2
    assert metrics["cross_game_successor_divergent_pairs"] == 1
    assert metrics["collision_groups"] == 1
    assert metrics["successor_divergent_collision_groups"] == 1


def test_pairwise_no_collision():
    rows = [
        {"game_id": "g1", "position_id": "p1", "signatures": {"L": "a"}, "successor_fingerprint": "A"},
        {"game_id": "g2", "position_id": "p2", "signatures": {"L": "b"}, "successor_fingerprint": "B"},
    ]
    metrics = audit(rows)["families"]["L"]
    assert metrics["collision_pairs"] == 0
    assert metrics["cross_game_successor_divergent_pairs"] == 0
