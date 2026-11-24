import gzip
import hashlib
from pathlib import Path
import tempfile
import unittest
from research.mtdp.jsm1_lineage_reproduction import extract_verified, compare_pair, reproduce


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        (self.root / 'objects').mkdir()
        self.raw = b'original payload'
        packed = gzip.compress(self.raw, mtime=0)
        self.source = self.root / 'objects/in.gz'
        self.source.write_bytes(packed)
        self.obj = dict(path='objects/in.gz', stored_bytes=len(packed),
                        stored_sha256=hashlib.sha256(packed).hexdigest(),
                        uncompressed_bytes=len(self.raw),
                        uncompressed_sha256=hashlib.sha256(self.raw).hexdigest())

    def test_extract_preserves_exact_bytes_and_refuses_replacement(self):
        dest = self.root / 'out'
        extract_verified(self.root, self.obj, dest)
        self.assertEqual(dest.read_bytes(), self.raw)
        with self.assertRaises(FileExistsError):
            extract_verified(self.root, self.obj, dest)

    def test_bad_stored_and_decompressed_integrity_rejected(self):
        for k, v in [('stored_sha256', '0'*64), ('uncompressed_sha256', '0'*64),
                     ('uncompressed_bytes', len(self.raw)-1), ('stored_bytes', 0)]:
            with self.subTest(k=k), self.assertRaises(ValueError):
                extract_verified(self.root, dict(self.obj, **{k:v}), self.root / k)

    def test_matching_data_does_not_hide_metadata_mismatch(self):
        d, m = self.root / 'd', self.root / 'm'
        d.write_bytes(self.raw)
        m.write_bytes(b'other metadata')
        result = compare_pair(d, m, (self.obj, self.obj))
        self.assertTrue(result['data']['matches'])
        self.assertFalse(result['both_payloads_reproduced'])

    def test_unpinned_code_refused_before_work_creation(self):
        fake = self.root / 'fake.py'
        fake.write_text('raise RuntimeError("must not execute")')
        with self.assertRaisesRegex(ValueError, 'unpinned'):
            reproduce(self.root, fake, self.root / 'work')
        self.assertFalse((self.root / 'work').exists())


if __name__ == '__main__':
    unittest.main()
