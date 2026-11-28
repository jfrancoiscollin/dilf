import unittest
from pedagogy.game import Move
from research.mtdp.king_origin_inventory_impact import compare_actions
from research.mtdp.return_capture_oracle import root_key


class ImpactMetricsTests(unittest.TestCase):
    def test_path_only_change_not_root_disagreement(self):
        a=Move((31,22,13),(27,18));b=Move((31,24,13),(18,27))
        m,_=compare_actions([a],[a,b],[root_key(a)])
        self.assertTrue(m['path_sets_changed'])
        self.assertFalse(m['root_sets_changed'])
        self.assertFalse(m['corrected_jass_mismatch'])

    def test_added_action_can_fix_old_mismatch(self):
        a=Move((31,26));b=Move((31,27))
        m,_=compare_actions([a],[a,b],[root_key(a),root_key(b)])
        self.assertTrue(m['legacy_jass_mismatch'])
        self.assertFalse(m['corrected_jass_mismatch'])
        self.assertEqual(m['added_root_count'],1)

    def test_removals_and_new_mismatch_are_not_hidden(self):
        a=Move((31,26));b=Move((31,27))
        m,w=compare_actions([a,b],[a],[root_key(a),root_key(b)])
        self.assertTrue(m['newly_introduced_jass_mismatch'])
        self.assertEqual(m['removed_root_count'],1)
        self.assertEqual(w['removed_roots'],[root_key(b)])

    def test_reference_duplicates_reported_separately(self):
        a=Move((31,26))
        m,_=compare_actions([a],[a],[root_key(a),root_key(a)])
        self.assertTrue(m['jass_duplicate_root_keys'])
        self.assertFalse(m['corrected_jass_mismatch'])


if __name__=='__main__':unittest.main()
