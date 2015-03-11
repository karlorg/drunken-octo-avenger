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

casper.test.begin 'Test the login procedure', 2, (test) ->
  casper.start serverUrl, ->
    test.assertTitle 'Go', 'The front page title is the one expected'

  casper.thenClick '#persona_login'
  casper.waitForPopup /persona/
  casper.withPopup /persona/, ->
    test.assertTitleMatch /Persona/i, 'Persona login popup has expected title'

  casper.then ->
    test.done()

casper.test.begin "Game interface", 5, (test) ->
  casper.start()

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
    casper.page.addCookie
      'name': name
      'value': value
      'path': path

countStonesAndPoints = ->
  countImgsWith = (name) ->
    casper.evaluate ((name) ->
      allElems = $('table.goban img').toArray()
      allStrs = allElems.map (x) -> $(x).attr 'src'
      matching = allStrs.filter (x) -> x.indexOf(name) > -1
      return matching.length
    ), name
  counts =
    'empty': countImgsWith 'e.gif'
    'black': countImgsWith 'b.gif'
    'white': countImgsWith 'w.gif'
  return counts

# @fill "form[action='/search']", q: "casperjs", true

# casper.then ->
  # aggregate results for the 'casperjs' search
#   links = @evaluate getLinks
  # search for 'phantomjs' from google form
#   @fill "form[action='/search']", q: "phantomjs", true

# casper.then ->
  # concat results for the 'phantomjs' search
#   links = links.concat @evaluate(getLinks)

# casper.run ->
  # display results
#  @echo links.length + " links found:"
#  @echo(" - " + links.join("\n - ")).exit()

casper.run ->
  casper.log "shutting down..."
  casper.open 'http://localhost:5000/shutdown',
    method: 'post'
