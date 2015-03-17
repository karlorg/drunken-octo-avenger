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

# test suites

casper.test.begin 'Test the login procedure', 3, (test) ->
  casper.start serverUrl, ->
    test.assertTitle 'Go', 'The front page title is the one expected'

  casper.thenClick '#persona_login'
  casper.waitForPopup /persona/
  casper.withPopup /persona/, ->
    test.assertTitleMatch /Persona/i, 'Persona login popup has expected title'
    this.sendKeys '#authentication_email', 'test@mockmyid.com'
    this.thenClick 'button:enabled'
    # TODO: finish this.  Clicking this button seems to have an effect (most of
    # the popup window contents vanish), but the onlogin callback registered
    # with navigator.id.watch is never called.

  casper.then () ->
    test.skip 1
    # test.assertExists '#logout'

  casper.then ->
    test.done()

casper.test.begin "Game interface", 23, (test) ->
  casper.start()

  countStonesAndPoints = ->
    counts = casper.evaluate () ->
      goPoints = $('table.goban .gopoint').length
      blackStones = $('.blackstone').length
      whiteStones = $('.whitestone').length
      counts =
        'empty': goPoints - (blackStones + whiteStones)
        'black': blackStones
        'white': whiteStones
      return counts
    return counts

  pointSelector = (x, y) -> ".col-#{x}.row-#{y}"

  test.assertPointIsBlack = (x,y) ->
    test.assertExists pointSelector(x,y) + ".blackstone"
  test.assertPointIsWhite = (x,y) ->
    test.assertExists pointSelector(x,y) + ".whitestone"
  test.assertPointIsEmpty = (x,y) ->
    test.assertExists pointSelector(x,y) + ".nostone"

  ONE_EMAIL = 'player@one.com'
  TWO_EMAIL = 'playa@dos.es'
  # create a couple of games
  clear_games_for_player ONE_EMAIL
  clear_games_for_player TWO_EMAIL
  create_game ONE_EMAIL, TWO_EMAIL
  create_game ONE_EMAIL, TWO_EMAIL

  # -- PLAYER ONE
  # player one logs in and gets the front page; should see a page listing
  # games
  create_login_session ONE_EMAIL
  casper.thenOpen serverUrl, ->
    test.assertExists '#your_turn_games'
    test.assertEqual 2,
                     (casper.evaluate -> $('#your_turn_games a').length),
                     'exactly two games listed'
  # select the most recent game
  casper.thenClick '#your_turn_games li:last-child a', ->
    # on the game page is a table with class 'goban'
    test.assertExists 'table.goban'
    # on the game page are 19x19 imgs representing empty board points
    empty = countStonesAndPoints().empty
    test.assertEqual 19*19, empty, "19x19 empty points on board"
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
  casper.thenClick pointSelector(15, 3), ->
    # now on the board is one black stone and 19x19-1 empty points
    counts = countStonesAndPoints()
    test.assertEquals 19*19-1, counts.empty
    test.assertEquals 1, counts.black
    # a confirm button is now available
    test.assertExists '.confirm_button:enabled'

  # we click a different point, and now our new stone is on that point
  # instead of the previous one
  casper.thenClick pointSelector(15, 2), ->
    counts = countStonesAndPoints()
    test.assertEquals 19*19-1, counts.empty
    test.assertEquals 1, counts.black
    test.assertPointIsEmpty 15, 3
    test.assertPointIsBlack 15, 2

  # we confirm this new move
  casper.thenClick '.confirm_button', ->
    # now we're taken back to the status page
    test.assertExists '#your_turn_games'

  # -- PLAYER TWO
  # now the white player logs in and visits the same game
  create_login_session TWO_EMAIL
  casper.thenOpen serverUrl, ->
    test.assertEqual 1,
                     (casper.evaluate -> $('#your_turn_games a').length),
                     "exactly one game listed in which it's P2's turn"
  casper.thenClick '#your_turn_games a'

  # clicking the point with a black stone does nothing
  casper.thenClick pointSelector(15, 2), ->
    # still one black stone, no white, rest empty
    counts = countStonesAndPoints()
    test.assertEquals 19*19-1, counts.empty
    test.assertEquals 1, counts.black
    test.assertEquals 0, counts.white

  # user clicks an empty spot
  casper.thenClick pointSelector(3, 3), ->
    # now one black stone, one white, rest empty
    counts = countStonesAndPoints()
    test.assertEquals 19*19-2, counts.empty
    test.assertEquals 1, counts.black
    test.assertEquals 1, counts.white

  # confirm move
  casper.thenClick '.confirm_button'
  # reload front page and get the other game
  # (it should be the first listed under 'not your turn')
  casper.thenClick '#not_your_turn_games li:first-child a', ->
    # we should be back to an empty board
    test.assertExists '.goban'
    counts = countStonesAndPoints()
    test.assertEquals 19*19, counts.empty, 'second board empty'

  casper.then ->
    test.done()

# helper functions

clear_games_for_player = (email) ->
  casper.thenOpen "#{serverUrl}/testing_clear_games_for_player",
    method: 'post'
    data:
      'email': email

create_game = (black_email, white_email) ->
  casper.thenOpen "#{serverUrl}/testing_create_game",
    method: 'post'
    data:
      'black_email': black_email
      'white_email': white_email

create_login_session = (email) ->
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

casper.run ->
  casper.log "shutting down..."
  casper.open 'http://localhost:5000/shutdown',
    method: 'post'
