from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
import logging
import time
import multiprocessing
from datetime import datetime

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
from sqlalchemy import and_, not_, or_
from sqlalchemy.exc import SQLAlchemyError
import werkzeug.security as ws
from wtforms import HiddenField, IntegerField, PasswordField, StringField
from wtforms.validators import DataRequired
from wtforms.widgets import HiddenInput

from config import DOMAIN
from app import go
from app import sgftools


IMG_PATH_EMPTY = '/static/images/goban/e.gif'
IMG_PATH_BLACK = '/static/images/goban/b.gif'
IMG_PATH_WHITE = '/static/images/goban/w.gif'

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.undefined = jinja2.StrictUndefined
if app.debug:
    logging.basicConfig(level=logging.DEBUG)
db = SQLAlchemy(app)


def redirect_url(default='front_page'):
    """ A simple helper function to redirect the user back to where they came
        from. See: http://flask.pocoo.org/docs/0.10/reqcontext/ and also
        here: http://stackoverflow.com/questions/14277067/redirect-back-in-flask
    """
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

# Views
#
# Since view functions tend to have side-effects and to depend on global state,
# try to keep complexity (if, for...) out of them and move it into pure
# function helpers instead.

@app.route('/')
def front_page():
    if is_logged_in():
        return redirect(url_for('status'))
    return render_template_with_basics("frontpage.html")

@app.route('/game/<int:game_no>')
def game(game_no):
    try:
        game = db.session.query(Game).filter_by(id=game_no).one()
    except SQLAlchemyError:
        flash("Game #{} not found".format(game_no))
        return redirect('/')
    sgf = game.sgf
    comments = game.comments
    color_turn = go.next_color(sgf).name
    is_your_turn = is_players_turn_in_game(game)
    is_passed_twice = go.is_sgf_passed_twice(sgf)
    form_data = {'game_no': game.id, 'data': sgf}
    form = PlayStoneForm(data=form_data)
    chatform = ChatForm(data=form_data)
    return render_template_with_basics(
        "game.html",
        black_user=game.black,
        white_user=game.white,
        color_turn=color_turn,
        form=form, chatform=chatform, game_no=game_no,
        on_turn=is_your_turn, with_scoring=is_passed_twice,
        comments=comments)

@app.route('/chat/<int:game_no>', methods=['POST'])
def comment(game_no):
    try:
        game = db.session.query(Game).filter_by(id=game_no).one()
    except SQLAlchemyError:
        flash("Game #{} not found".format(game_no))
        return redirect('/')
    try:
        current_user = logged_in_user()
    except NoLoggedInPlayerException:
        flash("You must be logged in to comment.")
        return redirect(redirect_url())

    form = ChatForm()
    if form.validate_on_submit():
        comment = GameComment(game, form.comment.data, current_user)
        db.session.add(comment)
        db.session.commit()
        return redirect(redirect_url())
    flash("Comment not validated!")
    return redirect(redirect_url())

@app.route('/play/<int:game_no>', methods=['POST'])
def play(game_no):
    try:
        game = db.session.query(Game).filter_by(id=game_no).one()
    except SQLAlchemyError:
        flash("Game #{} not found".format(game_no))
        return redirect('/')
    if not is_players_turn_in_game(game):
        flash("It's not your turn in that game.")
        return redirect('/')
    arguments = request.form.to_dict()
    if 'resign_button' in arguments:
        game.finished = True
        return redirect(redirect_url())
    try:
        go.check_continuation(old_sgf=game.sgf,
                              new_sgf=arguments['response'],
                              allowed_new_moves=1)
    except go.ValidationException as e:
        flash("Invalid move: {}".format(e.args[0]))
        return redirect(url_for('game', game_no=game_no))
    except KeyError:
        flash("Invalid request.")
        return redirect(url_for('game', game_no=game_no))
    game.sgf = arguments['response']
    _check_gameover_and_update(game)
    db.session.commit()
    return redirect(redirect_url())

def _check_gameover_and_update(game):
    """If game is over, update the appropriate fields."""
    if go.ends_by_agreement(game.sgf):
        game.finished = True

@app.route('/challenge', methods=('GET', 'POST'))
def challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        game = Game(black=form.opponent.data,
                    white=logged_in_user(),
                    sgf="(;)")
        db.session.add(game)
        db.session.commit()
        return redirect(url_for('status'))
    return render_template_with_basics("challenge.html", form=form)

@app.route('/status')
def status():
    try:
        user = logged_in_user()
    except NoLoggedInPlayerException:
        return redirect('/')
    your_turn_games, not_your_turn_games = get_status_lists(user)
    return render_template_with_basics(
            "status.html",
            your_turn_games=your_turn_games,
            not_your_turn_games=not_your_turn_games)

def get_status_lists(user):
    """Return two lists of games for the player, split by on-turn or not.

    Accesses database.
    """
    player_games = get_player_games(user)

    your_turn_games = [g for g in player_games
                       if user_to_move_in_game(g) == user]
    not_your_turn_games = [g for g in player_games
                           if user_to_move_in_game(g) != user]
    return (your_turn_games, not_your_turn_games)

def get_player_games(user):
    """Returns the list of games in which `user` is involved.

    Only includes running games, ie. not finished.

    Accesses database.
    """
    games = Game.query.filter(and_(not_(Game.finished),
                                   or_(Game.black == user,
                                       Game.white == user))).all()
    return games

def is_players_turn_in_game(game):
    """Test if it's the logged-in player's turn to move in `game`.

    Reads user from the session.
    """
    try:
        current_user = logged_in_user()
    except NoLoggedInPlayerException:
        return False
    next_in_game = user_to_move_in_game(game)
    return next_in_game == current_user

def user_to_move_in_game(game):
    """Return the user id of the player to move in game.

    Accesses database.  Return None if game is finished.
    """
    if game.finished:
        return None
    black_or_white = go.next_color(game.sgf)
    next_in_game = {go.Color.black: game.black,
                    go.Color.white: game.white}[black_or_white]
    return next_in_game


@app.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = (db.session.query(User)
                 .filter_by(username=form.username.data).all())
        if len(users) == 0:
            flash('Username not found')
            return redirect(redirect_url())
        user = users[0]
        if not user.check_password(form.password.data):
            flash('Password incorrect')
            return redirect(redirect_url())
        set_logged_in_user(form.username.data)
        return redirect(redirect_url())
    else:
        return redirect(redirect_url())


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = CreateAccountForm()
    if form.validate_on_submit():
        if form.password1.data != form.password2.data:
            flash("Passwords don't match")
            return render_template_with_basics('create_account.html',
                                               form=form)
        user = User(username=form.username.data,
                    password=form.password1.data)
        db.session.add(user)
        db.session.commit()
        set_logged_in_user(form.username.data)
        return redirect('/')
    else:
        return render_template_with_basics('create_account.html',
                                           form=form)


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
        set_logged_in_user(session_update.email)
        session.update({'persona_email': session_update.email})
        # we're only accessed through AJAX, the response doesn't matter
        return ''
    else:
        abort(500)

@app.route('/finished', methods=['GET'])
def finished():
    try:
        user = logged_in_user()
    except NoLoggedInPlayerException:
        return redirect('/')
    finished_games = (
        db.session.query(Game)
        .filter(Game.finished == True)  # noqa
        .filter(or_(Game.black == user, Game.white == user))
        .all()
    )
    return render_template_with_basics(
            "finished.html",
            finished_games=finished_games)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        logout_current_user()
    except KeyError:
        pass
    try:
        del session['persona_email']
    except KeyError:
        pass
    if request.method == 'POST':
        return ''
    else:
        return redirect('/')

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

@app.test_only_route('/testing_delete_user', methods=['POST'])
def testing_delete_user():
    """Delete the user with the given username."""
    username = request.form['username']
    users = db.session.query(User).filter_by(username=username).all()
    for user in users:
        db.session.delete(user)
    db.session.commit()
    return ''

@app.test_only_route('/testing_create_login_session', methods=['POST'])
def testing_create_login_session():
    """Log in the given user id."""
    set_logged_in_user(request.form['email'])
    return ''

@app.test_only_route('/testing_create_game', methods=['POST'])
def testing_create_game():
    """Create a custom game in the database directly"""
    black_user = request.form['black_email']
    white_user = request.form['white_email']
    stones = json.loads(request.form['stones'])
    create_game_internal(black_user, white_user, stones)
    return ''

def create_game_internal(black, white,
                         sgf_or_stones=None,
                         stones=None, sgf=None):
    """Create a custom game for testing purposes.

    Can be initialized with an SGF or a 'text map', ie. a list of strings
    representing setup stones like this:

        ['w.',
         '.b']
    """
    assert sum(1 for x in [sgf_or_stones, stones, sgf]
               if x is not None) <= 1, \
        "can't supply more than one initial state to create_game_internal"
    if sgf_or_stones:
        if isinstance(sgf_or_stones, str):
            assert sgf_or_stones[0] == '(', \
                "invalid SGF passed to create_game_internal; if you meant " \
                "a text map, make it a list"
            sgf = sgf_or_stones
        else:
            stones = sgf_or_stones
    if not sgf:
        if not stones:
            stones = []
        sgf = sgf_from_text_map(stones)
    game = Game(black=black, white=white, sgf=sgf)
    db.session.add(game)
    db.session.commit()
    return game

def sgf_from_text_map(text_map):
    assert not isinstance(text_map, str), \
        "text maps should be lists of strings, not a single string"
    ab_coords = []
    aw_coords = []
    for rowno, row in enumerate(text_map):
        for colno, char in enumerate(row):
            if char == 'b':
                ab_coords.append((colno, rowno))
            elif char == 'w':
                aw_coords.append((colno, rowno))

    def sgfify(coords, tag):
        if not coords:
            return ''
        return (tag + '[' +
                ']['.join(sgftools.encode_coord(x, y)
                          for (x, y) in coords)
                + ']')
    ab_str = sgfify(ab_coords, 'AB')
    aw_str = sgfify(aw_coords, 'AW')
    return "(;{ab}{aw})".format(ab=ab_str, aw=aw_str)


@app.test_only_route('/testing_setup_finished_game', methods=['POST'])
def testing_setup_finished_game():
    """Create a finished game (in the marking phase)."""
    black_user = request.form['black_email']
    white_user = request.form['white_email']
    setup_finished_game_internal(black_user, white_user)
    return ''

def setup_finished_game_internal(black_user, white_user):
    stones = ['.....bww.wbb.......',
              '.bb...bw.wwbb......',
              '.wwbbb.bw.wbwwb..b.',
              'b.www..b.w.b.bbb.b.',
              '.w.w..bww.wwbbwwww.',
              '.bwwb.bw.w.wwbbbbbb',
              '.bbbbbbw.bbbbwwwwwb',
              '...bwwwbbbwbwww..ww',
              '....bbwwb.wwbbbww..',
              '.bbbbww.ww.ww..wb..',
              'bbwbw.....wbw..wb..',
              'bwww.w...wbbw......',
              'w.......w...w..w.ww',
              'w.w.....wbbbw...wwb',
              'bw...www.b.bbww.wbb',
              'bbwwwwbwbbwww.wwbb.',
              '.bbbwbbbwbbbwwbwb..',
              '...bbw.bwb..bbbb...',
              '...................']
    sgf = sgf_from_text_map(stones)
    passed_sgf = sgf[:-1] + 'B[];W[])'
    create_game_internal(black_user, white_user, sgf=passed_sgf)


@app.test_only_route('/testing_clear_games_for_player', methods=['POST'])
def testing_clear_games_for_player():
    """Clear all of `email`'s games from the database."""
    user = request.form['email']
    clear_games_for_player_internal(user)
    return ''

def clear_games_for_player_internal(user):
    games_as_black = Game.query.filter(Game.black == user).all()
    games_as_white = Game.query.filter(Game.white == user).all()
    games = games_as_black + games_as_white
    for game in games:
        db.session.delete(game)


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

def is_logged_in():
    """True if a user is logged in."""
    return 'user' in session

def set_logged_in_user(user):
    session.update(user=user)

def logout_current_user():
    del session['user']

class NoLoggedInPlayerException(Exception):
    pass

def logged_in_user():
    """Return user id of logged in player, or raise NoLoggedInPlayerException.

    Accesses the session.
    """
    try:
        return session['user']
    except KeyError:
        raise NoLoggedInPlayerException()

def render_template_with_basics(template_name_or_list, **context):
    """A wrapper around flask.render_template, setting always-present fields.

    Depends on the session object.
    """
    try:
        user = logged_in_user()
    except NoLoggedInPlayerException:
        user = ''
    try:
        persona_email = session['persona_email']
    except KeyError:
        persona_email = ''
    return render_template(
            template_name_or_list,
            current_user=user,
            current_persona_email=persona_email,
            login_form=LoginForm(),
            **context)

def max_with_sentinel(sentinel, *iterables):
    return max(itertools.chain([sentinel], *iterables))

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
    sgf = db.Column(db.Text())
    finished = db.Column(db.Boolean(), server_default="0")

    def __repr__(self):
        return "<Game {no}, {b} vs. {w}>".format(
            no=self.id, b=self.black, w=self.white)

class GameComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pub_date = db.Column(db.DateTime)
    speaker = db.Column(db.String(length=254))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    game = db.relationship('Game', 
                           backref=db.backref('comments', lazy='dynamic'))
    content = db.Column(db.Text())

    def __init__(self, game, content, speaker, pub_date=None):
        self.game = game
        self.content = content
        self.speaker = speaker
        self.pub_date = pub_date if pub_date is not None else datetime.utcnow()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(length=254))
    password_hash = db.Column(db.String(length=254))

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = ws.generate_password_hash(password,
                                                       method='pbkdf2:sha256')

    def check_password(self, password):
        return ws.check_password_hash(pwhash=self.password_hash,
                                      password=password)


# forms

class ChallengeForm(Form):
    opponent = StringField(
            "Opponent's email or username", validators=[DataRequired()])

class LoginForm(Form):
    username = StringField("Username",
                           validators=[DataRequired()],
                           description="Username")
    password = PasswordField("Password",
                             validators=[DataRequired()],
                             description="Password")

class CreateAccountForm(Form):
    username = StringField("Username",
                           validators=[DataRequired()])
    password1 = PasswordField("Password",
                              validators=[DataRequired()])
    password2 = PasswordField("Password again",
                              validators=[DataRequired()])

class HiddenInteger(IntegerField):
    widget = HiddenInput()

class PlayStoneForm(Form):
    game_no = HiddenInteger("game_no", validators=[DataRequired()])
    move_no = HiddenInteger("move_no", validators=[DataRequired()])
    data = HiddenField("data")
    response = HiddenField("response", validators=[DataRequired()])

class ChatForm(Form):
    game_no = HiddenInteger("game_no", validators=[DataRequired()])
    # move_no = HiddenInteger("move_no", validators=[DataRequired()])
    comment = StringField('Comment', validators=[DataRequired()])
