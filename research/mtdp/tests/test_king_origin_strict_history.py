"""Score-blind identity and replay accounting tests on synthetic transitions."""
from pathlib import Path
import tempfile
import unittest

from pedagogy.game import Move, parse_fen, state_to_fen
from research.mtdp.pdn import PdnGame
from research.mtdp.historical_quarantine_frontier import explore
from research.mtdp.historical_base_quarantine_frontier import bind_sources
from research.mtdp.jass_benchmark.named_arena_replay import trajectory_fingerprint
from research.mtdp.king_origin_strict_history import (
    board_sequence_digest, load_fixed_history, load_quarantine_evidence)
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.tests.test_historical_quarantine_frontier import Model


class StrictHistoryTests(unittest.TestCase):
    def setUp(self):
        self.a = parse_fen('W:W31:B18,27')
        self.b = parse_fen('B:W13:B18')
        self.c = parse_fen('B:W13:B27')
        self.d = parse_fen('W:W8:B')
        self.m1 = Move((31, 22, 13), (27, 18))
        self.m2 = Move((31, 24, 13), (28, 19))
        self.m3 = Move((13, 8))
        self.game = PdnGame(1, {'FEN': 'W:W31:B18,27'}, ('31x13', '13-8'))

    def test_exact_legacy_serializer_without_terminal_newline(self):
        visited = {self.a: {0}, self.b: {1}, self.d: {2}}
        actual = board_sequence_digest(visited, 2, True)
        trajectory = [(0, '', self.a), (1, '31x13', self.b), (2, '13-8', self.d)]
        self.assertEqual(actual, trajectory_fingerprint(trajectory))
        raw = '\n'.join(state_to_fen(s) for s in (self.a, self.b, self.d)).encode()
        self.assertNotEqual(actual, digest(raw + b'\n'))

    def test_path_ambiguity_keeps_board_hash_without_action_certificate(self):
        report, visited = explore(self.game, Model({self.a: {self.m1: self.b, self.m2: self.b},
                                                 self.b: {self.m3: self.d}}))
        self.assertTrue(report['ambiguities'])
        self.assertEqual(board_sequence_digest(visited, 2, True),
                         trajectory_fingerprint([(0, '', self.a), (1, '', self.b), (2, '', self.d)]))
        self.assertTrue(report['strict_action_quarantine_retained'])

    def test_divergence_even_if_remerged_has_no_unique_sequence_hash(self):
        report, visited = explore(self.game, Model({self.a: {self.m1: self.b, self.m2: self.c},
                                                 self.b: {self.m3: self.d}, self.c: {self.m3: self.d}}))
        self.assertTrue(report['complete_board_frontier_replay'])
        self.assertIsNone(board_sequence_digest(visited, 2, True))

    def test_truncated_or_capped_run_cannot_reuse_a_full_hash(self):
        for kw in ({'frontier_limit': 1}, {'action_limit': 1}):
            report, visited = explore(self.game, Model({self.a: {self.m1: self.b, self.m2: self.c}}), **kw)
            self.assertIsNone(board_sequence_digest(visited, 2, report['complete_board_frontier_replay']))
        self.assertIsNone(board_sequence_digest({self.a: {0}}, 2, True))

    def test_wrong_ply_and_repeated_state_chronology(self):
        self.assertEqual(board_sequence_digest({self.a: {0, 2}, self.b: {1}}, 2, True),
                         trajectory_fingerprint([(0, '', self.a), (1, '', self.b), (2, '', self.a)]))
        for plies in ({-1}, {3}, {True}):
            with self.assertRaisesRegex(ValueError, 'outside'):
                board_sequence_digest({self.a: plies}, 2, True)

    def test_adapter_raw_fallback_still_requires_exact_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = root / 'artifact'; artifact.mkdir()
            adapter = root / 'adapter'; adapter.mkdir()
            pdn = adapter / 'different-name.pdn'; pdn.write_bytes(b'old pinned PDN')
            required = [{'file': 'historical.pdn', 'sha256': digest(b'old pinned PDN')}]
            self.assertEqual(bind_sources(artifact, required, extra_roots=(adapter,))['historical.pdn'], pdn)
            pdn.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'missing exact raw source'):
                bind_sources(artifact, required, extra_roots=(adapter,))

    def test_changed_historical_member_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'P1RUlfJc-exclusions.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'member digest'):
                load_fixed_history(tmp, tmp)

    def test_changed_reused_report_rejected_before_candidate_can_supply_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'research/mtdp/validation'; p.mkdir(parents=True)
            (p / 'king-origin-reconstruction-2026-11-26.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'reconstruction report changed'):
                load_quarantine_evidence(tmp, tmp, set())


if __name__ == '__main__':
    unittest.main()
