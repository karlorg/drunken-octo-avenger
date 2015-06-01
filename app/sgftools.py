from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import re

class ParseError(Exception):
    pass


class SgfTree(object):
    # at the moment just a wrapper around 'nodes', a list of
    # dictionaries representing SGF tags.  This wrapper exists in case
    # we want to add sub-trees, navigation methods etc. later, in
    # which case I suggest following the general shape of the objects
    # used by the Javascript library at
    # https://github.com/neagle/smartgame

    def __init__(self, nodes=None):
        if nodes is None:
            nodes = []
        self.nodes = nodes

    def main_line(self):
        """Return a list of nodes on the main branch of the game."""
        return self.nodes


def generate(sgf_tree):
    sgf = '('
    for node in sgf_tree.nodes:
        sgf += ';'
        for tag, values in node.items():
            if not values:
                continue
            sgf += tag
            for value in values:
                sgf += '[' + value + ']'
    sgf += ')'
    return sgf

def parse(sgf):

    d = {}
    d['rest'] = sgf

    def accept(char):
        return accept_re('\\' + char)

    def accept_re(pattern):
        """If pattern matches at current point in input, advance and return.

        If the pattern contains a group, return the content of the
        group.  Otherwise, return the entire match.

        Either way, advance the current point over the entire match.

        If pattern does not match, do nothing and return None.
        """
        regexp = re.compile(pattern)
        match = regexp.match(d['rest'])
        if match:
            whole = match.group()
            groups = match.groups()
            if len(groups) > 0:
                result = groups[0]
            else:
                result = whole
            d['rest'] = d['rest'][len(whole):]
            return result
        else:
            return None

    def expect(char):
        if not accept(char):
            raise ParseError()

    def sequence():
        expect('(')
        nodes_ = nodes()
        expect(')')
        return SgfTree(nodes_)

    def nodes():
        result = []
        while accept(';'):
            result.append(node_body())
        return result

    def node_body():
        result = {}
        while True:
            tag = accept_re(r"[A-Z]+")
            if not tag:
                break
            values = tag_values()
            result[tag] = values
        return result

    def tag_values():
        result = []
        while True:
            value = accept_re(r"\[([^]]*)\]")
            if not value:
                break
            result.append(value)
        return result

    return sequence()

_ord_a = ord('a')

def encode_coord(x, y):
    return "{}{}".format(chr(x + _ord_a), chr(y + _ord_a))

def decode_coord(chars):
    try:
        x = ord(chars[0]) - _ord_a
        y = ord(chars[1]) - _ord_a
    except IndexError:
        raise ValueError("not enough digits in encoded coord: '{}'".format(
            chars))
    return x, y
