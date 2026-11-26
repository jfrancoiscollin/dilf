import unittest
from research.mtdp.return_capture_oracle import decode_key,parse_catalogues


class CatalogueTests(unittest.TestCase):
    def test_self_return_capture_is_not_quiet_move(self):
        self.assertEqual(decode_key('48x48x20x39'),'48x48')
        self.assertEqual(decode_key('3-8'),'3-8')

    def test_untrusted_field_and_square_rejected(self):
        for key in ['48x48','0-8','3-51','3-8x9','garbage']:
            with self.subTest(key=key),self.assertRaises(ValueError):
                decode_key(key)

    def test_position_identity_and_promotion_checked(self):
        fen='W:W31:B1'
        self.assertEqual(parse_catalogues(fen+'\t31-26=0\n',[fen]),[[('31-26',False)]])
        for raw in ['B:W31:B1\t31-26=0\n',fen+'\t31-26=2\n','']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                parse_catalogues(raw,[fen])


if __name__=='__main__':
    unittest.main()
