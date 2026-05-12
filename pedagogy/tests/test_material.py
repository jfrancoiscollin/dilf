"""Tests for material counting."""

from __future__ import annotations

from pedagogy.features.material import KING_VALUE, count_material, material_balance, total_pieces
from pedagogy.game import initial_state, state_from_pieces


def test_initial_state_material_is_balanced() -> None:
    counts = count_material(initial_state())
    assert counts == {
        "white_men": 20,
        "white_kings": 0,
        "black_men": 20,
        "black_kings": 0,
        "balance": 0,
    }


def test_king_is_worth_three_men_in_balance() -> None:
    s = state_from_pieces(white_kings=[28], black_men=[1, 2, 3])
    counts = count_material(s)
    assert counts["white_kings"] == 1
    assert counts["black_men"] == 3
    # 0 + 3*1 - (3 + 3*0) = 0
    assert counts["balance"] == 0
    assert material_balance(s) == 0
    assert KING_VALUE == 3


def test_material_balance_sign_favours_white_when_extra_man() -> None:
    s = state_from_pieces(
        white_men=[31, 32, 33], white_kings=[], black_men=[1, 2], black_kings=[]
    )
    assert material_balance(s) == 1


def test_total_pieces_counts_men_and_kings() -> None:
    s = state_from_pieces(
        white_men=[31, 32], white_kings=[28], black_men=[1], black_kings=[2]
    )
    assert total_pieces(s) == 5
    assert total_pieces(initial_state()) == 40
