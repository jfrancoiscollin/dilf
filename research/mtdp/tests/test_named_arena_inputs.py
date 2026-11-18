import copy
import json
from pathlib import Path

import pytest

from pedagogy.game import Move, parse_fen
from research.mtdp.jass_benchmark import named_arena_inputs as gate
from research.mtdp.pdn import PdnGame

ROOT = Path(__file__).resolve().parents[3]


def fixtures(tmp_path):
    reg = gate.registration(ROOT)
    metadata = copy.deepcopy(reg['event'])
    metadata['isFinished'] = True
    first, repeat = tmp_path / 'first.pdn', tmp_path / 'repeat.pdn'
    first.write_bytes(b'synthetic fixture, not an acquired event')
    repeat.write_bytes(first.read_bytes())
    record = {'url': f'https://lidraughts.org/api/tournament/{gate.EVENT}/games',
              'sha256': gate.digest(first.read_bytes()), 'bytes': first.stat().st_size,
              'retrieved_at_utc': '2026-11-18T20:58:00Z'}
    log = {'candidate': {'first': {**record, 'request_id': 'one'},
                         'independent_repeat': {**record, 'request_id': 'two'}}}
    return metadata, first, repeat, log


def invoke(tmp_path, metadata, first, repeat, log, now='2026-11-18T21:00:00Z'):
    meta, receipts = tmp_path / 'metadata.json', tmp_path / 'downloads.json'
    meta.write_text(json.dumps(metadata))
    receipts.write_text(json.dumps(log))
    return gate.check_final(ROOT, meta, first, repeat, receipts, now=gate.utc(now))


def test_matching_inputs_remain_distinct_from_a_scientific_freeze(tmp_path):
    assert invoke(tmp_path, *fixtures(tmp_path))['scientific_freeze'] is False


def test_prefinish_refusal_precedes_reading_pdn_files(tmp_path):
    metadata, _, _, log = fixtures(tmp_path)
    with pytest.raises(ValueError, match='scheduled finish'):
        invoke(tmp_path, metadata, tmp_path / 'missing1', tmp_path / 'missing2', log,
               now='2026-11-18T20:56:59Z')


@pytest.mark.parametrize('changed', [False, 'true', 1, None])
def test_finished_flag_requires_literal_true(tmp_path, changed):
    metadata, first, repeat, log = fixtures(tmp_path)
    metadata['isFinished'] = changed
    with pytest.raises(ValueError, match='not confirmed finished'):
        invoke(tmp_path, metadata, first, repeat, log)


@pytest.mark.parametrize('key,value', [('id', 'other'), ('clock', {'limit': 180, 'increment': 0}),
                                       ('startsAt', '2026-11-18T19:00:00Z')])
def test_format_and_identity_cannot_drift(tmp_path, key, value):
    metadata, first, repeat, log = fixtures(tmp_path)
    metadata[key] = value
    with pytest.raises(ValueError, match='changed'):
        invoke(tmp_path, metadata, first, repeat, log)


def test_distinct_files_and_matching_bytes_are_required(tmp_path):
    metadata, first, repeat, log = fixtures(tmp_path)
    with pytest.raises(ValueError, match='distinct export files'):
        invoke(tmp_path, metadata, first, first, log)
    repeat.write_bytes(b'changed')
    with pytest.raises(ValueError, match='differ or are empty'):
        invoke(tmp_path, metadata, first, repeat, log)


@pytest.mark.parametrize('field,value', [('request_id', 'one'), ('sha256', '0' * 64),
                                        ('retrieved_at_utc', '2026-11-18T20:56:00Z')])
def test_download_receipts_are_bound_to_the_final_inputs(tmp_path, field, value):
    metadata, first, repeat, log = fixtures(tmp_path)
    log['candidate']['independent_repeat'][field] = value
    with pytest.raises(ValueError):
        invoke(tmp_path, metadata, first, repeat, log)


def test_registration_bytes_are_pinned(tmp_path):
    for name in (gate.REGISTRATION, gate.PROTOCOL):
        dst = tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / name).read_bytes())
    (tmp_path / gate.REGISTRATION).write_text('{}')
    with pytest.raises(ValueError, match='selection or protocol changed'):
        gate.registration(tmp_path)


def test_ambiguous_game_contributes_only_verified_prefix_states():
    class Rules:
        calls = 0

        def legal_moves(self, state):
            if state.turn == 'white':
                return [Move((31, 26))]
            return [Move((1, 23, 40), (18, 34)), Move((1, 29, 40), (18, 34))]

        def apply_move(self, state, move):
            self.calls += 1
            return parse_fen('B:W26:BK1')

    engine = Rules()
    game = PdnGame(46, {'FEN': 'W:W31:BK1'}, ('31-26', '1x40', '40-45'))
    fens, quarantined = gate.confirmed_prefixes([game], engine)
    assert fens == {'W:W31:BK1', 'B:W26:BK1'}
    assert engine.calls == 1
    assert quarantined[0]['game'] == 46 and quarantined[0]['ply'] == 2
