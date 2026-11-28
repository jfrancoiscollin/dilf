import pytest

from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists, evaluate_target, summarize
from research.mtdp.top_k_transfer import _action


@pytest.fixture
def position():
    keys = ("9-4", "2-7", "10-5", "3-8")
    moves = [{"jass_key": key, "action": [[int(part) for part in key.split("-")], [], False]}
             for key in keys]
    target = {"source_fen": "s", "target_fen": "t", "target_games": ["g2", "g1"], "legal_moves": moves}
    return target, {_action(move): 0 for move in moves}


def test_bytewise_ties_and_input_order(position):
    target, source = position
    moves = target["legal_moves"]
    outcome = evaluate_target(target, source, source)
    assert outcome == evaluate_target({**target, "legal_moves": moves[::-1]},
                                      dict(reversed(list(source.items()))), source)
    assert outcome["transfer"] == outcome["canonical"] == ["10-5", "2-7", "3-8"]
    assert outcome["source_tie_at_cutoff"]
    assert outcome["source_tied_scores"] == {0: 4}
    assert outcome["target_game"] == "g1"


def test_small_legal_sets_are_retained(position):
    target, _ = position
    moves = target["legal_moves"][:2]
    source = {_action(move): score for move, score in zip(moves, (10, 0), strict=True)}
    row = evaluate_target({**target, "legal_moves": moves}, source, source)
    result = summarize({"event": [row]})
    assert row["legal_count"] == row["overlap"] == 2
    assert row["transfer"] == ["9-4", "2-7"]
    assert row["canonical"] == ["2-7", "9-4"]
    assert result["equal_candidate_sets"] == 1
    assert result["coverage_table"] == {"both": 1, "transfer_only": 0, "canonical_only": 0, "neither": 0}


@pytest.mark.parametrize("duplicate", ["jass_key", "action"])
def test_duplicate_mapping_rejected(position, duplicate):
    target, source = position
    a, b, *rest = target["legal_moves"]
    with pytest.raises(ValueError, match="Ambiguous"):
        candidate_lists([a, {**b, duplicate: a[duplicate]}, *rest], source)


@pytest.mark.parametrize("which", ["Source", "Target"])
def test_missing_action_rejected(position, which):
    target, scores = position
    partial = dict(list(scores.items())[:-1])
    source = partial if which == "Source" else scores
    target_scores = partial if which == "Target" else scores
    with pytest.raises(ValueError, match=f"{which} scores differ"):
        evaluate_target(target, source, target_scores)


def test_target_scores_cannot_change_lists_and_categories_stay_separate(position):
    target, source = position
    action = _action(target["legal_moves"][0])
    source[action] = 10
    target_scores = dict.fromkeys(source, 0)
    target_scores[action] = 9500
    row = evaluate_target(target, source, target_scores)
    other = evaluate_target(target, source, dict.fromkeys(source, 0))
    assert row["transfer"] == other["transfer"] and row["canonical"] == other["canonical"]
    result = summarize({"event": [row]})
    assert result["coverage_table"]["transfer_only"] == 1
    assert result["ordinary_pairs"] == 0
    assert result["arms"]["canonical"]["category_changes"] == {"win->ordinary": 1}
    assert result["regret_delta_mean_centimen"] is None
