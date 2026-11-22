"""Synthetic tests only; no FMJD cohort is enrolled."""
from research.mtdp.decision_equivalence.corpus_admission import audit

H = "a" * 64
J = "b" * 64
K = "c" * 64
EX = {"game_ids": [], "raw_sha256": [], "trajectory_sha256": [], "canonical_sha256": []}


def row(game="g1", split="train", fen="W:W31:B20", pos=H, ply=1, event="other", tournament="t1"):
    return dict(game_id=game, split=split, fen=fen, canonical_sha256=pos,
                raw_sha256=J, trajectory_sha256=K, ply=ply,
                event_id=event, tournament_id=tournament)


def test_clean_structural_pass_not_historical_proof():
    result = audit([row()], EX)
    assert result["admissible_structurally"]
    assert result["historical_exclusion_proven"] is False


def test_missing_registry_fails_closed():
    assert "missing_authenticated_exclusion_registry" in audit([row()], {})["errors"]


def test_reserved_event_rejected():
    assert any("reserved_or_historical_overlap" in x
               for x in audit([row(event="fFgE7oED")], EX)["errors"])


def test_same_game_split_leak():
    result = audit([row(), row(split="test", ply=2, pos=J, tournament="t2")], EX)
    assert "cross_split_game_leakage" in result["errors"]


def test_same_position_cross_game_split_leak():
    result = audit([row(), row(game="g2", split="test", tournament="t2")], EX)
    assert "cross_split_position_leakage" in result["errors"]


def test_tournament_split_leak():
    result = audit([row(), row(game="g2", split="test", pos=J)], EX)
    assert "cross_split_tournament_overlap" in result["errors"]


def test_duplicate_game_ply():
    result = audit([row(), row(pos=J)], EX)
    assert any("duplicate_game_ply" in x for x in result["errors"])


def test_historical_hash_overlap():
    exclusions = {**EX, "trajectory_sha256": [K]}
    assert any("reserved_or_historical_overlap" in x
               for x in audit([row()], exclusions)["errors"])


def test_registry_rejects_unhashable_entries_without_crashing():
    result = audit([row()], {**EX, "game_ids": [{"unexpected": "object"}]})
    assert "invalid_exclusion_registry:game_ids" in result["errors"]
    assert not result["admissible_structurally"]


def test_registry_rejects_invalid_digest_without_crashing():
    result = audit([row()], {**EX, "canonical_sha256": ["NOT_A_SHA"]})
    assert "invalid_exclusion_registry:canonical_sha256" in result["errors"]


def test_registry_rejects_non_list_field():
    result = audit([row()], {**EX, "game_ids": "g1"})
    assert "missing_authenticated_exclusion_registry" in result["errors"]
    assert "invalid_exclusion_registry:game_ids" in result["errors"]


def test_non_string_fen_and_event_fail_closed():
    for field in ("fen", "event_id"):
        item = row()
        item[field] = {"unexpected": "object"}
        result = audit([item], EX)
        assert "row_0:invalid_provenance" in result["errors"]
        assert not result["admissible_structurally"]
