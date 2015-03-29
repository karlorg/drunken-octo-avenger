from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
from enum import IntEnum
import logging

from flask import (
        Flask, abort, flash, make_response, redirect, render_template, request,
        session, url_for
)
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import Form
import jinja2
import json
import requests
from wtforms import IntegerField, StringField
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
        flash("Game #{game_no} not found".format(game_no=game_no))
        return redirect('/')
    moves = game.moves
    setup_stones = game.setup_stones
    is_your_turn = is_players_turn_in_game(game, moves, [])
    goban = get_goban_from_moves(moves, setup_stones)
    form = PlayStoneForm(data=dict(
        game_no=game.id,
        move_no=len(moves)
    ))
    return render_template_with_email(
            "game.html",
            form=form, goban=goban, with_links=is_your_turn)

@app.route('/playstone', methods=['POST'])
def playstone():
    return play_move_or_pass("move")

@app.route('/playpass', methods=['POST'])
def playpass():
    return play_move_or_pass("pass")

def play_move_or_pass(which):
    """If a valid move was specified, play it (add to db).

    We require that the supplied move include the move number to help detect
    duplicated requests.
    """
    arguments = request.form.to_dict()
    try:
        game_no = int(arguments['game_no'])
    except (KeyError, ValueError):
        return redirect('/')
    game = Game.query.filter(Game.id == game_no).first()
    moves = game.moves

    new_object = get_move_or_pass_if_args_good(
            which=which, args=arguments, moves=moves, passes=[])

    if new_object is None:
        flash("Invalid move received")
        return redirect(url_for('status'))
    if not is_players_turn_in_game(game, moves, []):
        flash("It's not your turn!")
        return redirect(url_for('status'))

    if which == "move":
        # test legality
        board = get_rules_board_from_db_objects(
                moves=moves, setup_stones=game.setup_stones)
        try:
            board.update_with_move(
                    new_object.color,
                    new_object.row, new_object.column, new_object.move_no)
        except go_rules.IllegalMoveException as e:
            flash("Illegal move received: " + e.args[0])
            return redirect(url_for('game', game_no=game_no))

    db.session.add(new_object)
    db.session.commit()
    return redirect(url_for('status'))

def get_move_or_pass_if_args_good(which, args, moves, passes):
    """Check GET arguments and if a new move is indicated, return it.

    Pure function; does not commit the new stone to the database.
    """
    try:
        game_no = int(args['game_no'])
        move_no = int(args['move_no'])
        if which == "move":
            row = int(args['row'])
            column = int(args['column'])
    except (KeyError, ValueError):
        return None
    if move_no != len(moves) + len(passes):
        return None
    color = (Move.Color.black, Move.Color.white)[move_no % 2]
    if which == "move":
        return Move(
                game_no=game_no, move_no=move_no,
                row=row, column=column, color=color)
    elif which == "pass":
        return Pass(
                game_no=game_no, move_no=move_no, color=color)
    else:
        assert False, "bad argument to get_move_or_pass_if_args_good"


@app.route('/challenge', methods=('GET', 'POST'))
def challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        game = Game()
        game.black = form.opponent_email.data
        game.white = session['email']
        db.session.add(game)
        db.session.commit()
        return redirect(url_for('status'))
    return render_template_with_email("challenge.html", form=form)

@app.route('/status')
def status():
    if 'email' not in session:
        return redirect('/')
    logged_in_email = session['email']
    your_turn_games, not_your_turn_games = get_status_lists(logged_in_email)
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
    """Set up and return cookie data for a pre-authenticated login session"""
    email = request.form['email']
    cookie = get_login_session(email)
    response = make_response('\n'.join([cookie['name'],
                                        cookie['value'],
                                        cookie['path']]))
    response.headers['content-type'] = 'text/plain'
    return response

def get_login_session(email):
    """Set up a pre-authenticated login session.

    In contrast to the view function (for which this is a helper), this
    function only creates the session and returns the cookie name, value, and
    path without printing.
    """
    interface = app.session_interface
    session = interface.session_class()
    session['email'] = email
    # the following process for creating the cookie value is copied from
    # the Flask source; if the cookies created by this method stop
    # working, see if a Flask update has changed the cookie creation
    # procedure in flask/sessions.py -> SecureCookieSessionInterface
    # (currently the default) -> save_session
    cookie_value = (
            interface.get_signing_serializer(app).dumps(dict(session))
    )
    return dict(
            name=app.session_cookie_name,
            value=cookie_value,
            path=interface.get_cookie_path(app),
    )

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
    moves = Move.query.filter(Move.game == game).all()
    for move in moves:
        db.session.delete(move)
    setup_stones = SetupStone.query.filter(SetupStone.game == game).all()
    for setup_stone in setup_stones:
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

def get_goban_from_moves(moves, setup_stones=None):
    """Given the moves for a game, return game template data.

    Pure function.
    """
    if setup_stones is None:
        setup_stones = []
    rules_board = get_rules_board_from_db_objects(moves, setup_stones)
    goban = get_goban_data_from_rules_board(rules_board)
    return goban

def get_rules_board_from_db_objects(moves, setup_stones):
    """Get board layout resulting from given moves and setup stones.

    Pure function.
    """

    def rules_color(db_color):
        if db_color == Move.Color.black:
            color = go_rules.Color.black
        elif db_color == Move.Color.white:
            color = go_rules.Color.white
        else:
            color = go_rules.Color.empty
        return color

    def place_stones_for_move(n):
        for stone in filter(lambda s: s.before_move == n, setup_stones):
            board.set_point(stone.row, stone.column,
                            rules_color(stone.color))

    board = go_rules.Board()
    for move in sorted(moves, key=lambda m: m.move_no):
        place_stones_for_move(move.move_no)
        board.update_with_move(
                rules_color(move.color), move.row, move.column)
    max_move_no = max([-1] + [m.move_no for m in moves])
    place_stones_for_move(max_move_no + 1)
    return board

def get_goban_data_from_rules_board(rules_board):
    """Transform a dict of {(r,c): color} to a template-ready list of dicts.

    Each output dictionary contains information needed by the game template to
    render the corresponding board point.

    `classes` contains CSS classes used by the client-side scripts and browser
    tests to read the board state and locate specific points.  Currently:

    * each point should have classes `row-y` and `col-x` where `y` and `x` are
      numbers

    * points with stones should have `blackstone` or `whitestone`; empty points
      should have `nostone`

    Pure function.
    """
    black = go_rules.Color.black
    white = go_rules.Color.white
    empty = go_rules.Color.empty
    goban = [[dict(
        img=IMG_PATH_EMPTY,
        classes='gopoint row-{row} col-{col}'.format(row=str(j), col=str(i))
    )
             for i in range(19)]
             for j in range(19)]
    for (r, c), color in rules_board.items():
        if color == black:
            goban[r][c]['img'] = IMG_PATH_BLACK
            goban[r][c]['classes'] += ' blackstone'
        elif color == white:
            goban[r][c]['img'] = IMG_PATH_WHITE
            goban[r][c]['classes'] += ' whitestone'
        elif color == empty:
            goban[r][c]['classes'] += ' nostone'
    return goban

def get_status_lists(player_email):
    """Return two lists of games for the player, split by on-turn or not.

    Accesses database.
    """
    all_games = Game.query.all()
    current_player_games = get_player_games(player_email, all_games)
    games_to_moves = [
            (game, game.moves,)
            for game in current_player_games
    ]
    your_turn_games, not_your_turn_games = partition_by_turn(
            player_email, games_to_moves)
    return (your_turn_games, not_your_turn_games,)

def get_player_games(player_email, games):
    """Filter `games` to those involving player_email.

    Pure function.
    """
    def involved_in_game(game):
        return (player_email == game.black or player_email == game.white)
    return list(filter(involved_in_game, games))

def partition_by_turn(player_email, games_to_moves):
    """Partition games into two lists, player's turn and not player's turn.

    Pure function.  `games_to_moves` is a list of pairs mapping games to the
    moves for each game, since this function may not access the database
    itself.
    """
    yes_turn = []
    no_turn = []
    for (game, moves,) in games_to_moves:
        if is_players_turn_in_game(game, moves, [], email=player_email):
            yes_turn.append(game)
        else:
            no_turn.append(game)
    return (yes_turn, no_turn,)

def is_players_turn_in_game(game, moves, passes, email=None):
    """Test if it's `email`'s turn to move in `game` given `moves`.

    If `email` is passed, this acts as a pure function; otherwise, it reads
    email from the session.

    `moves` and `passes` should list moves and passes associated with `game`,
    since this function won't access the database itself.
    """
    if email is None:
        try:
            email = session['email']
        except KeyError:
            return False
    if len(moves) + len(passes) == 0:
        last_move_color = Move.Color.white  # black to move
    else:
        last_move = max(moves + passes,
                        key=lambda move_or_pass: move_or_pass.move_no)
        last_move_color = last_move.color
    if (game.black == email):
        return (last_move_color == Move.Color.white)
    else:  # player is white
        return (last_move_color == Move.Color.black)

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
        email = session['email']
    except KeyError:
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


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    black = db.Column(db.String(length=254))
    white = db.Column(db.String(length=254))
    moves = db.relationship('Move', backref='game')
    setup_stones = db.relationship('SetupStone', backref='game')

class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    game_no = db.Column(db.Integer, db.ForeignKey('games.id'))
    row = db.Column(db.Integer)
    column = db.Column(db.Integer)
    move_no = db.Column(db.Integer)

    class Color(IntEnum):
        black = 0
        white = 1
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


class ChallengeForm(Form):
    opponent_email = StringField(
            "Opponent's email", validators=[DataRequired(), Email()])

class HiddenInteger(IntegerField):
    widget = HiddenInput()

class PlayStoneForm(Form):
    game_no = HiddenInteger("game_no", validators=[DataRequired()])
    move_no = HiddenInteger("move_no", validators=[DataRequired()])
    row = HiddenInteger("row", validators=[DataRequired()])
    column = HiddenInteger("column", validators=[DataRequired()])
