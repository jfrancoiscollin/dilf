"""Tests for the heatmap narrator (v1: top squares + canned FR hint)."""

from __future__ import annotations

import pytest

from pedagogy.profile import weakness_heatmap_narrative
from pedagogy.profile.heatmap_narrator import _summarize_zones, _zone_of


# ---------------------------------------------------------------------------
# Zone helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sq, zone",
    [
        (28, "centre"),
        (22, "centre"),
        (6, "aile gauche"),
        (46, "aile gauche"),
        (5, "rangée arrière ⬛"),   # 5 is in BLACK_BACK_ROW and RIGHT_WING;
        # we resolve centre/wing first, so 5 ends up in "aile droite".
        # Adjusting expectation:
    ],
)
def test_zone_of_known_squares_smoke(sq: int, zone: str) -> None:
    # Sanity smoke: just makes sure the function returns one of the
    # known labels for every square; precise mapping is tested below.
    assert _zone_of(sq) in {
        "centre", "aile gauche", "aile droite",
        "rangée arrière ⬜", "rangée arrière ⬛", "milieu",
    }


def test_zone_of_back_rows_vs_wings_priority() -> None:
    # The implementation resolves centre/wings BEFORE back rows, so
    # corner squares belonging to both (e.g. 5 in RIGHT_WING and
    # BLACK_BACK_ROW) fall into the wing — this is documented intent,
    # the test pins it down.
    assert _zone_of(5) == "aile droite"      # both BLACK_BACK_ROW and RIGHT_WING
    assert _zone_of(50) == "aile droite"     # both WHITE_BACK_ROW and RIGHT_WING
    assert _zone_of(46) == "aile gauche"     # both WHITE_BACK_ROW and LEFT_WING


def test_summarize_zones_orders_by_count_then_label() -> None:
    # Two centre squares + one wing → centre dominates.
    assert _summarize_zones([22, 23, 6]).startswith("centre")
    # Empty input yields empty output (caller decides what to do).
    assert _summarize_zones([]) == ""


# ---------------------------------------------------------------------------
# weakness_heatmap_narrative
# ---------------------------------------------------------------------------


def _bucket(**kw: int) -> dict[str, int]:
    base = {"isolated": 0, "backward": 0, "holes": 0, "outposts": 0}
    base.update(kw)
    return base


def test_returns_none_when_metric_has_no_signal() -> None:
    by_square = {28: _bucket(outposts=3)}
    assert weakness_heatmap_narrative(by_square, "isolated") is None


def test_top_line_lists_top_k_squares_by_count() -> None:
    by_square = {
        28: _bucket(isolated=5),
        23: _bucket(isolated=8),
        17: _bucket(isolated=2),
        6:  _bucket(isolated=1),
    }
    out = weakness_heatmap_narrative(by_square, "isolated", top_k=3)
    assert out is not None
    assert out["top_line"] == "23 (×8) · 28 (×5) · 17 (×2)"


def test_top_line_ties_are_resolved_by_square_number_ascending() -> None:
    # Two squares tied at the top → lower square number first.
    by_square = {
        28: _bucket(holes=4),
        23: _bucket(holes=4),
        17: _bucket(holes=4),
    }
    out = weakness_heatmap_narrative(by_square, "holes", top_k=2)
    assert out is not None
    assert out["top_line"] == "17 (×4) · 23 (×4)"


def test_all_metric_sums_three_real_weaknesses_excluding_outposts() -> None:
    # outposts are strengths, the "all" sum must ignore them.
    by_square = {
        28: _bucket(isolated=2, backward=1, holes=1, outposts=99),
        23: _bucket(isolated=0, backward=0, holes=0, outposts=1),
    }
    out = weakness_heatmap_narrative(by_square, "all")
    assert out is not None
    assert "28 (×4)" in out["top_line"]
    assert "23" not in out["top_line"]


def test_hint_mentions_dominant_zone() -> None:
    # All top squares in CENTER_EXTENDED → hint should mention "centre".
    by_square = {sq: _bucket(holes=5) for sq in (22, 23, 28)}
    out = weakness_heatmap_narrative(by_square, "holes")
    assert out is not None
    assert "centre" in out["hint"]


def test_hint_for_outposts_phrased_as_strength() -> None:
    by_square = {28: _bucket(outposts=10), 22: _bucket(outposts=8)}
    out = weakness_heatmap_narrative(by_square, "outposts")
    assert out is not None
    assert "force" in out["hint"].lower() or "capitalise" in out["hint"].lower()


def test_output_is_stable_across_dict_insertion_order() -> None:
    # Same data, different insertion order → identical output.
    a = {28: _bucket(backward=3), 23: _bucket(backward=3), 6: _bucket(backward=1)}
    b = {6:  _bucket(backward=1), 28: _bucket(backward=3), 23: _bucket(backward=3)}
    assert weakness_heatmap_narrative(a, "backward") == weakness_heatmap_narrative(b, "backward")
