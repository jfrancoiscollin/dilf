"""Synthetic content-addressed D1 admission tests; NOT an independent cohort."""
import hashlib

import pytest

from pedagogy.game import state_to_fen
from research.mtdp.pdn import parse_games, validated_trajectory
from research.mtdp.tests.test_pdn import MockRules
from research.mtdp.decision_equivalence.content_addressed_admission import (
    audit_content_addressed_games,
)

PDN = b'[Event "synthetic"]\n1. 32-28 17-22 *\n'


def fixture(tmp_path):
    path = tmp_path / "source.pdn"
    path.write_bytes(PDN)
    digest = hashlib.sha256(PDN).hexdigest()
    game_id = f"{digest}:1"
    game = parse_games(PDN.decode())[0]
    positions = validated_trajectory(game, MockRules())
    rows = [{
        "game_id": game_id,
        "tournament_id": "synthetic-tournament",
        "event_id": "synthetic-event",
        "fen": state_to_fen(positions[ply][2]),
        "split": "train",
        "ply": ply,
        "source_pdn_sha256": digest,
    } for ply in (0, 1, 2)]
    return rows, {game_id: path}


def test_accepts_full_authenticated_trajectory_but_not_independent_cohort(tmp_path):
    rows, sources = fixture(tmp_path)
    result = audit_content_addressed_games(rows, sources, MockRules())
    assert result["manifest_game_id_binding_verified"]
    assert result["fmjd_legality_verified"]
    assert result["verified_games"] == 1
    assert result["independent_cohort_qualified"] is False


def test_rejects_arbitrary_game_id_even_with_correct_source(tmp_path):
    rows, sources = fixture(tmp_path)
    for row in rows:
        row["game_id"] = "unbound-id"
    with pytest.raises(ValueError, match="game_id must bind"):
        audit_content_addressed_games(rows, {"unbound-id": next(iter(sources.values()))}, MockRules())


@pytest.mark.parametrize("suffix", ["0", "01", "+1", "1x", "١"])
def test_rejects_noncanonical_game_index(tmp_path, suffix):
    rows, sources = fixture(tmp_path)
    digest = rows[0]["source_pdn_sha256"]
    for row in rows:
        row["game_id"] = f"{digest}:{suffix}"
    with pytest.raises(ValueError):
        audit_content_addressed_games(rows, {rows[0]["game_id"]: next(iter(sources.values()))}, MockRules())


def test_rejects_fen_from_wrong_ply(tmp_path):
    rows, sources = fixture(tmp_path)
    rows[2]["fen"] = rows[1]["fen"]
    with pytest.raises(ValueError, match="FEN"):
        audit_content_addressed_games(rows, sources, MockRules())


def test_rejects_tampered_pdn_bytes(tmp_path):
    rows, sources = fixture(tmp_path)
    next(iter(sources.values())).write_bytes(PDN + b"\n")
    with pytest.raises(ValueError, match="digest"):
        audit_content_addressed_games(rows, sources, MockRules())
