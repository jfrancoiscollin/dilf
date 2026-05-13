"""Unit tests for the offline parts of scripts/extract_diagrams.py.

These exercise pure-Python helpers (validation, JSON parsing, caption
regex, page-range expansion). The image / API parts are covered by hand
when the workflow is run on the user's machine.
"""

from __future__ import annotations

import pytest

from scripts.extract_diagrams import (
    _CAPTION_RE,
    STRICT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    _assistant_json_block,
    _count_diagram_captions,
    _parse_pages,
    _user_image_block,
    parse_api_response,
    validate_position,
)
from pedagogy.tests.fixtures.dubois_ground_truth import (
    EXAMPLES,
    FewShotExample,
    load_examples,
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


# ---------------------------------------------------------------------------
# _count_diagram_captions
# ---------------------------------------------------------------------------


def test_count_captions_matches_trait_aux() -> None:
    text = "D1 : trait aux blancs\nD2 : trait aux noirs"
    assert _count_diagram_captions(text) == 2


def test_count_captions_matches_rafle_continuations() -> None:
    text = "D5 : trait aux blancs\n1ère rafle\n2e rafle\n3e rafle"
    assert _count_diagram_captions(text) == 4


def test_count_captions_is_case_insensitive() -> None:
    assert _count_diagram_captions("TRAIT AUX BLANCS\n2E RAFLE") == 2


def test_count_captions_returns_zero_on_text_only_page() -> None:
    assert _count_diagram_captions("Une page de pure prose, sans diagramme.") == 0


def test_count_captions_ignores_rafle_mentions_in_body_text() -> None:
    text = "Cette rafle gagne facilement, comme on le voit en deux rafles."
    assert _count_diagram_captions(text) == 0


# ---------------------------------------------------------------------------
# STRICT_SYSTEM_PROMPT
# ---------------------------------------------------------------------------


def test_strict_prompt_extends_base_prompt() -> None:
    assert STRICT_SYSTEM_PROMPT.startswith(SYSTEM_PROMPT)
    assert "RETRY" in STRICT_SYSTEM_PROMPT
    assert "at most one" in STRICT_SYSTEM_PROMPT.lower()


def test_system_prompt_warns_against_hallucinated_kings() -> None:
    assert "ZERO kings" in SYSTEM_PROMPT
    assert "inner mark" in SYSTEM_PROMPT


def test_system_prompt_warns_against_regular_patterns() -> None:
    assert "Do NOT default to regular geometric patterns" in SYSTEM_PROMPT


def test_system_prompt_anchors_numbering_with_examples() -> None:
    assert "Square 1 is the top-left dark square" in SYSTEM_PROMPT
    assert "Square 50 is the bottom-right dark square" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------


def test_user_image_block_has_image_and_text_parts() -> None:
    block = _user_image_block(b"\x89PNG\r\n\x1a\n")
    assert block["role"] == "user"
    content = block["content"]
    assert content[0]["type"] == "image"
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[1]["type"] == "text"
    assert content[1]["text"] == "Extract the position."


def test_assistant_json_block_emits_compact_json() -> None:
    block = _assistant_json_block({"white_men": [31, 32], "turn": "white"})
    assert block["role"] == "assistant"
    text = block["content"][0]["text"]
    assert text == '{"white_men":[31,32],"turn":"white"}'


def test_load_examples_returns_empty_when_n_is_zero() -> None:
    assert load_examples(0) == []
    assert load_examples(-1) == []


def test_load_examples_empty_when_no_examples_registered() -> None:
    # Until ground-truth examples are populated EXAMPLES is empty and
    # load_examples gracefully returns nothing so --few-shot N > 0 is a no-op.
    if not EXAMPLES:
        assert load_examples(5) == []


def test_few_shot_example_dataclass_shape() -> None:
    example = FewShotExample(
        name="smoke",
        image_filename="x.png",
        position={"turn": "white"},
    )
    assert example.name == "smoke"
    assert example.image_filename == "x.png"
    assert example.position == {"turn": "white"}
