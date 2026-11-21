"""Synthetic lexical-admission tests; no FMJD legality or minimax claims."""
import pytest
from research.mtdp.decision_equivalence.lexical_trajectory_gate import lexical_trajectory_fingerprint as gate
from research.mtdp.decision_equivalence.trajectory_fingerprint import trajectory_fingerprint


def test_valid_tokens_preserve_original_hash_and_order():
    moves = ['31-26', '12x23x34']
    assert gate('W:W31:B20', moves) == trajectory_fingerprint('W:W31:B20', moves)
    assert gate('W:W31:B20', moves) != gate('W:W31:B20', moves[::-1])


def test_capture_paths_with_same_endpoints_remain_distinct():
    assert gate('W:W31:B20', ['12x23x34']) != gate('W:W31:B20', ['12x18x34'])


@pytest.mark.parametrize('moves', [
    '31-26', None, ['31-26', '31-26 '], ['31-26', '12x23-34'],
    ['31-26', '01-06'], ['31-26', '12x23x12'], ['31-26', 42],
])
def test_rejects_bad_sequence_or_any_bad_move(moves):
    with pytest.raises(ValueError):
        gate('W:W31:B20', moves)


def test_empty_trajectory_is_lexically_allowed_but_not_admitted_as_independent():
    assert gate('W:W31:B20', ()) == trajectory_fingerprint('W:W31:B20', [])
