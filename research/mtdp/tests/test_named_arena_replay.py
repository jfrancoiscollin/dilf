"""Synthetic legal-oracle fixtures; no named-event games or scores are used."""
import json

import pytest

from pedagogy.game import Move, parse_fen
from research.mtdp.jass_benchmark import named_arena_replay as gate
from research.mtdp.pdn import read_games


class Rules:
    def legal_moves(self, state):
        if state.white_kings or state.turn == 'black':
            return [Move((1, 23, 40), (18, 34)), Move((1, 29, 40), (18, 34))]
        return [Move((31, 26)), Move((31, 27))]

    def apply_move(self, state, move):
        return parse_fen('B:WK40:B') if move.is_capture else parse_fen('B:W26:BK1')


def write_games(path, rows):
    path.write_text('\n\n'.join(
        f'[Event "synthetic fixture"]\n[Site "https://lidraughts.org/{identity}"]\n[FEN "{fen}"]\n\n{moves} *'
        for identity, fen, moves in rows) + '\n')
    return path


def empty_registry():
    return {'public_game_ids': [], 'normalized_token_sequence_sha256': []}


def test_canonical_index_unifies_routes_and_quarantines_ambiguity(tmp_path):
    p = write_games(tmp_path / 'history.pdn', [
        ('Game0001', 'W:WK1:B18,34', '1x23x40'),
        ('Game0002', 'W:WK1:B18,34', '1x29x40'),
        ('Game0003', 'W:WK1:B18,34', '1x40'),
    ])
    result = gate.index_games([(p, 3)], Rules())
    assert result['status_counts'] == {'indexed': 1, 'duplicate': 1, 'quarantined': 1}
    assert len(result['fingerprints']) == 1
    assert 'trajectory_sha256' not in result['game_audit']['history.pdn:3']


def test_reidentified_different_tokens_are_excluded_by_board_trajectory(tmp_path):
    source = write_games(tmp_path / 'source.pdn', [('Old00001', 'W:WK1:B18,34', '1x23x40')])
    target = write_games(tmp_path / 'target.pdn', [('New00001', 'W:WK1:B18,34', '1x29x40')])
    game, = read_games(source)
    registry = empty_registry()
    registry['normalized_token_sequence_sha256'] = [gate.token_fingerprint(game)]
    indexed = gate.index_games([(source, 1)], Rules())
    states, owners, plies, audit = gate.replay_candidates(target, Rules(), registry, set(indexed['fingerprints']))
    assert states == owners == plies == {}
    assert audit['target.pdn:1']['status'] == 'excluded_canonical_trajectory'


def test_whole_game_quarantine_does_not_emit_a_valid_prefix(tmp_path):
    p = write_games(tmp_path / 'target.pdn', [('New00001', 'W:W31:BK1', '31-26 1x40')])
    states, owners, plies, audit = gate.replay_candidates(p, Rules(), empty_registry(), set())
    assert states == owners == plies == {}
    assert audit['target.pdn:1']['status'] == 'quarantined'


def test_within_event_duplicate_cannot_acquire_a_second_owner(tmp_path):
    p = write_games(tmp_path / 'target.pdn', [
        ('New00001', 'W:WK1:B18,34', '1x23x40'),
        ('New00002', 'W:WK1:B18,34', '1x29x40'),
    ])
    states, owners, plies, audit = gate.replay_candidates(p, Rules(), empty_registry(), set())
    assert len(states) == 2
    assert audit['target.pdn:1']['status'] == 'accepted'
    assert audit['target.pdn:2']['status'] == 'duplicate_within_event'
    assert all(value == {'target.pdn:1'} for value in owners.values())


def test_reserved_identity_or_token_is_excluded_before_oracle_calls(tmp_path):
    p = write_games(tmp_path / 'target.pdn', [('New00001', 'W:WK1:B18,34', '1x40')])
    registry = empty_registry()
    registry['public_game_ids'] = ['New00001']
    assert gate.replay_candidates(p, None, registry, set())[3]['target.pdn:1']['status'] == 'excluded_public_id'
    registry = empty_registry()
    registry['normalized_token_sequence_sha256'] = [gate.token_fingerprint(read_games(p)[0])]
    assert gate.replay_candidates(p, None, registry, set())[3]['target.pdn:1']['status'] == 'excluded_token_sequence'


def test_repeated_public_id_fails_before_emitting_positions(tmp_path):
    p = write_games(tmp_path / 'target.pdn', [
        ('New00001', 'W:WK1:B18,34', '1x23x40'),
        ('New00001', 'W:WK1:B18,34', '1x29x40'),
    ])
    with pytest.raises(ValueError, match='repeated public'):
        gate.replay_candidates(p, None, empty_registry(), set())


def test_empty_population_keeps_empty_catalogue(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, 'read_jass_catalogues', lambda exe, states: [])
    targets, receipt = gate.benchmark_manifest([], None, tmp_path)
    assert targets == [] and receipt['targets'] == receipt['distinct_positions'] == 0


def test_shared_selector_retains_source_order_and_exclusion_policy():
    source1, source2, target = 'W:W31:B1', 'W:W31:B2', 'W:W31:B3'
    sources = {source1: parse_fen(source1), source2: parse_fen(source2)}
    first = {source1: {'pc:2': [1]}, source2: {'pc:1': [9]}}
    states, owners = {target: parse_fen(target)}, {target: {'arena:2', 'arena:1'}}
    rows, categories, novel = gate.select_population(sources, first, states, owners, set(), Rules())
    assert len(rows) == 1 and novel == [target]
    assert rows[0]['games'] == ['arena:1', 'arena:2']
    assert rows[0]['source_fens'] == {'L': source2, 'LCB': source2}
    assert gate.select_population(sources, first, states, owners, {target}, Rules())[0] == []


def test_production_proposal_checks_final_receipts_before_engines(monkeypatch, tmp_path):
    def closed(*args, **kwargs):
        raise ValueError('scheduled finish guard closed')
    monkeypatch.setattr(gate, 'check_final', closed)
    monkeypatch.setattr(gate, 'checked_engine', lambda *a: pytest.fail('oracle invoked prematurely'))
    with pytest.raises(ValueError, match='guard closed'):
        gate.proposal(*([tmp_path] * 10))


def test_altered_canonical_history_index_is_rejected(tmp_path):
    p = tmp_path / 'index.json'
    p.write_text('{}')
    summary = tmp_path / gate.HISTORY_SUMMARY
    summary.parent.mkdir(parents=True)
    summary.write_text(json.dumps({'index_sha256': gate.INDEX_SHA}))
    with pytest.raises(ValueError, match='index changed'):
        gate.checked_history_index(tmp_path, p, {'sources': []})


def test_historical_quarantine_keeps_verified_prefix_only_for_exclusion(tmp_path):
    p = write_games(tmp_path / 'history.pdn', [('Old00001', 'W:W31:BK1', '31-26 1x40')])
    result = gate.index_games([(p, 1)], Rules())
    assert result['fingerprints'] == []
    assert set(result['confirmed_fens']) == {'W:W31:BK1', 'B:W26:BK1'}
    assert result['status_counts'] == {'quarantined': 1}
    assert result['game_audit']['history.pdn:1']['confirmed_prefix_positions'] == 2


def test_selected_rows_emit_complete_benchmark_action_mapping(monkeypatch, tmp_path):
    source, target = 'W:W31:B1', 'W:W31:B2'
    rows, _, _ = gate.select_population(
        {source: parse_fen(source)}, {source: {'pc:1': [1]}},
        {target: parse_fen(target)}, {target: {'arena:1'}}, set(), Rules())
    monkeypatch.setattr(gate, 'read_jass_catalogues', lambda exe, states: [
        [('31-26', False), ('31-27', False)] for state in states])
    targets, receipt = gate.benchmark_manifest(rows, Rules(), tmp_path)
    assert len(targets) == receipt['targets'] == 1
    assert receipt['target_action_occurrences'] == 2
    assert targets[0]['source_fens'] == {'L': source, 'LCB': source}
    assert {r['jass_key'] for r in targets[0]['legal_moves']} == {'31-26', '31-27'}
