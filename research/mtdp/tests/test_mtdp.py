"""Focused invariants for the first MTDP research dataset."""
from __future__ import annotations

import json

from pedagogy.game import initial_state, parse_fen
from research.mtdp.dataset import record, write_jsonl
from research.mtdp.metrics import compute_spatial_metrics


def test_initial_position() -> None:
    metrics = compute_spatial_metrics(initial_state())
    assert metrics.white_pieces == metrics.black_pieces == 20
    assert metrics.occupied_squares == 40
    assert metrics.occupied_fraction == 0.8
    assert metrics.material_balance == 0


def test_empty_position() -> None:
    metrics = compute_spatial_metrics(parse_fen("W:W:B"))
    assert metrics.occupied_squares == 0
    assert metrics.adjacency_edges_white == 0
    assert metrics.adjacency_edges_black == 0


def test_adjacency_counts_undirected_edges_once() -> None:
    metrics = compute_spatial_metrics(parse_fen("W:W31,26:B1"))
    assert metrics.adjacency_edges_white == 1
    assert metrics.adjacency_edges_black == 0


def test_record_is_deterministic_and_serializable(tmp_path) -> None:
    state = initial_state()
    a = record(state, source="test", source_id="initial")
    b = record(state, source="test", source_id="initial")
    assert a == b
    output = tmp_path / "sample.jsonl"
    assert write_jsonl([a], output) == 1
    assert json.loads(output.read_text(encoding="utf-8").strip()) == a
    assert a["schema_version"] == "mtdp-position-v1"
