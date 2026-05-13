"""Unit tests for the offline parts of scripts/extract_diagrams.py.

Covers pure-Python helpers (validation, caption regex, page-range expansion,
square numbering) and the pixel-sampling extractor on synthetic boards. The
PDF rendering path is exercised by hand when the workflow runs on real
corpus PDFs.
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.extract_diagrams import (
    _CAPTION_RE,
    _count_diagram_captions,
    _infer_turn,
    _parse_pages,
    _square_number,
    analyze_board_fen,
    validate_position,
)


# ---------------------------------------------------------------------------
# validate_position
# ---------------------------------------------------------------------------


def test_validate_position_accepts_well_formed_payload() -> None:
    ok, msg = validate_position(
        {
            "white_men": [31, 32, 33],
            "white_kings": [28],
            "black_men": [1, 2],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is True
    assert msg == ""


def test_validate_position_flags_missing_keys() -> None:
    ok, msg = validate_position({"white_men": [], "turn": "white"})
    assert ok is False
    assert "missing key" in msg


def test_validate_position_rejects_out_of_range_square() -> None:
    ok, msg = validate_position(
        {
            "white_men": [99],
            "white_kings": [],
            "black_men": [1],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is False
    assert "invalid square" in msg


def test_validate_position_rejects_overlapping_squares() -> None:
    ok, msg = validate_position(
        {
            "white_men": [28],
            "white_kings": [28],
            "black_men": [1],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is False
    assert "more than one" in msg


def test_validate_position_rejects_invalid_turn() -> None:
    ok, msg = validate_position(
        {
            "white_men": [31],
            "white_kings": [],
            "black_men": [1],
            "black_kings": [],
            "turn": "yellow",
        }
    )
    assert ok is False
    assert "turn" in msg


def test_validate_position_rejects_position_with_no_white_pieces() -> None:
    ok, msg = validate_position(
        {
            "white_men": [],
            "white_kings": [],
            "black_men": [1],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is False
    assert "white" in msg.lower()


def test_validate_position_rejects_position_with_no_black_pieces() -> None:
    ok, msg = validate_position(
        {
            "white_men": [31],
            "white_kings": [],
            "black_men": [],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is False
    assert "black" in msg.lower()


# ---------------------------------------------------------------------------
# _parse_pages
# ---------------------------------------------------------------------------


def test_parse_pages_all_yields_full_range() -> None:
    assert _parse_pages("all", 5) == [1, 2, 3, 4, 5]


def test_parse_pages_handles_single_value() -> None:
    assert _parse_pages("3", 10) == [3]


def test_parse_pages_handles_range_and_list() -> None:
    assert _parse_pages("5-7,10", 20) == [5, 6, 7, 10]


def test_parse_pages_clamps_to_page_count() -> None:
    assert _parse_pages("5-15", 7) == [5, 6, 7]
    assert _parse_pages("0,1,3", 5) == [1, 3]


# ---------------------------------------------------------------------------
# _CAPTION_RE / _count_diagram_captions
# ---------------------------------------------------------------------------


def test_caption_regex_matches_typical_line() -> None:
    line = "D1 : trait aux noirs              D2 : trait aux blancs"
    matches = list(_CAPTION_RE.finditer(line))
    assert [m.group(1) for m in matches] == ["D1", "D2"]
    assert [m.group(2).lower() for m in matches] == ["noirs", "blancs"]


def test_caption_regex_is_case_insensitive() -> None:
    matches = list(_CAPTION_RE.finditer("d12: TRAIT AUX BLANCS"))
    assert len(matches) == 1
    assert matches[0].group(1).upper() == "D12"


def test_count_captions_matches_trait_aux() -> None:
    assert _count_diagram_captions("D1 : trait aux blancs\nD2 : trait aux noirs") == 2


def test_count_captions_matches_rafle_continuations() -> None:
    text = "D5 : trait aux blancs\n1ère rafle\n2e rafle\n3e rafle"
    assert _count_diagram_captions(text) == 4


def test_count_captions_ignores_rafle_mentions_in_body_text() -> None:
    text = "Cette rafle gagne facilement, comme on le voit en deux rafles."
    assert _count_diagram_captions(text) == 0


# ---------------------------------------------------------------------------
# _infer_turn
# ---------------------------------------------------------------------------


def test_infer_turn_defaults_to_white_when_caption_is_none() -> None:
    assert _infer_turn(None) == "white"


def test_infer_turn_detects_black_from_trait_aux_noirs() -> None:
    assert _infer_turn("D5 : trait aux noirs") == "black"


def test_infer_turn_returns_white_for_other_captions() -> None:
    assert _infer_turn("D5 : trait aux blancs") == "white"
    assert _infer_turn("2e rafle") == "white"


# ---------------------------------------------------------------------------
# _square_number
# ---------------------------------------------------------------------------


def test_square_number_top_left_dark_square_is_1() -> None:
    # Row 0 col 1 is the first dark square in standard FMJD orientation.
    assert _square_number(0, 1) == 1


def test_square_number_top_right_dark_square_is_5() -> None:
    assert _square_number(0, 9) == 5


def test_square_number_bottom_right_dark_square_is_50() -> None:
    assert _square_number(9, 8) == 50


def test_square_number_light_squares_return_none() -> None:
    # (row + col) even -> light square
    assert _square_number(0, 0) is None
    assert _square_number(1, 1) is None


def test_square_numbers_cover_1_to_50_exactly_once() -> None:
    numbers = [
        _square_number(r, c)
        for r in range(10)
        for c in range(10)
        if _square_number(r, c) is not None
    ]
    assert sorted(numbers) == list(range(1, 51))


# ---------------------------------------------------------------------------
# analyze_board_fen
# ---------------------------------------------------------------------------


def _synthetic_board(
    *,
    size: int = 500,
    margin: int = 10,
    white_squares: set[int] = frozenset(),
    black_squares: set[int] = frozenset(),
    radius: int = 12,
) -> np.ndarray:
    """Render a 10x10 fake Dubois-style page.

    Light squares ~255, dark squares ~120 (empty case), pieces painted as
    discs of pixel value 250 (white piece) or 30 (black piece) at each
    requested FMJD square's center.
    """
    img = np.full((size + 2 * margin, size + 2 * margin), 255, dtype=np.uint8)
    sq = size / 10.0
    for row in range(10):
        for col in range(10):
            if (row + col) % 2 == 0:
                continue  # light square stays white
            x0 = int(margin + col * sq)
            y0 = int(margin + row * sq)
            x1 = int(margin + (col + 1) * sq)
            y1 = int(margin + (row + 1) * sq)
            img[y0:y1, x0:x1] = 120

            n = _square_number(row, col)
            cx = (x0 + x1) // 2
            cy = (y0 + y1) // 2
            yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
            if n in white_squares:
                img[mask] = 250
            elif n in black_squares:
                img[mask] = 30
    return img


def test_analyze_board_fen_classifies_single_white_and_single_black() -> None:
    gray = _synthetic_board(white_squares={31}, black_squares={20})
    whites, blacks = analyze_board_fen(gray, (10, 10, 510, 510))
    assert whites == [31]
    assert blacks == [20]


def test_analyze_board_fen_returns_empty_on_blank_board() -> None:
    gray = _synthetic_board()
    whites, blacks = analyze_board_fen(gray, (10, 10, 510, 510))
    assert whites == []
    assert blacks == []


def test_analyze_board_fen_dense_starting_position() -> None:
    """Materialise a standard FMJD start: white 31-50, black 1-20."""
    gray = _synthetic_board(
        white_squares=set(range(31, 51)),
        black_squares=set(range(1, 21)),
    )
    whites, blacks = analyze_board_fen(gray, (10, 10, 510, 510))
    assert whites == sorted(range(31, 51))
    assert blacks == sorted(range(1, 21))


def test_analyze_board_fen_does_not_misclassify_neighbours() -> None:
    """Putting a piece on square 31 must not contaminate squares 32 or 27."""
    gray = _synthetic_board(white_squares={31})
    whites, blacks = analyze_board_fen(gray, (10, 10, 510, 510))
    assert whites == [31]
    assert 32 not in whites
    assert 27 not in whites
