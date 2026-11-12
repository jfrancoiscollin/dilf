from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import geometry_ablation as ablation

A = ((31, 26), (), False)
B = ((32, 27), (), False)
C = ((33, 28), (), False)


def test_same_actions_different_geometry_and_lexicographic_selection():
    a, b, c = ("pc:1", 9, "A"), ("pc:1", 4, "B"), ("pc:2", 1, "C")
    index = {(A, B): [(a, "same"), (b, "other"), (c, "same")]}
    assert ablation.enumerate_matches(index, ((A, B), "same")) == {
        "L": [b, a, c], "LG": [a, c],
    }


def test_empty_geometry_arm_and_missing_legal_catalogue():
    source = ("pc:1", 9, "A")
    index = {(A, B): [(source, "other")]}
    assert ablation.enumerate_matches(index, ((A, B), "same")) == {"L": [source], "LG": []}
    assert ablation.enumerate_matches(index, ((A, C), "same")) == {"L": [], "LG": []}
    result = ablation.paired_summary([])
    assert result["paired"] == 0
    assert result["top3"]["coverage_delta"] is None
    assert result["top3"]["regret_ci"] == {"games": 0, "ci95": None}


def test_source_ties_break_by_canonical_action_and_target_cannot_select():
    source = {C: 1, B: 4, A: 4}
    target = {C: 100, B: 80, A: 0}
    result = ablation.outcomes(source, target, 3)
    assert result["prefix"] == [A, B, C]
    assert result["disjoint_optima"]
    assert result["top1"]["ordinary_regret_centimen"] == 100
    assert result["top3"]["covered"]
    with pytest.raises(ValueError, match="catalogues differ"):
        ablation.outcomes(source, {A: 0, B: 80}, 3)


def test_quiet_catalogue_fails_on_ambiguous_or_capturing_actions(monkeypatch):
    monkeypatch.setattr(ablation, "_quiet_signature", lambda _: "quiet")
    quiet = SimpleNamespace(path=(31, 26), captures=(), promotion=False)
    capture = SimpleNamespace(path=(31, 22), captures=(27,), promotion=False)
    for moves in ([quiet, quiet], [capture, quiet]):
        engine = SimpleNamespace(legal_moves=lambda _: moves)
        with pytest.raises(ValueError, match="Ambiguous or capturing"):
            ablation.quiet_catalogue(None, engine)


def test_target_leakage_excludes_pcblues_and_all_prior_sources_and_manifests():
    held = dict.fromkeys(("pc", "earlier-pdn", "earlier-manifest", "novel"))
    assert ablation.novel_targets(held, {"pc": None}, {"earlier-pdn": None},
                                  {"earlier-manifest"}) == ["novel"]
