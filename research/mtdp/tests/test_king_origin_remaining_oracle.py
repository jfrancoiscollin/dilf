"""Frozen scope cannot be changed by caller-provided FEN files or summaries."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.mtdp.king_origin_remaining_oracle import frozen_scope


class FrozenKingScopeTests(unittest.TestCase):
    def test_changed_frozen_scope_rejected_before_cache_or_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'research/mtdp/validation'; p.mkdir(parents=True)
            (p / 'king-origin-remaining-active-king-scope-2026-11-26.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'Frozen active-king scope changed'):
                frozen_scope(tmp, tmp, tmp)

    def test_recomputed_scope_must_equal_frozen_counts_and_selected_hash(self):
        root = Path(__file__).resolve().parents[3]
        p = root / 'research/mtdp/validation/king-origin-remaining-active-king-scope-2026-11-26.json'
        original = json.loads(p.read_bytes())
        forged = {**original, 'remaining_historical_active_king_fens': 1}
        with patch('research.mtdp.king_origin_remaining_oracle.authenticated_scope', return_value=(forged, b'W:WK48:B1\n')):
            with self.assertRaisesRegex(ValueError, 'differs from preregistration'):
                frozen_scope(root, 'unused', 'unused')

    def test_truncated_payload_cannot_enter_even_if_counts_claim_full_scope(self):
        root = Path(__file__).resolve().parents[3]
        p = root / 'research/mtdp/validation/king-origin-remaining-active-king-scope-2026-11-26.json'
        original = json.loads(p.read_bytes())
        with patch('research.mtdp.king_origin_remaining_oracle.authenticated_scope', return_value=(original, b'W:WK48:B1\n')):
            with self.assertRaisesRegex(ValueError, 'differs from preregistration'):
                frozen_scope(root, 'unused', 'unused')


    def test_replaced_full_size_payload_is_rejected_by_its_own_digest(self):
        root = Path(__file__).resolve().parents[3]
        p = root / 'research/mtdp/validation/king-origin-remaining-active-king-scope-2026-11-26.json'
        original = json.loads(p.read_bytes())
        payload = b'X\n' * 48653 + b'X' * (original['selected_fens_bytes'] - 2 * 48653 - 1) + b'\n'
        self.assertEqual(len(payload), original['selected_fens_bytes'])
        self.assertEqual(len(payload.splitlines()), 48654)
        with patch('research.mtdp.king_origin_remaining_oracle.authenticated_scope', return_value=(original, payload)):
            with self.assertRaisesRegex(ValueError, 'differs from preregistration'):
                frozen_scope(root, 'unused', 'unused')


if __name__ == '__main__':
    unittest.main()
