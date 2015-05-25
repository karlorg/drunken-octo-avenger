from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)


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

_ord_a = ord('a')

def encode_coord(x, y):
    return "{}{}".format(chr(x + _ord_a), chr(y + _ord_a))
