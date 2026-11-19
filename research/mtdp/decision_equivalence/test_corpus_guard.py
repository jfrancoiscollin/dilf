"""Synthetic corpus-guard tests; no FMJD scores or held-out FENs."""
import pytest
from research.mtdp.decision_equivalence.corpus_guard import audit


def row(game="g1", event="historical", split="train", fen="W:W31:B20", ply=1):
    return dict(game_id=game, tournament_id=event, event_id=event,
                split=split, fen=fen, ply=ply)


def test_deterministic_and_chronology_sensitive():
    a, b = row(), row(game="g2", event="other", split="test", fen="B:W31:B20")
    assert audit([a, b]) == audit([a, b])
    assert audit([a, b])["canonical_sha256"] != audit([b, a])["canonical_sha256"]


def test_reserved_event_rejected_whole():
    with pytest.raises(ValueError, match="reserved event"):
        audit([row(event="fFgE7oED")])


def test_game_split_leakage():
    with pytest.raises(ValueError, match="game crosses"):
        audit([row(), row(split="test", ply=2, fen="B:W31:B20")])


def test_fen_split_leakage():
    with pytest.raises(ValueError, match="FEN crosses"):
        audit([row(), row(game="g2", event="other", split="test")])


def test_duplicate_and_provenance():
    with pytest.raises(ValueError, match="duplicate"):
        audit([row(), row()])
    with pytest.raises(ValueError, match="provenance"):
        audit([row(), row(event="other", ply=2, fen="B:W31:B20")])


def test_invalid_input():
    for bad in ([], [row(ply=True)], [row(split="validation")], [row(fen="")]):
        with pytest.raises(ValueError):
            audit(bad)


def test_event_level_split_leakage_across_distinct_games():
    with pytest.raises(ValueError, match="event crosses splits"):
        audit([row(game="g1", split="train"),
               row(game="g2", split="test", fen="B:W31:B20")])


def test_within_game_ply_must_increase_even_if_interleaved():
    with pytest.raises(ValueError, match="nonchronological"):
        audit([row(game="g1", ply=3), row(game="g2", ply=1, fen="B:W31:B20"),
               row(game="g1", ply=2, fen="W:W32:B20")])
    assert audit([row(game="g1", ply=1), row(game="g2", ply=1, fen="B:W31:B20"),
                  row(game="g1", ply=3, fen="W:W32:B20")])["rows"] == 3


def test_tournament_split_leakage_even_with_different_event_ids():
    first = row(game="g1", event="historical-a", split="train")
    second = row(game="g2", event="historical-b", split="test",
                 fen="B:W31:B20")
    second["tournament_id"] = first["tournament_id"]
    with pytest.raises(ValueError, match="tournament crosses splits"):
        audit([first, second])


def test_distinct_tournaments_may_occupy_distinct_splits():
    first = row(game="g1", event="historical-a", split="train")
    second = row(game="g2", event="historical-b", split="test",
                 fen="B:W31:B20")
    assert audit([first, second])["games_by_split"] == {"test": 1, "train": 1}


def test_fen_alias_across_splits_rejected():
    first = row(game="g1", event="event-a", split="train", fen="W:W31,K32:B20")
    second = row(game="g2", event="event-b", split="test", fen="w:wK32,31:b20")
    with pytest.raises(ValueError, match="FEN crosses splits"):
        audit([first, second])


@pytest.mark.parametrize("fen", ["W:W31:B31", "W:W0:B20", "W:W31,31:B20",
                                  "W:W51:B20", "W:W31-35:B20", "W:B20:W31"])
def test_malformed_fen_rejected(fen):
    with pytest.raises(ValueError):
        audit([row(fen=fen)])


def test_fen_canonicalizer_preserves_side_and_king_status():
    from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
    assert canonical_fen(" w:wK32,31:b20,k2 ") == "W:W31,K32:BK2,20"
    assert canonical_fen("W:W31:B20") != canonical_fen("B:W31:B20")
    assert canonical_fen("W:WK31:B20") != canonical_fen("W:W31:B20")


def test_reserved_tournament_id_rejected_even_with_renamed_event():
    record = row(event="historical-alias")
    record["tournament_id"] = "fFgE7oED"
    with pytest.raises(ValueError, match="reserved event/tournament"):
        audit([record])


def test_unreserved_distinct_tournament_id_allowed():
    record = row(event="historical-alias")
    record["tournament_id"] = "independent-historical-tournament"
    assert audit([record])["rows"] == 1


@pytest.mark.parametrize("field", ["score", "Scan-Score", "best_move", "regret", "WDL", "pv"])
def test_target_derived_fields_forbidden_before_freeze(field):
    record = row()
    record[field] = 0
    with pytest.raises(ValueError, match="target-derived field"):
        audit([record])


def test_score_blind_manifest_accepts_source_metadata():
    record = row()
    record["source_pdn_sha256"] = "a" * 64
    assert audit([record])["score_blind"] is True


@pytest.mark.parametrize("payload", [
    {"metadata": {"scan_score": 1.0}},
    {"provenance": [{"source": "pdn"}, {"Best-Move": "31-26"}]},
    {"notes": {"analysis": {"WDL": [1, 0, 0]}}},
])
def test_nested_target_derived_fields_rejected(payload):
    record = row()
    record.update(payload)
    with pytest.raises(ValueError, match="target-derived field"):
        audit([record])


def test_nested_score_blind_source_metadata_allowed():
    record = row()
    record["metadata"] = {"source": {"pdn_sha256": "a" * 64}, "tags": ["historical"]}
    assert audit([record])["score_blind"] is True


@pytest.mark.parametrize("extra", [
    {"engine_rating": 0.7},
    {"metadata": {"unknown": {"engine_rating": 0.7}}},
    {"metadata": {"source": {"pdn_sha256": "a" * 64, "score_hint": 1}}},
    {"metadata": {"tags": ["ok", 7]}},
    {"source_pdn_sha256": "not-a-digest"},
])
def test_closed_manifest_schema_rejects_unreviewed_fields(extra):
    record = row()
    record.update(extra)
    with pytest.raises(ValueError, match="unknown|invalid"):
        audit([record])


def test_closed_manifest_schema_accepts_reviewed_provenance():
    record = row()
    record["source_pdn_sha256"] = "a" * 64
    record["metadata"] = {"source": {"pdn_sha256": "a" * 64}, "tags": ["historical"]}
    assert audit([record])["rows"] == 1


def test_conflicting_source_hashes_rejected():
    record = row()
    record["source_pdn_sha256"] = "a" * 64
    record["metadata"] = {"source": {"pdn_sha256": "b" * 64}}
    with pytest.raises(ValueError, match="conflicting source PDN"):
        audit([record])


def test_matching_source_hashes_allowed():
    record = row()
    record["source_pdn_sha256"] = "a" * 64
    record["metadata"] = {"source": {"pdn_sha256": "a" * 64}}
    assert audit([record])["score_blind"] is True


def test_conflicting_pdn_digest_across_plies_of_same_game_rejected():
    first = row(ply=1)
    first["source_pdn_sha256"] = "a" * 64
    second = row(ply=2, fen="B:W31:B20")
    second["metadata"] = {"source": {"pdn_sha256": "b" * 64}}
    with pytest.raises(ValueError, match="within game"):
        audit([first, second])


def test_matching_pdn_digest_across_plies_of_same_game_allowed():
    first = row(ply=1)
    first["source_pdn_sha256"] = "a" * 64
    second = row(ply=2, fen="B:W31:B20")
    second["metadata"] = {"source": {"pdn_sha256": "a" * 64}}
    assert audit([first, second])["rows"] == 2


def test_later_digest_cannot_disagree_with_first_known_digest():
    first = row(ply=1)
    second = row(ply=2, fen="B:W31:B20")
    second["source_pdn_sha256"] = "a" * 64
    third = row(ply=3, fen="W:W32:B20")
    third["source_pdn_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="within game"):
        audit([first, second, third])
