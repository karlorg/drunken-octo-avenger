import unittest

from ..sgftools import (
    ParseError, SgfTree, generate, parse
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
        """Special case: SGF requires one node even when empty, should
        parse to no nodes."""
        actual = parse('(;)')
        expected = SgfTree([])
        self.assertEqual(actual.nodes, expected.nodes)

    def test_single_pass(self):
        actual = parse('(;B[])')
        expected = SgfTree([{'B': ['']}])
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


class TestGenerate(unittest.TestCase):

    def test_empty_tree(self):
        """Special case: SGF requires at least one node."""
        actual = generate(SgfTree([]))
        expected = '(;)'
        self.assertEqual(actual, expected)
