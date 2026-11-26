"""Stream integrity and compact evidence retain full comparison failures."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from pedagogy.game import Move, parse_fen
from research.mtdp.complement_successor_audit import records_stream, compact_evidence, file_metadata, load_scope
from research.mtdp.king_origin_inventory_impact import encoded
from research.mtdp.risk_successor_audit import compare_record


class ComplementAuditTests(unittest.TestCase):
    def fixture(self, root, records):
        path = root / 'manifest'; raw = b''.join(encoded(r) for r in records); path.write_bytes(raw)
        fens = ''.join(r['fen'] + '\n' for r in records).encode()
        scope = dict(manifest=file_metadata(path), selected_fens={'bytes': len(fens), 'sha256': hashlib.sha256(fens).hexdigest()},
                     summary=dict(selected_fens=len(records), selected_total_legal_roots=sum(len(r['legal_roots']) for r in records)))
        return path, scope

    def test_stream_checks_actual_bytes_and_counts_at_eof(self):
        rows = [dict(fen='B:W31:B20', catalogue_id='nonking', legal_roots=[['20-24', False]]),
                dict(fen='W:W31:B20', catalogue_id='nonking', legal_roots=[['31-26', False]])]
        with tempfile.TemporaryDirectory() as tmp:
            path, scope = self.fixture(Path(tmp), rows)
            self.assertEqual(list(records_stream(path, scope)), rows)
            scope['summary']['selected_fens'] += 1
            with self.assertRaisesRegex(ValueError, 'Consumed complement'):
                list(records_stream(path, scope))

    def test_consumed_bytes_cannot_change_after_startup_hash(self):
        row = dict(fen='W:W31:B20', catalogue_id='nonking', legal_roots=[['31-26', False]])
        with tempfile.TemporaryDirectory() as tmp:
            path, scope = self.fixture(Path(tmp), [row]); path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaises((ValueError, TypeError)):
                list(records_stream(path, scope))

    def test_unknown_fields_and_unordered_duplicate_parents_refused(self):
        a = dict(fen='W:W31:B20', catalogue_id='nonking', legal_roots=[])
        b = dict(fen='B:W31:B20', catalogue_id='nonking', legal_roots=[])
        with tempfile.TemporaryDirectory() as tmp:
            for records in [[{**a, 'target_score': 1}], [a, a], [a, b]]:
                path, scope = self.fixture(Path(tmp), records)
                with self.assertRaises(ValueError):
                    list(records_stream(path, scope))

    def test_compact_digest_keeps_failure_and_piece_type_change(self):
        a = Move((31, 26))
        parent = dict(fen='W:W31:B20', catalogue_id='nonking', categories=[], legal_roots=[['31-26', False]])
        reference = [('31-26', False, 'B:W26:B20')]
        good = compare_record(0, parent, [a], lambda s, m: parse_fen('B:W26:B20'), reference)
        bad = compare_record(0, parent, [a], lambda s, m: parse_fen('B:WK26:B20'), reference)
        good_compact, bad_compact = compact_evidence(0, good), compact_evidence(0, bad)
        self.assertTrue(good_compact['all_roots_and_successors_equal'])
        self.assertFalse(bad_compact['all_roots_and_successors_equal'])
        self.assertNotEqual(good_compact['root_successor_lists_sha256'], bad_compact['root_successor_lists_sha256'])
        self.assertEqual(len(bad['shared_root_successor_mismatches']), 1)

    def test_file_metadata_and_frozen_scope_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'data'; p.write_bytes(b'abc\n')
            self.assertEqual(file_metadata(p), dict(bytes=4, sha256=hashlib.sha256(b'abc\n').hexdigest()))
            root = Path(__file__).resolve().parents[3]
            with self.assertRaisesRegex(ValueError, 'Frozen complement manifest/list changed'):
                load_scope(root, p, p)


if __name__ == '__main__':
    unittest.main()
