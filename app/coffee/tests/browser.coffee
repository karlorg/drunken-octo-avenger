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

runAll = ->
  for test in allTestObjects
    test.run()

# test suites
class BrowserTest
  # An abstract base class for our browser tests
  #
  # Instances should define the following properties:
  #
  # * test_body: called by `run` below to execute the test
  # * names: array of names by which a caller can identify this test (with the
  #          `--single` command line option)
  # * description
  # * num_tests: expected number of assertions

  run: =>
    casper.test.begin @description, @num_tests, (test) =>
      casper.start()
      @test_body(test)
      casper.then ->
        test.done()

  names: []
  description: 'This class needs a description'
  num_tests: 0

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

  assertEmptyBoard: (test) =>
    @assertStonePointCounts test, 19*19, 0, 0

  assertPointIsBlack: (test, x, y) ->
    test.assertExists pointSelector(x,y) + ".blackstone",
                      'There is a black stone at the expected point'

  assertPointIsWhite: (test, x, y) ->
    test.assertExists pointSelector(x,y) + ".whitestone",
                      'There is a white stone at the expected point'

  assertPointIsEmpty: (test, x, y) ->
    test.assertExists pointSelector(x,y) + ".nostone",
                      'The specified point is empty as expected'

  countStonesAndPoints: ->
    counts = casper.evaluate () ->
      emptyStones = $('.goban .nostone').length
      blackStones = $('.goban .blackstone').length
      whiteStones = $('.goban .whitestone').length
      counts =
        'empty': emptyStones
        'black': blackStones
        'white': whiteStones
      return counts
    return counts
  assertStonePointCounts: (test, nostone, black, white) =>
    counts = @countStonesAndPoints()
    test.assertEqual counts.empty, nostone, 'Expected number of empty points'
    test.assertEqual counts.black, black, 'Expected number of black stones'
    test.assertEqual counts.white, white, 'Expected number of white stones'


class ClientSideJsTest extends BrowserTest
  names: ['ClientSideJsTest', 'qunit']
  description: "Run client-side JS tests and ensure they pass."
  num_tests: 1
  test_body: (test) ->
    casper.thenOpen serverUrl + "/static/tests/tests.html", ->
      predicate = ->
        (casper.exists '.qunit-pass') or (casper.exists '.qunit-fail')
      foundFunc = ->
        if casper.exists '.qunit-pass'
          test.pass 'Qunit tests passed'
        else if casper.exists '.qunit-fail'
          test.fail 'Qunit tests failed'
      timeoutFunc = -> test.fail "Couldn't detect pass or fail for Qunit tests"
      casper.waitFor predicate, foundFunc, timeoutFunc, 5000

registerTest new ClientSideJsTest


class LoginTest extends BrowserTest
  names: ['LoginTest', 'login']
  description: 'Test the login procedure'
  num_tests: 3
  test_body: (test) ->
    casper.thenOpen serverUrl, ->
      test.assertTitle 'Go', 'The front page title is the one expected'

    casper.thenClick '#persona_login'
    casper.waitForPopup /persona/
    casper.withPopup /persona/, ->
      test.assertTitleMatch /Persona/i, 'Persona login popup has expected title'
      this.sendKeys '#authentication_email', 'test@mockmyid.com'
      this.thenClick 'button:enabled'
      # TODO: finish this.  Clicking this button seems to have an effect
      # (most of the popup window contents vanish), but the onlogin callback
      # registered with navigator.id.watch is never called.

    casper.then () ->
      test.skip 1
      # test.assertExists '#logout'

registerTest new LoginTest

class StatusTest extends BrowserTest
  names: ['StatusTest', 'status']
  description: 'Test the status listings'
  num_tests: 12
  test_body: (test) =>
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
  num_tests: 17
  test_body: (test) =>
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
      form_values = 'input[name="opponent_email"]' : TOUYA_EMAIL
      # The final 'true' argument means that the form is submitted.
      @fillSelectors 'form', form_values, true

    # both players load the front page and see links to the same game

    shindous_game_link = null
    # Shindou
    casper.thenOpen serverUrl, =>
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
  num_tests: 18
  test_body: (test) =>
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
      test.assertExists 'table.goban', 'The Go board does exist.'
      # on the game page are 19*19 points, most of which should be empty but
      # there are the initial stones set in 'createGame'
      @assertStonePointCounts test, initialEmptyCount, 3, 1
      # no (usable) confirm button appears yet
      test.assertDoesntExist '.confirm_button:enabled',
                             'no usable confirm button appears'

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

class GameInterfaceTest extends BrowserTest
  names: ['GameInterfaceTest', 'game']
  description: "Game interface"
  num_tests: 43
  test_body: (test) =>

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
      test.assertExists 'table.goban', 'The Go board does exist.'
      # on the game page are 19*19 points, most of which should be empty but
      # there are the initial stones set in 'createGame'
      @assertStonePointCounts test, initialEmptyCount, 2, 2
      # check one of those images can be loaded
      test.assertTrue (casper.evaluate ->
        result = false
        $.ajax $('table.goban img').attr('src'),
          'async': false
          'success': -> result = true
        return result), 'an image on the board can be loaded'
      # no (usable) confirm button appears yet
      test.assertDoesntExist '.confirm_button:enabled',
                             'no usable confirm button appears'

    # user clicks an empty spot, which is a link
    casper.thenClick pointSelector(1, 1), =>
      # the board updates to show a stone there and other stones captured
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0
      # a confirm button is now available
      test.assertExists '.confirm_button:enabled'

    # we click a different point
    casper.thenClick pointSelector(15, 3), =>
      # now the capture is undone
      @assertStonePointCounts test, initialEmptyCount-1, 3, 2
      @assertPointIsEmpty test, 1, 1
      @assertPointIsWhite test, 1, 0

    # we click the capturing point again, as we'll want to see what happens when
    # we confirm a capturing move
    casper.thenClick pointSelector(1, 1), =>
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0

    # we confirm this new move
    casper.thenClick '.confirm_button', =>
      # now we're taken back to the status page
      @assertNumGames test, 1, 1

    # -- PLAYER TWO
    # now the white player logs in and visits the same game
    createLoginSession TWO_EMAIL
    casper.thenOpen serverUrl, =>
      @assertNumGames test, 1, 1

    # It should be the only game in player two's 'your_turn' games
    casper.thenClick (@lastGameSelector true), =>
      # the captured stones are still captured
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0

    # clicking the point with a black stone does nothing
    casper.thenClick pointSelector(1, 1), =>
      @assertStonePointCounts test, initialEmptyCount+1, 3, 0

    # user clicks an empty spot
    casper.thenClick pointSelector(3, 3), =>
      # a white stone is placed, reduces the empty count by 1 and increments
      # the count of white stones
      @assertStonePointCounts test, initialEmptyCount, 3, 1

    # confirm move
    casper.thenClick '.confirm_button'
    # reload front page and get the other game
    # (it should be the first listed under 'not your turn')
    casper.thenClick '#not_your_turn_games li:first-child a', =>
      # we should be back to an empty board
      test.assertExists '.goban', 'The Go board still exists.'
      @assertEmptyBoard test

registerTest new GameInterfaceTest


# helper functions

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

createLoginSession = (email) ->
  "Add steps to the stack to create a login session on the server and set its
  cookie in the browser."
  casper.thenOpen "#{serverUrl}/testing_create_login_session",
    method: 'post'
    data:
      'email': email
  casper.then ->
    content = casper.getPageContent()
    [name, value, path] = content.split '\n'
    casper.page.clearCookies()
    casper.page.addCookie
      'name': name
      'value': value
      'path': path

pointSelector = (x, y) -> ".col-#{x}.row-#{y}"

# run it

if casper.cli.has("single")
  runTest casper.cli.options['single']
else
  runAll()

casper.run ->
  casper.log "shutting down..."
  casper.open 'http://localhost:5000/shutdown',
    method: 'post'
