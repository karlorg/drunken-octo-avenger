import unittest

from .. import go
from ..go import (_Board, Color, _Coord, _GameNode, ValidationException,
                  check_continuation, ends_by_agreement,
                  is_sgf_passed_twice, next_color, next_move_no)
from app import sgftools

empty = Color.empty
white = Color.white
black = Color.black


class TestIsSgfPassedTwice(unittest.TestCase):

    def test_various_cases(self):
        expected = [("(;)", False),
                    ("(;B[])", False),
                    ("(;B[ab];W[])", False),
                    ("(;B[];W[])", True),
                    ("(;B[ab];W[];B[])", True),
                    ("(;B[ab];W[];B[];W[bc])", False),
                    ("(;SZ[2];B[ab];W[];B[];TB[aa][ba][bb])", True),
                    ("(;B[ab];W[];B[];TCRESUME[])", False)]
        for sgf, value in expected:
            self.assertEqual(is_sgf_passed_twice(sgf), value,
                             "{sgf} should be {value}".format(sgf=sgf,
                                                              value=value))

class TestCheckContinuation(unittest.TestCase):

    def test_various_cases_one_move_allowed(self):

        # each tuple is a test case:
        # (old sgf, new sgf, (expected exception abbrev or True, move no))
        e = [("(;)", "(;)", ('ve', 0)),
             ("(;)", "(;B[ba])", (True,)),
             ("(;B[ba])", "(;B[ba])", ('ve', 1)),
             ("(;B[ba])", "(;B[ba];W[])", (True,)),
             ("(;B[ba])", "(;B[ba];W[];B[])", ('ve', 2)),
             ("(;B[ba])", "(;B[ba];W[bc])", (True,)),
             ("(;B[ab])", "(;B[ba];W[bc])", ('ve', 0)),
             ("(;B[bc])", "(;B[bc];W[bc])", ('ve', 1)),
             ("(;AW[ba])", "(;AW[ba]B[bc])", (True,)),
             ("(;)", "(;RE[W+Resign])", (True,)),
             ("(;B[ba])", "(;RE[B+Resign]B[ba])", (True,)),
             ("(;B[ba])", "(;RE[0]B[ba])", ('ve', 1)),
             ("(;)", "(;FF[4];B[ba])", (True,)),
             ("(;FF[4])", "(;B[ba])", (True,)),
             ("(;SZ[19]FF[4];AW[ba])", "(;AW[ba]B[bc])", (True,))]

        def should_msg(expected):
            if expected[0] is True:
                return "should be OK"
            elif expected[0] == 've':
                return "should fail at move {m}".format(m=expected[1])
            else:
                assert False, "bad expected result type"

        for old_sgf, new_sgf, expected in e:
            try:
                result = check_continuation(old_sgf, new_sgf,
                                            allowed_new_moves=1)
            except ValidationException as ex:
                msg = ("{o} -> {n} failed with message '{msg}' at move {m}, " +
                       should_msg(expected)).format(
                           o=old_sgf, n=new_sgf, m=ex.move_no, msg=str(ex))
                self.assertEqual(expected[0], 've', msg)
                self.assertEqual(expected[1], ex.move_no, msg)
            else:
                if result is not True:
                    self.fail("{o} -> {n} did not raise nor return True")
                    return
                msg = ("{o} -> {n} was OK, " +
                       should_msg(expected)).format(o=old_sgf, n=new_sgf)
                self.assertIs(expected[0], True, msg)

class TestEndsByAgreement(unittest.TestCase):

    def test_various_cases(self):
        e = [("(;)", False),
             ("(;SZ[2];B[aa];W[];B[])", False),
             ("(;SZ[2];B[aa];W[];B[];TB[ab][ba][bb])", False),
             ("(;SZ[2];B[aa];W[];B[];TB[ab][ba][bb];TB[ab][ba][bb])", True),
             ("(;SZ[2];B[aa];W[];B[];TB[ab][ba][bb];TW[aa][ab][ba][bb])",
              False),
             ]
        for sgf, result in e:
            actual = ends_by_agreement(sgf)
            msg = "ends_by_agreement('{sgf}') was {a}, should be {e}".format(
                sgf=sgf, a=actual, e=result)
            self.assertEqual(actual, result, msg)


class TestNextMoveNo(unittest.TestCase):

    def test_various_cases(self):
        e = [("(;)", 0),
             ("(;B[ab])", 1),
             ("(;AB[ab])", 0),
             ("(;SZ[2];B[ab];W[];B[])", 3),
             ("(;SZ[2];B[ab];W[];B[];TB[aa][ba][bb])", 4),
             ("(;SZ[2];B[ab];W[];B[];TCRESUME[])", 4)]
        for sgf, no in e:
            actual = next_move_no(sgf)
            msg = "next_move_no('{sgf}') was {a}, should be {e}".format(
                sgf=sgf, a=actual, e=no)
            self.assertEqual(actual, no, msg)

class TestNextColor(unittest.TestCase):

    def test_various_cases(self):
        e = [("(;)", black),
             ("(;B[ab])", white),
             ("(;B[ab];W[bc])", black),
             ("(;AB[ab])", black),
             ("(;AB[ab]B[bc])", white),
             ("(;SZ[2];B[ab];W[];B[])", white),
             ("(;SZ[2];B[ab];W[];B[];TB[aa][ba][bb])", black),
             ("(;SZ[2];B[ab];W[];B[];TCRESUME[])", white),
             ("(;SZ[2];B[ab];W[];B[];TCRESUME[];W[bb])", black),
             ("(;SZ[2];B[ab];W[];B[];TB[aa][ba][bb];TCRESUME[])", white),
             ("(;SZ[2];B[];W[];TCRESUME[])", black),
             ("(;SZ[2];B[];W[];TB[aa][ab][ba][bb];TCRESUME[])", black)]
        for sgf, no in e:
            actual = next_color(sgf)
            msg = "next_color('{sgf}') was {a}, should be {e}".format(
                sgf=sgf, a=actual, e=no)
            self.assertEqual(actual, no, msg)


class TestScoring(unittest.TestCase):
    # TODO: So I really want to test that the scoring I have added into 'go.py'
    # is correct. In particular, it should count dead stones correctly.
    # wb.
    # .bw
    # .bw
    def test_scoring(self):
        sgf = ("(;SZ[3];B[ba];W[aa];B[bb];W[cb];B[bc];W[cc];"
               "TB[aa][ab][ac][ca][cb][cc];"
               "TB[aa][ab][ac][ca][cb][cc])")
        black_score, white_score = go.get_finished_game_scores(sgf)
        self.assertEqual(black_score, 9)
        self.assertEqual(white_score, 0)

# test helper Board facilities

def board_from_strings(rows):
    """Convenience function for setting up positions easily"""
    board = _Board(len(rows[0]))
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char == 'b':
                board[_Coord(c, r)] = black
            elif char == 'w':
                board[_Coord(c, r)] = white
    return board

class TestUpdateBoardWithMove(unittest.TestCase):

    def test_place_stone(self):
        board = board_from_strings(['..', '..'])
        board.update_with_move(0, 0, black, move_no=0)
        self.assertEqual(board[_Coord(0, 0)], black)

    def test_single_stone_capture(self):
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        board.update_with_move(2, 1, black, move_no=0)
        self.assertEqual(board[_Coord(1, 1)], empty)

    def test_regression_single_capture_with_non_identity(self):
        # check for case where color of stone to be captured is equal to, but
        # not identical to (`==`, not `is`), the enemy color
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        board[_Coord(1, 1)] = int(Color.white)
        board.update_with_move(2, 1, black, move_no=0)
        self.assertEqual(board[_Coord(1, 1)], empty)

    def test_group_capture(self):
        board = board_from_strings(['.bb.',
                                    'bwwb',
                                    '.b..'])
        board.update_with_move(2, 2, black, move_no=0)
        self.assertEqual(board[_Coord(1, 1)], empty)
        self.assertEqual(board[_Coord(x=2, y=1)], empty)

    def test_group_capture_with_self_capture(self):
        # to avoid false passes depending on the order in which neighbours are
        # inspected for captures, do this twice rotated 180 degrees
        board = board_from_strings(['.bb..',
                                    'bwwb.',
                                    'b.wb.',
                                    'wbbw.',
                                    '.ww..'])
        board.update_with_move(1, 2, white, move_no=0)
        self.assertEqual(board[_Coord(x=1, y=1)], white)
        self.assertEqual(board[_Coord(x=2, y=2)], white)
        self.assertEqual(board[_Coord(x=1, y=3)], empty)
        self.assertEqual(board[_Coord(x=2, y=3)], empty)

        board = board_from_strings(['.ww..',
                                    'wbbw.',
                                    'bw.b.',
                                    'bwwb.',
                                    '.bb..'])
        board.update_with_move(2, 2, white, move_no=0)
        self.assertEqual(board[_Coord(x=1, y=2)], white)
        self.assertEqual(board[_Coord(x=2, y=3)], white)
        self.assertEqual(board[_Coord(x=1, y=1)], empty)
        self.assertEqual(board[_Coord(x=2, y=1)], empty)

    def test_exception_on_simple_illegal_move(self):
        board = board_from_strings(['..', '.b'])
        with self.assertRaises(ValidationException) as cm:
            board.update_with_move(1, 1, black, move_no=1)
        e = cm.exception
        self.assertEqual(e.move_no, 1)

    def test_playing_into_no_liberties_is_illegal(self):
        board = board_from_strings(['.w.',
                                    'w.w',
                                    '.w.'])
        with self.assertRaises(ValidationException) as cm:
            board.update_with_move(1, 1, black, move_no=1)
        e = cm.exception
        self.assertEqual(e.move_no, 1)
        # also, the board should not have changed
        self.assertEqual(board[_Coord(1, 1)], empty)

class TestCountLiberties(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(go.EmptyPointLibertiesException):
            board._count_liberties(_Coord(0, 0))

    def test_groups_share_liberties(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board._count_liberties(_Coord(0, 1))
        self.assertEqual(top_left, 2)
        middle_white = board._count_liberties(_Coord(1, 1))
        self.assertEqual(middle_white, 3)

class TestGetGroup(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(go.EmptyPointGroupException):
            board.get_group(_Coord(0, 0))

    def test_identifies_sample_groups(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board.get_group(_Coord(1, 0))
        self.assertEqual(top_left, set([_Coord(0, 0),
                                        _Coord(1, 0),
                                        _Coord(0, 1)]))
        middle_white = board.get_group(_Coord(1, 1))
        self.assertEqual(middle_white, set([_Coord(1, 1), _Coord(x=2, y=1)]))
        bottom_black = board.get_group(_Coord(x=1, y=2))
        self.assertEqual(bottom_black, set([_Coord(x=1, y=2)]))

# test Game Tree/Node helper classes

class TestGameNode(unittest.TestCase):

    @staticmethod
    def node_from_sgf(sgf):
        return _GameNode.from_sgf_node(sgftools.parse(sgf).main_line[0])

    def test_instance_equality(self):
        e = [("(;B[])", "(;B[])", True),
             ("(;B[])", "(;W[])", False),
             ("(;B[ba])", "(;B[ab])", False)]
        for s1, s2, result in e:
            n1 = self.node_from_sgf(s1)
            n2 = self.node_from_sgf(s2)
            self.assertEqual(n1 == n2, result,
                             "{s1} == {s2} should be {result}".format(
                                 s1=s1, s2=s2, result=result))
