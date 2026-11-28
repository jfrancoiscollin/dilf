"""Score-blind pair-denominator regression tests (synthetic only)."""
import pytest

from research.mtdp.decision_equivalence.signature_collision_metrics import measure


def row(pid, gid, signature):
    return {"position_id": pid, "game_id": gid, "signature": signature}


def test_pair_denominators_are_all_unordered_positions_not_just_collisions():
    rows = [row("p1", "g1", "a"), row("p2", "g1", "a"),
            row("p3", "g2", "a"), row("p4", "g3", "b")]
    m = measure(rows)
    assert m["collision_pairs"] == 3
    assert m["same_game_collision_pairs"] == 1
    assert m["cross_game_collision_pairs"] == 2
    assert m["collision_pair_fraction"] == pytest.approx(3 / 6)
    assert m["cross_game_pair_fraction_all_positions"] == pytest.approx(2 / 6)
    assert m["cross_game_collision_pair_fraction"] == pytest.approx(2 / 3)
    assert not m["decision_equivalence_established"]
    assert not m["minimax_equivalence_established"]


def test_single_position_has_undefined_pair_rates():
    m = measure([row("p1", "g1", "a")])
    assert m["collision_pairs"] == 0
    assert m["same_game_collision_pairs"] == 0
    assert m["collision_pair_fraction"] is None
    assert m["cross_game_pair_fraction_all_positions"] is None


def test_no_collisions_two_positions_have_zero_unconditional_rates():
    m = measure([row("p1", "g1", "a"), row("p2", "g2", "b")])
    assert m["collision_pair_fraction"] == 0
    assert m["cross_game_pair_fraction_all_positions"] == 0
    assert m["cross_game_collision_pair_fraction"] is None
