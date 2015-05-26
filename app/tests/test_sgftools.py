from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from ..sgftools import (
    ParseError, SgfTree, parse
)


class TestParse(unittest.TestCase):

    def test_empty_string(self):
        with self.assertRaises(ParseError):
            parse('')

    def test_empty_sequence(self):
        actual = parse('()')
        expected = SgfTree([])
        self.assertEqual(actual.nodes, expected.nodes)

    def test_empty_node(self):
        actual = parse('(;)')
        expected = SgfTree([{}])
        self.assertEqual(actual.nodes, expected.nodes)

    def test_single_pass(self):
        actual = parse('(;B[])')
        expected = SgfTree([{'B': []}])
        self.assertEqual(actual.nodes, expected.nodes)

    def test_single_move(self):
        actual = parse('(;B[ab])')
        expected = SgfTree([{'B': ['ab']}])
        self.assertEqual(actual.nodes, expected.nodes)

    def test_complex(self):
        actual = parse('(;FF[4]SZ[19];B[ab];W[cc]C[hello world!])')
        expected = SgfTree([
            {'FF': ['4'], 'SZ': ['19']},
            {'B': ['ab']},
            {'W': ['cc'], 'C': ['hello world!']}])
        self.assertEqual(actual.nodes, expected.nodes)
