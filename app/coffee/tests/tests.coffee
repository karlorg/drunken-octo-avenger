# helpers

$pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
imageSrc = ($point) -> $point.find('img').attr('src')

contains_selector = tesuji_charm.game_common.contains_selector

isPointEmpty = ($point) -> not(contains_selector $point, '.stone,.territory')
isPointBlack = ($point) -> contains_selector $point, '.stone.black'
isPointWhite = ($point) -> contains_selector $point, '.stone.white'
isPointBlackScore = ($point) ->
  (contains_selector $point, '.territory.black') and
  (not (contains_selector $point, '.territory.white'))
isPointWhiteScore = ($point) ->
  (contains_selector $point, '.territory.white') and
  (not (contains_selector $point, '.territory.black'))
isPointDame = ($point) ->
  contains_selector $point, '.territory.neutral'
isPointBlackDead = ($point) -> contains_selector $point, '.stone.black.dead'
isPointWhiteDead = ($point) -> contains_selector $point, '.stone.white.dead'
isPointLastPlayed = ($point) -> contains_selector $point, '.last-played'


# ============================================================================


module 'Persona'

test 'init function sets request and logout callbacks', ->
  requestCalled = false
  logoutCalled = false
  watchCalled = false
  mockNavigator =
    id:
      logout: -> logoutCalled = true
      request: -> requestCalled = true
      watch: (params) ->
        p_user = params.loggedInUser
        t_user = tesuji_charm.currentPersonaEmail
        ok(
          (t_user == '' and p_user == null) or
          (t_user != '' and p_user == t_user),
            'navigator.id.watch passed good loggedInUser')
        ok typeof params.onlogin is 'function',
          'navigator.id.watch passed function for onlogin'
        ok typeof params.onlogout is 'function',
          'navigator.id.watch passed function for onlogout'
        watchCalled = true
  # main test sequence begins here
  equal watchCalled, false
  tesuji_charm.currentPersonaEmail = ''
  tesuji_charm.persona.initialize mockNavigator
  equal watchCalled, true, 'navigator.id.watch called'
  tesuji_charm.currentPersonaEmail = 'bob@example.com'
  tesuji_charm.persona.initialize mockNavigator

  equal requestCalled, false
  equal logoutCalled, false
  $('#persona_login').click()
  equal requestCalled, true, 'login request called correctly'
  equal logoutCalled, false
  $('#logout').click()
  equal logoutCalled, true, 'logout callback called correctly'

test 'logout callback not set when not logged in with Persona', ->
  logoutCalled = false
  mockNavigator =
    id:
      logout: -> logoutCalled = true
      request: ->
      watch : ->
  tesuji_charm.currentPersonaEmail = ''
  tesuji_charm.persona.initialize mockNavigator

  $('#logout').click()
  equal logoutCalled, false


# ============================================================================

# helpers for game page tests

setInputSgf = (sgf) -> $('input#data').val sgf
getResponseSgf = -> $('input#response').val()

QUnit.assert.prisonerCounts = (black, white, message = null) ->
  message = if message then "#{message}: " else ''
  actualBlack = $('.prisoners.black').text()
  @equal parseInt(actualBlack, 10), black,
    "#{message}Black prisoners should be #{black}, is #{actualBlack}"
  actualWhite = $('.prisoners.white').text()
  @equal parseInt(actualWhite, 10), white,
    "#{message}White prisoners should be #{white}, is #{actualWhite}"

QUnit.assert.scores = (black, white, message = null) ->
  message = if message then "#{message}: " else ''
  actualBlack = $('.score.black').text()
  @equal parseInt(actualBlack, 10), black,
    "#{message}Black score should be #{black}, is #{actualBlack}"
  actualWhite = $('.score.white').text()
  @equal parseInt(actualWhite, 10), white,
    "#{message}White score should be #{white}, is #{actualWhite}"

# ============================================================================

module "helper function for testing"

boardFromChars = (chars2d) ->
  "Produce a board state from a character-based shorthand.

  eg. ['.b.', 'bw.', '.b.']"
  for row in chars2d
    for char in row
      switch char
        when 'b' then 'black'
        when 'w' then 'white'
        else 'empty'

test "test of testing helper function boardFromChars", (assert) ->
  assert.deepEqual (boardFromChars ['.b.', 'bw.', '.b.']),
                   [['empty', 'black', 'empty']
                    ['black', 'white', 'empty']
                    ['empty', 'black', 'empty']]

# ============================================================================

module "common game page functions",
  setup: ->
    setInputSgf ''
    tesuji_charm.game_common.initialize()

QUnit.assert.boardState = (chars2d, message) ->
  expected = boardFromChars chars2d
  actual = tesuji_charm.game_common.readBoardState()
  result = true
  for row, j in expected
    for point, i in row
      (result = false) if actual[j][i] != point
  @push result, actual, expected, (message or "")

setViewMoveNo = (n) ->
  $select = $('.move_select')
  $select.val(n).trigger 'input'
  return

test "helper function readBoardState and assert.boardState", (assert) ->
  # readBoardState is invoked by the boardState assert
  setInputSgf '(;SZ[3];B[ca];W[bc])'
  tesuji_charm.game_common.initialize()
  assert.boardState ['..b'
                     '...'
                     '.w.']


test "initialize creates board from SGF data", (assert) ->
  setInputSgf '(;SZ[3];B[ca];W[bc])'
  tesuji_charm.game_common.initialize()
  assert.equal $('.goban').length, 1, "exactly one goban element exists"
  assert.ok isPointEmpty($pointAt 0, 0), "(0,0) empty"
  assert.ok isPointBlack($pointAt 2, 0), "(2,0) black"
  assert.ok isPointWhite($pointAt 1, 2), "(1,2) white"
  assert.ok $('.row-2.col-2').length == 1, "board is at least 3x3"
  assert.ok $('.row-3.col-3').length == 0, "board is smaller than 4x4"

test "setup stones in SGF (tags AB & AW)", (assert) ->
  # ensure we test both a list of setup stones (AB here) and a single
  # setup stone (AW here) since the smartgame library produces an
  # array for one and a single value for the other
  setInputSgf '(;SZ[3];AB[ba][ab][bc]AW[bb])'
  tesuji_charm.game_common.initialize()
  assert.boardState ['.b.'
                     'bw.'
                     '.b.']

test "prisoner counts set from SGF", (assert) ->
  testSgf = (sgf, black, white) ->
    setInputSgf sgf
    tesuji_charm.game_common.initialize()
    assert.prisonerCounts(black, white)

  testSgf '(;SZ[3];AW[ab]B[aa])', 0, 0
  # regression: score elements are not duplicated
  testSgf '(;SZ[3];AW[ab]B[aa])', 0, 0
  assert.equal $('.prisoners.black').length, 1,
    "only one black prisoner element"
  testSgf '(;SZ[3];AW[ab]B[aa];W[ba])', 1, 0
  testSgf '(;SZ[3];AW[aa]AB[ba]B[ab])', 0, 1

test "can view past board states", (assert) ->
  setInputSgf '(;SZ[3];AB[aa]B[ac];W[ab];B[bb];W[ca])'
  tesuji_charm.game_common.initialize()
  assert.boardState ['b.w'
                     '.b.'
                     'b..'], "initial board state"

  setViewMoveNo 0
  assert.boardState ['...', '...', '...'], "board state at move 0"
  assert.notOk $('.last-played').length, "no last-move marker on move 0"

  setViewMoveNo 2
  assert.boardState ['b..', 'w..', 'b..'], "board state at move 2"
  assert.equal $('.last-played').length, 1, "exactly one last-move marker"
  assert.ok $('.col-0.row-1').find('.last-played').length,
    "last-move marker is at (0,1)"

  setViewMoveNo 3
  assert.boardState ['b..', '.b.', 'b..'], "board state at move 3"
  assert.equal $('.last-played').length, 1, "exactly one last-move marker"
  assert.ok $('.col-1.row-1').find('.last-played').length,
    "last-move marker is at (1,1)"


# ============================================================================


module 'Basic game page',
  setup: ->
    setInputSgf '(;SZ[3])'
    $('input#response').val ''
    tesuji_charm.onTurn = true
    tesuji_charm.game_basic.initialize()

  afterEach: ->
    tesuji_charm.game_common.offViewMoveNo()

test 'clicking multiple points moves black stone', ->
  $point1 = $pointAt 0, 0
  $point2 = $pointAt 1, 2

  ok isPointEmpty($point1), 'first point is initially empty'
  $point1.click()
  notOk isPointEmpty($point1), 'after click, no longer empty'
  ok isPointBlack($point1), 'after click, is black stone'
  $point2.click()
  ok isPointEmpty($point1), 'after second click, first clicked point clear'
  ok isPointBlack($point2), 'after second click, second clicked point black'

test "off turn, no hover effects and can't play stones", (assert) ->
  tesuji_charm.onTurn = false
  tesuji_charm.game_basic.initialize()
  assert.notOk $('.goban .placement').length, "hover effect is disabled"
  $point = $pointAt 0, 0
  $point.click()
  assert.ok isPointEmpty($point), "no stone placed"

test "white stones play correctly", ->
  setInputSgf '(;SZ[3];B[aa])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  ok isPointWhite($point), 'second player should be White'

test "last move correctly indicated", ->
  setInputSgf '(;SZ[3];B[ab])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 0, 1
  ok isPointLastPlayed($point), 'last placed stone indicated'

test "next player correctly determined with info node", ->
  setInputSgf '(;SZ[3])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  ok isPointBlack($point), 'first player should be Black despite SGF info node'

test 'clicking multiple points updates hidden form', ->
  setInputSgf '(;SZ[3])'
  tesuji_charm.game_basic.initialize()
  $point1 = $pointAt 0, 0
  $point2 = $pointAt 1, 2

  $point1.click()
  equal getResponseSgf(), '(;SZ[3];B[aa])', "first stone sets correct SGF"
  $point2.click()
  equal getResponseSgf(), '(;SZ[3];B[bc])', "second stone sets correct SGF"

test 'Confirm button disabled until stone placed', ->
  $button = $('button.confirm_button')
  equal $button.prop('disabled'), true,
    'starts out disabled'
  $('.goban .gopoint').first().click()
  equal $button.prop('disabled'), false,
    'enabled after stone placed'

test 'Pass button sets data and submits', ->
  setInputSgf '(;SZ[3])'
  tesuji_charm.game_basic.initialize()
  form = $('#main_form').get(0)
  oldSubmit = form.submit
  submitCalled = false
  form.submit = -> submitCalled = true

  $('.pass_button').click()

  equal getResponseSgf(), '(;SZ[3];B[])', "pass button sets SGF in response"
  ok submitCalled, "form submit function called"
  form.submit = oldSubmit

test 'Pass move is for correct color', ->
  setInputSgf '(;SZ[3];B[])'
  tesuji_charm.game_basic.initialize()
  form = $('#main_form').get(0)
  oldSubmit = form.submit
  form.submit = ->

  $('.pass_button').click()

  equal getResponseSgf(), '(;SZ[3];B[];W[])', "white pass added after black"
  form.submit = oldSubmit

test "clicking a pre-existing stone does nothing", (assert) ->
  setInputSgf '(;SZ[3];AW[bb])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  assert.notOk isPointBlack($point), "point has not become black"
  assert.notOk $('input#response').val().match(/B\[bb]/),
    "SGF response does not contain black stone"

test "captured stones are removed and prisoner counts updated", (assert) ->
  setInputSgf '(;SZ[3];B[ba];W[aa])'
  tesuji_charm.game_basic.initialize()
  assert.prisonerCounts 0, 0
  # now make the capture
  $pointAt(0, 1).click()
  # corner should be blank now
  assert.ok isPointEmpty($pointAt(0, 0)), "corner point is now empty"
  assert.prisonerCounts 0, 1

test "prisoner counts with pre-existing prisoners", (assert) ->
  setInputSgf ('(;SZ[5];AB[ab][ee]AW[aa][de]' +
               ';B[ba];W[ed]' +
               ';AB[ce][dd])')
  tesuji_charm.game_basic.initialize()
  assert.prisonerCounts 1, 1
  $pointAt(2, 2).click()
  assert.prisonerCounts 1, 1
  $pointAt(4, 4).click()
  assert.prisonerCounts 1, 2

test "correct color after resume with two passes (black first)", (assert) ->
  setInputSgf '(;SZ[3];B[];W[];TCRESUME[])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  assert.ok isPointBlack($point)

test "correct color after resume with three passes (black first)", (assert) ->
  setInputSgf '(;SZ[3];B[];W[];B[];TCRESUME[])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  assert.ok isPointBlack($point)

test "correct color after resume with two passes (white first)", (assert) ->
  setInputSgf '(;SZ[3];B[aa];W[];B[];TCRESUME[])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  assert.ok isPointWhite($point)

test "correct color after resume with three passes (white first)", (assert) ->
  setInputSgf '(;SZ[3];B[aa];W[];B[];W[];TCRESUME[])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  assert.ok isPointWhite($point)

test "behaviour changes while viewing past moves", (assert) ->
  setInputSgf '(;SZ[3];B[aa];W[bb])'
  tesuji_charm.game_basic.initialize()
  $confirm_button = $('button.confirm_button')
  $point = $pointAt 2, 2
  $point.click()

  setViewMoveNo 1
  assert.ok isPointEmpty($point), "proposed stone vanishes on viewing past move"
  assert.ok $confirm_button.prop('disabled'), "confirm button disabled"
  assert.notOk $point.find('.placement').length, "hover effect is gone"

  $point.click()
  assert.ok isPointEmpty($point), "no stone appears"

  setViewMoveNo 2
  assert.ok $confirm_button.prop('disabled'), "confirm button still disabled"
  assert.ok isPointEmpty($point), "proposed stone does not reappear"
  assert.ok $point.find('.placement').length, "hover effect is back"

  $point.click()
  assert.ok isPointBlack($point), "after returning to end, stone can be placed"
  assert.notOk $confirm_button.prop('disabled'), "confirm button enabled"


# ============================================================================


module 'Game page with marking interface',
  beforeEach: ->
    $('#with_scoring').remove()
    $("#qunit-fixture").append $("<div/>",
                                 id: 'with_scoring'
                                 class: 'with_scoring')
    tesuji_charm.onTurn = true
    setInputSgf '(;SZ[3])'

  afterEach: ->
    tesuji_charm.game_common.offViewMoveNo()

test "clicking empty points in marking mode does nothing", (assert) ->
  tesuji_charm.game_marking.initialize()
  $point = $pointAt(1, 1)
  assert.ok isPointDame($point), "centre point starts dame"
  $point.click()
  assert.ok isPointDame($point), "still dame after click"

test "mixed scoring board", (assert) ->
  setInputSgf '(;SZ[3];B[ba];W[bb];B[ab];W[cb];B[cc];W[bc])'
  # .b.
  # bww
  # .w.
  tesuji_charm.game_marking.initialize()
  assert.ok isPointBlackScore($pointAt(0, 0)), "(0,0) black"
  assert.notOk isPointWhiteScore($pointAt(0, 0)), "(0,0) white"
  for [x, y] in [[0,1], [0,2], [1,0], [1,1], [1,2], [2,0], [2,1]]
    assert.notOk isPointBlackScore($pointAt(x, y)), "(#{x},#{y}) black"
    assert.notOk isPointWhiteScore($pointAt(x, y)), "(#{x},#{y}) white"
  assert.notOk isPointBlackScore($pointAt(2, 2)), "(2,2) black"
  assert.ok isPointWhiteScore($pointAt(2, 2)), "(2,2) white"

test "clicking live stones makes them dead, " + \
     "clicking again brings them back", (assert) ->
  setInputSgf '(;SZ[3];B[aa];W[ab];B[bb];W[ca];B[bc];W[cc];B[ac])'
  # b.w
  # .b.  (white captured at ab)
  # bbw
  tesuji_charm.game_marking.initialize()
  assert.prisonerCounts 0, 1, "initial layout"
  assert.scores 2, 0, "initial layout"

  $pointAt(1, 1).click()
  assert.ok isPointBlackDead($pointAt(1, 1)),
    "clicked stone (1, 1) is marked dead"
  assert.ok isPointWhiteScore($pointAt(1, 1)),
    "dead black stone (1, 1) has white score class"
  assert.ok isPointBlackDead($pointAt(0, 0)),
    "other black stone (0, 0) in the region is also dead"
  assert.ok isPointWhiteScore($pointAt(0, 1)),
    "(0, 1) becomes white score with black stones dead"
  assert.ok isPointWhiteScore($pointAt(2, 1)),
    "(2, 1) becomes white score with black stones dead"
  assert.prisonerCounts 4, 1, "black marked dead"
  assert.scores 1, 11, "black marked dead"

  $pointAt(1, 1).click()
  assert.ok isPointBlack($pointAt(1, 1)),
    "clicked stone (1, 1) is live again"
  assert.notOk isPointWhiteScore($pointAt(1, 1)),
    "revived stone (1, 1) no longer counts as white score"
  assert.ok isPointBlack($pointAt(0, 0)),
    "other dead stone (0, 0) is live again"
  assert.ok isPointBlackScore($pointAt(0, 1)),
    "(0, 1) counts for black again with black stones restored"
  assert.notOk isPointWhiteScore($pointAt(2, 1)),
    "(2, 1) is neutral again with black stones restored"
  assert.prisonerCounts 0, 1, "black stones revived"
  assert.scores 2, 0, "black stones revived"

test "killing stones revives neighbouring enemy groups " + \
     "automatically", (assert) ->
  setInputSgf '(;SZ[3];AB[aa][ca][bb][ac][bc]AW[cc])'
  # b.b
  # .b.
  # bbw
  tesuji_charm.game_marking.initialize()
  $pointAt(1, 1).click()
  $pointAt(2, 2).click()
  assert.notOk isPointBlackDead($pointAt 1, 1),
    "first clicked stone (1, 1) is no longer dead"
  assert.notOk isPointBlackDead($pointAt 0, 0),
    "neighboring black group (0, 0) is no longer dead"

test "initialization sets initial dead stones from SGF", (assert) ->
  setInputSgf '(;SZ[3];B[aa];W[ab];B[bb];W[ca];B[bc];W[cc];B[ac]
                ;W[];B[];TW[aa][ba][bb][bc][ac][bc])'
  # bww
  # .b.
  # bbw
  tesuji_charm.game_marking.initialize()
  assert.ok isPointBlackDead($pointAt 0, 0), "(0, 0) is dead"
  assert.ok isPointBlackDead($pointAt 1, 1), "(1, 1) is dead"
  assert.ok isPointWhiteScore($pointAt 0, 1), "(0, 1) scores for White"
  assert.ok isPointWhiteScore($pointAt 1, 1), "(1, 1) scores for White"

test "Form is updated with current dead stones", (assert) ->
  setInputSgf '(;SZ[3];AB[aa][ca][bb][ac][ab]AW[cb])'
  # b.b
  # .b.
  # bbw
  tesuji_charm.game_marking.initialize()
  $pointAt(1, 1).click()
  # to keep test simple, we just look for right number of elements in
  # each tag so that we can accept any order
  expected = ///
    AB(\[\w\w]){5}  # sanity check: black setup is retained with 5 coords
    .*              # (don't check white setup as we can't guarantee the order)
    TW(\[\w\w]){8}  # white territory has 8 coords
    ///
  tbPattern = /// TB\[ ///
  actual = $('input#response').val()
  assert.ok actual.match(expected), "correct number of TW coords"
  assert.notOk actual.match(tbPattern), "no TB property in SGF"

  # here we check for a specific coord
  $pointAt(2, 1).click()
  expected = /TB[\]\[\w]*\[bc]/  # TB, any number of [] and letters, [cc]
  actual = $('input#response').val()
  assert.ok actual.match(expected), "dead white stone found as black territory"

test "Resume button updates response and submits", (assert) ->
  setInputSgf '(;SZ[3];B[];W[])'
  tesuji_charm.game_marking.initialize()
  form = $('#main_form').get(0)
  oldSubmit = form.submit
  submitCalled = false
  form.submit = -> submitCalled = true

  $('.resume_button').click()

  equal getResponseSgf(), '(;SZ[3];B[];W[];TCRESUME[])',
    "resume button sets SGF in response"
  ok submitCalled, "form submit function called"
  form.submit = oldSubmit

test "behaviour changes while viewing past moves", (assert) ->
  setInputSgf ('(;SZ[3];B[aa];W[ab];B[bb];W[ca];B[bc];W[cc];B[ac];W[];B[]' +
               ';TW[aa][ba][ab][bb][cb][ac][bc]')
  # b.w
  # .b.  (white captured at ab)
  # bbw
  tesuji_charm.game_marking.initialize()
  assert.ok isPointBlackDead($pointAt 0, 0), "initial layout shows dead stones"
  ($pointAt 2, 0).click()
  assert.ok isPointWhiteDead($pointAt 2, 0), "click kills stone"

  setViewMoveNo 6
  assert.notOk isPointDame($pointAt 1, 0),
    "earlier move, dame points not marked"
  assert.ok isPointEmpty($pointAt 1, 0), "earlier move, dame points not marked"
  assert.notOk isPointWhiteDead($pointAt 2, 0),
    "earlier move, dead stones are unmarked"
  ($pointAt 2, 0).click()
  assert.notOk isPointWhiteDead($pointAt 2, 0),
    "earlier move, click does nothing"

  setViewMoveNo 9
  assert.notOk isPointBlackDead($pointAt 0, 0),
    "before black stones marked dead, black stone not shown as dead"
  assert.ok isPointDame($pointAt 1, 0),
    "before black stones marked dead, dame point marked"
  ($pointAt 2, 0).click()
  assert.notOk isPointWhiteDead($pointAt 2, 0),
    "before black stones marked dead, click does nothing"

  setViewMoveNo 10
  assert.ok isPointBlackDead($pointAt 0, 0),
    "return to latest move, dead stones from other player re-marked"
  assert.notOk isPointWhiteDead($pointAt 2, 0),
    "latest move, dead stones we set up before are not re-marked"
  ($pointAt 2, 0).click()
  assert.ok isPointWhiteDead($pointAt 2, 0), "click once again kills stone"


# ============================================================================


module 'Go rules'

go_rules = tesuji_charm.go_rules

QUnit.assert.legal = (color, x, y, state, message) ->
  go_rules.getNewState(color, x, y, state)
  @push true, true, true, message ? "move is legal"

QUnit.assert.illegal = (color, x, y, state, message) ->
  try
    go_rules.getNewState(color, x, y, state)
  catch error
    if error.message is 'illegal move'
      @push true, false, false, message ? "move is illegal"
      return
  @push false, true, false, message ? "move is illegal"

QUnit.assert.captures = (color, x, y, state, black, white, message) ->
  message or= "move makes capture"
  {_, captures} = go_rules.getNewStateAndCaptures(color, x, y, state)
  @equal captures.black, black, message + ": black"
  @equal captures.white, white, message + ": white"

test "playing on an existing stone is illegal", (assert) ->
  board = [ ['empty', 'black'], ['empty', 'empty'] ]
  assert.legal('white', 0, 1, board)
  assert.illegal('white', 1, 0, board)

test "playing a stone with no liberties is illegal", (assert) ->
  board = [ ['empty', 'black'], ['black', 'empty'] ]
  assert.illegal 'white', 0, 0, board,
    "white stone surrounded by black"
  board = [ ['empty', 'black'], ['black', 'black'] ]
  assert.illegal 'black', 0, 0, board,
    "black stone filling the board with black"

test "a move that would have no liberties is legal if it captures", (assert) ->
  board = [ ['empty', 'black'], ['black', 'black'] ]
  assert.legal 'white', 0, 0, board

test "playing a move sets the point color", (assert) ->
  board = [ ['empty', 'black'], ['empty', 'empty'] ]
  plusBlack = [ ['empty', 'black'], ['black', 'empty'] ]
  plusWhite = [ ['empty', 'black'], ['white', 'empty'] ]
  assert.deepEqual(
    go_rules.getNewState('black', 0, 1, board), plusBlack)
  assert.deepEqual(
    go_rules.getNewState('white', 0, 1, board), plusWhite)

test "removing a single stone's last liberty removes it", (assert) ->
  board = [ ['white', 'black'], ['empty', 'empty'] ]
  afterCapture = [ ['empty', 'black'], ['black', 'empty'] ]
  assert.deepEqual(
    go_rules.getNewState('black', 0, 1, board), afterCapture)

test "removing a group's last liberty removes the group", (assert) ->
  board = [
    ['empty', 'empty', 'black', 'empty']
    ['black', 'white', 'white', 'empty']
    ['empty', 'black', 'black', 'empty']
  ]
  b1 = go_rules.getNewState('black', 3, 1, board)
  assert.equal b1[1][2], 'white',
    "white stones still around with one liberty remaining"
  b2 = go_rules.getNewState('black', 1, 0, b1)
  expected = [
    ['empty', 'black', 'black', 'empty']
    ['black', 'empty', 'empty', 'black']
    ['empty', 'black', 'black', 'empty']
  ]
  assert.deepEqual(b2, expected, "group capture succeeded")

test "capturing with own last liberty does not remove own stones", (assert) ->
  board = [
    ['empty', 'black', 'black', 'empty']
    ['black', 'white', 'white', 'black']
    ['black', 'empty', 'white', 'black']
    ['white', 'black', 'black', 'white']
    ['empty', 'white', 'white', 'empty']
  ]
  expected = [
    ['empty', 'black', 'black', 'empty']
    ['black', 'white', 'white', 'black']
    ['black', 'white', 'white', 'black']
    ['white', 'empty', 'empty', 'white']
    ['empty', 'white', 'white', 'empty']
  ]
  b1 = go_rules.getNewState('white', 1, 2, board)
  assert.deepEqual(b1, expected, "group capture succeeded")

test "capture counts are reported correctly", (assert) ->
  board = [ ['black', 'black'], ['empty', 'white'] ]
  assert.captures('black', 0, 1, board, 0, 1,
    "Black captures one white stone")
  assert.captures('white', 0, 1, board, 2, 0,
    "White captures two black stones")

test "helper function neighboringPoints", (assert) ->
  board = [
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
  ]
  assert.equal(go_rules.neighboringPoints(0, 0, board).length, 2)
  assert.equal(go_rules.neighboringPoints(1, 0, board).length, 3)
  assert.equal(go_rules.neighboringPoints(1, 1, board).length, 4)

test "_countLiberties: single stones", (assert) ->
  board = [
    ['black', 'empty', 'black']
    ['empty', 'black', 'white']
    ['empty', 'empty', 'empty']
  ]
  assert.equal(go_rules._countLiberties(0, 0, board), 2)
  assert.equal(go_rules._countLiberties(1, 1, board), 3)
  assert.equal(go_rules._countLiberties(2, 1, board), 1)

test "_countLiberties: groups share liberties", (assert) ->
  board = [
    ['black', 'black', 'empty']
    ['black', 'white', 'white']
    ['empty', 'black', 'empty']
  ]
  assert.equal(go_rules._countLiberties(1, 0, board), 2)
  assert.equal(go_rules._countLiberties(1, 1, board), 2)

test "_countLiberties: regression test: shared liberties not
      double counted", (assert) ->
  board = [
    ['black', 'black', 'empty']
    ['black', 'empty', 'white']
    ['empty', 'black', 'empty']
  ]
  assert.equal go_rules._countLiberties(1, 0, board), 3,
    "centre liberty counts only once, for total of 3"

test "groupPoints: identifies groups correctly", (assert) ->
  board = [
    ['black', 'black', 'empty']
    ['black', 'white', 'white']
    ['empty', 'black', 'empty']
  ]
  blackGroup = [ [1,0], [0,0], [0,1] ]
  whiteGroup = [ [1,1], [2,1] ]
  assert.deepEqual go_rules.groupPoints(1, 0, board), blackGroup,
    "black group"
  assert.deepEqual go_rules.groupPoints(1, 1, board), whiteGroup,
    "white group"

test "groupPoints: optional argument 'colors' works", (assert) ->
  board = [
    ['blackdead', 'blackdead', 'empty']
    ['black',     'empty',     'white']
    ['empty',     'black',     'white']
  ]
  expected = [ [0,0], [1,0], [1,1], [2,0] ]
  actual = go_rules.groupPoints(0, 0, board, ['empty', 'blackdead'])
  assert.deepEqual actual, expected
