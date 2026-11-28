"""Exclusion-role attacks and real pinned D1 structural checks, never admission."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.mtdp.conservative_exclusion_ledger import (
    historical_supplement, derive, encoded, load_verified_ledger, digest)
from research.mtdp.authenticated_corpus_bridge import (
    canonical_position_sha256, export_known_exclusions, audit_authenticated_corpus)
from research.mtdp.decision_equivalence.corpus_admission import audit


HISTORICAL = 'B:WK48:BK32'
FRESH = 'W:W31:B20'


def owner(role, key='example:1'):
    return {'role': role, 'game_key': key, 'plies': [2]}


def record(fen, owners, legacy=False):
    return {'fen': fen, 'owners': owners, 'legacy_cache_member': legacy}


class RoleFilter(unittest.TestCase):
    def test_fresh_only_never_self_excludes(self):
        self.assertEqual(historical_supplement([record(FRESH, [owner('fresh_candidate')])], set()), [])

    def test_shared_board_keeps_only_historical_evidence(self):
        result = historical_supplement([record(HISTORICAL, [owner('fresh_candidate', 'BZZ0yME2'),
                    owner('historical_quarantines')])], set())
        self.assertEqual(result[0]['historical_owners'], [owner('historical_quarantines')])
        self.assertEqual(result[0]['canonical_sha256'], digest(HISTORICAL.encode()))
        self.assertNotIn('BZZ0yME2', str(result))

    def test_legacy_is_not_duplicated(self):
        self.assertEqual(historical_supplement([record(HISTORICAL,
              [owner('historical_quarantines')], True)], {HISTORICAL}), [])

    def test_malformed_ownership_or_membership_rejected(self):
        bad = [record(HISTORICAL, [owner('unknown')]),
               record(HISTORICAL, [owner('historical_quarantines')], True),
               record(HISTORICAL, [{'role': 'historical_quarantines', 'game_key': 'x', 'plies': [True]}])]
        for row in bad:
            with self.subTest(row=row), self.assertRaises(ValueError):
                historical_supplement([row], set())

    def test_duplicate_or_noncanonical_fen_rejected(self):
        row = record(HISTORICAL, [owner('historical_quarantines')])
        with self.assertRaises(ValueError):
            historical_supplement([row, row], set())
        with self.assertRaises(ValueError):
            historical_supplement([record('B:WK48,13:BK32', [owner('historical_quarantines')])], set())


class PinnedLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
        cls.inventory = os.environ.get('MTDP_CORRECTED_INVENTORY')
        if not cls.cache or not cls.inventory:
            if os.environ.get('MTDP_REQUIRE_CONSERVATIVE_LEDGER') == '1':
                raise AssertionError('Pinned ledger inputs required')
            raise unittest.SkipTest('Pinned ledger inputs unavailable')
        cls.temp = tempfile.TemporaryDirectory()
        cls.manifest, cls.payload, cls.union = derive(cls.cache, cls.inventory)
        cls.paths = {'inventory': cls.inventory,
                     'manifest': Path(cls.temp.name) / 'manifest.json',
                     'supplement': Path(cls.temp.name) / 'supplement.jsonl'}
        cls.paths['manifest'].write_bytes(encoded(cls.manifest))
        cls.paths['supplement'].write_bytes(cls.payload)
        cls.registry = export_known_exclusions(cls.cache, exclusion_ledger=cls.paths)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_denominators_and_no_fresh_owners(self):
        self.assertEqual(len(self.registry['canonical_sha256']), 455582)
        self.assertEqual(len(self.registry['trajectory_sha256']), 4468)
        self.assertEqual(len(self.registry['game_ids']), 4790)
        self.assertEqual(len(self.registry['raw_sha256']), 25)
        self.assertEqual(len(self.union), 455582)
        self.assertNotIn(b'fresh_candidate', self.payload)
        self.assertNotIn(b'BZZ0yME2', self.payload)
        for key in ('scientific_freeze', 'independent_cohort_qualified', 'complete_historical_exclusion_registry'):
            self.assertIs(self.manifest[key], False)

    def test_d1_rejects_old_and_supplementary_positions_but_not_fresh_only(self):
        rows = [json.loads(line) for line in Path(self.inventory).read_bytes().splitlines()]
        fresh = next(r['fen'] for r in rows if not r['legacy_cache_member'] and
                     all(o['role'] == 'fresh_candidate' for o in r['owners']))
        old = next(r['fen'] for r in rows if r['legacy_cache_member'])
        for fen, blocked in [(old, True), (HISTORICAL, True), (fresh, False)]:
            candidate = {'tournament_id': 'synthetic', 'event_id': 'synthetic',
                'game_id': 'synthetic:1', 'ply': 0, 'fen': fen, 'split': 'train',
                'raw_sha256': 'a' * 64, 'trajectory_sha256': 'b' * 64,
                'canonical_sha256': canonical_position_sha256(fen)}
            result = audit([candidate], self.registry)
            self.assertEqual(result['admissible_structurally'], not blocked)
            self.assertIs(result['historical_exclusion_proven'], False)
        self.assertNotIn(fresh, self.union)

    def test_real_public_bridge_rejects_supplement_before_admission(self):
        candidate = {'tournament_id': 'synthetic', 'event_id': 'synthetic',
            'game_id': 'a' * 64 + ':1', 'ply': 0, 'fen': HISTORICAL, 'split': 'train',
            'raw_sha256': 'a' * 64, 'trajectory_sha256': 'b' * 64,
            'canonical_sha256': canonical_position_sha256(HISTORICAL)}
        proof = {'trajectory_checks': {'a' * 64: {'games': [
            {'source_game_index': 1, 'trajectory_sha256': 'b' * 64}]}}}
        with patch('research.mtdp.authenticated_corpus_bridge.checked_engine', return_value=object()), \
             patch('research.mtdp.authenticated_corpus_bridge.preflight_sources', return_value=proof):
            with self.assertRaisesRegex(ValueError, 'reserved_or_historical_overlap'):
                audit_authenticated_corpus([candidate], {}, root='.', adapter='.',
                    historical_cache=self.cache, exclusion_ledger=self.paths)

    def test_clean_structural_bridge_never_grants_independence(self):
        rows = [json.loads(line) for line in Path(self.inventory).read_bytes().splitlines()]
        fen = next(r['fen'] for r in rows if not r['legacy_cache_member'] and
                   all(o['role'] == 'fresh_candidate' for o in r['owners']))
        candidate = {'tournament_id': 'synthetic', 'event_id': 'synthetic',
            'game_id': 'a' * 64 + ':1', 'ply': 0, 'fen': fen, 'split': 'train',
            'raw_sha256': 'a' * 64, 'trajectory_sha256': 'b' * 64,
            'canonical_sha256': canonical_position_sha256(fen)}
        proof = {'trajectory_checks': {'a' * 64: {'games': [
            {'source_game_index': 1, 'trajectory_sha256': 'b' * 64}]}}}
        # Registry bytes were authenticated in setUpClass; only upstream replay is synthetic.
        with patch('research.mtdp.authenticated_corpus_bridge.export_known_exclusions', return_value=self.registry), \
             patch('research.mtdp.authenticated_corpus_bridge.checked_engine', return_value=object()), \
             patch('research.mtdp.authenticated_corpus_bridge.preflight_sources', return_value=proof):
            result = audit_authenticated_corpus([candidate], {}, root='.', adapter='.',
                    historical_cache=self.cache, exclusion_ledger=self.paths)
        self.assertTrue(result['structural_preflight']['admissible_structurally'])
        self.assertTrue(result['conservative_exclusion_sidecar_authenticated'])
        self.assertEqual(result['conservative_exclusion_manifest_sha256'], digest(encoded(self.manifest)))
        for key in ('independent_cohort_qualified', 'scientific_freeze',
                    'complete_historical_exclusion_registry', 'external_event_identity_authenticated'):
            self.assertIs(result[key], False)

    def test_tampered_manifest_or_supplement_rejected(self):
        for member in ('manifest', 'supplement'):
            path = self.paths[member]
            original = path.read_bytes()
            try:
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'differs from authenticated'):
                    load_verified_ledger(self.cache, **self.paths)
            finally:
                path.write_bytes(original)

    def test_unpinned_inventory_rejected(self):
        fake = Path(self.temp.name) / 'fake.jsonl'
        fake.write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'inventory digest'):
            derive(self.cache, fake)


if __name__ == '__main__':
    unittest.main()
