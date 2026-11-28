"""Synthetic checks for eligible-pair collision denominators (score-blind)."""
from research.mtdp.decision_equivalence.signature_collision_metrics import measure


def r(pid, game, signature):
    return {"position_id": pid, "game_id": game, "signature": signature}


def test_eligible_denominators_separate_within_and_cross_game():
    rows = [r("a1", "A", "x"), r("a2", "A", "x"),
            r("a3", "A", "y"), r("b1", "B", "x")]
    m = measure(rows)
    # Six total pairs: three within A, three across A/B.
    # x-group has one same-game collision and two cross-game collisions.
    assert m["eligible_same_game_pairs"] == 3
    assert m["eligible_cross_game_pairs"] == 3
    assert m["same_game_collision_pairs"] == 1
    assert m["cross_game_collision_pairs"] == 2
    assert m["same_game_collision_rate_eligible"] == 1 / 3
    assert m["cross_game_collision_rate_eligible"] == 2 / 3
    assert m["cross_game_pair_fraction_all_positions"] == 2 / 6
    assert not m["decision_equivalence_established"]
    assert not m["minimax_equivalence_established"]


def test_no_cross_game_pairs_is_undefined_not_zero():
    m = measure([r("a1", "A", "x"), r("a2", "A", "x")])
    assert m["eligible_cross_game_pairs"] == 0
    assert m["cross_game_collision_rate_eligible"] is None
    assert m["eligible_same_game_pairs"] == 1
    assert m["same_game_collision_rate_eligible"] == 1


def test_all_cross_game_pairs_have_no_within_game_denominator():
    m = measure([r("a1", "A", "x"), r("b1", "B", "y")])
    assert m["eligible_cross_game_pairs"] == 1
    assert m["cross_game_collision_rate_eligible"] == 0
    assert m["eligible_same_game_pairs"] == 0
    assert m["same_game_collision_rate_eligible"] is None
