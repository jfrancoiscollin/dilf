"""Regression tests for score-blind collision input parsing."""
import json
import unittest
from research.mtdp.decision_equivalence.signature_collision_audit import reject_duplicate_keys


class CollisionJsonIntegrityTests(unittest.TestCase):
    def test_duplicate_top_level_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: game_id"):
            json.loads('{"game_id":"a","game_id":"b"}', object_pairs_hook=reject_duplicate_keys)

    def test_duplicate_nested_signature_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: L"):
            json.loads('{"signatures":{"L":"x","L":"y"}}', object_pairs_hook=reject_duplicate_keys)

    def test_unique_nested_keys_preserved(self):
        obj = json.loads('{"signatures":{"L":"x","LCB":"y"}}', object_pairs_hook=reject_duplicate_keys)
        self.assertEqual(obj["signatures"], {"L": "x", "LCB": "y"})


if __name__ == "__main__":
    unittest.main()
