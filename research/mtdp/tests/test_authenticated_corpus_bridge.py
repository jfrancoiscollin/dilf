"""Bridge refusal tests, no real prospective sample, signatures or target scores."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from research.mtdp.authenticated_corpus_bridge import (
    canonical_position_sha256, export_known_exclusions, verify_derived_rows,
    audit_authenticated_corpus,
)
from research.mtdp.historical_fen_bridge import CACHE_SHA256

DIGEST = 'a' * 64
TRAJECTORY = 'b' * 64
FEN = 'B:W13,K48:B3,K46'


def row():
    return {'game_id': DIGEST + ':1', 'fen': FEN, 'raw_sha256': DIGEST,
            'canonical_sha256': canonical_position_sha256(FEN),
            'trajectory_sha256': TRAJECTORY, 'tournament_id': 'synthetic',
            'event_id': 'synthetic', 'split': 'train', 'ply': 0}


def proof():
    return {'trajectory_checks': {DIGEST: {'games': [
        {'source_game_index': 1, 'trajectory_sha256': TRAJECTORY}]}}}


def test_canonical_hash_uses_occupancy_syntax_and_no_newline():
    expected = hashlib.sha256(b'B:W13,K48:B3,K46').hexdigest()
    assert canonical_position_sha256(FEN) == expected
    assert canonical_position_sha256('B:WK48,13:BK46,3') == expected
    assert expected != hashlib.sha256((FEN + '\n').encode()).hexdigest()


@pytest.mark.parametrize('key', ['raw_sha256', 'canonical_sha256', 'trajectory_sha256'])
def test_forged_declared_hash_never_passes(key):
    candidate = {**row(), key: 'c' * 64}
    with pytest.raises(ValueError, match='disagrees'):
        verify_derived_rows([candidate], proof())


@pytest.mark.parametrize('games', [[], [
    {'source_game_index': 1, 'trajectory_sha256': TRAJECTORY},
    {'source_game_index': 1, 'trajectory_sha256': TRAJECTORY}], [
    {'source_game_index': 2, 'trajectory_sha256': TRAJECTORY}]])
def test_missing_duplicate_or_wrong_game_trajectory_refused(games):
    p = {'trajectory_checks': {DIGEST: {'games': games}}}
    with pytest.raises(ValueError, match='unique authenticated'):
        verify_derived_rows([row()], p)


def test_matching_claims_preserve_rows_without_granting_qualification():
    r = row()
    assert verify_derived_rows([r], proof()) == [r]
    assert 'independent_cohort_qualified' not in r


def test_unverified_registry_fails_before_rules_or_sources(tmp_path):
    fake = tmp_path / 'cache.json'
    fake.write_text('{}')
    with pytest.raises(ValueError, match='cache digest'):
        audit_authenticated_corpus([row()], {}, root=tmp_path, adapter=tmp_path,
                                  historical_cache=fake)


def test_public_bridge_produces_own_proof_and_keeps_external_gate(monkeypatch):
    import research.mtdp.authenticated_corpus_bridge as module
    forbidden = {key: [] for key in
                 ('game_ids', 'raw_sha256', 'trajectory_sha256', 'canonical_sha256')}
    calls = []
    monkeypatch.setattr(module, 'export_known_exclusions', lambda path: forbidden)
    engine = object()
    monkeypatch.setattr(module, 'checked_engine', lambda path: engine)
    def preflight(rows, sources, actual_engine, **kw):
        assert actual_engine is engine
        assert kw['historical_cache'] == Path('cache')
        calls.append('replayed')
        return proof()
    monkeypatch.setattr(module, 'preflight_sources', preflight)
    result = audit_authenticated_corpus([row()], {}, root='.', adapter='.', historical_cache='cache')
    assert calls == ['replayed']
    assert result['structural_preflight']['admissible_structurally'] is True
    assert result['declared_hashes_recomputed_and_verified'] is True
    for key in ('external_event_identity_authenticated', 'complete_historical_exclusion_registry',
                'independent_cohort_qualified', 'scientific_freeze'):
        assert result[key] is False


def test_public_bridge_keeps_d1_split_leakage_refusal(monkeypatch):
    import research.mtdp.authenticated_corpus_bridge as module
    monkeypatch.setattr(module, 'export_known_exclusions', lambda path: {
        key: [] for key in ('game_ids', 'raw_sha256', 'trajectory_sha256', 'canonical_sha256')})
    monkeypatch.setattr(module, 'checked_engine', lambda path: object())
    monkeypatch.setattr(module, 'preflight_sources', lambda *args, **kw: proof())
    with pytest.raises(ValueError, match='cross_split_game_leakage'):
        audit_authenticated_corpus([row(), {**row(), 'ply': 1, 'split': 'test'}], {},
                                  root='.', adapter='.', historical_cache='cache')


def test_real_cache_export_contains_all_known_canonical_aliases():
    cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
    if not cache:
        if os.environ.get('MTDP_REQUIRE_HISTORICAL_ALIASES') == '1':
            pytest.fail('Pinned historical cache required')
        pytest.skip('Pinned historical cache unavailable')
    result = export_known_exclusions(cache)
    root = Path(__file__).resolve().parents[3]
    expected = json.loads((root / 'research/mtdp/validation/authenticated-d1-exclusion-export-2026-11-22.json').read_text())
    assert {key: len(value) for key, value in result.items()} == expected['exclusion_counts']
    raw = (json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n').encode()
    assert hashlib.sha256(raw).hexdigest() == expected['derived_registry_sha256']
    assert len(result['raw_sha256']) == 25
    assert len(result['game_ids']) == 4790
    assert len(result['trajectory_sha256']) == 4468
    assert len(result['canonical_sha256']) == len(set(result['canonical_sha256']))
    assert canonical_position_sha256('W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20') in result['canonical_sha256']


def test_real_pcblues_game_cannot_enter_via_forged_d1_labels():
    cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
    adapter = os.environ.get('MTDP_HISTORICAL_ADAPTER')
    if not cache or not adapter:
        if os.environ.get('MTDP_REQUIRE_HISTORICAL_ALIASES') == '1':
            pytest.fail('Pinned historical cache and adapter required')
        pytest.skip('Pinned inputs unavailable')
    root = Path(__file__).resolve().parents[3]
    source = root / 'data/exports/pcblues/pcblues_games.pdn'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    fen = 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'
    candidate = {**row(), 'game_id': digest + ':1', 'source_pdn_sha256': digest,
                 'raw_sha256': digest, 'fen': fen,
                 'canonical_sha256': canonical_position_sha256(fen)}
    with pytest.raises(ValueError, match='Historical canonical FEN overlap'):
        audit_authenticated_corpus([candidate], {candidate['game_id']: source}, root=root,
                                  adapter=adapter, historical_cache=cache)


def test_projection_removes_only_hash_claims_and_preserves_closed_schema(monkeypatch):
    import research.mtdp.authenticated_corpus_bridge as module
    monkeypatch.setattr(module, 'export_known_exclusions', lambda path: {})
    monkeypatch.setattr(module, 'checked_engine', lambda path: object())
    def preflight(rows, *args, **kw):
        from research.mtdp.decision_equivalence.corpus_guard import audit
        assert all(key not in rows[0] for key in
                   ('raw_sha256', 'trajectory_sha256', 'canonical_sha256'))
        return audit(rows)
    monkeypatch.setattr(module, 'preflight_sources', preflight)
    candidate = {**row(), 'source_pdn_sha256': DIGEST, 'secret_outcome': 1}
    with pytest.raises(ValueError, match='unknown manifest fields'):
        audit_authenticated_corpus([candidate], {}, root='.', adapter='.', historical_cache='cache')
