"""Regression tests for exact FEN overlap quarantine (synthetic only)."""
import pytest

from research.mtdp.decision_equivalence.fen_overlap_guard import audit_exact_fen_overlap


def row(game, position, fen):
    return {"game_id": game, "position_id": position, "fen": fen}


def test_accept_and_reproduce_ordered_digest():
    rows = [row("g1", "p1", "W:W31:B20"), row("g2", "p2", "B:W31:B20")]
    first = audit_exact_fen_overlap(rows)
    assert first == audit_exact_fen_overlap(rows)
    assert first["unique_exact_fens"] == 2
    assert first["sha256"] != audit_exact_fen_overlap(rows[::-1])["sha256"]


def test_reject_same_fen_across_games():
    with pytest.raises(ValueError, match="duplicate exact FEN"):
        audit_exact_fen_overlap([row("a", "1", "W:W31:B20"),
                                 row("b", "2", "W:W31:B20")])


def test_reject_same_fen_within_game():
    with pytest.raises(ValueError, match="duplicate exact FEN"):
        audit_exact_fen_overlap([row("a", "1", "W:W31:B20"),
                                 row("a", "2", "W:W31:B20")])


def test_reject_reserved_prospective_fen():
    with pytest.raises(ValueError, match="reserved prospective"):
        audit_exact_fen_overlap([row("a", "1", "W:W31:B20")],
                                reserved_fens=["W:W31:B20"])


def test_reject_nested_target_score():
    item = row("a", "1", "W:W31:B20")
    item["metadata"] = {"engine": [{"Best_Move": "31-27"}]}
    with pytest.raises(ValueError, match="target score leakage"):
        audit_exact_fen_overlap([item])


@pytest.mark.parametrize("rows", [[], [row("a", "1", "")], [row("a", "1", None)]])
def test_reject_invalid_input(rows):
    with pytest.raises(ValueError):
        audit_exact_fen_overlap(rows)


def test_reject_whitespace_alias_between_games():
    with pytest.raises(ValueError, match="duplicate FEN whitespace alias"):
        audit_exact_fen_overlap([row("a", "1", "W:W31:B20"),
                                 row("b", "2", " W:W31:B20 ")])


def test_reject_whitespace_alias_against_reserved():
    with pytest.raises(ValueError, match="reserved prospective FEN whitespace alias"):
        audit_exact_fen_overlap([row("a", "1", " W:W31:B20 ")],
                                reserved_fens=["W:W31:B20"])


def test_distinct_fens_still_accepted():
    result = audit_exact_fen_overlap([row("a", "1", "W:W31:B20"),
                                      row("b", "2", "B:W31:B20")])
    assert result["positions"] == 2
