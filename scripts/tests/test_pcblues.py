"""Unit tests for the PC Blues refinery (rules, notation, replay).

The end-to-end fixture is the Demesmaecker - Verpoest H. 1959 fragment
(deel 15, page 12, diagram 5): its published sequence exercises backward
man rafles ("29x20" = triple), a sacrifice chain and a 3-capture finish —
all from a pixel-extracted anchor position.
"""

import pytest

from pedagogy.game import GameState, parse_fen
from scripts.pcblues.notation import extract_runs, parse_line_tokens
from scripts.pcblues.replay import anchor_run, replay_tokens
from scripts.pcblues.rules import (
    IllegalMoveError,
    apply_move,
    legal_moves,
    match_token,
)

DIAG5_FEN = "W:W29,30,36,37,39,42,43,45,47,48:B3,12,13,14,15,16,18,21,22,26"


def test_prise_maximale_globale() -> None:
    # White can capture 1 with 28 (28x19) or 2 with 39 (39x19) -> only the
    # 2-capture is legal, and the quiet moves disappear.
    state = parse_fen("W:W28,39,40:B23,33,34")
    moves = [r.move for r in legal_moves(state)]
    assert all(m.is_capture for m in moves)
    assert {len(m.captures) for m in moves} == {2}


def test_quiet_move_rejected_when_capture_available() -> None:
    state = parse_fen("W:W28,40:B23")
    with pytest.raises(IllegalMoveError, match="capture is mandatory"):
        match_token(state, 40, 34, is_capture=False)


def test_promotion_on_move_end_only() -> None:
    state = parse_fen("W:W6:B20")
    resolved = match_token(state, 6, 1, is_capture=False)
    after = apply_move(state, resolved)
    assert 1 in after.white_kings and not after.white_men


def test_man_backward_capture() -> None:
    # International rules: men capture backward. White 29 must take 33.
    state = parse_fen("W:W29:B33,20")
    resolved = match_token(state, 29, 38, is_capture=True)
    assert set(resolved.move.captures) == {33}


def test_tokenizer_grades_ellipsis_and_results() -> None:
    line = "37. 45-40 ?! 18-23 ?  38. 29x20 15x33  39. 42-38 33x31"
    groups = parse_line_tokens(line)
    assert len(groups) == 1
    toks = groups[0]
    assert [(t.frm, t.to, t.capture) for t in toks] == [
        (45, 40, False), (18, 23, False), (29, 20, True),
        (15, 33, True), (42, 38, False), (33, 31, True),
    ]
    assert toks[0].grade == "?!" and toks[1].grade == "?"

    runs = extract_runs("16. ...  14-19  17. 25x23 22-28\n40. 36x07  2-0")
    assert runs[0].black_starts
    assert runs[-1].result == "2-0"


def test_tokenizer_prose_gap_splits_inline_alternative() -> None:
    line = "46. 20-14 ! 27-31   Met 26-31 komt zwart nog aan een gelijk spel"
    groups = parse_line_tokens(line)
    assert [(t.frm, t.to) for t in groups[0]] == [(20, 14), (27, 31)]
    assert [(t.frm, t.to) for t in groups[1]] == [(26, 31)]


def test_zero_padded_squares() -> None:
    toks = parse_line_tokens("50. 05x19 08-13")[0]
    assert [(t.frm, t.to) for t in toks] == [(5, 19), (8, 13)]


def test_diag5_fragment_replays_end_to_end() -> None:
    state0 = parse_fen(DIAG5_FEN)
    runs = extract_runs(
        "37. 45-40 ?! 18-23 ?  38. 29x20 15x33  39. 42-38 33x31\n"
        "40. 36x07  2-0"
    )
    assert len(runs) == 1
    res = anchor_run(state0, runs[0])
    assert res.ok, res.failure
    # "29x20" resolves to the triple backward rafle 29x18x9x20
    triple = res.plies[2].resolved.move
    assert set(triple.captures) == {23, 13, 14}
    # "36x07" finishes 3 pieces down the board
    final = res.plies[-1].resolved.move
    assert final.to_square == 7 and len(final.captures) == 3
    assert res.plies[-1].state_after.pieces_of("black") == frozenset({3, 16, 21, 26})


def test_replay_fails_on_wrong_board() -> None:
    # Same sequence from a shifted position must NOT replay (anchor gate).
    wrong = parse_fen("W:W30,31,36,37,39,42,43,45,47,48:B3,12,13,14,15,16,18,21,22,26")
    runs = extract_runs("37. 45-40 18-23 38. 29x20 15x33 39. 42-38 33x31 40. 36x07")
    res = anchor_run(wrong, runs[0])
    assert not res.ok


def test_auto_king_on_promotion_row() -> None:
    from scripts.pcblues.boards import DetectedBoard
    from scripts.pcblues.extract_combos import board_to_state

    board = DetectedBoard(
        page=1, index=0, bbox=(0, 0, 1, 1),
        white_men=(5, 40), black_men=(20, 50),
    )
    st = board_to_state(board)
    assert st.white_kings == frozenset({5}) and st.white_men == frozenset({40})
    assert st.black_kings == frozenset({50}) and st.black_men == frozenset({20})


def test_king_capture_replay() -> None:
    # Black king on 50 (auto-promoted), rafle over 39 and 28.
    state = parse_fen("B:W28,39:BK50")
    res = replay_tokens(state, extract_runs("50x22")[0].tokens, "black")
    assert res.ok
    assert set(res.plies[0].resolved.move.captures) == {39, 28}
