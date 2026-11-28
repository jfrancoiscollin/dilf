"""Adversarial parser tests; no claim about historical cohort independence."""
import unittest

from research.mtdp.decision_equivalence.strict_manifest_jsonl import decode_line


class StrictManifestJSONLTests(unittest.TestCase):
    def test_reject_duplicate_split(self):
        with self.assertRaisesRegex(ValueError, "duplicate_json_key:split"):
            decode_line('{"split":"train","split":"test"}')

    def test_reject_nested_duplicate(self):
        with self.assertRaisesRegex(ValueError, "duplicate_json_key:game_id"):
            decode_line('{"metadata":{"game_id":"a","game_id":"b"}}')

    def test_reject_nonfinite(self):
        with self.assertRaisesRegex(ValueError, "nonfinite_json_constant"):
            decode_line('{"x":NaN}')

    def test_accept_unambiguous_manifest(self):
        row = decode_line('{"split":"train","fen":"F","game_id":"G","trajectory_id":"T"}')
        self.assertEqual(row["split"], "train")


if __name__ == "__main__":
    unittest.main()
