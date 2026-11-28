import unittest
from research.mtdp.king_origin_reconstruction import add_owner


class ReconstructionOwnershipTests(unittest.TestCase):
    def test_same_identifier_in_distinct_roles_is_not_merged(self):
        positions={}
        add_owner(positions,'F','historical_quarantines','game',[1])
        add_owner(positions,'F','fresh_candidate','game',[2])
        self.assertEqual(len(positions['F']),2)
        self.assertEqual(positions['F'][('historical_quarantines','game')],{1})
        self.assertEqual(positions['F'][('fresh_candidate','game')],{2})

    def test_repeated_plies_and_other_owner_remain_explicit(self):
        positions={}
        add_owner(positions,'F','fresh_candidate','g1',[1,3])
        add_owner(positions,'F','fresh_candidate','g1',[3,5])
        add_owner(positions,'F','fresh_candidate','g2',[8])
        self.assertEqual(positions['F'][('fresh_candidate','g1')],{1,3,5})
        self.assertEqual(positions['F'][('fresh_candidate','g2')],{8})


if __name__=='__main__':unittest.main()
