"""Integration checks without a rules engine or any reference search."""
import hashlib
from pathlib import Path

import pytest

from pedagogy.game import initial_state, state_to_fen
from research.mtdp.prospective_source_preflight import preflight_sources
from research.mtdp.reserved_source_inventory import BASE
from research.mtdp.tests.test_pdn import MockRules

ROOT = Path(__file__).resolve().parents[3]
RAW = b'[Event "synthetic"]\n[FEN "W:W32:B1"]\n1. 32-28 *\n'


class NeverReplay:
    def legal_moves(self, state):
        raise AssertionError('Reserved/schema/digest checks must finish before replay')


def row(digest, index=1, ply=0, fen='W:W32:B1'):
    return {'game_id': f'{digest}:{index}', 'tournament_id': 'untrusted-label',
            'event_id': 'untrusted-label', 'split': 'train', 'ply': ply,
            'fen': fen, 'source_pdn_sha256': digest}


def candidate(tmp_path):
    path = tmp_path / 'candidate.pdn'
    path.write_bytes(RAW)
    r = row(hashlib.sha256(RAW).hexdigest())
    return r, {r['game_id']: path}


def reserved():
    path = ROOT / BASE / 'two-named-arenas-final/s7ahYqL4/first.pdn'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    r = row(digest, fen=state_to_fen(initial_state()))
    return r, {r['game_id']: path}


def test_clean_synthetic_source_gets_membership_but_never_freeze_qualification(tmp_path):
    r, sources = candidate(tmp_path)
    r1 = {**r, 'ply': 1, 'fen': 'B:W28:B1'}
    report = preflight_sources([r, r1], sources, MockRules(), root=ROOT)
    assert report['known_reserved_sources_screened']
    assert report['manifest_game_id_binding_verified']
    assert report['fmjd_legality_verified']
    assert len(report['source_checks']) == 1
    assert report['independent_cohort_qualified'] is False
    assert report['eligible_for_freeze'] is False
    assert report['complete_historical_exclusion_registry'] is False


def test_reserved_export_rejected_despite_forged_manifest_event_labels():
    r, sources = reserved()
    with pytest.raises(ValueError, match='Reserved source overlap'):
        preflight_sources([r], sources, NeverReplay(), root=ROOT)


def test_entire_batch_checked_before_any_clean_game_replay(tmp_path):
    good, good_sources = candidate(tmp_path)
    bad, bad_sources = reserved()
    with pytest.raises(ValueError, match='Reserved source overlap'):
        preflight_sources([good, bad], {**good_sources, **bad_sources}, NeverReplay(), root=ROOT)


def test_tampered_source_fails_before_replay(tmp_path):
    r, sources = candidate(tmp_path)
    next(iter(sources.values())).write_bytes(RAW + b'\n')
    with pytest.raises(ValueError, match='digest'):
        preflight_sources([r], sources, NeverReplay(), root=ROOT)


def test_target_fields_cannot_enter_preflight(tmp_path):
    r, sources = candidate(tmp_path)
    r['metadata'] = {'source': {'pdn_sha256': r['source_pdn_sha256'], 'score': 1}}
    with pytest.raises(ValueError, match='target-derived'):
        preflight_sources([r], sources, NeverReplay(), root=ROOT)


def test_missing_reserved_registry_cannot_grant_clearance(tmp_path):
    r, sources = candidate(tmp_path)
    with pytest.raises(FileNotFoundError):
        preflight_sources([r], sources, NeverReplay(), root=tmp_path)
