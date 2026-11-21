"""Synthetic controls, not independent FMJD observations."""
import pytest
from research.mtdp.decision_equivalence.legal_action_collision_audit import audit_action_sets

def r(pos, sig, moves):
    return dict(game_id="synthetic", position_id=pos, signature=sig, legal_moves=moves)

def test_signature_collision_does_not_imply_action_identity():
    report = audit_action_sets([r("a", "S", ["1-6"]), r("b", "S", ["2-7"])])
    assert report["collision_pairs"] == 1
    assert report["different_legal_action_set_pairs"] == 1
    assert not report["minimax_equivalence_proven"]

def test_order_is_not_action_set():
    report = audit_action_sets([r("a", "S", ["1-6", "2-7"]), r("b", "S", ["2-7", "1-6"])])
    assert report["different_legal_action_set_pairs"] == 0
    assert not report["best_move_equivalence_proven"]

@pytest.mark.parametrize("rows", [
    [r("a", "S", ["1-6"]), r("a", "S", ["1-6"])],
    [r("a", "S", ["1-6", "1-6"])],
    [r("a", "S", [])],
    [r("a", "", ["1-6"])],
])
def test_invalid_rows_fail_closed(rows):
    with pytest.raises(ValueError):
        audit_action_sets(rows)
