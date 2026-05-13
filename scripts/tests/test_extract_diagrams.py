"""Unit tests for the offline parts of scripts/extract_diagrams.py.

These exercise pure-Python helpers (validation, JSON parsing, caption
regex, page-range expansion). The image / API parts are covered by hand
when the workflow is run on the user's machine.
"""

from __future__ import annotations

import pytest

from scripts.extract_diagrams import (
    _CAPTION_RE,
    _parse_pages,
    parse_api_response,
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
            "black_men": [],
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
            "black_men": [],
            "black_kings": [],
            "turn": "white",
        }
    )
    assert ok is False
    assert "more than one" in msg


def test_validate_position_rejects_invalid_turn() -> None:
    ok, msg = validate_position(
        {
            "white_men": [],
            "white_kings": [],
            "black_men": [],
            "black_kings": [],
            "turn": "yellow",
        }
    )
    assert ok is False
    assert "turn" in msg


def test_validate_position_propagates_model_error_payload() -> None:
    ok, msg = validate_position({"error": "image_unclear"})
    assert ok is False
    assert "image_unclear" in msg


# ---------------------------------------------------------------------------
# parse_api_response
# ---------------------------------------------------------------------------


def test_parse_api_response_handles_plain_json() -> None:
    payload = parse_api_response('{"turn": "white"}')
    assert payload == {"turn": "white"}


def test_parse_api_response_strips_markdown_fences() -> None:
    raw = '```json\n{"turn": "black"}\n```'
    assert parse_api_response(raw) == {"turn": "black"}


def test_parse_api_response_strips_unlabelled_fences() -> None:
    raw = '```\n{"turn": "white"}\n```'
    assert parse_api_response(raw) == {"turn": "white"}


def test_parse_api_response_raises_on_garbage() -> None:
    with pytest.raises(Exception):
        parse_api_response("not json at all")


# ---------------------------------------------------------------------------
# _CAPTION_RE
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


def test_caption_regex_ignores_lines_without_diagram_id() -> None:
    matches = list(_CAPTION_RE.finditer("Une combinaison naturelle (trait aux blancs)"))
    assert matches == []


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
