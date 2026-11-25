"""Real immutable receipt fixture and adversarial source-integrity checks."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from research.mtdp import fresh_candidate_integrity_replay as audit

ARCHIVE = Path(__file__).resolve().parents[1] / 'fresh_intake/2026-11-25-uDIrrl1c.zip'


class IntakeIntegrityTests(unittest.TestCase):
    def test_real_receipt_and_double_export_verified(self):
        receipt, row, pdn = audit.verify_archive(ARCHIVE)
        self.assertEqual(row['event'], 'uDIrrl1c')
        self.assertEqual(audit.digest(pdn), row['export_1_sha256'])
        self.assertFalse(receipt['independent_cohort_admitted'])

    def test_changed_outer_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad.zip'
            p.write_bytes(ARCHIVE.read_bytes() + b'X')
            with self.assertRaisesRegex(ValueError, 'ZIP digest'):
                audit.verify_archive(p)

    def test_rehashed_outer_archive_cannot_hide_member_changes(self):
        for member in ['receipt.json', 'listing.json', 'uDIrrl1c-detail.json', 'uDIrrl1c-export-2.pdn']:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / 'bad.zip'
                with zipfile.ZipFile(ARCHIVE) as source, zipfile.ZipFile(p, 'w') as target:
                    for name in source.namelist():
                        b = source.read(name)
                        target.writestr(name, b + b' ' if name == member else b)
                # Repin only the hypothetical outer ZIP to exercise nested evidence checks.
                with patch.object(audit, 'ARCHIVE_SHA', audit.digest(p.read_bytes())):
                    with self.assertRaises(ValueError):
                        audit.verify_archive(p)


if __name__ == '__main__':
    unittest.main()
