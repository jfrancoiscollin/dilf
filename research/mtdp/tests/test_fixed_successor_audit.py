"""Synthetic failure witnesses and strict transport parsing, no efficacy claims."""
from pathlib import Path
import tempfile
import unittest

from pedagogy.game import Move, parse_fen
from research.mtdp.fixed_successor_audit import parse_successors, compare_case, check_manual, load_fixtures, project_legal_catalogue
from research.mtdp.return_capture_oracle import root_key


class SuccessorOracleTests(unittest.TestCase):
    def setUp(self):
        self.parent = parse_fen('W:W31:B18,27')
        self.a = Move((31, 22, 13), (27, 18))
        self.b = Move((31, 24, 13), (18, 27))
        self.child = parse_fen('B:W13:B')
        self.reference = [(root_key(self.a)[0], False, 'B:W13:B')]

    def test_two_paths_to_same_root_and_board_remain_explicit(self):
        row = compare_case('synthetic', self.parent, [self.a, self.b], lambda s, m: self.child, self.reference)
        self.assertTrue(row['all_roots_and_successors_equal'])
        self.assertEqual(row['python_paths'], 2)
        self.assertEqual(row['python_unique_roots'], 1)
        self.assertEqual(row['multiple_python_paths_same_root'][0]['distinct_successors'], 1)
        self.assertEqual(len(row['python_path_successors']), 2)

    def test_divergent_path_is_not_hidden_by_first_successor(self):
        row = compare_case('synthetic', self.parent, [self.a, self.b],
            lambda s, m: self.child if m == self.a else parse_fen('B:WK13:B'), self.reference)
        self.assertFalse(row['all_roots_and_successors_equal'])
        self.assertEqual(len(row['shared_root_successor_mismatches']), 1)
        self.assertEqual(len(row['python_roots_with_multiple_successors']), 1)

    def test_wrong_turn_is_a_scientific_difference_not_transport_error(self):
        raw = 'W:W31:B18,27\t31x13x18x27=0>W:W13:B\n'
        parsed = parse_successors(raw, ['W:W31:B18,27'])
        row = compare_case('synthetic', self.parent, [self.a], lambda s, m: self.child, parsed[0])
        self.assertEqual(len(row['shared_root_successor_mismatches']), 1)

    def test_duplicate_reference_and_missing_root_are_reported(self):
        duplicate = compare_case('synthetic', self.parent, [self.a], lambda s, m: self.child, self.reference * 2)
        self.assertEqual(duplicate['jass_duplicate_root_keys'], 1)
        self.assertFalse(duplicate['all_roots_and_successors_equal'])
        missing = compare_case('synthetic', self.parent, [self.a], lambda s, m: self.child, [])
        self.assertEqual(len(missing['python_only_roots']), 1)

    def test_reference_same_root_different_boards_remains_a_witness(self):
        reference = self.reference + [(root_key(self.a)[0], False, 'B:WK13:B')]
        row = compare_case('synthetic', self.parent, [self.a], lambda s, m: self.child, reference)
        self.assertEqual(len(row['jass_roots_with_multiple_successors']), 1)
        self.assertEqual(len(row['shared_root_successor_mismatches']), 1)

    def test_missing_rows_wrong_echo_and_malformed_fields_refused(self):
        parent = 'W:W31:B18,27'
        invalid = ['', 'B:W31:B18,27\n', parent + '\t31x13=0>B:W13:B\n',
                   parent + '\t31x13x27x18=0>B:W13:B\n',
                   parent + '\t31x13x18x27=2>B:W13:B\n', parent + '\t31x13x18x27=0>B:W51:B\n']
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_successors(raw, [parent])

    def test_terminal_row_and_legal_projection(self):
        self.assertEqual(parse_successors('W:W:B\n', ['W:W:B']), [[]])
        raw = 'W:W31:B18,27\t31x13x18x27=0>B:W13:B\n'
        self.assertEqual(project_legal_catalogue(raw), 'W:W31:B18,27\t31x13x18x27=0\n')

    def test_manual_promotion_claim_cannot_use_same_board_with_wrong_root_flag(self):
        row = {'root_successors': [{'root': ['6-1', False], 'python_successors': ['B:WK1:B45'], 'jass_successors': ['B:WK1:B45']}]}
        check = {'case': 'synthetic', 'root_key': '6-1', 'promotion': True, 'successor_fen': 'B:WK1:B45'}
        self.assertFalse(check_manual(check, row)['passed'])

    def test_manual_expected_piece_type_cannot_be_silently_changed(self):
        row = compare_case('synthetic', self.parent, [self.a], lambda s, m: self.child, self.reference)
        check = {'case': 'synthetic', 'root_key': root_key(self.a)[0], 'promotion': False, 'successor_fen': 'B:WK13:B'}
        self.assertFalse(check_manual(check, row)['passed'])

    def test_fixture_integrity_before_engines(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'research/mtdp/validation'; p.mkdir(parents=True)
            (p / 'fixed-successor-fixtures-2026-11-26.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'fixtures changed'):
                load_fixtures(tmp)


if __name__ == '__main__':
    unittest.main()
