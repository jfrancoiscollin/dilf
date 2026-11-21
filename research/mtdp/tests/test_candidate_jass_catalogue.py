import pytest
from pedagogy.game import Move
from research.mtdp.jass_benchmark.candidate_jass_catalogue import compare

TARGET = "W:W31,33:B1"
SOURCE = "W:W31,32:B1"


class Rules:
    def legal_moves(self, state):
        return [Move((31, 26))]


def row():
    return {"fen": TARGET, "source_fens": {"L": SOURCE, "LCB": SOURCE},
            "legal": [[[31, 26], [], False]]}


def test_complete_source_and_target_bijections():
    result = compare([row()], Rules(), [[("31-26", False)]] * 2)
    assert result["targets"] == result["distinct_sources"] == 1
    assert result["distinct_positions"] == 2
    assert len({p["mapping_sha256"] for p in result["positions"]}) == 1


def test_reject_replay_action_corruption():
    r = row()
    r["legal"] = [[[31, 27], [], False]]
    with pytest.raises(ValueError, match="replay action"):
        compare([r], Rules(), [[("31-26", False)]] * 2)


def test_reject_missing_catalogue():
    with pytest.raises(ValueError, match="Incomplete"):
        compare([row()], Rules(), [])


def test_reject_source_target_mismatch_even_when_each_catalogue_matches():
    class DifferentRules:
        def legal_moves(self, state):
            return [Move((31, 26))] if 33 in state.white_men else [Move((32, 27))]

    fens = sorted([SOURCE, TARGET])
    catalogues = [[("31-26" if fen == TARGET else "32-27", False)] for fen in fens]
    with pytest.raises(ValueError, match="Source and target"):
        compare([row()], DifferentRules(), catalogues)


def test_reject_changed_replay_before_invoking_engines(tmp_path):
    from research.mtdp.jass_benchmark.candidate_jass_catalogue import audit
    replay = tmp_path / "changed.json"
    replay.write_text('{"candidate_targets": []}')
    with pytest.raises(ValueError, match="verified pre-score"):
        audit(replay, tmp_path, tmp_path, tmp_path)
