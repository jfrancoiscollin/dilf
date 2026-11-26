from pathlib import Path
import tempfile
import unittest
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.historical_base_quarantine_frontier import bind_sources


class RawBindingTests(unittest.TestCase):
    def test_binding_uses_exact_bytes_not_plausible_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'expected.pdn').write_bytes(b'wrong')
            (root/'repeat.pdn').write_bytes(b'correct')
            result=bind_sources(root,[{'file':'expected.pdn','sha256':digest(b'correct')}])
            self.assertEqual(result['expected.pdn'].read_bytes(),b'correct')

    def test_wrong_raw_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'expected.pdn').write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'missing exact raw source'):
                bind_sources(tmp,[{'file':'expected.pdn','sha256':digest(b'correct')}])

    def test_duplicate_declared_source_identity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'a.pdn').write_bytes(b'correct')
            row={'file':'a.pdn','sha256':digest(b'correct')}
            with self.assertRaisesRegex(ValueError,'duplicate declared'):
                bind_sources(tmp,[row,row])

    def test_repository_archive_fallback_keeps_exact_source_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            artifact=root/'artifact'; artifact.mkdir()
            repository=root/'repository'; repository.mkdir()
            (repository/'first.pdn').write_bytes(b'original')
            result=bind_sources(artifact,[{'file':'P1.pdn','sha256':digest(b'original')}],repository)
            self.assertEqual(result['P1.pdn'].read_bytes(),b'original')


if __name__=='__main__':
    unittest.main()
