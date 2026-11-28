"""Prospective strict parsing without changing archived parser dependencies."""
import hashlib

import pytest

from pedagogy.game import initial_state, state_to_fen
from research.mtdp.pdn import PdnReplayError
from research.mtdp.pdn_strict import parse_games_strict
from research.mtdp.pdn_membership_proof import prove_pdn_position
from research.mtdp.tests.test_pdn import MockRules


@pytest.mark.parametrize('trailing', ['32-28', 'garbage', '1-0', '2. 17-22'])
def test_rejects_tokens_after_game_result(trailing):
    with pytest.raises(PdnReplayError, match='after result'):
        parse_games_strict(f'[Event "A"]\n1. 32-28 * {trailing}')


def test_comments_after_game_result_are_allowed():
    games = parse_games_strict('[Event "A"]\n1. 32-28 * {end note} ; end of line')
    assert len(games) == 1 and games[0].moves == ('32-28',)


def test_terminal_result_does_not_reject_next_game_header():
    games = parse_games_strict('[Event "A"]\n1. 32-28 *\n\n[Event "B"]\n1. 31-27 *\n')
    assert [g.moves for g in games] == [('32-28',), ('31-27',)]


def test_original_grammar_rejects_unsupported_pre_result_token():
    with pytest.raises(PdnReplayError, match='Unsupported'):
        parse_games_strict('[Event "A"]\n1. 32-28 ?! *')


def test_membership_gate_uses_strict_parser_on_authenticated_bytes(tmp_path):
    raw = b'[Event "A"]\n1. 32-28 * 17-22\n'
    path = tmp_path / 'synthetic.pdn'; path.write_bytes(raw)
    with pytest.raises(PdnReplayError, match='after result'):
        prove_pdn_position(path, hashlib.sha256(raw).hexdigest(), 1, 0,
                           state_to_fen(initial_state()), MockRules())
