"""Independent uncertainty calculation keeps the frozen owner frame."""
from research.mtdp.jass_benchmark.verify_full_residual_quality import boot


def test_all_owner_games_retained_even_when_estimand_is_empty():
    frame = [{'event': 's7ahYqL4', 'owner': str(i)} for i in range(3)]
    out = boot([], frame, 'cost')
    assert out['sampling_owner_games'] == {'s7ahYqL4': 3, 'D9PF2OSW': 0}
    assert out['undefined_draws'] == 10000 and out['ci95'] is None


def test_sparse_undefined_draws_suppress_unconditional_interval():
    frame = [{'event': 's7ahYqL4', 'owner': str(i)} for i in range(3)]
    out = boot([{'event': 's7ahYqL4', 'owner': '0', 'cost': 9}], frame, 'cost')
    assert 0 < out['undefined_draws'] < 10000 and out['ci95'] is None
    assert out['positions'] == out['owner_games'] == 1


def test_zero_paired_difference_retains_all_rows_and_games():
    rows = [{'event': e, 'owner': str(i), 'cost': 0} for e in ('s7ahYqL4', 'D9PF2OSW') for i in range(2)]
    out = boot(rows, rows, 'cost')
    assert out['positions'] == out['owner_games'] == 4
    assert out['mean'] == 0 and out['ci95'] == [0, 0] and out['undefined_draws'] == 0
