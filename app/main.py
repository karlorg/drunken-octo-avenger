from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
import logging
import time
import multiprocessing

from flask import (
        Flask, abort, flash, redirect, render_template, request,
        session, url_for
)
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import Form
import itertools
import jinja2
import json
import requests
from sqlalchemy import and_, or_
from wtforms import HiddenField, IntegerField, StringField
from wtforms.validators import DataRequired, Email
from wtforms.widgets import HiddenInput

from config import DOMAIN
from app import go_rules


IMG_PATH_EMPTY = '/static/images/goban/e.gif'
IMG_PATH_BLACK = '/static/images/goban/b.gif'
IMG_PATH_WHITE = '/static/images/goban/w.gif'

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.undefined = jinja2.StrictUndefined
if app.debug:
    logging.basicConfig(level=logging.DEBUG)
db = SQLAlchemy(app)


# Views
#
# Since view functions tend to have side-effects and to depend on global state,
# try to keep complexity (if, for...) out of them and move it into pure
# function helpers instead.

@app.route('/')
def front_page():
    if 'email' in session:
        return redirect(url_for('status'))
    return render_template_with_email("frontpage.html")

@app.route('/game/<int:game_no>')
def game(game_no):
    game = Game.query.filter(Game.id == game_no).first()
    if game is None:
        flash("Game #{} not found".format(game_no))
        return redirect('/')
    moves = game.moves
    resumptions = game.resumptions
    passes = game.passes
    is_your_turn = is_players_turn_in_game(game)
    sgf = get_sgf_from_game(game)
    is_passed_twice = check_two_passes(moves, passes, resumptions)
    if not is_passed_twice:
        form = PlayStoneForm(data={'game_no': game.id,
                                   'move_no': game.move_no,
                                   'data': sgf})
    else:
        form = MarkDeadForm(data={'game_no': game.id,
                                  'move_no': game.move_no,
                                  'data': sgf})
    return render_template_with_email(
            "game.html",
            form=form, on_turn=is_your_turn, with_scoring=is_passed_twice)

def get_sgf_from_game(game):
    """Return an SGF representing the given game.

    Reads database.
    """
    rules_board = get_rules_board_from_db_game(game)
    sgf = get_sgf_from_rules_board(rules_board)
    return sgf

def get_rules_board_from_db_game(game):
    """Get board layout resulting from given moves and setup stones.

    Reads database.
    """
    def place_stones_for_move(n):
        for stone in filter(lambda s: s.before_move == n, game.setup_stones):
            board[stone.row, stone.column] = stone.color

    moves = game.moves
    moves_by_no = {m.move_no: m for m in moves}
    max_move_no = max(itertools.chain([-1], (m.move_no for m in moves)))
    board = go_rules.Board()
    for move_no in range(max_move_no+2):
        # max_move_no +1 to include setup stones on move 0 with no move played,
        # +1 again since `range` excludes the stop value
        place_stones_for_move(move_no)
        try:
            board.update_with_move(moves_by_no[move_no])
        except KeyError:
            pass
    return board

def get_sgf_from_rules_board(rules_board):
    """Transform a dict of {(r,c): color} to an sgf.

    Pure function.
    """
    return "(;FF[4]SZ[19])"
#    black = go_rules.Color.black
#    white = go_rules.Color.white
#    empty = go_rules.Color.empty
#
#    color_images = {black: IMG_PATH_BLACK,
#                    white: IMG_PATH_WHITE,
#                    empty: IMG_PATH_EMPTY}
#    color_classes = {black: 'blackstone',
#                     white: 'whitestone',
#                     empty: 'nostone'}
#
#    def create_goban_point(row, column, color):
#        classes_template = 'gopoint row-{row} col-{col} {color_class}'
#        classes = classes_template.format(row=str(row),
#                                          col=str(column),
#                                          color_class=color_classes[color])
#        return dict(img=color_images[color], classes=classes)
#
#    goban = [[create_goban_point(j, i, rules_board[j, i])
#              for i in range(19)]
#             for j in range(19)]
#    return goban


@app.route('/playstone', methods=['POST'])
def playstone():
    return play_general_move("move")

@app.route('/playpass', methods=['POST'])
def playpass():
    return play_general_move("pass")

@app.route('/resumegame', methods=['POST'])
def resumegame():
    return play_general_move("resume")

@app.route('/markdead', methods=['POST'])
def markdead():
    return play_general_move("markdead")

@app.route('/resign', methods=['POST'])
def resign():
    return play_general_move("resign")

def play_general_move(which):
    try:
        email = logged_in_email()
    except NoLoggedInPlayerException:
        return redirect('/')
    arguments = request.form.to_dict()
    try:
        game_no = int(arguments['game_no'])
    except (KeyError, ValueError):
        flash("Invalid game number")
        return redirect('/')
    game = Game.query.filter(Game.id == game_no).first()

    try:
        validate_turn_and_record(which, email, game, arguments)
    except go_rules.IllegalMoveException as e:
        flash("Illegal move received: " + e.args[0])
        return redirect(url_for('game', game_no=game_no))

    return redirect(url_for('status'))

def validate_turn_and_record(which, player, game, arguments):
    if game.to_move() != player:
        raise go_rules.IllegalMoveException("It's not your turn!")
    move_no = get_and_validate_move_no(arguments, game)
    color = game.to_move_color()

    if which == "pass":
        turn_object = Pass(game_no=game.id, move_no=move_no, color=color)
    elif which == "move":
        turn_object = create_and_validate_move(move_no, color, game, arguments)
    elif which == "markdead":
        record_dead_stones_from_json_and_check_end(game, arguments)
        turn_object = Pass(game_no=game.id, move_no=move_no, color=color)
    elif which == "resume":
        for dead_stone in game.dead_stones:
            db.session.delete(dead_stone)
        db.session.commit()
        if game.first_to_pass() == color:
            # the current player should be the next to play after resumption;
            # insert a padding Pass entry to make it so
            db.session.add(Pass(game_no=game.id, move_no=move_no, color=color))
            move_no += 1
            color = {Move.Color.black: Move.Color.white,
                     Move.Color.white: Move.Color.black}[color]
        turn_object = Resumption(game_no=game.id, move_no=move_no, color=color)
    elif which == "resign":
        game.winner = {Move.Color.black: game.white,
                       Move.Color.white: game.black}[color]
        db.session.commit()
        return
    else:
        assert False, "'{}' is not a valid value for `which`".format(which)

    db.session.add(turn_object)
    db.session.commit()

def get_and_validate_move_no(arguments, game):
    try:
        move_no = int(arguments['move_no'])
    except (KeyError, ValueError):
        raise go_rules.IllegalMoveException("Invalid request received")
    if move_no != game.move_no:
        raise go_rules.IllegalMoveException(
                "Move number supplied not sequential")
    return move_no

def create_and_validate_move(move_no, color, game, arguments):
    try:
        row = int(arguments['row'])
        column = int(arguments['column'])
    except (KeyError, ValueError):
        raise go_rules.IllegalMoveException("Invalid request made.")

    move = Move(game_no=game.id, move_no=move_no,
                row=row, column=column, color=color)

    # test legality, if `board.update_with_move` raises an IllegalMoveException
    # this will be caught above and displayed to the user.
    board = get_rules_board_from_db_game(game)
    board.update_with_move(move)
    # But if no exception is raised then we return the move
    return move

def record_dead_stones_from_json_and_check_end(game, arguments):
    """Get dead stones list from args; check game over; record both."""
    try:
        coords_as_lists = json.loads(arguments['dead_stones'])
        dead_stones = []
        for [column, row] in coords_as_lists:
            dead_stones.append(DeadStone(game.id, row=row, column=column))
    except ValueError as e:
        raise go_rules.IllegalMoveException(
                "Invalid JSON: {}".format(e.args[0]))
    if dead_stones_matches_db(game, dead_stones):
        game.winner = True
    else:
        DeadStone.query.filter(DeadStone.game_no == game.id).delete()
        db.session.commit()
        for dead_stone in dead_stones:
            db.session.add(dead_stone)
        db.session.commit()

def dead_stones_matches_db(game, dead_stones):
    """True if dead stones list matches what's in the db for given game."""
    db_stones = DeadStone.query.filter(DeadStone.game_no == game.id).all()
    if len(db_stones) != len(dead_stones):
        return False
    key_func = lambda ds: (ds.row, ds.column)
    dead_stones_sorted = sorted(dead_stones, key=key_func)
    db_stones_sorted = sorted(db_stones, key=key_func)
    for db_stone, new_stone in zip(db_stones_sorted, dead_stones_sorted):
        if db_stone.row != new_stone.row:
            return False
        if db_stone.column != new_stone.column:
            return False
    return True

@app.route('/challenge', methods=('GET', 'POST'))
def challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        game = Game()
        game.black = form.opponent_email.data
        game.white = logged_in_email()
        db.session.add(game)
        db.session.commit()
        return redirect(url_for('status'))
    return render_template_with_email("challenge.html", form=form)

@app.route('/status')
def status():
    if 'email' not in session:
        return redirect('/')
    your_turn_games, not_your_turn_games = get_status_lists(logged_in_email())
    return render_template_with_email(
            "status.html",
            your_turn_games=your_turn_games,
            not_your_turn_games=not_your_turn_games)

@app.route('/persona/login', methods=['POST'])
def persona_login():
    if 'assertion' not in request.form:
        abort(400)
    data = {
            'assertion': request.form['assertion'],
            'audience': DOMAIN,
    }
    response = requests.post(
            'https://verifier.login.persona.org/verify',
            data=data, verify=True
    )
    session_update = process_persona_response(response)
    if session_update.do:
        # we separate out our internal "who's logged in" email from the one
        # used by Persona so that when the browser automation tests need to
        # create a fake login session, Persona doesn't get confused by a user
        # appearing who it doesn't remember processing.
        session.update({'email': session_update.email})
        session.update({'persona_email': session_update.email})
        # we're only accessed through AJAX, the response doesn't matter
        return ''
    else:
        abort(500)

@app.route('/logout', methods=['POST'])
def logout():
    try:
        del session['email']
    except KeyError:
        pass
    try:
        del session['persona_email']
    except KeyError:
        pass
    return ''

# test-only routes (used in testing to access the server more directly than
# users are normally allowed to), and their helpers.  These should all use the
# `test_only_route` decorator below:

def test_only_route(self, rule, **options):
    """A wrapper for `app.route`, that disables the route outside testing"""
    def decorator(f):
        # we can't just check at compile time whether testing mode is on,
        # because it's not set until after this file is imported (until then,
        # the importing module has no app object to set the testing flag on).
        #
        # Therefore we have to check at the time the wrapped view function is
        # called.
        def guarded_f(*f_args, **f_options):
            if self.config['TESTING']:
                return f(*f_args, **f_options)
            else:
                return ""
        if 'endpoint' not in options:
            options['endpoint'] = f.__name__
        self.route(rule, **options)(guarded_f)
        return guarded_f
    return decorator

Flask.test_only_route = test_only_route

@app.test_only_route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the Werkzeug dev server, if we're using it.

    From http://flask.pocoo.org/snippets/67/"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:  # pragma: no cover
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.test_only_route('/testing_create_login_session', methods=['POST'])
def testing_create_login_session():
    """Log in the given email address."""
    email = request.form['email']
    session.update({'email': email})
    return ''

@app.test_only_route('/testing_create_game', methods=['POST'])
def testing_create_game():
    """Create a custom game in the database directly"""
    black_email = request.form['black_email']
    white_email = request.form['white_email']
    stones = json.loads(request.form['stones'])
    create_game_internal(black_email, white_email, stones)
    return ''

def create_game_internal(black_email, white_email, stones=None):
    game = Game()
    game.black = black_email
    game.white = white_email
    db.session.add(game)
    db.session.commit()
    if stones is not None:
        add_stones_from_text_map_to_game(stones, game)
    return game

@app.test_only_route('/testing_clear_games_for_player', methods=['POST'])
def testing_clear_games_for_player():
    """Clear all of `email`'s games from the database."""
    email = request.form['email']
    clear_games_for_player_internal(email)
    return ''

def clear_games_for_player_internal(email):
    games_as_black = Game.query.filter(Game.black == email).all()
    games_as_white = Game.query.filter(Game.white == email).all()
    games = games_as_black + games_as_white
    for game in games:
        delete_game_from_db(game)

def delete_game_from_db(game):
    for move in game.moves:
        db.session.delete(move)
    for resumption in game.resumptions:
        db.session.delete(resumption)
    for pass_ in game.passes:
        db.session.delete(pass_)
    for setup_stone in game.setup_stones:
        db.session.delete(setup_stone)
    db.session.delete(game)
    db.session.commit()


# helper functions

_SessionUpdate = namedtuple('_SessionUpdate', ['do', 'email'])
def process_persona_response(response):
    """Given an HTTP response from Mozilla, determine who to log in.

    Pure function.
    """
    if not response.ok:
        logging.debug("Response not 'ok' for persona login attempt")
        return _SessionUpdate(do=False, email='')
    verification_data = response.json()
    if (
            'status' not in verification_data or
            verification_data['status'] != 'okay' or
            'email' not in verification_data
    ):
        logging.debug("Persona login has a problem with the verification data")
        logging.debug(str(verification_data))
        return _SessionUpdate(do=False, email='')
    return _SessionUpdate(do=True, email=verification_data['email'])

def get_status_lists(player_email):
    """Return two lists of games for the player, split by on-turn or not.

    Accesses database.
    """
    player_games = get_player_games(player_email)

    your_turn_games = [g for g in player_games
                       if g.to_move() == player_email]
    not_your_turn_games = [g for g in player_games
                           if g.to_move() != player_email]
    return (your_turn_games, not_your_turn_games)

def get_player_games(player_email):
    """Returns the list of games in which `player_email` is involved.

    Only includes running games, ie. not finished.

    Accesses database.
    """
    unfinished_predicate = Game.winner == None  # noqa
    # ORM doesn't accept 'is None', linter doesn't like '== None'
    games = Game.query.filter(and_(unfinished_predicate,
                                   or_(Game.black == player_email,
                                       Game.white == player_email))).all()
    return games

def check_two_passes(moves, passes, resumptions):
    """True if last two actions are both passes, false otherwise."""
    move_no_iter = (m.move_no for m in moves)
    resume_no_iter = (r.move_no for r in resumptions)
    last_move = max(itertools.chain([-1], move_no_iter, resume_no_iter))
    last_pass = max([-1] + [p.move_no for p in passes])
    if last_move >= last_pass:
        return False
    sorted_passes = sorted(passes, key=lambda p: p.move_no)
    try:
        if sorted_passes[-2].move_no == last_pass - 1:
            return True
        else:
            return False
    except IndexError:
        return False

class NoLoggedInPlayerException(Exception):
    pass

def logged_in_email():
    """Return email of logged in player, or raise NoLoggedInPlayerException.

    Accesses the session.
    """
    try:
        return session['email']
    except KeyError:
        raise NoLoggedInPlayerException()

def is_players_turn_in_game(game):
    """Test if it's the logged-in player's turn to move in `game`.

    Reads email from the session.
    """
    try:
        return game.to_move() == logged_in_email()
    except NoLoggedInPlayerException:
        return False

def add_stones_from_text_map_to_game(text_map, game):
    """Given a list of strings, add setup stones to the given game.

    An example text map is [[".b.","bw.",".b."]]
    """
    stones = get_stones_from_text_map(text_map, game)
    for stone in stones:
        db.session.add(stone)
    db.session.commit()

def get_stones_from_text_map(text_map, game):
    """Given a list of strings, return a list of setup stones for `game`.

    An example text map is [[".b.","bw.",".b."]]

    Pure function; does not commit stones to the database.
    """
    stones = []
    for rowno, row in enumerate(text_map):
        for colno, stone in enumerate(row):
            if stone not in ['b', 'w']:
                continue
            game_no = game.id
            before_move = 0
            color = {
                    'b': Move.Color.black,
                    'w': Move.Color.white
            }[stone]
            row = rowno
            column = colno
            setup_stone = SetupStone(game_no, before_move, row, column, color)
            stones.append(setup_stone)
    return stones

def render_template_with_email(template_name_or_list, **context):
    """A wrapper around flask.render_template, setting the email.

    Depends on the session object.
    """
    try:
        email = logged_in_email()
    except NoLoggedInPlayerException:
        email = ''
    try:
        persona_email = session['persona_email']
    except KeyError:
        persona_email = ''
    return render_template(
            template_name_or_list,
            current_user_email=email,
            current_persona_email=persona_email,
            **context)

# Server player

class ServerPlayer(object):
    """ A class used to represent server players. The hope is that to create a
        new server player, one need only override the `act` method. It should
        be then possible to create a daemon which runs all registered server
        players at convenient times.
    """
    def __init__(self, player_email, rest_interval=3600):
        """ Specify the player-email and the rest-interval in seconds. This can
            be specified as a floating point number for more accuracy than
            seconds if need be.
        """
        self.player_email = player_email
        self.rest_interval = rest_interval

    def _daemon(self):
        while True:
            self.act()
            time.sleep(self.rest_interval)

    def start_daemon(self):
        self._daemon_process = multiprocessing.Process(target=self._daemon)
        self._daemon_process.daemon = True
        self._daemon_process.start()

    def terminate_daemon(self):
        if self._daemon_process is not None:
            db.session.commit()
            db.session.close()
            self._daemon_process.terminate()

    def act(self):
        """ The base `act` method of the `ServerPlayer` is so simple that it
            plays a pass on every waiting game.
        """
        waiting_games, _not_waiting_games = get_status_lists(self.player_email)
        for game in waiting_games:
            # A request would normally include the 'move number' to make sure
            # we are not replaying a previous move. But we're directly
            # accessing the db here, so we get the move number from the db
            # itself. Note that this still prevents replaying a move in the
            # case in which (presumably, accidentally) we have two daemons
            # running the same computer player.
            arguments = {'move_no': game.move_no}
            validate_turn_and_record(
                    "pass", self.player_email, game, arguments)


# models

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    black = db.Column(db.String(length=254))
    white = db.Column(db.String(length=254))
    moves = db.relationship('Move', backref='game')
    passes = db.relationship('Pass', backref='game')
    resumptions = db.relationship('Resumption', backref='game')
    dead_stones = db.relationship('DeadStone', backref='game')
    setup_stones = db.relationship('SetupStone', backref='game')
    winner = db.Column(db.String(length=254), nullable=True)

    @property
    def move_no(self):
        return len(self.moves) + len(self.passes) + len(self.resumptions)

    def to_move(self):
        move_no = self.move_no
        return (self.black, self.white)[move_no % 2]

    def to_move_color(self):
        move_no = self.move_no
        return (Move.Color.black, Move.Color.white)[move_no % 2]

    def first_to_pass(self):
        """In the latest string of passes, which color passed first?"""
        passes = self.passes
        assert passes, "no passes in this game"
        last = None
        for move_no in reversed(sorted(map(lambda p: p.move_no, passes))):
            if last is None:
                last = move_no
            elif move_no == last - 1:
                last = move_no
            else:
                break
        return (Move.Color.black, Move.Color.white)[last % 2]

class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    row = db.Column(db.Integer)
    column = db.Column(db.Integer)
    move_no = db.Column(db.Integer)

    Color = go_rules.Color
    color = db.Column(db.Integer)

    def __init__(self, game_no, move_no, row, column, color):
        self.game_no = game_no
        self.move_no = move_no
        self.row = row
        self.column = column
        self.color = color

    def __repr__(self):
        return '<Move {0}: {1} at ({2},{3})>'.format(
                self.move_no, Move.Color(self.color).name,
                self.column, self.row)

class Pass(db.Model):
    __tablename__ = 'passes'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    move_no = db.Column(db.Integer)
    color = db.Column(db.Integer)

    def __init__(self, game_no, move_no, color):
        self.game_no = game_no
        self.move_no = move_no
        self.color = color

    def __repr__(self):
        return '<Pass {0}: {1}>'.format(
                self.move_no, Move.Color(self.color).name)

class Resumption(db.Model):
    __tablename__ = 'resumptions'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    move_no = db.Column(db.Integer)
    color = db.Column(db.Integer)

    def __init__(self, game_no, move_no, color):
        self.game_no = game_no
        self.move_no = move_no
        self.color = color

    def __repr__(self):
        return '<Resumption {0}: {1}>'.format(
                self.move_no, Move.Color(self.color).name)

class DeadStone(db.Model):
    __tablename__ = 'deadstones'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    row = db.Column(db.Integer)
    column = db.Column(db.Integer)

    def __init__(self, game_no, row, column):
        self.game_no = game_no
        self.row = row
        self.column = column

    def __repr__(self):
        return '<DeadStone (Game {0}): ({1}, {2})>'.format(
                self.game_no, self.column, self.row)

class SetupStone(db.Model):
    __tablename__ = 'setupstones'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    row = db.Column(db.Integer)
    column = db.Column(db.Integer)
    before_move = db.Column(db.Integer)
    color = db.Column(db.Integer)

    def __init__(self, game_no, before_move, row, column, color):
        self.game_no = game_no
        self.before_move = before_move
        self.row = row
        self.column = column
        self.color = color

    def __repr__(self):
        return '<SetupStone {0}: {1} at ({2},{3})>'.format(
                self.before_move, Move.Color(self.color).name,
                self.column, self.row)


# forms

class ChallengeForm(Form):
    opponent_email = StringField(
            "Opponent's email", validators=[DataRequired(), Email()])

class HiddenInteger(IntegerField):
    widget = HiddenInput()

class PlayStoneForm(Form):
    game_no = HiddenInteger("game_no", validators=[DataRequired()])
    move_no = HiddenInteger("move_no", validators=[DataRequired()])
    data = HiddenField("data")
    row = HiddenInteger("row", validators=[DataRequired()])
    column = HiddenInteger("column", validators=[DataRequired()])

class MarkDeadForm(Form):
    game_no = HiddenInteger("game_no", validators=[DataRequired()])
    move_no = HiddenInteger("move_no", validators=[DataRequired()])
    data = HiddenField("data")
