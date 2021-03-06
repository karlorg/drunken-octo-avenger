from collections import namedtuple
import enum

from app import sgftools

class Color(enum.IntEnum):
    empty = 0
    black = 1
    white = 2

class ValidationException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no

def is_sgf_passed_twice(sgf):
    """True if this game has been passed twice and not resumed."""
    passes = 0
    for node in reversed(_GameTree.from_sgf(sgf).main_line):
        if node.is_pass:
            passes += 1
            if passes == 2:
                return True
        elif node.is_move or node.is_resumption:
            return False
    return False

def check_continuation(old_sgf, new_sgf, allowed_new_moves=1):
    """True if new_sgf is a valid continuation of old_sgf.

    If not True, raises a ValidationException with details.

    Only one new move is expected.  (In the future we may support
    setting allowed_new_moves to a different number, or None to remove
    this restriction.)
    """
    assert allowed_new_moves == 1, "(allowed_new_moves != 1) not implemented"
    new_is_valid = _is_valid(new_sgf)
    new_continues_old = _is_continuation(old_sgf, new_sgf)
    return new_is_valid and new_continues_old

def _is_valid(sgf):
    _Board(sgf=sgf)
    # if none of those updates raised, it's a valid sequence
    return True

def _is_continuation(old_sgf, new_sgf):
    old_nodes = _GameTree.from_sgf(old_sgf).main_line
    new_nodes = _GameTree.from_sgf(new_sgf).main_line
    if len(old_nodes) == len(new_nodes):
        if _is_valid_resignation(old_sgf, new_sgf):
            return True
        else:
            raise ValidationException("no new node",
                                      move_no=len(new_nodes))
    if len(old_nodes) > len(new_nodes):
        raise ValidationException("no new node",
                                  move_no=len(new_nodes))
    if len(new_nodes) - len(old_nodes) > 1:
        raise ValidationException("too many new moves",
                                  move_no=len(old_nodes) + 1)
    if old_nodes != new_nodes[:-1]:
        raise ValidationException("games don't match",
                                  move_no=0)
    return True

def _is_valid_resignation(old_sgf, new_sgf):
    old_game = _GameTree.from_sgf(old_sgf)
    new_game = _GameTree.from_sgf(new_sgf)
    if old_game.winner is not None:
        return False
    if new_game.winner is None:
        return False
    return True

def check_resignation(old_sgf, new_sgf):
    """Given a valid continuation, is the game being resigned?

    We're assuming that check_continuation has already been tried and
    has raised no exception.
    """
    return _is_valid_resignation(old_sgf, new_sgf)


def agreed_marking(sgf):
    """Returns the final agreed proposal if an sgf ends in two identical
    proposals and None otherwise."""
    try:
        reversed_nodes = reversed(_GameTree.from_sgf(sgf).main_line)
        last_node = next(reversed_nodes)
        penultimate_node = next(reversed_nodes)
        if ((last_node.is_mark and penultimate_node.is_mark) and
            (last_node.black_coords == penultimate_node.black_coords) and
            (last_node.white_coords == penultimate_node.white_coords)):
                return last_node
        return None
    except StopIteration:
        return None


def ends_by_agreement(sgf):
    """True if sgf ends with two identical territory proposals."""
    return agreed_marking(sgf) is not None


class GameResult(enum.Enum):
    white_by_resign = "WBR"
    white_by_count = "WBC"
    black_by_resign = "BBR"
    black_by_count = "BBC"
    draw = "D"
    not_finished = ""

class GameNotFinishedException(Exception):
    pass

def get_finished_game_scores(sgf):
    marking = agreed_marking(sgf)
    if not marking:
        raise GameNotFinishedException()
    board = _Board(sgf=sgf)
    return board.scores(marking)


def get_game_result(sgf):
    game = _GameTree.from_sgf(sgf)
    if game.winner is not None:
        return {Color.black: GameResult.black_by_resign,
                Color.white: GameResult.white_by_resign}[game.winner]
    try:
        black_score, white_score = get_finished_game_scores(sgf)
    except GameNotFinishedException:
        return GameResult.not_finished
    if black_score > white_score:
        return GameResult.black_by_count
    elif white_score > black_score:
        return GameResult.white_by_count
    else:
        return GameResult.draw



def next_color(sgf):
    """Return the color that is next to move in sgf."""

    def opponent(color):
        return {Color.black: Color.white,
                Color.white: Color.black}[color]

    nodes = _GameTree.from_sgf(sgf).main_line
    next_ = Color.black
    for index, node in enumerate(nodes):
        if node.is_move or node.is_pass or node.is_mark:
            next_ = opponent(next_)
        elif node.is_resumption:
            last_pass = None
            for node in reversed(nodes[:index-1]):
                if node.is_move:
                    break
                elif node.is_pass:
                    last_pass = node.color
            if not last_pass:
                raise ValidationException(
                    "resumption without preceding passes", move_no=index)
            next_ = last_pass
    return next_

def next_move_no(sgf):
    """Return the number of the next move to be played on sgf."""
    game_tree = _GameTree.from_sgf(sgf)
    return sum(1 for node in game_tree.main_line if _is_action(node))

def _is_action(node):
    """Should the node advance the move count?"""
    return (node.is_move or node.is_pass or node.is_mark
            or node.is_resumption)

# helper facilities for playing out a simulated game on a board and checking
# legality

_Coord = namedtuple("Coord", ["x", "y"])

class _Board(object):
    """Emulates a dict mapping `_Coord`s to `Color`s."""

    def __init__(self, size=19, sgf=None):
        self._points = {_Coord(x, y): Color.empty
                        for x in range(size)
                        for y in range(size)}
        self.prisoner_points = {Color.black: 0, Color.white: 0}
        if sgf:
            nodes = _GameTree.from_sgf(sgf).main_line
            self.update_with_nodes(nodes, starting_move_no=0)

    def __getitem__(self, coord):
        return self._points[coord]

    def __setitem__(self, coord, color):
        self._points[coord] = color

    def __iter__(self):
        return self._points.__iter__()

    def items(self):
        return self._points.items()

    def scores(self, marking_node):
        black_points = sum(2 if self._points[coord] == Color.white else 1
                           for coord in marking_node.black_coords)
        white_points = sum(2 if self._points[coord] == Color.black else 1
                           for coord in marking_node.white_coords)
        black_score = black_points + self.prisoner_points[Color.black]
        white_score = white_points + self.prisoner_points[Color.white]
        return (black_score, white_score)


    def update_with_nodes(self, nodes, starting_move_no=0):
        move_no = starting_move_no
        for node in nodes:
            if node.is_setup:
                for coord in node.black_coords:
                    self[coord] = Color.black
                for coord in node.white_coords:
                    self[coord] = Color.white
            elif node.is_move:
                self.update_with_move(node.coord.x, node.coord.y,
                                      node.color, move_no)
                move_no += 1

    def update_with_move(self, x, y, color, move_no):
        """Update board to the state it should be in after the move is played.

        Modifies self.
        """
        coord = _Coord(x,y)
        try:
            enemy = {Color.white: Color.black,
                     Color.black: Color.white}.get(color)
        except:  # pragma: no cover
            assert False, "attempted board update with invalid color"

        if self[coord] == Color.empty:
            self[coord] = color
        else:
            raise ValidationException("point already occupied", move_no)

        # Note, this already updates the board with the captures, hence assuming
        # that this point is valid, so we must first check that the move is
        # valid before calling this. However, we cannot check if a player is
        # playing into a place with zero liberties until we removes the
        # captures. Nicely, a move will not be valid for that reason if it makes
        # any captures, and if it does not, then `process_captures` won't make
        # any updates to the board that we would need to undo.
        def process_captures(coord0):
            for n_coord in self._get_neighbours(coord0):
                if self[n_coord] == enemy:
                    if self._count_liberties(n_coord) == 0:
                        for p in self.get_group(n_coord):
                            self.prisoner_points[color] += 1
                            self[p] = Color.empty

        process_captures(coord)

        if self._count_liberties(coord) == 0:
            # thankfully, if we still have no liberties then no captures have
            # occurred, so we can revert the board position simply by removing
            # the stone we just played
            self[coord] = Color.empty
            raise ValidationException("playing into no liberties", move_no)

    def get_group(self, coord, include=None):
        """Return the group of the stone at coord as an iterable of coords.

        Pure function.
        """
        if include is None:
            include = [self[coord]]
            if include[0] is Color.empty:
                raise EmptyPointGroupException

        def get_group_recursive(coord, group_so_far):
            # group_so_far is a set
            group_so_far |= set([coord])
            neighbours_to_recurse = (
                n for n in self._get_neighbours(coord)
                if self[n] in include and n not in group_so_far)
            for n_coord in neighbours_to_recurse:
                group_so_far |= get_group_recursive(n_coord, group_so_far)
            return group_so_far

        return get_group_recursive(coord, set())

    def _get_neighbours(self, coord):
        """Return the neighbouring points of coord as an iterable of coords.

        Pure function.
        """
        x = coord.x
        y = coord.y
        return (_Coord(x=x0, y=y0)
                for x0, y0 in ((x, y-1), (x+1, y), (x, y+1), (x-1, y))
                if _Coord(x=x0, y=y0) in self)

    def _count_liberties(self, coord):
        """Count the liberties of the group containing the stone (r,c).

        Pure function.
        """
        if self[coord] is Color.empty:
            raise EmptyPointLibertiesException
        liberties = set()
        for g_coord in self.get_group(coord):
            liberties |= set(n for n in self._get_neighbours(g_coord)
                             if self[n] == Color.empty)
        return len(liberties)


class EmptyPointGroupException(Exception):
    pass

class EmptyPointLibertiesException(Exception):
    pass

# GameTree abstraction of a parsed game

class _GameTree(object):
    """An abstract representation of a game history.

    Use `.main_line` to obtain a list of _GameNodes.  A node is either
    a move, a pass, or setup stones.
    """

    def __init__(self, sgf_tree):
        """Don't call directly please, may change.

        Use classmethod instantiators instead.
        """
        self.main_line = self._nodes_from_sgf_nodes(sgf_tree.main_line)
        self.winner = self._winner_from_sgf_nodes(sgf_tree.main_line)

    @classmethod
    def from_sgf(cls, sgf):
        sgf_tree = sgftools.parse(sgf)
        return cls(sgf_tree)

    @classmethod
    def from_sgf_tree(cls, sgf_tree):
        return cls(sgf_tree)

    @staticmethod
    def _nodes_from_sgf_nodes(sgf_nodes):
        result = []
        for node in sgf_nodes:
            result.extend(_GameNode.from_sgf_node(node))
        return result

    @staticmethod
    def _winner_from_sgf_nodes(sgf_nodes):
        for node in sgf_nodes:
            winner = _winner_from_sgf_node(node)
            if winner is not None:
                return winner
        return None

    def winner(self):
        return self._winner

def _winner_from_sgf_node(sgf_node):
    if 'RE' not in sgf_node:
        return None
    letter = sgf_node['RE'][0][0]
    return {'B': Color.black, 'W': Color.white}.get(letter, None)

class _GameNode(object):
    """Represents a node in a game tree.

    Unlike SGF nodes, these nodes never mix setup stones with actions.
    Each set of setup stones gets a node to itself.
    """

    def __init__(self):
        """Not for use by client code"""
        self.is_move = False
        """Does this node represent a stone played at a coordinate?"""
        self.is_pass = False
        """Does this node represent a pass?"""
        self.is_setup = False
        """Does this node place setup stones outside the game rules?"""
        self.is_mark = False
        """Does this node represent one player marking dead stones?"""
        self.is_resumption = False
        """Does this node represent a player resuming a finished game?"""

    @classmethod
    def from_sgf_node(cls, sgf_node):
        """Return a list of nodes built from the given SGF node.

        If one SGF node is broken into several GameNodes, the order
        will be correct so that earlier nodes 'occur' before later
        ones in the game.
        """
        nodes = []
        if 'AB' in sgf_node or 'AW' in sgf_node:
            nodes.append(cls._make_setup(sgf_node))
        if 'TCRESUME' in sgf_node:
            nodes.append(_ResumptionNode())
        if 'B' in sgf_node:
            nodes.append(cls._make_move_or_pass(Color.black, sgf_node['B']))
        elif 'W' in sgf_node:
            nodes.append(cls._make_move_or_pass(Color.white, sgf_node['W']))
        if 'TB' in sgf_node or 'TW' in sgf_node:
            nodes.append(cls._make_mark(sgf_node))
        return nodes

    @classmethod
    def _make_move_or_pass(cls, color, tag_value):
        coord = cls._decode_or_none(tag_value[0])
        if coord:
            return _MoveNode(color, coord)
        else:
            return _PassNode(color)

    @classmethod
    def _make_setup(cls, sgf_node):
        black_coords = set(cls._decode(chars)
                           for chars in sgf_node.get('AB', []))
        white_coords = set(cls._decode(chars)
                           for chars in sgf_node.get('AW', []))
        return _SetupNode(black_coords, white_coords)

    @classmethod
    def _make_mark(cls, sgf_node):
        black_coord = set(cls._decode(chars)
                          for chars in sgf_node.get('TB', []))
        white_coord = set(cls._decode(chars)
                          for chars in sgf_node.get('TW', []))
        return _MarkNode(black_coord, white_coord)

    @classmethod
    def _decode_or_none(cls, chars):
        try:
            return cls._decode(chars)
        except ValueError:
            return None

    @staticmethod
    def _decode(chars):
        x, y = sgftools.decode_coord(chars)
        return _Coord(x=x, y=y)


class _MoveNode(_GameNode):

    def __init__(self, color, coord):
        super(_MoveNode, self).__init__()
        self.is_move = True
        self.coord = coord
        """The coordinate played at."""
        self.color = color
        """The color of the stone being placed."""

    def __eq__(self, other):
        return (other.is_move
                and self.color == other.color
                and self.coord == other.coord)

    def __repr__(self):
        return "Move node: {col} ({x},{y})".format(
            col={Color.black: "Black", Color.white: "White"}[self.color],
            x=self.coord.x, y=self.coord.y)


class _PassNode(_GameNode):

    def __init__(self, color):
        super(_PassNode, self).__init__()
        self.is_pass = True
        self.color = color
        """The color of the passing player."""

    def __eq__(self, other):
        return (other.is_pass and self.color == other.color)

    def __repr__(self):
        return "Pass node: {col}".format(
            col={Color.black: "Black", Color.white: "White"}[self.color])


class _SetupNode(_GameNode):

    def __init__(self, black_coords, white_coords):
        """Create a node from two sets of coords.

        :param black_coords: a set of _Coord
        :param white_coords: a set of _Coord
        """
        super(_SetupNode, self).__init__()
        self.is_setup = True
        self.black_coords = black_coords
        """A set of _Coord representing black setup stones."""
        self.white_coords = white_coords
        """A set of _Coord representing white setup stones."""

    def __eq__(self, other):
        return (other.is_setup
                and self.black_coords == other.black_coords
                and self.white_coords == other.white_coords)

    def __repr__(self):
        return ("Setup node:\n"
                " Black: {b}\n"
                " White: {w}".format(b=self.black_coords, w=self.white_coords))


class _MarkNode(_GameNode):

    def __init__(self, black_coords, white_coords):
        """A node that marks territories in a Game tree.

        :param black_coords: a set of _Coord
        :param white_coords: a set of _Coord
        """
        super(_MarkNode, self).__init__()
        self.is_mark = True
        self.black_coords = black_coords
        """A set of _Coord representing black territory."""
        self.white_coords = white_coords
        """A set of _Coord representing white territory."""

    def __eq__(self, other):
        return (other.is_mark
                and self.black_coords == other.black_coords
                and self.white_coords == other.white_coords)

    def __repr__(self):
        return ("Territory marking node:\n"
                " Black: {b}\n"
                " White: {w}".format(b=self.black_coords, w=self.white_coords))


class _ResumptionNode(_GameNode):

    def __init__(self):
        """A node signalling that a finished game should resume."""
        super(_ResumptionNode, self).__init__()
        self.is_resumption = True

    def __eq__(self, other):
        return other.is_resumption

    def __repr__(self):
        return "Resumption node"
