# compute server url from arguments

fs = require('fs')

logFileName = 'generated/casper_tests.log'

do ->
  oldLog = casper.log
  casper.log = (message, level, space) ->
    mySpace = space or ""
    fs.write logFileName, "[#{level}] [#{mySpace}] #{message}\n", "a"
    oldLog.call this, message, level, space

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

  gameSelector: (div_id, first_or_last) ->
    return "\##{div_id} .game-list-row:#{first_or_last}-child td a"


  lastFinishedGameSelector: ->
    @gameSelector 'finished_games', 'last'

  statusGameSelector: (your_turn, first_or_last) ->
    div_id = if your_turn then 'your_turn_games' else 'not_your_turn_games'
    @gameSelector div_id, first_or_last

  firstGameSelector: (your_turn) ->
    @statusGameSelector your_turn, 'first'

  lastGameSelector: (your_turn) ->
    @statusGameSelector your_turn, 'last'

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

  registerNewAccount: (username, password, repeat=password) ->
      casper.fill 'form#new_account_form', {
        username: username
        password1: password
        password2: repeat
        }, true  # true = submit form

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
    casper.thenClick '#new_account', =>
      @registerNewAccount 'darrenlamb', 'iknowandy', 'imdarrenlamb'

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
    casper.then =>
      @registerNewAccount 'darrenlamb', 'iknowandy'

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


class UserListTest extends BrowserTest
  names: ['UserListTest', 'users']
  description: "Tests the lists of users, user profiles, and challenge links"
  numTests: 15

  testBody: (test) =>
    allan = "allanxlkadsf9120293"
    karl = "karlasdlkjsad0f932"
    batman = "batmanlkasjdfwa0932"

    deleteUser allan
    deleteUser karl
    deleteUser batman
    clearGamesForPlayer p for p in [allan, karl, batman]

    # allan

    casper.thenOpen serverUrl, ->
      if casper.exists '#logout'
        casper.click '#logout'
      casper.waitForSelector '#new_account', ->
        test.assertExists '#new_account'
    casper.thenClick '#new_account', =>
      @registerNewAccount allan, 'insecure'
      casper.waitForSelector '#logout'
    casper.thenClick '#logout'
    casper.thenClick '#new_account', =>
      @registerNewAccount karl, 'alsoinsecure'
    casper.thenClick '#logout'
    casper.thenClick '#new_account', =>
      @registerNewAccount batman, 'LKJ;lkjaskasdflkew932qa2oir3laksdj'

    casper.thenClick '#user-list-link', =>
      # Batman should be able to see all three users.
      for name in [allan, karl, batman]
        test.assertExists ".user-profile-link[data-username=\"#{name}\"]"
    # Now batman is going to challenge karl to a match
    casper.thenClick ".user-challenge-link[data-username=\"#{karl}\"]", =>
      test.assertSelectorHasText \
        'form#challenge-form input[name="opponent"]', karl
    casper.thenClick '#send_challenge', =>
      casper.waitForSelector '#your_turn_games'
      @assertNumGames test, 0, 1
    # Now he goes back to the user list and check's out allan's profile page,
    # also starting a game against allan.
    casper.thenClick '#user-list-link', =>
      casper.thenClick ".user-profile-link[data-username=\"#{allan}\"]", =>
        test.assertSelectorHasText '.user-profile-title', allan
    casper.thenClick '.user-challenge-link', =>
      test.assertSelectorHasText \
        'form#challenge-form input[name="opponent"]', allan
    casper.thenClick '#send_challenge', =>
      casper.waitForSelector '#your_turn_games', =>
      @assertNumGames test, 0, 2

registerTest new UserListTest


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
  names: ['PlaceStonesTest', 'place']
  description: "Test Placing Stones"
  numTests: 19
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
      test.assertDoesntExist '.submit_and_next_game_button:enabled',
                             'no usable submit (-> next game) button appears'

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
  numTests: 27

  testBody: (test) =>
    addComment = (comment) ->
      form_values = 'input[name="comment"]' : comment
      # The final 'true' argument means that the form is submitted.
      casper.fillSelectors 'form#chat-form', form_values, true

    checkComment = (color, comment, testMessage) ->
      casper.waitForText comment, ->
        comments_selector = ".game-chat .chat-comments .chat-comment-#{color}"
        test.assertSelectorHasText comments_selector, comment, testMessage

    ONE_EMAIL = 'player@one.com'
    TWO_EMAIL = 'playa@dos.es'

    ONE_CHAT = ['Are you dancing?', "I'm asking"]
    TWO_CHAT =  ['Are you asking?', "I'm dancing"]

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
    casper.thenClick (@lastGameSelector true), =>
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      addComment ONE_CHAT[0], true
      checkComment 'black', ONE_CHAT[0], 'Black sees their own first comment'

    createLoginSession TWO_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 0, 1

    casper.thenClick (@lastGameSelector false), =>
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      checkComment 'black', ONE_CHAT[0], "White sees black's first comment."
      addComment TWO_CHAT[0], true
      checkComment 'white', TWO_CHAT[0], "White sees their own first comment."

    # Back to player one.
    createLoginSession ONE_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 0

    # select the most recent game
    casper.thenClick (@lastGameSelector true), =>
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      checkComment 'white', TWO_CHAT[0], "Black sees white's first comment."
      addComment ONE_CHAT[1], true
      checkComment 'black', ONE_CHAT[1], "Black sees their own second comment."

    # And back to player 2.
    createLoginSession TWO_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 0, 1

    # select the most recent game
    casper.thenClick (@lastGameSelector false), =>
      # on the game page is a game chat.
      test.assertExists '.game-chat', 'The game chat does exist.'
      checkComment 'black', ONE_CHAT[1], "White sees black's second comment."
      addComment TWO_CHAT[1], true
      checkComment 'white', TWO_CHAT[1], "White sees their own second comment."

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
    casper.thenClick @statusGameSelector(false, 'first'), =>
      # we should be back to an empty board
      test.assertExists '.goban', 'The Go board still exists.'
      @assertEmptyBoard test

registerTest new GameInterfaceTest


class SubmitAndNextGameTest extends BrowserTest
  names: ['SubmitAndNextGameTest', 'nextgame']
  description: "'Submit and go to next game' button"
  numTests: 0
  testBody: (test) =>
    EMAILS = ['hero@zero.com',
              'player@one.com',
              'playa@dos.es',
              'plagxo@tri.eo']
    [HERO, P1, P2, P3] = EMAILS
    clearGamesForPlayer p for p in EMAILS
    createGame HERO, P1
    createGame P2, HERO
    createGame P3, HERO

    # convenience function
    goToGame = (email, thenFn=(->)) =>
      createLoginSession email
      casper.thenOpen serverUrl
      casper.thenClick (@lastGameSelector true), thenFn  # true = our turn

    goToHeroFirstGame = (thenFn=(->)) =>
      createLoginSession HERO
      casper.thenOpen serverUrl
      casper.thenClick (@firstGameSelector true), thenFn

    # two makes a move, then shortly after, three makes a move
    goToGame P2
    casper.thenClick (pointSelector 3, 3)
    casper.thenClick '.submit_button'
    casper.wait 50
    goToGame P3
    casper.thenClick (pointSelector 3, 3)
    casper.thenClick '.submit_button'
    # now when hero moves against P1...
    goToHeroFirstGame()
    casper.thenClick (pointSelector 3, 3)
    casper.thenClick '.submit_and_next_game_button', ->
      # she lands on the game against P2, who moved least recently
      test.assertSelectorHasText '#match-info', P2,
        "hero lands on P2's game after playing a move against P1"

    # hero moves in P2 and P3's games, and P1 moves in his game,
    # leaving the same players to play as when we started
    casper.thenClick (pointSelector 15, 15)
    casper.thenClick '.submit_and_next_game_button', ->
      test.assertSelectorHasText '#match-info', P3,
        "hero lands on P3's game after playing a move against P2"
    casper.thenClick (pointSelector 15, 15)
    casper.thenClick '.submit_and_next_game_button'
    goToGame P1
    casper.thenClick (pointSelector 15, 15)
    casper.thenClick '.submit_and_next_game_button'

    # this time P3 and P2 move in the opposite order:
    # three makes a move, then shortly after, two makes a move
    goToGame P3
    casper.thenClick (pointSelector 9, 9)
    casper.thenClick '.submit_button'
    casper.wait 50
    goToGame P2
    casper.thenClick (pointSelector 9, 9)
    casper.thenClick '.submit_button'
    # now when hero moves against P1...
    goToHeroFirstGame()
    casper.thenClick (pointSelector 9, 9)
    casper.thenClick '.submit_and_next_game_button', ->
      # she lands on the game against P3, who moved least recently
      test.assertSelectorHasText '#match-info', P3,
        "hero lands on P3's game after playing a move against P1"

    # and after moving against P3 and P2...
    casper.thenClick (pointSelector 4, 15)
    casper.thenClick '.submit_and_next_game_button', ->
      test.assertSelectorHasText '#match-info', P2
    casper.thenClick (pointSelector 4, 15)
    casper.thenClick '.submit_and_next_game_button', ->
      # she lands back at the status page as no games are pending
      test.assertExists '#your_turn_games',
        "hero lands on status page after playing a move against P2"

registerTest new SubmitAndNextGameTest


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
    goToGame BLACK_EMAIL, ->
      formTarget = casper.getElementAttribute '#main_form', 'action'
      casper.log "main form will post to #{formTarget}", "debug"
    # finally, Black accepts White's proposal
    casper.thenClick '.submit_button'
    casper.then ->
      casper.log "submit clicked", "debug"

    # game is now finished
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true), "no games on turn"
      test.assertDoesntExist (@lastGameSelector false), "no games off turn"

registerTest new PassAndScoringTest


class ResignTest extends BrowserTest
  names: ['ResignTest', 'resign']
  description: "resignation"
  numTests: 9
  testBody: (test) =>
    BLACK_EMAIL = "quitter@nomo.re"
    WHITE_EMAIL = "recipient@easyw.in"
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    createGame BLACK_EMAIL, WHITE_EMAIL

    casper.thenOpen serverUrl + "/logout"
    casper.thenClick '#new_account', =>
      @registerNewAccount BLACK_EMAIL, 'password'
    casper.waitForSelector '#logout', ->
      casper.click '#logout'

    casper.thenOpen serverUrl
    casper.thenClick '#new_account', =>
      @registerNewAccount WHITE_EMAIL, 'password'


    # Black opens the game and, tormented by the blank slate, resigns
    createLoginSession BLACK_EMAIL
    casper.thenOpen serverUrl
    casper.thenClick (@lastGameSelector true) # true = our turn
    casper.then ->
      # log the form's POST target in case of random test failure
      formTarget = casper.getElementAttribute '#main_form', 'action'
      casper.log "main form will post to #{formTarget}", "debug"
    casper.thenClick '#resign-button'  # Click the resign button
    casper.waitUntilVisible '.confirm-resign-button', ->
      test.assertVisible '.confirm-resign-button'
      casper.thenClick '.confirm-resign-button'

    # the game is no longer visible on Black's status page
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true),
        "Black no longer sees the resigned game on his status page"
      test.assertDoesntExist (@lastGameSelector false),
        "it's not in the off-turn games list either"

    # But it is visible on Black's finished games list:
    casper.thenOpen serverUrl
    casper.thenClick '.finished_games_link', ->
      gamesCount = casper.evaluate -> $('#finished_games .game-list-row').length
      test.assertEqual gamesCount, 1, "White: exactly one finished game listed"
      test.assertSelectorHasText '.game-list-row', 'White (resignation)',
        'Check that the White win by resignation is in the finished games list'
    casper.thenClick (@lastFinishedGameSelector()), ->
      test.assertSelectorHasText '#game-result-summary',
        'White won by resignation',
        'The game displays the result summary correctly.'

    # White logs in an is greated by a notification that they have won a game
    createLoginSession WHITE_EMAIL
    casper.thenOpen serverUrl, ->
      casper.waitForSelector '.unread.notification'
      test.assertSelectorHasText '.unread.notification',
        'Your game has ended, white won by resignation.',
        'Check that white has an unread notification'

    casper.thenClick '.unread.notification .game-link', ->
      test.assertSelectorHasText '#game-result-summary',
        'White won by resignation',
        'White also sees the correct game result summary within the game.'
    casper.thenOpen serverUrl, ->
      casper.click '.unread.notification .mark-as-read'
    casper.thenOpen serverUrl, ->
      test.assertDoesntExist '.unread.notification'

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
    goToGame WHITE_EMAIL, ->
      formTarget = casper.getElementAttribute '#main_form', 'action'
      casper.log "main form will post to #{formTarget}", "debug"
    casper.thenClick '.submit_button'

    casper.thenOpen serverUrl
    casper.thenClick '.finished_games_link', ->
      gamesCount = casper.evaluate -> $('#finished_games .game-list-row').length
      test.assertEqual gamesCount, 1, "White: exactly one finished game listed"

    # Black logs in and views the finished game
    createLoginSession BLACK_EMAIL
    casper.thenOpen serverUrl
    casper.thenClick '.finished_games_link', ->
      gamesCount = casper.evaluate -> $('#finished_games .game-list-row').length
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
  casper.exit()
