"""Synthetic score-blind MTDP-D1 audit tests; no empirical strength claim."""
import json

import pytest

from research.mtdp.decision_equivalence.score_blind_audit import audit


def row(fen, game, actions, l, q):
    return {"fen": fen, "game_id": game, "actions": actions,
            "signatures": {"L": l, "Q": q}}


def test_collisions_are_score_blind_and_deterministic():
    a = row("A", "game-1", [["31", "26"]], "shared", "safe")
    b = row("B", "game-2", [["31", "26"]], "shared", "safe")
    c = row("C", "game-3", [["32", "28"]], "shared", "different")
    first = audit([c, a, b])
    second = audit([b, c, a])
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["distinct_fens"] == 3
    assert first["signature_audits"]["L"]["distinct_fen_pairs"] == 3
    assert first["signature_audits"]["L"]["different_legal_action_pairs"] == 2
    assert first["signature_audits"]["Q"]["different_legal_action_pairs"] == 0
    assert first["signature_audits"]["Q"]["same_legal_action_pairs"] == 1
    assert first["signature_audits"]["Q"]["cross_game_pairs"] == 1
    assert first["signature_audits"]["Q"]["compression_fraction"] == pytest.approx(1 / 3)


def test_duplicate_fen_merges_game_provenance_without_inflating_pairs():
    a = row("A", "g1", [[1]], 0, "q")
    b = row("B", "g1", [[1]], 0, "q")
    a2 = row("A", "g2", [[1]], 0, "q")
    result = audit([a, b, a2])
    assert result["observations"] == 3
    assert result["distinct_fens"] == 2
    assert result["signature_audits"]["Q"]["distinct_fen_pairs"] == 1
    assert result["signature_audits"]["Q"]["cross_game_pairs"] == 1


@pytest.mark.parametrize("bad", [
    {"fen": "", "game_id": "g", "actions": [], "signatures": {"L": 1}},
    {"fen": "A", "game_id": "", "actions": [], "signatures": {"L": 1}},
    {"fen": "A", "game_id": "g", "actions": [[1], [1]], "signatures": {"L": 1}},
    {"fen": "A", "game_id": "g", "actions": [], "signatures": {}},
])
def test_invalid_records_fail_closed(bad):
    with pytest.raises(ValueError):
        audit([bad])


def test_conflicting_duplicate_fen_fails_closed():
    with pytest.raises(ValueError, match="contradictory duplicate"):
        audit([row("A", "g1", [[1]], "l", "q"),
               row("A", "g2", [[2]], "l", "q")])


def test_missing_signature_variant_fails_closed():
    with pytest.raises(ValueError, match="incomplete"):
        audit([row("A", "g1", [[1]], "l", "q"),
               {"fen": "B", "game_id": "g2", "actions": [[1]],
                "signatures": {"L": "l"}}])


def test_empty_input_is_well_defined():
    report = audit([])
    assert report["distinct_fens"] == 0
    assert report["signature_audits"] == {}
