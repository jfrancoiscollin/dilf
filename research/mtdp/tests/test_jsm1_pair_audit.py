"""Synthetic integrity attacks; no real source or game identity is admitted."""
import gzip
import hashlib
from pathlib import Path
import tempfile
import unittest

from research.mtdp.jsm1_pair_audit import audit, audit_pair, HEADER, RECORD, META


class PairAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'objects').mkdir()
        self.board = RECORD.pack(1, 0, 2, 0, 0, 7, 1)
        self.praw = HEADER.pack(b'JNNW', 2) + self.board * 2
        self.mraw = HEADER.pack(b'JSM1', 2) + META.pack(5, 6, 0) + META.pack(5, 7, 1)
        self.p = self.write('p.gz', 'jnnw', self.praw)
        self.m = self.write('m.gz', 'jsm1', self.mraw)

    def write(self, name, fmt, raw):
        compressed = gzip.compress(raw, mtime=0)
        (self.root / 'objects' / name).write_bytes(compressed)
        return dict(path='objects/' + name, format=fmt, record_count=2,
                    record_count_unit='positions' if fmt == 'jnnw' else 'metadata_rows',
                    stored_bytes=len(compressed), stored_sha256=hashlib.sha256(compressed).hexdigest(),
                    uncompressed_bytes=len(raw), uncompressed_sha256=hashlib.sha256(raw).hexdigest())

    def test_compatible_files_still_not_admitted(self):
        result = audit_pair(self.root, self.p, self.m)
        self.assertEqual(result['rows_structurally_checked'], 2)
        self.assertEqual(result['distinct_sampled_game_ids'], 1)
        self.assertEqual(result['distinct_sampled_opening_ids'], 2)
        self.assertEqual(result['seeded_rows'], 1)
        self.assertFalse(result['row_alignment_authenticated'])
        self.assertFalse(result['independent_cohort_admitted'])

    def test_swapped_metadata_is_not_detectable_as_semantic_alignment(self):
        swapped = self.mraw[:8] + self.mraw[25:] + self.mraw[8:25]
        m = self.write('swap.gz', 'jsm1', swapped)
        self.assertFalse(audit_pair(self.root, self.p, m)['row_alignment_authenticated'])

    def test_bad_header_count_truncation_trailer_and_seed_rejected(self):
        variants = [b'JSM2' + self.mraw[4:], HEADER.pack(b'JSM1', 3) + self.mraw[8:],
                    self.mraw[:-1], self.mraw + b'X', self.mraw[:-1] + b'\x02']
        for i, raw in enumerate(variants):
            with self.subTest(i=i), self.assertRaises(ValueError):
                audit_pair(self.root, self.p, self.write('bad.gz', 'jsm1', raw))

    def test_stored_and_uncompressed_hashes_rejected(self):
        for key in ('stored_sha256', 'uncompressed_sha256'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit_pair(self.root, self.p, dict(self.m, **{key: '0' * 64}))

    def test_wrong_row_count_unit_and_budget_rejected(self):
        for change in ({'record_count': 3}, {'record_count': True}, {'format': 'jsm2'},
                       {'record_count_unit': 'positions'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit_pair(self.root, self.p, dict(self.m, **change))
        with self.assertRaises(ValueError):
            audit_pair(self.root, self.p, self.m, sample_budget=1025)

    def test_invalid_board_outside_sample_is_rejected(self):
        invalid = RECORD.pack(1, 0, 1, 0, 0, 0, 0)
        p = self.write('bad-p.gz', 'jnnw', self.praw[:8] + self.board + invalid)
        with self.assertRaises(ValueError):
            audit_pair(self.root, p, self.m, sample_budget=1)

    def test_symlink_rejected(self):
        (self.root / 'objects' / 'link.gz').symlink_to(self.root / self.m['path'])
        with self.assertRaises(ValueError):
            audit_pair(self.root, self.p, dict(self.m, path='objects/link.gz'))

    def test_unpinned_manifest_rejected_before_reading_objects(self):
        (self.root / 'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'unpinned'):
            audit(self.root)


if __name__ == '__main__':
    unittest.main()
