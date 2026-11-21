import unittest

from research.mtdp.decision_equivalence.r2_inventory import summarize


class InventoryTests(unittest.TestCase):
    def test_counts_are_objects_not_positions(self):
        r = summarize([{"Path": "runs/a/x.jsonl", "Size": 3}, {"Path": "historical/b.gz", "Size": 7}])
        self.assertEqual((r["objects"], r["total_bytes"]), (2, 10))
        self.assertEqual(r["top_level_prefix_counts"], {"historical": 1, "runs": 1})
        self.assertIsNone(r["position_count"])
        self.assertFalse(r["corpus_admissible"])

    def test_rejects_unsafe_and_duplicate_entries(self):
        for entries in ([{"Path": "../secret", "Size": 1}],
                        [{"Path": "x", "Size": True}],
                        [{"Path": "x", "Size": -1}],
                        [{"Path": "x", "Size": 1}, {"Path": "x", "Size": 2}]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                summarize(entries)

    def test_rejects_non_array(self):
        with self.assertRaises(ValueError):
            summarize({"Path": "x", "Size": 1})


if __name__ == "__main__":
    unittest.main()
