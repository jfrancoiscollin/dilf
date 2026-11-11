import os
from pathlib import Path

import pytest

from pedagogy.game import Move, initial_state, parse_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_move_mapping import (
    MoveMappingError,
    map_root_moves,
    read_jass_catalogues,
)


def test_mapping_preserves_full_canonical_identity_and_sorts_victims():
    moves = [
        Move((48, 37, 19, 30), (42, 32, 24)),
        Move((48, 26, 8, 30), (24, 42, 12)),
    ]
    assert map_root_moves(moves, [("48x30x12x24x42", False), ("48x30x24x32x42", False)]) == {
        ((48, 37, 19, 30), (24, 32, 42), False): "48x30x24x32x42",
        ((48, 26, 8, 30), (12, 24, 42), False): "48x30x12x24x42",
    }


def test_mapping_rejects_collapsed_capture_paths():
    moves = [Move((37, 28, 5), (32, 14)), Move((37, 23, 5), (32, 14))]
    with pytest.raises(MoveMappingError, match="Ambiguous DILF root key: 37x5x14x32"):
        map_root_moves(moves, [("37x5x14x32", False)])


@pytest.mark.parametrize(
    "catalogue, message",
    [
        ([], "Root catalogue mismatch"),
        ([("7-1", True), ("7-2", True)], "Root catalogue mismatch"),
        ([("7-1", False)], "Root catalogue mismatch"),
        ([("7-1", True), ("7-1", True)], "Duplicate Jass root key"),
    ],
)
def test_mapping_checks_entire_catalogue(catalogue, message):
    with pytest.raises(MoveMappingError, match=message):
        map_root_moves([Move((7, 1), promotion=True)], catalogue)


def test_against_pinned_jass_catalogue():
    executable = os.environ.get("MTDP_JASS_CATALOGUE")
    if not executable:
        pytest.skip("Build the optional Jass integration target and set MTDP_JASS_CATALOGUE")
    engine = create_engine()
    states = [
        initial_state(),
        parse_fen("W:W7,8:B40"),
        parse_fen("W:WK48:B4,7,12,16,24,32,42"),
        parse_fen("W:WK37:B14,32,35,39,47,49"),
        parse_fen("W:W:B14"),
    ]
    quiet, promotion, captures, ambiguous, terminal = read_jass_catalogues(Path(executable), states)
    assert len(map_root_moves(engine.legal_moves(states[0]), quiet)) == 9
    assert any(promotes for _, promotes in promotion)
    assert len(map_root_moves(engine.legal_moves(states[1]), promotion)) == 4
    assert len(map_root_moves(engine.legal_moves(states[2]), captures)) == 4
    assert ("37x5x14x32", False) in ambiguous
    with pytest.raises(MoveMappingError, match="Ambiguous DILF root key"):
        map_root_moves(engine.legal_moves(states[3]), ambiguous)
    assert map_root_moves(engine.legal_moves(states[4]), terminal) == {}
