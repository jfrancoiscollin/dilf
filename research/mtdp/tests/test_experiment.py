"""Checks for deterministic material/phase stratification."""
from __future__ import annotations

from pedagogy.game import initial_state, parse_fen
from research.mtdp.dataset import record
from research.mtdp.experiment import audit_strata, position_stratum


def test_initial_state_stratum() -> None:
    r = record(initial_state(), source="test", source_id="initial")
    s = position_stratum(r)
    assert s.material_balance == 0
    assert s.total_pieces_bin == "31-40"
    assert s.turn == "white"


def test_strata_distinguish_material_and_phase() -> None:
    a = record(initial_state(), source="test", source_id="a")
    b = record(parse_fen("B:W31:B18,19"), source="test", source_id="b")
    result = audit_strata([a, b])
    assert len(result["strata"]) == 2
    assert sum(s["observations"] for s in result["strata"]) == 2
