# compute server url from arguments

defaultHost = "http://localhost"
host = casper.cli.options['host'] or defaultHost
port = casper.cli.options['port'] or
  if host is defaultHost then "5000" else "80"

portString = if port == "80" or port == 80 then "" else ":#{port}"

unless (host.match /localhost/) or (host.match /staging/)
  casper.die "Server url contains neither 'localhost' nor 'staging', aborting"

serverUrl = "#{host}#{portString}"
casper.echo "Testing against server at #{serverUrl}"

debug_dump_html = () ->
  "Occasionally can be useful during debugging just to dump the current HTML."
  casper.echo (casper.getHTML())


# test inventory management

testObjectsByName = {}
allTestObjects = []

registerTest = (test) ->
  allTestObjects.push test
  for name in test.names
    testObjectsByName[name] = test

runTest = (name) ->
  test = testObjectsByName[name]
  test.run()

runAll = () ->
  for test in allTestObjects
    test.run()

# test suites
class BrowserTest
  # An abstract base class for our browser tests
  #
  # Instances should define the following properties:
  #
  # * testBody: called by `run` below to execute the test
  # * names: array of names by which a caller can identify this test (with the
  #          `--single` command line option)
  # * description
  # * numTests: expected number of assertions

  run: =>
    casper.test.begin @description, @numTests, (test) =>
      casper.start()
      @testBody(test)
      casper.then ->
        test.done()

  names: []
  description: 'This class needs a description'
  numTests: 0

  # Utility functions used by more than one test class
  assertNumGames: (test, players_turn, players_wait) ->
    casper.thenOpen serverUrl, ->
      test.assertExists '#your_turn_games',
                        "Status has a list of 'your turn' games"
      test.assertExists '#not_your_turn_games',
                        "Status has a list of 'not your turn' games"
      game_counts = casper.evaluate () ->
        counts =
          'your_turn': $('#your_turn_games a').length
          'not_your_turn': $('#not_your_turn_games a').length
        return counts
      test.assertEqual game_counts.your_turn, players_turn,
                       'Expected number of your-turn games'
      test.assertEqual game_counts.not_your_turn, players_wait,
                       'Expected number of not-your-turn games'

  lastFinishedGameSelector: ->
    list_id = 'finished_games'
    return '#' + list_id + ' li:last-child a'

  lastGameSelector: (your_turn) ->
    list_id = if your_turn then 'your_turn_games' else 'not_your_turn_games'
    return '#' + list_id + ' li:last-child a'

  getLastGameLink: (your_turn) =>
    evaluate_fun = (selector) ->
      link =
        target: $(selector).attr('href')
        text: $(selector).text()
      return link
    casper.evaluate evaluate_fun, @lastGameSelector(your_turn)

  imageSrc: (x, y) ->
    casper.evaluate ((x, y) ->
      $("td.row-#{y}.col-#{x}").css('background-image')),
        x, y

  check_flashed_message: (test, expected_message, category,
                          test_message = 'Checking flashed message') ->
    selector = "div.alert.alert-#{category}"
    test.assertSelectorHasText selector, expected_message, test_message

  numberJQSelector: (selector) ->
    " Caspers test.assertExist is great but only works with CSS selectors,
      not JQuery selectors, hence this helper function, which can be used with
      assertEqual"
    casper.evaluate ((selector) ->
      $(selector).length),
      selector

  assertPointIs: (test, x, y, property, message) ->
    selector = ".goban " + pointSelector(x,y) + property
    num_matching_points = @numberJQSelector selector
    test.assertEqual num_matching_points, 1, message

  assertPointIsBlack: (test, x, y) ->
    @assertPointIs test, x, y, ":has(.stone.black:not(dead))",
                   'There is a black stone at the expected point'

  assertPointIsWhite: (test, x, y) ->
    @assertPointIs test, x, y, ":has(.stone.white:not(dead))",
                   'There is a white stone at the expected point'

  assertPointIsEmpty: (test, x, y) ->
    @assertPointIs test, x, y, ":not(:has(.stone))",
                   'The specified point is empty as expected'

  assertPointIsDeadBlack: (test, x, y) ->
    @assertPointIs test, x, y, ":has(.stone.black.dead)",
                   'There is a dead black stone at the expected point'

  assertPointIsDeadWhite: (test, x, y) ->
    @assertPointIs test, x, y, ":has(.stone.white.dead)",
                   'There is a white dead stone at the expected point'

  assertPointIsWhiteTerritory: (test, x, y) ->
    @assertPointIs test, x, y, ":has(.territory.white)",
                   'There is a white territory at the expected point'

  countStonesAndPoints: ->
    casper.evaluate ->
      'empty':      $('.goban .gopoint:not(:has(.stone))').length
      'black':      $('.goban .stone.black:not(.dead)').length
      'white':      $('.goban .stone.white:not(.dead)').length
      'blackscore': $('.goban .territory.black').length
      'whitescore': $('.goban .territory.white').length
      'blackdead':  $('.goban .stone.black.dead').length
      'whitedead':  $('.goban .stone.white.dead').length
      'dame':    $('.goban .territory.neutral').length

  assertGeneralPointCounts: (test, expected) =>
    "Run multiple assertions on the number of points with certain contents.

    expected should be an object mapping the names of point types from
    countStonesAndPoints above to expected counts.  You only need to supply the
    counts you're interested in; no assertions will be run for missing counts.

    The name 'label' in expected is special, providing a string to show in the
    test output against these results, for readability."
    label = expected.label ? "unlabeled"
    delete expected.label
    counts = @countStonesAndPoints()
    for own type, count of expected
      test.assertEqual counts[type], count,
          "in #{label}: #{type} should be #{count}, was #{counts[type]}"
    return

  assertStonePointCounts: (test, nostone, black, white, label=null) =>
    counts = @countStonesAndPoints()
    @assertGeneralPointCounts test,
      'label': label
      'empty': nostone
      'black': black
      'white': white

  assertEmptyBoard: (test) =>
    @assertStonePointCounts test, 19*19, 0, 0

  assertPrisoners: (test, counts) ->
    for color, count of counts
      actualCount = parseInt casper.evaluate(
        (color) -> $(".prisoners.#{color}").text(),
        color), 10
      test.assertEqual actualCount, count,
        "#{color} prisoners should be #{count}, is #{actualCount}"

  assertScores: (test, scores) ->
    for color, score of scores
      actualScore = parseInt casper.evaluate(
        (color) -> $(".score.#{color}").text(),
        color), 10
      test.assertEqual actualScore, score,
        "#{color} score should be #{score}, is #{actualScore}"


class ClientSideJsTest extends BrowserTest
  names: ['ClientSideJsTest', 'qunit', 'client']
  description: "Run client-side JS tests and ensure they pass."
  numTests: 1
  testBody: (test) ->
    qunitUrl = serverUrl + "/static/tests/tests.html"
    casper.thenOpen qunitUrl, ->
      predicate = ->
        (casper.exists '.qunit-pass') or (casper.exists '.qunit-fail')
      foundFunc = ->
        if casper.exists '.qunit-pass'
          test.pass 'Qunit tests passed'
        else if casper.exists '.qunit-fail'
          test.fail "Qunit tests failed.  " +
                    "Load the test page in your browser for details."
      timeoutFunc = ->
        test.fail "Couldn't detect pass or fail for Qunit tests.  " +
                  "Load the test page in your browser for details."
      casper.waitFor predicate, foundFunc, timeoutFunc, 5000

registerTest new ClientSideJsTest


class NativeLoginTest extends BrowserTest
  names: ['NativeLoginTest', 'login', 'nlogin']
  description: 'Test our native username/password login procedure'
  numTests: 14
  testBody: (test) ->
    deleteUser 'darrenlamb'
    casper.thenOpen serverUrl, ->
      @fill 'form#login_form', {
        username: 'darrenlamb'
        password: 'iknowandy'
        }, true  # true = submit form
    casper.then =>
      # Darren is not known to us; he is returned to the login form
      # and sees a message that his username is not found
      test.assertExists '#login_form',
        "After trying to log in without an account, returned to login form"
      @check_flashed_message test, 'Username not found', 'danger',
        "After trying to log in without an account, message appears"

    # he sets up a new account
    # at first he gets overenthusiastic and tries to set two different passwords
    casper.thenClick '#new_account', ->
      @fill 'form#new_account_form', {
        username: 'darrenlamb'
        password1: 'iknowandy'
        password2: 'imdarrenlamb'
        }, true  # true = submit form
    # he is returned to the new account form with an error message
    casper.then =>
      casper.waitForText 'Passwords do not match', =>
        test.assertExists 'form#new_account_form',
          "Darren tried non-matching passwords, is returned to form"
        @check_flashed_message test, "Passwords do not match", 'danger',
          "Darren is warned about his passwords not matching"
        # he is not logged in
        test.assertDoesntExist '#logout'

    # he tries again with matching passwords
    casper.then ->
      @fill 'form#new_account_form', {
        username: 'darrenlamb'
        password1: 'iknowandy'
        password2: 'iknowandy'
        }, true  # true = submit form
    # Darren is automatically logged in
    casper.waitForSelector '#logout', ->
      # the next page has a logout button
      test.assertExists '#logout',
        "Darren logged in automatically, logout button appears"
      # and shows Darren's username
      user_menu_selector = '#user-dropdown-menu a'
      test.assertSelectorHasText user_menu_selector, 'darrenlamb',
        "Darren logged in for first time, his name appears"

    # he logs out
    casper.thenClick '#logout', ->
      test.assertDoesntExist '#logout',
        "Darren logs out, logout button disappears"
      test.assertExists 'form#login_form',
        "Darren logged out, the login form is back"

    # later, he logs in again
    casper.thenOpen serverUrl, ->
      # at first he forgets what password he settled on
      @fill 'form#login_form', {
        username: 'darrenlamb'
        password: 'imdarrenlamb'
        }, true  # true = submit form
    casper.then =>
      test.assertDoesntExist '#logout',
        "After trying incorrect password, logout button doesn't appear"
      @check_flashed_message test, 'Password incorrect', 'danger',
        "After trying incorrect password, a message to that effect appears"
      test.assertExists 'form#login_form',
        "After trying incorrect password, login form is presented again"

    # he tries once more with the correct password
    casper.then ->
      @fill 'form#login_form', {
        username: 'darrenlamb'
        password: 'iknowandy'
        }, true  # true = submit form
    # this time he gets in
    casper.then ->
      test.assertExists '#logout',
        "Darren logs in again, logout button appears"
      test.assertTextExists 'darrenlamb',
        "Darren logs in again, his name appears on the page"

registerTest new NativeLoginTest


class StatusTest extends BrowserTest
  names: ['StatusTest', 'status']
  description: 'Test the status listings'
  numTests: 12
  testBody: (test) =>
    ONE_EMAIL = 'playa@uno.es'
    TWO_EMAIL = 'player@two.co.uk'
    THREE_EMAIL = 'plagxo@tri.eo'
    clearGamesForPlayer p for p in [ONE_EMAIL, TWO_EMAIL, THREE_EMAIL]

    createGame ONE_EMAIL, TWO_EMAIL
    createGame ONE_EMAIL, THREE_EMAIL
    createGame THREE_EMAIL, ONE_EMAIL

    assertNumGames = (player, players_turn, players_wait) =>
      createLoginSession player
      @assertNumGames test, players_turn, players_wait

    # player one has two games in which it's her turn, and one other
    assertNumGames ONE_EMAIL, 2, 1
    # player two has no games in which it's her turn, and one other
    assertNumGames TWO_EMAIL, 0, 1
    # player three has one game in which it's her turn, and one other
    assertNumGames THREE_EMAIL, 1, 1

registerTest new StatusTest

class ChallengeTest extends BrowserTest
  names: ['ChallengeTest', 'challenge']
  description: "Tests the 'Challenge a player process"
  numTests: 17
  testBody: (test) =>
  # Be sure not to use the 'createGame' shortcut.
    SHINDOU_EMAIL = 'shindou@ki-in.jp'
    TOUYA_EMAIL = 'touya@ki-in.jp'
    OCHI_EMAIL = 'ochino1@ki-in.jp'

    clearGamesForPlayer p for p in [SHINDOU_EMAIL, TOUYA_EMAIL, OCHI_EMAIL]

    # Shindou opens the front page and follows a link to create a new game
    createLoginSession SHINDOU_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 0, 0

    casper.thenClick '#challenge_link', ->
      form_values = 'input[name="opponent"]' : TOUYA_EMAIL
      # The final 'true' argument means that the form is submitted.
      @fillSelectors 'form#challenge-form', form_values, true

    # both players load the front page and see links to the same game

    shindous_game_link = null
    # Shindou
    casper.waitForSelector '#your_turn_games', =>
      @assertNumGames test, 0, 1
      shindous_game_link = @getLastGameLink false

    ## Touya
    createLoginSession TOUYA_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 0
      touyas_game_link = @getLastGameLink true
      test.assertEqual shindous_game_link, touyas_game_link,
                       "both players see the same game link (target & text)"

    # a third user, Ochi, logs in.  The new game is not on his list.
    createLoginSession OCHI_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 0, 0

registerTest new ChallengeTest


class PlaceStonesTest extends BrowserTest
  names: ['PlaceStonesTest']
  description: "Test Placing Stones"
  numTests: 18
  testBody: (test) =>
    ONE_EMAIL = 'player@one.com'
    TWO_EMAIL = 'playa@dos.es'

    clearGamesForPlayer ONE_EMAIL
    clearGamesForPlayer TWO_EMAIL
    createGame ONE_EMAIL, TWO_EMAIL, ['.b.',
                                      'bw.',
                                      '.b.']
    initialEmptyCount = 19*19-4

    # -- PLAYER ONE
    # player one logs in and gets the front page;
    # should see a page listing games
    createLoginSession ONE_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 0

    # select the most recent game
    casper.thenClick (@lastGameSelector true), =>
      # on the game page is a table with class 'goban'
      test.assertExists '.goban', 'The Go board does exist.'
      # on the game page are 19*19 points, most of which should be empty but
      # there are the initial stones set in 'createGame'
      @assertStonePointCounts test, initialEmptyCount, 3, 1,
        "Black opens the game"
      # no (usable) submit button appears yet
      test.assertDoesntExist '.submit_button:enabled',
                             'no usable submit button appears'

      # the 3x3 block at top left is as we specified
      @assertPointIsEmpty test, 0, 0
      @assertPointIsBlack test, 1, 0
      @assertPointIsEmpty test, 2, 0

      @assertPointIsBlack test, 0, 1
      @assertPointIsWhite test, 1, 1
      @assertPointIsEmpty test, 2, 1

      @assertPointIsEmpty test, 0, 2
      @assertPointIsBlack test, 1, 2
      @assertPointIsEmpty test, 2, 2

registerTest new PlaceStonesTest

class BasicChatTest extends BrowserTest
  names: ['BasicChatTest', 'chat']
  description: "Very basic chat functionality test"
  numTests: 11
  testBody: (test) =>
    ONE_EMAIL = 'player@one.com'
    TWO_EMAIL = 'playa@dos.es'

    MY_CHAT = ['Are you dancing?', 'Are you asking?',
               "I'm asking", "I'm dancing"]

    clearGamesForPlayer ONE_EMAIL
    clearGamesForPlayer TWO_EMAIL
    createGame ONE_EMAIL, TWO_EMAIL

    # -- PLAYER ONE
    # player one logs in and gets the front page;
    # should see a page listing games
    createLoginSession ONE_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 0

    # select the most recent game
    casper.thenClick (@lastGameSelector true), ->
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      form_values = 'input[name="comment"]' : MY_CHAT[0]
      # The final 'true' argument means that the form is submitted.
      @fillSelectors 'form#chat-form', form_values, true
      comments_selector = '.game-chat .chat-comments .chat-comment-black'
      casper.waitForSelector comments_selector

    createLoginSession TWO_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 0, 1

    casper.thenClick (@lastGameSelector false), ->
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      comments_selector = '.game-chat .chat-comments .chat-comment-black'
      test.assertSelectorHasText comments_selector, MY_CHAT[0],
                 "Player one's comment has appeared in the chat area."

      form_values = 'input[name="comment"]' : MY_CHAT[1]
      # The final 'true' argument means that the form is submitted.
      @fillSelectors 'form#chat-form', form_values, true


registerTest new BasicChatTest

class FeedbackTest extends BrowserTest
  names: ['FeedbackTest']
  description: "Tests the feedback mechanism."
  numTests: 2

  testBody: (test) ->
    casper.thenOpen serverUrl, ->
      test.assertExists '#feedback-link'
    casper.thenClick '#feedback-link', ->
      form_values =
        'input[name="feedback_email"]' : 'avid_user@google.com'
        'input[name="feedback_name"]' : 'Avid User'
        'textarea[name="feedback_text"]' : 'I think this site is great.'
      # The final 'true' argument means that the form is submitted.
      @fillSelectors 'form#give-feedback', form_values, true
    casper.then =>
      @check_flashed_message test, 'Thanks for your feedback!', 'info'

registerTest new FeedbackTest

# TODO A test which attempts a XSS attack, the script should be escaped.

class GameInterfaceTest extends BrowserTest
  names: ['GameInterfaceTest', 'game']
  description: "Game interface"
  numTests: 46
  testBody: (test) =>

    ONE_EMAIL = 'player@one.com'
    TWO_EMAIL = 'playa@dos.es'

    clearGamesForPlayer ONE_EMAIL
    clearGamesForPlayer TWO_EMAIL
    createGame ONE_EMAIL, TWO_EMAIL
    createGame ONE_EMAIL, TWO_EMAIL, ['wwb',
                                      'b..']
    initialEmptyCount = 19*19-4

    # -- PLAYER ONE
    # player one logs in and gets the front page; should see a page listing
    # games
    createLoginSession ONE_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 2, 0

    # select the most recent game
    casper.thenClick (@lastGameSelector true), =>
      # on the game page is a table with class 'goban'
      test.assertExists '.goban', 'The Go board does exist.'
      # on the game page are 19*19 points, most of which should be empty but
      # there are the initial stones set in 'createGame'
      @assertStonePointCounts test, initialEmptyCount, 2, 2,
        "initial board layout"
      # check one of those images can be loaded
      test.assertTrue (casper.evaluate ->
        result = false
        $.ajax $('table.goban img').attr('src'),
          'async': false
          'success': -> result = true
        return result), 'an image on the board can be loaded'
      # no (usable) submit button appears yet
      test.assertDoesntExist '.submit_button:enabled',
                             'no usable submit button appears'

    # user clicks an empty spot, which is a link
    casper.thenClick pointSelector(1, 1), =>
      # the board updates to show a stone there and other stones captured
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0,
        "Black places a stone capturing two white stones"
      # a submit button is now available
      test.assertExists '.submit_button:enabled'

    # we click a different point
    casper.thenClick pointSelector(15, 3), =>
      # now the capture is undone
      @assertStonePointCounts test, initialEmptyCount-1, 3, 2,
        "Black clicks another point, capture is undone"
      @assertPointIsEmpty test, 1, 1
      @assertPointIsWhite test, 1, 0

    # we click the capturing point again, as we'll want to see what happens when
    # we submit a capturing move
    casper.thenClick pointSelector(1, 1), =>
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0,
        "Black clicks capture for second time"

    # we submit this new move
    casper.thenClick '.submit_button', =>
      # now we're taken back to the status page
      @assertNumGames test, 1, 1

    # opening the game from 'not your turn' list, Black can no longer
    # place stones
    casper.thenOpen serverUrl
    casper.thenClick (@lastGameSelector false)  # false = not our turn
    casper.thenClick (pointSelector 3, 3), =>
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0,
        "Black attempts to place a stone off-turn"

    # -- PLAYER TWO
    # now the white player logs in and visits the same game
    createLoginSession TWO_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 1

    # It should be the only game in player two's 'your_turn' games
    casper.thenClick (@lastGameSelector true), =>
      # the captured stones are still captured
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0,
        "White opens the board, white stones still captured"

    # clicking the point with a black stone does nothing
    casper.thenClick pointSelector(1, 1), =>
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0,
        "White clicks a black stone, nothing happens"

    # user clicks an empty spot
    casper.thenClick pointSelector(3, 3), =>
      # a white stone is placed, reduces the empty count by 1 and increments
      # the count of white stones
      @assertStonePointCounts test, initialEmptyCount, 3, 1,
        "White clicks an empty point, white stone appears"

    # submit move
    casper.thenClick '.submit_button'
    # reload front page and get the other game
    # (it should be the first listed under 'not your turn')
    casper.thenOpen serverUrl
    casper.thenClick '#not_your_turn_games li:first-child a', =>
      # we should be back to an empty board
      test.assertExists '.goban', 'The Go board still exists.'
      @assertEmptyBoard test

registerTest new GameInterfaceTest


class PassAndScoringTest extends BrowserTest
  names: ['PassAndScoringTest', 'pass', 'score', 'scoring']
  description: "pass moves and scoring system"
  numTests: 62
  testBody: (test) =>
    BLACK_EMAIL = 'black@schwarz.de'
    WHITE_EMAIL = 'white@wit.nl'
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    createGame BLACK_EMAIL, WHITE_EMAIL, ['....b',
                                          'bb.wb',
                                          '...wb',
                                          'wwwwb',
                                          'bbbbb']

    # convenience function
    goToGame = (email, thenFn=(->)) =>
      createLoginSession email
      casper.thenOpen serverUrl
      casper.thenClick (@lastGameSelector true), thenFn  # true = our turn

    # Black passes
    goToGame BLACK_EMAIL
    casper.thenClick '.pass_button'
    # White plays (0,0)
    goToGame WHITE_EMAIL
    casper.thenClick pointSelector(0, 0)
    casper.thenClick '.submit_button'
    # Black opens the game
    goToGame BLACK_EMAIL, =>
      # there are currently no prisoners
      @assertPrisoners test, { black: 0, white: 0 }
    casper.thenClick pointSelector(1, 0), =>
      # the captured white stone is reflected in the prisoner counts
      @assertPrisoners test, { black: 0, white: 1 }
    casper.thenClick '.submit_button'

    # White plays one more stone (to get the game back to the state in which
    # this test was originally written)
    goToGame WHITE_EMAIL
    casper.thenClick pointSelector(3, 0)
    casper.thenClick '.submit_button'

    # black opens the game and passes
    goToGame BLACK_EMAIL
    casper.thenClick '.pass_button'
    # for now we're not defining where the player should end up after passing.
    # navigate back to the game; it should not be our turn and there should no
    # longer be a usable pass button
    casper.thenOpen serverUrl
    casper.thenClick (@lastGameSelector false), ->  # not our turn
      test.assertDoesntExist '.pass_button:enabled'

    # white opens the game and passes
    goToGame WHITE_EMAIL
    casper.thenClick '.pass_button'

    # black opens the game and is invited to mark dead stones
    goToGame BLACK_EMAIL, =>
      test.assertExists '.goban'
      @assertPointIsBlack test, 1, 1
      @assertPointIsEmpty test, 2, 2
      @assertGeneralPointCounts test,
        label: "initial marking layout"
        dame: 5
        black: 3 + 9
        white: 7
        blackscore: 19*19 - 25 + 1
        whitescore: 0
      @assertPrisoners test, black: 0, white: 1
      @assertScores test, black: 19*19 - 25 + 2, white: 0
    # clicking an empty point does nothing
    casper.thenClick (pointSelector 0, 0), =>
      @assertGeneralPointCounts test,
        label: "after clicking empty point"
        empty: 19*19 - 3 - 7 - 9

    # we click the top left black group; the stones change appearance to show
    # they are considered dead, and the scores change
    casper.thenClick (pointSelector 1, 0), =>
      @assertPointIsDeadBlack test, 1, 1
      @assertPointIsWhiteTerritory test, 2, 2
      @assertGeneralPointCounts test,
        label: "black stones marked dead"
        white: 7
        dame: 0
        blackscore: 19*19 - 25
        whitescore: 9
        blackdead: 3
        black: 9
      @assertPrisoners test, black: 3, white: 1
      @assertScores test, black: 19*19 - 25 + 1, white: 12

    # we click the white group; the neighbouring dead black stones are restored
    # automatically
    casper.thenClick (pointSelector 3, 3), =>
      @assertGeneralPointCounts test,
        label: "white stones marked dead"
        black: 12
        blackdead: 0
        white: 0
        whitedead: 7
        dame: 0
        blackscore: 19*19 - 12
        whitescore: 0
    # Black submits this pleasing result
    casper.thenClick '.submit_button'
    # Black then revisits the same game off-turn to bask in the glory of his
    # big win
    casper.thenOpen serverUrl
    casper.thenClick @lastGameSelector(false), =>  # false = not our turn
      # the marks are still the same
      @assertGeneralPointCounts test,
        label: "Black views game off-turn"
        black: 12
        blackdead: 0
        white: 0
        whitedead: 7
        dame: 0
        blackscore: 19*19 - 12
        whitescore: 0
    # Black wonders if the devs remembered to turn off toggling dead stones
    # off-turn
    casper.thenClick pointSelector(3, 3), =>
      # nothing changes
      @assertGeneralPointCounts test,
        label: "Black tries toggling marks off-turn"
        black: 12
        blackdead: 0
        white: 0
        whitedead: 7
        dame: 0
        blackscore: 19*19 - 12
        whitescore: 0

    # White then logs in and opens the game
    goToGame WHITE_EMAIL, =>
      # we are in marking mode and the white stones are already marked dead
      @assertGeneralPointCounts test,
        label: "White views Black's proposal"
        black: 12
        white: 0
        whitedead: 7
        blackscore: 19*19 - 12
    # White prepares a counter-proposal, and sends it back to Black
    casper.thenClick (pointSelector 1, 1)
    casper.thenClick '.submit_button'

    # Black logs in and opens the game
    goToGame BLACK_EMAIL, =>
      # White's proposed dead stones show correctly
      @assertGeneralPointCounts test,
        label: "Black views White's counter-proposal"
        black: 9
        white: 7
        blackdead: 3
    # Black reverts the proposal and submits
    casper.thenClick (pointSelector 3, 1)
    casper.thenClick '.submit_button'

    # seeing the reverted proposal, White resumes play
    goToGame WHITE_EMAIL
    casper.thenClick '.resume_button'

    # White being the last to pass, Black has the turn
    goToGame BLACK_EMAIL
    casper.thenClick (pointSelector 2, 1)
    casper.thenClick '.submit_button'
    # White is ready to give this up
    goToGame WHITE_EMAIL
    casper.thenClick '.pass_button'
    goToGame BLACK_EMAIL
    casper.thenClick '.pass_button'
    goToGame WHITE_EMAIL, =>
      # marked stones have been reverted since the game was resumed
      @assertGeneralPointCounts test,
        label: "White is first to mark stones after resumption"
        black: 4 + 9
        white: 7
    casper.thenClick (pointSelector 3, 0)
    casper.thenClick '.submit_button'
    goToGame BLACK_EMAIL
    # finally, Black accepts White's proposal
    casper.thenClick '.submit_button'

    # game is now finished
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true), "no games on turn"
      test.assertDoesntExist (@lastGameSelector false), "no games off turn"

registerTest new PassAndScoringTest


class ResignTest extends BrowserTest
  names: ['ResignTest', 'resign']
  description: "resignation"
  numTests: 3
  testBody: (test) =>
    BLACK_EMAIL = "quitter@nomo.re"
    WHITE_EMAIL = "recipient@easyw.in"
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    createGame BLACK_EMAIL, WHITE_EMAIL

    # Black opens the game and, tormented by the blank slate, resigns
    createLoginSession BLACK_EMAIL
    casper.thenOpen serverUrl
    casper.thenClick (@lastGameSelector true) # true = our turn
    casper.thenClick '#resign-button', ->
      test.assertVisible '.resign_button'
      casper.thenClick '.resign_button'
    # the game is no longer visible on Black's status page
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true),
        "Black no longer sees the resigned game on his status page"
      test.assertDoesntExist (@lastGameSelector false),
        "it's not in the off-turn games list either"

registerTest new ResignTest


class FinishedGamesTest extends BrowserTest
  names: ['FinishedGamesTest', 'finished', 'fin']
  description: "finished games page"
  numTests: 26
  testBody: (test) =>
    BLACK_EMAIL = "black@black.com"
    WHITE_EMAIL = "white@white.com"
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    setupFinishedGame BLACK_EMAIL, WHITE_EMAIL

    goToGame = (email, thenFn=(->)) =>
      createLoginSession email
      casper.thenOpen serverUrl
      casper.thenClick (@lastGameSelector true), thenFn  # true = our turn

    # mark dead stones and finish game
    goToGame BLACK_EMAIL
    casper.thenClick pointSelector(1, 2)
    casper.thenClick pointSelector(12, 2)
    casper.thenClick pointSelector(7, 7)
    casper.thenClick pointSelector(12, 8)
    casper.thenClick pointSelector(8, 17), =>
      # check scores and board markings to make sure we hit the right
      # points there, and for comparison with test below
      @assertPrisoners test, black: 14, white: 18
      @assertScores test, black: 117, white: 89
      @assertGeneralPointCounts test,
        label: "before submitting dead stones"
        blackdead: 14
        whitedead: 18
        blackscore: 117 - 18
        whitescore: 89 - 14
    casper.thenClick '.submit_button'
    goToGame WHITE_EMAIL
    casper.thenClick '.submit_button'

    casper.thenOpen serverUrl
    casper.thenClick '.finished_games_link', ->
      gamesCount = casper.evaluate -> $('#finished_games li').length
      test.assertEqual gamesCount, 1, "White: exactly one finished game listed"

    # Black logs in and views the finished game
    createLoginSession BLACK_EMAIL
    casper.thenOpen serverUrl
    casper.thenClick '.finished_games_link', ->
      gamesCount = casper.evaluate -> $('#finished_games li').length
      test.assertEqual gamesCount, 1, "Black: exactly one finished game listed"
    casper.thenClick @lastFinishedGameSelector(), =>
      # check scores and board markings are still the same
      @assertPrisoners test, black: 14, white: 18
      @assertScores test, black: 117, white: 89
      @assertGeneralPointCounts test,
        label: "viewing finished game"
        blackdead: 14
        whitedead: 18
        blackscore: 117 - 18
        whitescore: 89 - 14

    # Black clicks a dead stone.  Although it would be Black's turn if the game
    # were still running, nothing happens
    casper.thenClick pointSelector(1, 2), =>
      @assertPrisoners test, black: 14, white: 18
      @assertScores test, black: 117, white: 89
      @assertGeneralPointCounts test,
        label: "Black clicks a dead stone after end of game"
        blackdead: 14
        whitedead: 18
        blackscore: 117 - 18
        whitescore: 89 - 14

registerTest new FinishedGamesTest


# helper functions

deleteUser = (username) ->
  casper.thenOpen "#{serverUrl}/testing_delete_user",
    method: 'post'
    data:
      username: username

clearGamesForPlayer = (email) ->
  casper.thenOpen "#{serverUrl}/testing_clear_games_for_player",
    method: 'post'
    data:
      'email': email

createGame = (black_email, white_email, stones=[]) ->
  casper.thenOpen "#{serverUrl}/testing_create_game",
    method: 'post'
    data:
      'black_email': black_email
      'white_email': white_email
      'stones': JSON.stringify stones

setupFinishedGame = (blackEmail, whiteEmail) ->
  casper.thenOpen "#{serverUrl}/testing_setup_finished_game",
    method: 'post'
    data:
      black_email: blackEmail
      white_email: whiteEmail

createLoginSession = (email) ->
  "Add steps to the stack to create a login session on the server."
  casper.thenOpen "#{serverUrl}/testing_create_login_session",
    method: 'post'
    data:
      'email': email

pointSelector = (x, y) -> ".col-#{x}.row-#{y}"

# run it

if casper.cli.has("single")
  runTest casper.cli.options['single']
else
  runAll()

casper.run ->
  casper.log "shutting down ..."