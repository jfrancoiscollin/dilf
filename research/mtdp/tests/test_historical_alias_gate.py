"""H13 score-blind historical aliases; no independent cohort admission."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from research.mtdp.historical_alias_gate import (
    load_historical_aliases, public_id, reconcile, reject_historical_source,
    screen_historical_source,
)
from research.mtdp.jass_benchmark.named_arena_replay import token_fingerprint
from research.mtdp.pdn_strict import parse_games_strict

RAW = b'[Event "synthetic"]\n[Site "https://lidraughts.org/Ab12Cd34/white"]\n[FEN "W:W32:B1"]\n1. 32-28 *\n'
ROOT = Path(__file__).resolve().parents[3]


def aliases(**kw):
    return {key: frozenset(kw.get(key, ())) for key in
            ('source_sha256', 'public_game_ids', 'notation_sha256')}


def report(raw=RAW, known=None):
    return screen_historical_source(raw, hashlib.sha256(raw).hexdigest(), known or aliases())


@pytest.mark.parametrize('key,value,reason', [
    ('source_sha256', hashlib.sha256(RAW).hexdigest(), 'historical_source_digest'),
    ('public_game_ids', 'Ab12Cd34', 'historical_public_game_id'),
    ('notation_sha256', token_fingerprint(parse_games_strict(RAW.decode())[0]),
     'historical_normalized_notation'),
])
def test_each_identity_channel_independently_rejects(key, value, reason):
    result = report(known=aliases(**{key: [value]}))
    assert result['findings'] == [{'source_game_index': 1, 'reasons': [reason]}]
    with pytest.raises(ValueError, match='entire prospective batch'):
        reject_historical_source(result)


def test_metadata_and_comments_cannot_hide_notation():
    token = token_fingerprint(parse_games_strict(RAW.decode())[0])
    raw = RAW.replace(b'synthetic', b'relabelled').replace(b'32-28', b'{comment} 32-28')
    assert report(raw, aliases(notation_sha256=[token]))['findings'][0]['reasons'] == [
        'historical_normalized_notation']


def test_one_known_game_rejects_complete_mixed_export():
    raw = RAW.replace(b'Ab12Cd34', b'New12345') + RAW
    result = report(raw, aliases(public_game_ids=['Ab12Cd34']))
    assert result['candidate_games'] == 2
    assert result['findings'][0]['source_game_index'] == 2
    with pytest.raises(ValueError):
        reject_historical_source(result)


def test_unknown_export_never_qualifies_independence():
    result = report()
    reject_historical_source(result)
    assert not result['findings']
    assert result['eligible_for_freeze'] is False
    assert result['independent_cohort_qualified'] is False


def test_tampered_bytes_and_unverified_cache_fail(tmp_path):
    with pytest.raises(ValueError, match='digest'):
        screen_historical_source(RAW, '0' * 64, aliases())
    path = tmp_path / 'cache.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='cache digest'):
        load_historical_aliases(path)


@pytest.mark.parametrize('raw', [b'', RAW + b'17-22\n'])
def test_empty_or_trailing_tokens_cannot_clear(raw):
    with pytest.raises(ValueError):
        report(raw)


@pytest.mark.parametrize('site,expected', [
    ('https://lidraughts.org/Ab12Cd34/black', 'Ab12Cd34'),
    ('https://lidraughts.org.evil/Ab12Cd34', None),
    ('https://example.org/Ab12Cd34', None),
])
def test_public_id_host_and_player_suffix(site, expected):
    game = parse_games_strict(RAW.decode().replace('https://lidraughts.org/Ab12Cd34/white', site))[0]
    assert public_id(game) == expected


def test_preflight_alias_match_rejects_before_any_engine_replay(tmp_path, monkeypatch):
    import research.mtdp.prospective_source_preflight as module
    from research.mtdp.tests.test_prospective_source_preflight import row as manifest_row
    # Use the production manifest byte check; engine must never be reached.
    path = tmp_path / 'candidate.pdn'
    path.write_bytes(RAW)
    row = manifest_row(hashlib.sha256(RAW).hexdigest())
    monkeypatch.setattr(module, 'load_historical_fens', lambda p: {})
    monkeypatch.setattr(module, 'reject_historical_fen_overlap', lambda r, v: None)
    monkeypatch.setattr(module, 'load_historical_aliases', lambda p: aliases(public_game_ids=['Ab12Cd34']))
    with pytest.raises(ValueError, match='Historical source alias overlap'):
        module.preflight_sources([row], {row['game_id']: path}, object(), root=ROOT,
                                 historical_cache=tmp_path / 'pinned-cache')


def test_real_25_sources_reconcile_exact_registry_sets():
    cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
    adapter = os.environ.get('MTDP_HISTORICAL_ADAPTER')
    if not cache or not adapter:
        if os.environ.get('MTDP_REQUIRE_HISTORICAL_ALIASES') == '1':
            pytest.fail('Required pinned historical inputs unavailable')
        pytest.skip('Pinned historical inputs not provided')
    actual = reconcile(ROOT, Path(adapter).resolve(), Path(cache))
    expected = json.loads((ROOT / 'research/mtdp/validation/historical-source-alias-reconciliation-2026-11-22.json').read_text())
    assert actual == expected
    assert actual['game_records'] == actual['matched_game_records'] == 4824
    assert actual['public_game_ids'] == 4790
    assert actual['notation_fingerprints'] == 4658
