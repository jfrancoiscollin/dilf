"""No future games or target scores: temporal, alias and pre-score mask checks."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.mtdp.jass_benchmark import two_arena_replay as replay
from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark.named_arena_rehearsal import FIXTURE_FEN
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes


def test_proposal_checks_joint_inputs_before_backend_or_target_reads(monkeypatch, tmp_path):
    def blocked(*args):
        raise ValueError('closed joint gate')
    monkeypatch.setattr(replay.acquisition, 'check', blocked)
    monkeypatch.setattr(replay, 'checked_engine', lambda *args: pytest.fail('backend reached'))
    with pytest.raises(ValueError, match='closed joint gate'):
        replay.proposal(tmp_path, tmp_path/'missing', tmp_path/'missing-cache', tmp_path, tmp_path)
    assert not list(tmp_path.iterdir())


def test_changed_cache_refused_even_if_its_summary_is_changed(tmp_path):
    path = tmp_path/'cache.json'; path.write_bytes(_bytes({}))
    summary = tmp_path/replay.SUMMARY; summary.parent.mkdir(parents=True)
    summary.write_text(json.dumps({'exclusions_sha256': replay.digest(path.read_bytes())}))
    with pytest.raises(ValueError, match='historical exclusion cache'):
        replay.checked_exclusions(tmp_path, path)


def test_freeze_full_mask_both_strata_and_fixed_owner():
    other = FIXTURE_FEN.replace(':B2,3,', ':B1,3,')  # change mover-men geometry
    targets = [{'target_fen': FIXTURE_FEN, 'source_fens': {'L': FIXTURE_FEN, 'LCB': other},
                'target_games': ['arena:9', 'arena:2']}]
    got, = replay.full_signature_labels(targets)
    assert got['same_full_quiet_signature'] == {'L': True, 'LCB': False}
    assert got['bootstrap_owner'] == 'arena:2'
    assert 'same_full_quiet_signature' not in targets[0]


def test_empty_mask_is_reportable():
    assert replay.full_signature_labels([]) == []


def test_undefined_full_mask_refused():
    targets = [{'target_fen': 'W:WK31:B1', 'source_fens': {'L': FIXTURE_FEN, 'LCB': FIXTURE_FEN},
                'target_games': ['g']}]
    with pytest.raises(ValueError, match='undefined full signature'):
        replay.full_signature_labels(targets)


def test_extension_includes_all_aliases_and_confirmed_quarantine_prefixes(monkeypatch, tmp_path):
    old = {k: ['old'] for k in ('public_game_ids','normalized_token_sequence_sha256','fingerprints','confirmed_fens')}
    games = [SimpleNamespace(index=1), SimpleNamespace(index=2)]
    monkeypatch.setattr(replay, 'read_games', lambda p: games)
    monkeypatch.setattr(replay, 'public_ids', lambda p: ['id-good','id-quarantined'])
    monkeypatch.setattr(replay, 'token_fingerprint', lambda g: f'token-{g.index}')
    extension = {'fingerprints': ['complete-good'], 'confirmed_fens': ['valid-good','quarantine-prefix'],
                 'game_audit': {'good': {'status':'indexed'}, 'bad': {'status':'quarantined'}}}
    monkeypatch.setattr(replay, 'index_games', lambda paths, engine: extension)
    value, audit = replay.extend_exclusions(old, tmp_path/'arena.pdn', None)
    assert value == {'public_game_ids':['id-good','id-quarantined','old'],
                     'normalized_token_sequence_sha256':['old','token-1','token-2'],
                     'fingerprints':['complete-good','old'],
                     'confirmed_fens':['old','quarantine-prefix','valid-good']}
    assert audit is extension
    assert all(v == ['old'] for v in old.values())


def test_wrong_event_order_refused_before_replay():
    with pytest.raises(ValueError, match='registered arena order'):
        replay.joint_population(dict.fromkeys(reversed(study.EVENTS)), {}, {}, {}, None, None)


def test_same_filename_would_collide_owners_and_is_refused(tmp_path):
    with pytest.raises(ValueError, match='Canonical event filename'):
        replay.joint_population(dict.fromkeys(study.EVENTS, tmp_path/'first.pdn'), {}, {}, {}, None, None)


def test_later_selection_receives_entire_earlier_prefix_index(monkeypatch, tmp_path):
    paths = {e:tmp_path/f'mtdp-lidraughts-{e}.pdn' for e in study.EVENTS}
    for path in paths.values(): path.write_bytes(b'fixture')
    initial = {k: ['old'] for k in ('public_game_ids','normalized_token_sequence_sha256','fingerprints','confirmed_fens')}
    after_a = {k: ['old','earlier'] for k in initial}
    seen = []
    def candidates(path, engine, known, fingerprints):
        seen.append((path.name, known, fingerprints))
        return {}, {}, {}, {}
    overlap = []
    def select(s,p,t,o,excluded,engine):
        overlap.append(excluded)
        return [], {}, []
    monkeypatch.setattr(replay, 'replay_candidates', candidates)
    monkeypatch.setattr(replay, 'select_population', select)
    monkeypatch.setattr(replay, 'benchmark_manifest', lambda *args: ([], {}))
    monkeypatch.setattr(replay, 'extend_exclusions', lambda known,path,e: (after_a, {}))
    events = replay.joint_population(paths, initial, {}, {}, None, None)
    assert seen[0][1] is initial and seen[1][1] is after_a
    assert seen[1][2] == {'old','earlier'}
    assert overlap == [{'old'},{'old','earlier'}]
    assert all(v['full_signature_strata'] == {a:{'equal':0,'different':0} for a in ('L','LCB')} for v in events.values())
    assert all(v['benchmark_targets'] == [] for v in events.values())
