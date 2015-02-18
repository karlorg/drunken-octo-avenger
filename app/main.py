from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
from enum import IntEnum
import logging

from flask import (
        Flask, abort, flash, redirect, render_template, request, session,
        url_for
)
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import Form
import jinja2
import requests
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Email
from wtforms.widgets import HiddenInput

from config import DOMAIN


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
    is_your_turn = is_players_turn_in_game(game, moves)
    # imgs = get_img_array_from_moves(moves)
    # goban = annotate_with_classes(imgs)
    goban = get_goban_from_moves(moves)
    form = PlayStoneForm(data=dict(
        game_no=game.id,
        move_no=len(moves)
    ))
    return render_template_with_email(
            "game.html",
            form=form, goban=goban, with_links=is_your_turn)

@app.route('/playstone', methods=['POST'])
def playstone():
    """If a valid move was specified, play it (add to db)."""
    arguments = request.form.to_dict()
    try:
        game_no = int(arguments['game_no'])
    except (KeyError, ValueError):
        return redirect('/')
    game = Game.query.filter(Game.id == game_no).first()
    moves = game.moves
    stone = get_stone_if_args_good(args=arguments, moves=moves)
    if stone is None:
        flash("Invalid move received")
    elif not is_players_turn_in_game(game, moves):
        flash("It's not your turn!")
    else:
        db.session.add(stone)
        db.session.commit()
    return redirect(url_for('status'))

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

def get_stone_if_args_good(args, moves):
    """Check GET arguments and if a new move is indicated, return it.

    Pure function; does not commit the new stone to the database.
    """
    try:
        game_no = int(args['game_no'])
        move_no = int(args['move_no'])
        row = int(args['row'])
        column = int(args['column'])
    except (KeyError, ValueError):
        return None
    if move_no != len(moves):
        return None
    color = (Move.Color.black, Move.Color.white)[move_no % 2]
    return Move(
            game_no=game_no, move_no=move_no,
            row=row, column=column, color=color)

def get_goban_from_moves(moves):
    """Given the moves for a game, return a 2d array of dicts for the board.

    Each dictionary contains information needed to render the corresponding
    board point.

    `.classes` contains CSS classes used by the client-side scripts and browser
    tests to read the board state and locate specific points.  Currently:

    * each point should have classes `row-y` and `col-x` where `y` and `x` are
      numbers

    * points with stones should have `blackstone` or `whitestone`

    Pure function.
    """
    goban = [[dict(
        img=IMG_PATH_EMPTY,
        classes='row-{row} col-{col}'.format(row=str(j), col=str(i))
    )
             for i in range(19)]
             for j in range(19)]
    for move in moves:
        if move.color == Move.Color.black:
            goban[move.row][move.column]['img'] = IMG_PATH_BLACK
            goban[move.row][move.column]['classes'] += ' blackstone'
        elif move.color == Move.Color.white:
            goban[move.row][move.column]['img'] = IMG_PATH_WHITE
            goban[move.row][move.column]['classes'] += ' whitestone'
        else:
            assert False, "unknown move color"
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
        if is_players_turn_in_game(game, moves, email=player_email):
            yes_turn.append(game)
        else:
            no_turn.append(game)
    return (yes_turn, no_turn,)

def is_players_turn_in_game(game, moves, email=None):
    """Test if it's `email`'s turn to move in `game` given `moves`.

    If `email` is passed, this acts as a pure function; otherwise, it reads
    email from the session.

    `moves` should be the list of moves associated with `game`, since this
    function won't access the database itself.
    """
    if email is None:
        try:
            email = session['email']
        except KeyError:
            return False
    if len(moves) == 0:
        last_move_color = Move.Color.white  # black to move
    else:
        last_move = max(moves, key=lambda move: move.move_no)
        last_move_color = last_move.color
    if (game.black == email):
        return (last_move_color == Move.Color.white)
    else:  # player is white
        return (last_move_color == Move.Color.black)

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
                self.move_no, self.Color(self.color).name,
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
