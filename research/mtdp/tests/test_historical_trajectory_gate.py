"""Whole-game identity gate; synthetic rules only, no score or cohort claim."""
import hashlib
from pathlib import Path

import pytest

from pedagogy.game import parse_fen, state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_trajectory_gate import (
    audit_source_trajectories, load_historical_trajectories, reject_historical_trajectories,
)
from research.mtdp.jass_benchmark.named_arena_replay import trajectory_fingerprint
from research.mtdp.pdn import parse_games, validated_trajectory
from research.mtdp.prospective_source_preflight import preflight_sources
from research.mtdp.tests.test_pdn import MockRules

RAW = b'[Event "synthetic"]\n[FEN "W:W32:B1"]\n1. 32-28 *\n'
ROOT = Path(__file__).resolve().parents[3]


def source(tmp_path, raw=RAW):
    p = tmp_path / 'candidate.pdn'
    p.write_bytes(raw)
    return p, hashlib.sha256(raw).hexdigest()


def known():
    return {trajectory_fingerprint(validated_trajectory(parse_games(RAW.decode())[0], MockRules()))}


def test_historical_hash_preserves_king_first_order_and_exact_newlines():
    states = [parse_fen('B:W13,K48:B3,K46'), parse_fen('W:W13,K48:B3,K45')]
    trajectory = [(i, None, s) for i, s in enumerate(states)]
    expected = 'B:WK48,13:BK46,3\nW:WK48,13:BK45,3'
    assert '\n'.join(state_to_fen(s) for s in states) == expected
    assert trajectory_fingerprint(trajectory) == hashlib.sha256(expected.encode()).hexdigest()
    reordered = '\n'.join(canonical_fen(state_to_fen(s)) for s in states)
    assert hashlib.sha256(reordered.encode()).hexdigest() != trajectory_fingerprint(trajectory)


def test_changed_metadata_digest_cannot_hide_a_known_trajectory(tmp_path):
    path, digest = source(tmp_path, RAW.replace(b'synthetic', b'another-label'))
    assert digest != hashlib.sha256(RAW).hexdigest()
    report = audit_source_trajectories(path, digest, [1], MockRules(), known())
    assert report['complete_legal_games_verified'] == 1
    assert report['known_historical_trajectory_matches'] == 1
    assert report['independent_cohort_qualified'] is False
    with pytest.raises(ValueError, match='Historical complete trajectory overlap'):
        reject_historical_trajectories(report)


def test_novel_trajectory_is_only_a_known_registry_screen(tmp_path):
    path, digest = source(tmp_path)
    report = audit_source_trajectories(path, digest, [1], MockRules(), set())
    reject_historical_trajectories(report)
    assert report['scientific_freeze'] is False
    assert report['independent_cohort_qualified'] is False


@pytest.mark.parametrize('indices', [[], [True], [0], [2], [1, 1]])
def test_invalid_or_absent_source_index_fails(tmp_path, indices):
    path, digest = source(tmp_path)
    with pytest.raises(ValueError):
        audit_source_trajectories(path, digest, indices, MockRules(), set())


def test_source_tampering_fails_before_rules(tmp_path):
    path, digest = source(tmp_path)
    path.write_bytes(RAW + b'\n')
    with pytest.raises(ValueError, match='digest'):
        audit_source_trajectories(path, digest, [1], object(), set())


def test_illegal_late_move_cannot_clear_the_whole_game(tmp_path):
    path, digest = source(tmp_path, RAW.replace(b'32-28 *', b'32-28 18-23 *'))
    with pytest.raises(ValueError):
        audit_source_trajectories(path, digest, [1], MockRules(), set())


def test_post_result_tokens_cannot_be_silently_dropped(tmp_path):
    path, digest = source(tmp_path, RAW + b'17-22\n')
    with pytest.raises(ValueError, match='after result'):
        audit_source_trajectories(path, digest, [1], MockRules(), set())


def test_fake_historical_registry_is_rejected(tmp_path):
    path, _ = source(tmp_path, b'{}')
    with pytest.raises(ValueError, match='cache digest'):
        load_historical_trajectories(path)


def test_preflight_rejects_whole_game_even_if_fen_screen_has_no_match(tmp_path, monkeypatch):
    # Synthetic narrow FEN view solely to isolate the trajectory wiring.
    # Real production views always require the exact pinned full cache bytes.
    import research.mtdp.prospective_source_preflight as module
    path, digest = source(tmp_path)
    monkeypatch.setattr(module, 'load_historical_fens', lambda p: {
        'canonical_fens': frozenset(), 'historical_cache_sha256': 'synthetic-only'})
    monkeypatch.setattr(module, 'load_historical_trajectories', lambda p: known())
    gid = digest + ':1'
    row = {'game_id': gid, 'tournament_id': 'untrusted', 'event_id': 'untrusted',
           'split': 'train', 'ply': 0, 'fen': 'W:W32:B1', 'source_pdn_sha256': digest}
    with pytest.raises(ValueError, match='Historical complete trajectory overlap'):
        preflight_sources([row], {gid: path}, MockRules(), root=ROOT, historical_cache=path)


def test_real_cache_and_pinned_rules_recover_all_26_baseline_trajectories():
    import os
    from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
    cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
    adapter = os.environ.get('MTDP_HISTORICAL_ADAPTER')
    if not cache or not adapter:
        if os.environ.get('MTDP_REQUIRE_HISTORICAL_TRAJECTORIES') == '1':
            raise AssertionError('Required real historical cache/rules unavailable')
        pytest.skip('Dedicated historical workflow supplies real cache and rules')
    historical = load_historical_trajectories(cache)
    assert len(historical) == 4468
    path = ROOT / 'data/exports/pcblues/pcblues_games.pdn'
    digest = '025ad0a1a9ddcf508e3284eef65eb1cf76ebf7763d1241a127432f99eac3d8be'
    report = audit_source_trajectories(path, digest, range(1, 27),
                                       checked_engine(Path(adapter).resolve()), historical)
    assert report['complete_legal_games_verified'] == 26
    assert report['known_historical_trajectory_matches'] == 26
    with pytest.raises(ValueError, match='Historical complete trajectory overlap'):
        reject_historical_trajectories(report)


def test_preflight_known_registry_clearance_still_cannot_qualify_a_cohort(tmp_path, monkeypatch):
    import research.mtdp.prospective_source_preflight as module
    path, digest = source(tmp_path)
    monkeypatch.setattr(module, 'load_historical_fens', lambda p: {
        'canonical_fens': frozenset(), 'historical_cache_sha256': 'synthetic-only'})
    monkeypatch.setattr(module, 'load_historical_trajectories', lambda p: frozenset())
    gid = digest + ':1'
    first = {'game_id': gid, 'tournament_id': 'untrusted', 'event_id': 'untrusted',
             'split': 'train', 'ply': 0, 'fen': 'W:W32:B1', 'source_pdn_sha256': digest}
    report = preflight_sources([first, {**first, 'ply': 1, 'fen': 'B:W28:B1'}],
                              {gid: path}, MockRules(), root=ROOT, historical_cache=path)
    assert report['historical_complete_trajectories_screened'] is True
    assert report['trajectory_checks'][digest]['complete_legal_games_verified'] == 1
    assert report['trajectory_checks'][digest]['known_historical_trajectory_matches'] == 0
    assert report['independent_cohort_qualified'] is False
    assert report['eligible_for_freeze'] is False
    assert report['complete_historical_exclusion_registry'] is False
