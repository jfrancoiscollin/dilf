"""Scientific failure modes of the offline fixed-reference reconciliation."""
from pathlib import Path
import pytest
from research.mtdp.jass_benchmark import full_residual_quality as q


def fixture(scores):
    actions = {str(i): ((i,), (), False) for i in range(len(scores))}
    main = {a: {'summary': {'best_move': '0'}} for a in q.raw.ARMS}
    return main, dict(zip(actions.values(), scores)), actions


def test_complete_optimum_ties_are_accepted():
    arms = q.compare_arms(*fixture([12, 12, -4]))
    assert all(a['covered'] and a['ordinary_regret_centimen'] == 0 for a in arms.values())


def test_ordinary_cost_uses_reference_score_not_jass_score():
    arms = q.compare_arms(*fixture([-3, 8]))
    assert all(a['ordinary_regret_centimen'] == 11 for a in arms.values())


def test_category_transition_is_retained_without_numeric_subtraction():
    arms = q.compare_arms(*fixture([1, 10000]))
    assert all(a['ordinary_regret_centimen'] is None and not a['covered'] for a in arms.values())


def test_incomplete_action_vector_rejected():
    main, scores, actions = fixture([1, 2])
    scores.pop(next(iter(scores)))
    with pytest.raises(ValueError):
        q.compare_arms(main, scores, actions)


def test_missing_residual_arm_rejected():
    main, scores, actions = fixture([1, 2]); main.pop('native_residual')
    with pytest.raises(ValueError):
        q.compare_arms(main, scores, actions)


def test_failed_publication_gate_prevents_reference_access(monkeypatch):
    def fail(*args):
        raise ValueError('Unpublished implementation')
    monkeypatch.setattr(q, 'gate', fail)
    monkeypatch.setattr(q, 'pinned', lambda *args: pytest.fail('Target accessed before gate'))
    with pytest.raises(ValueError, match='Unpublished'):
        q.analyze(Path('/nonexistent'), 'not-published')
