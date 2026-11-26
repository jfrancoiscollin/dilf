"""Synthetic stream/metric wiring and fail-closed fixed scope tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pedagogy.game import Move
from research.mtdp.nonking_oracle import StreamEvidence, compare_batches, frozen_scope
from research.mtdp.return_capture_oracle import root_key


class EngineModel:
    def __init__(self, moves):
        self.moves = moves
    def legal_moves(self, state):
        return self.moves


class StreamingOracleTests(unittest.TestCase):
    def test_incremental_hash_matches_exact_bytes_and_exclusive_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'evidence'
            with StreamEvidence(p) as sink:
                sink.emit(b'first\n'); sink.emit(b'\x00\xff'); sink.emit(b'')
            raw = p.read_bytes()
            self.assertEqual(sink.metadata(), {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            with self.assertRaises(FileExistsError):
                StreamEvidence(p)

    def test_chunk_boundaries_preserve_all_indices_and_binary_metadata(self):
        fens = ['W:W31:B20', 'B:W31:B20', 'W:W32:B20']
        a = Move((31, 26)); calls = []
        def reference(chunk):
            calls.append(chunk)
            return [[root_key(a)] for _ in chunk], ('\n'.join(chunk) + '\n').encode()
        with tempfile.TemporaryDirectory() as tmp:
            summary, metadata = compare_batches(fens, EngineModel([a]), EngineModel([a]), reference, tmp, batch_size=2)
            rows = [json.loads(line) for line in (Path(tmp) / 'position-ledger.jsonl').read_bytes().splitlines()]
            self.assertEqual([r['index'] for r in rows], [0, 1, 2])
            self.assertEqual([len(c) for c in calls], [2, 1])
            self.assertEqual(summary['positions'], 3)
            self.assertEqual(summary['corrected_jass_mismatch'], 0)
            for key, name in [('position_ledger', 'position-ledger.jsonl'), ('witnesses', 'change-witnesses.jsonl'), ('raw_catalogue', 'jass-catalogues.txt')]:
                raw = (Path(tmp) / name).read_bytes()
                self.assertEqual(metadata[key], {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

    def test_regression_and_witness_are_not_hidden(self):
        a, b = Move((31, 26)), Move((31, 27))
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = compare_batches(['W:W31:B20'], EngineModel([a, b]), EngineModel([a]),
                lambda chunk: ([[root_key(a), root_key(b)]], b'synthetic\n'), tmp)
            self.assertEqual(summary['newly_introduced_jass_mismatch'], 1)
            self.assertEqual(summary['removed_roots'], 1)
            witness = json.loads((Path(tmp) / 'change-witnesses.jsonl').read_bytes())
            self.assertEqual(witness['removed_roots'], [[root_key(b)[0], root_key(b)[1]]])

    def test_wrong_reference_length_and_active_king_fail(self):
        a = Move((31, 26))
        for fen, catalogues in [('W:W31:B20', []), ('W:WK48:B20', [[root_key(a)]])]:
            with self.subTest(fen=fen), tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
                compare_batches([fen], EngineModel([a]), EngineModel([a]), lambda chunk: (catalogues, b''), tmp)

    def test_altered_frozen_scope_rejected_before_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'research/mtdp/validation'; p.mkdir(parents=True)
            (p / 'nonking-oracle-scope-2026-11-26.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'Frozen nonking scope changed'):
                frozen_scope(tmp, tmp, tmp)

    def test_truncated_or_replaced_payload_cannot_reuse_frozen_claims(self):
        root = Path(__file__).resolve().parents[3]
        expected = json.loads((root / 'research/mtdp/validation/nonking-oracle-scope-2026-11-26.json').read_bytes())
        payloads = [b'W:W31:B20\n', b'X\n' * 384621 + b'X' * (expected['selected_fens_bytes'] - 2 * 384621 - 1) + b'\n']
        for payload in payloads:
            with patch('research.mtdp.nonking_oracle.authenticated_scope', return_value=(expected, payload)):
                with self.assertRaisesRegex(ValueError, 'differs from preregistration'):
                    frozen_scope(root, 'unused', 'unused')


if __name__ == '__main__':
    unittest.main()
