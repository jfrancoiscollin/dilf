import unittest
from research.mtdp.fresh_membership_evidence import verify_page


class MembershipTests(unittest.TestCase):
    def setUp(self):
        self.page = (b'<meta property="og:url" content="https://lidraughts.org/abcd1234">'
                     b'<section class="game__tournament-link"><a href="/tournament/uDIrrl1c">Arena</a></section>')

    def test_scoped_identity(self):
        self.assertEqual(verify_page(self.page, 'abcd1234')['event_id'], 'uDIrrl1c')

    def test_unrelated_tournament_link_is_insufficient(self):
        with self.assertRaises(ValueError):
            verify_page(self.page.replace(b'game__tournament-link', b'navigation'), 'abcd1234')

    def test_other_game_cannot_supply_membership(self):
        with self.assertRaises(ValueError):
            verify_page(self.page, 'efgh5678')

    def test_conflicting_event_rejected(self):
        with self.assertRaises(ValueError):
            verify_page(self.page.replace(b'uDIrrl1c', b'fFgE7oED'), 'abcd1234')

    def test_duplicate_identities_rejected(self):
        with self.assertRaises(ValueError):
            verify_page(self.page + self.page, 'abcd1234')

    def test_script_text_is_not_membership(self):
        with self.assertRaises(ValueError):
            verify_page(b'<script>' + self.page + b'</script>', 'abcd1234')


if __name__ == '__main__':
    unittest.main()
