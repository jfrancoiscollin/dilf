"""Tests for ``scripts.scan_citations``.

Reads the live ``scan_analysis_debutant.json`` so every test exercises
the real JSON schema. The assertions check formatting invariants, not
specific eval numbers, so they survive future Scan re-runs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.scan_citations import (
    FORCED_GAIN_THRESHOLD,
    ScanEntry,
    citation_block,
    load_index,
    table_header,
    table_row,
)


@pytest.fixture(scope="module")
def index() -> dict[str, ScanEntry]:
    return load_index()


def test_index_covers_full_debutant_corpus(index):
    """All 166 BEG_CHnn_mmm fixtures are indexed."""
    assert len(index) == 166
    chapters = {fid.split("_")[1] for fid in index}
    assert chapters == {f"CH{n:02d}" for n in range(1, 17)}


def test_every_entry_is_verified(index):
    """All entries are Scan-verified — this is the precondition of the refactor."""
    not_verified = [fid for fid, e in index.items() if not e.verified]
    assert not_verified == [], f"unverified entries: {not_verified}"


def test_citation_block_includes_required_fields(index):
    entry = index["BEG_CH07_001"]
    block = citation_block(entry)
    assert "PV Scan" in block
    assert f"profondeur {entry.scan_depth}" in block
    assert f"{entry.eval_after_pv:+.2f}" in block
    # PV is rendered with × not x
    assert "×" in block or not any("x" in ply for ply in entry.pv)
    assert "x " not in block  # bare lowercase x is the only thing we forbid


def test_citation_block_flags_divergence(index):
    diverg = index["BEG_CH15_004"]
    block = citation_block(diverg)
    assert "Divergence flaggée" in block
    assert "33-29" in block  # the Scan first move
    assert "34-29" in block  # the published first move from the note


def test_citation_block_omits_divergence_when_clean(index):
    clean = index["BEG_CH07_001"]
    assert "Divergence" not in citation_block(clean)


def test_forced_gain_phrasing(index):
    """Evals ≥ +90 trigger the 'gain forcé' wording, not 'blancs gagnants'."""
    forced = next(e for e in index.values() if e.eval_after_pv >= FORCED_GAIN_THRESHOLD)
    block = citation_block(forced)
    assert "gain forcé" in block
    assert "blancs gagnants" not in block


def test_normal_eval_phrasing(index):
    """Evals in the normal range use the side-label without 'gain forcé'."""
    normal = next(
        e for e in index.values()
        if 0.5 < e.eval_after_pv < FORCED_GAIN_THRESHOLD and e.winning_for == "white"
    )
    block = citation_block(normal)
    assert "blancs gagnants" in block
    assert "gain forcé" not in block


def test_table_row_marks_forced_gain_with_asterisk(index):
    forced = next(e for e in index.values() if e.eval_after_pv >= FORCED_GAIN_THRESHOLD)
    row = table_row(forced)
    assert "*" in row.split("|")[3]  # eval cell


def test_table_row_uses_redflag_for_divergence(index):
    diverg = index["BEG_CH15_004"]
    row = table_row(diverg)
    assert "🔴" in row


def test_table_row_uses_dash_when_no_divergence(index):
    clean = index["BEG_CH07_001"]
    row = table_row(clean)
    # Divergence cell is the last one before the trailing pipe
    cells = [c.strip() for c in row.split("|")]
    assert cells[-2] == "—"


def test_table_header_column_count_matches_row(index):
    header = table_header()
    row = table_row(index["BEG_CH07_001"])
    assert header.split("\n")[0].count("|") == row.count("|")


def test_pv_normalization_uses_uppercase_cross():
    """The lowercase 'x' from the JSON PV is rewritten to '×' in output."""
    fake = ScanEntry(
        fixture_id="TEST_001",
        best_move="32-28",
        eval_after_pv=1.0,
        scan_depth=20,
        verified=True,
        winning_for="white",
        pv=("32-28", "19x28x21x32", "37x28"),
        notes="",
    )
    block = citation_block(fake)
    assert "19×28×21×32" in block
    assert "x" not in block.split(":")[1]  # no lowercase x in the PV
