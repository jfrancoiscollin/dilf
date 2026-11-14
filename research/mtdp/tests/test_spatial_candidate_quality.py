from research.mtdp.jass_benchmark.spatial_candidate_quality import evaluate


def test_initial_candidates_use_jass_key_tie_break_and_best_of_three():
    moves = [{"jass_key": f"{start}-{end}", "action": [[start, end], [], False]}
             for start, end in ((2, 7), (10, 14), (20, 24), (30, 34))]
    actions = [(tuple(move["action"][0]), (), False) for move in moves]
    target = {"target_fen": "target", "target_games": ["game"], "legal_moves": moves,
              "source_fens": {"L": "legal", "LCB": "geometry"}}
    scores = {
        "source": {
            "legal": dict(zip(actions, (10, 10, 0, -10), strict=True)),
            "geometry": dict(zip(actions, (-10, 5, 10, 0), strict=True)),
        },
        "target": {"target": dict(zip(actions, (0, -3, -1, 10), strict=True))},
    }
    result = evaluate(target, scores)
    assert result["L"]["prefix"] == ["10-14", "2-7", "20-24"]
    assert result["L"]["top1"]["ordinary_regret_centimen"] == 13
    assert result["LCB"]["top1"]["ordinary_regret_centimen"] == 11
    assert not result["L"]["top3"]["covered"]
    assert result["LCB"]["top3"]["covered"]
