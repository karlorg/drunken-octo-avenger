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
    casper.evaluate ((x, y) -> $(".row-#{y}.col-#{x} img").attr('src')),
      x, y

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
    casper.evaluate ->
      'empty':      $('.goban .nostone').length
      'black':      $('.goban .blackstone').length
      'white':      $('.goban .whitestone').length
      'blackscore': $('.goban .blackscore').length
      'whitescore': $('.goban .whitescore').length
      'blackdead':  $('.goban .blackdead').length
      'whitedead':  $('.goban .whitedead').length
      'noscore':    $('.goban td:not(.blackscore):not(.whitescore)').length

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

  assertStonePointCounts: (test, nostone, black, white) =>
    counts = @countStonesAndPoints()
    @assertGeneralPointCounts test,
      'empty': nostone
      'black': black
      'white': white

  assertEmptyBoard: (test) =>
    @assertStonePointCounts test, 19*19, 0, 0


class ClientSideJsTest extends BrowserTest
  names: ['ClientSideJsTest', 'qunit', 'client']
  description: "Run client-side JS tests and ensure they pass."
  numTests: 1
  testBody: (test) ->
    casper.thenOpen serverUrl + "/static/tests/tests.html", ->
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


class LoginTest extends BrowserTest
  names: ['LoginTest', 'login']
  description: 'Test the login procedure'
  numTests: 3
  testBody: (test) ->
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
  numTests: 43
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


class PassAndScoringTest extends BrowserTest
  names: ['PassAndScoringTest', 'pass', 'score', 'scoring']
  description: "pass moves and scoring system"
  numTests: 29
  testBody: (test) =>
    BLACK_EMAIL = 'black@schwarz.de'
    WHITE_EMAIL = 'white@wit.nl'
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    createGame BLACK_EMAIL, WHITE_EMAIL, ['.b.wb',
                                          'bb.wb',
                                          '...wb',
                                          'wwwwb',
                                          'bbbbb']

    # convenience function
    goToGame = (email, thenFn=(->)) =>
      createLoginSession email
      casper.thenOpen serverUrl
      casper.thenClick (@lastGameSelector true), thenFn  # true = our turn

    # black opens the game and passes
    # (it should be black's turn since there are no actual moves in this game,
    # only setup stones)
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
    originalImageSrc11 = null
    originalImageSrc22 = null
    goToGame BLACK_EMAIL, =>
      test.assertExists 'table.goban'
      originalImageSrc11 = @imageSrc 1, 1
      originalImageSrc22 = @imageSrc 2, 2
      @assertGeneralPointCounts test,
        label: "initial marking layout"
        noscore: 3 + 5 + 7 + 9  # black group, dame, white group, black group
        blackscore: 19*19 - 25 + 1
        whitescore: 0
    # clicking an empty point does nothing
    casper.thenClick (pointSelector 0, 0), =>
      @assertGeneralPointCounts test,
        label: "after clicking empty point"
        empty: 19*19 - 3 - 7 - 9

    # we click the top left black group; the stones change appearance to show
    # they are considered dead, and the scores change
    casper.thenClick (pointSelector 1, 0), =>
      imageSrc11 = @imageSrc 1, 1
      test.assertNotEquals imageSrc11, originalImageSrc11,
        "black stone image source is not still #{originalImageSrc11}"
      imageSrc22 = @imageSrc 2, 2
      test.assertNotEquals imageSrc22, originalImageSrc22,
        "empty point image source is not still #{originalImageSrc22}"
      @assertGeneralPointCounts test,
        label: "black stones marked dead"
        noscore: 7 + 9  # just white and black stones at the border
        blackscore: 19*19 - 25
        whitescore: 9
        blackdead: 3
        black: 9

    # we click the white group; the neighbouring dead black stones are restored
    # automatically
    casper.thenClick (pointSelector 3, 3), =>
      @assertGeneralPointCounts test,
        label: "white stones marked dead"
        black: 12
        blackdead: 0
        noscore: 12
        blackscore: 19*19 - 12
        whitescore: 0
    # Black confirms this pleasing result
    casper.thenClick '.confirm_button'

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
    casper.thenClick '.confirm_button'

    # Black logs in and opens the game
    goToGame BLACK_EMAIL, =>
      # White's proposed dead stones show correctly
      @assertGeneralPointCounts test,
        label: "Black views White's counter-proposal"
        black: 9
        white: 7
        blackdead: 3
    # Black reverts the proposal and confirms
    casper.thenClick (pointSelector 3, 1)
    casper.thenClick '.confirm_button'

    # seeing the reverted proposal, White resumes play
    goToGame WHITE_EMAIL
    casper.thenClick '.resume_button'

    # White being the last to pass, Black has the turn
    goToGame BLACK_EMAIL
    casper.thenClick (pointSelector 2, 1)
    casper.thenClick '.confirm_button'
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
    casper.thenClick '.confirm_button'
    goToGame BLACK_EMAIL
    # finally, Black accepts White's proposal
    casper.thenClick '.confirm_button'

    # game is now finished
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true)
      test.assertDoesntExist (@lastGameSelector false)

    # TODO: add ability to view finished games, verify scores, winner etc.

registerTest new PassAndScoringTest


class ResignTest extends BrowserTest
  names: ['ResignTest', 'resign']
  description: "resignation"
  numTests: 2
  testBody: (test) =>
    BLACK_EMAIL = "quitter@nomo.re"
    WHITE_EMAIL = "recipient@easyw.in"
    clearGamesForPlayer p for p in [BLACK_EMAIL, WHITE_EMAIL]
    createGame BLACK_EMAIL, WHITE_EMAIL

    # Black opens the game and, tormented by the blank slate, resigns
    createLoginSession BLACK_EMAIL
    casper.thenOpen serverUrl
    casper.thenClick (@lastGameSelector true)  # true = our turn
    casper.thenClick '.resign_button'
    # the game is no longer visible on Black's status page
    casper.thenOpen serverUrl, =>
      test.assertDoesntExist (@lastGameSelector true),
        "Black no longer sees the resigned game on his status page"
      test.assertDoesntExist (@lastGameSelector false),
        "it's not in the off-turn games list either"

registerTest new ResignTest


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
  casper.log "shutting down..."
  casper.open 'http://localhost:5000/shutdown',
    method: 'post'
