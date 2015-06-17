# helpers

$pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
imageSrc = ($point) -> $point.find('img').attr('src')

contains_selector = tesuji_charm.game_common.contains_selector

isPointEmpty = ($point) -> not(contains_selector $point, '.stone,.territory')
isPointBlack = ($point) -> contains_selector $point, '.stone.black'
isPointWhite = ($point) -> contains_selector $point, '.stone.white'
isPointBlackScore = ($point) ->
  (contains_selector $point '.territory.black') and
  (not (contains_selector $point '.territory.white'))
isPointWhiteScore = ($point) ->
  (contains_selector $point '.territory.white') and
  (not (contains_selector $point '.territory.black'))
isPointBlackDead = ($point) -> contains_selector $point, '.stone.black.dead'
isPointWhiteDead = ($point) -> contains_selector $point, '.stone.white.dead'


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


# ============================================================================

# helpers for game page tests

setInputSgf = (sgf) -> $('input#data').val sgf
getResponseSgf = -> $('input#response').val()

# ============================================================================


module "common game page functions",
  setup: ->
    setInputSgf ''
    tesuji_charm.game_common.initialize()


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
  expected = [ [ 'empty', 'black', 'empty' ]
               [ 'black', 'white', 'empty' ]
               [ 'empty', 'black', 'empty' ] ]
  assert.deepEqual tesuji_charm.game_common.readBoardState(), expected

test "helper function readBoardState", (assert) ->
  setInputSgf '(;SZ[3];B[ca];W[bc])'
  tesuji_charm.game_common.initialize()
  expected = [ [ 'empty', 'empty', 'black' ]
               [ 'empty', 'empty', 'empty' ]
               [ 'empty', 'white', 'empty' ] ]
  assert.deepEqual tesuji_charm.game_common.readBoardState(), expected


# ============================================================================


module 'Basic game page',
  setup: ->
    setInputSgf '(;SZ[3])'
    $('input#response').val ''
    tesuji_charm.game_basic.initialize()

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

test "white stones play correctly", ->
  setInputSgf '(;SZ[3];B[aa])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  ok isPointWhite($point), 'second player should be White'

test "next player correctly determined with info node", ->
  setInputSgf '(;SZ[3])'
  tesuji_charm.game_basic.initialize()
  $point = $pointAt 1, 1
  $point.click()
  ok isPointBlack($point), 'first player should be Black despite SGF info node'

test 'clicking multiple points updates hidden form', ->
  setInputSgf '(;)'
  tesuji_charm.game_basic.initialize()
  $point1 = $pointAt 0, 0
  $point2 = $pointAt 1, 2

  $point1.click()
  equal getResponseSgf(), '(;B[aa])', "first stone sets correct SGF"
  $point2.click()
  equal getResponseSgf(), '(;B[bc])', "second stone sets correct SGF"

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

test "captured stones are removed from the board", (assert) ->
  setInputSgf '(;SZ[3];B[ba];W[aa])'
  tesuji_charm.game_basic.initialize()
  # now make the capture
  $pointAt(0, 1).click()
  # corner should be blank now
  assert.ok isPointEmpty($pointAt(0, 0)), "corner point is now empty"

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


# ============================================================================


module 'Game page with marking interface',
  beforeEach: ->
    $("#qunit-fixture").append $("<div/>",
                                 id: 'with_scoring'
                                 class: 'with_scoring')
    setInputSgf '(;SZ[3])'

test "clicking empty points in marking mode does nothing", (assert) ->
  tesuji_charm.game_marking.initialize()
  $point = $pointAt(1, 1)
  assert.ok isPointEmpty($point), "centre point starts empty"
  $point.click()
  assert.ok isPointEmpty($point), "still empty after click"

test "mixed scoring board", (assert) ->
  setInputSgf '(;SZ[3];B[ba];W[bb];B[ab];W[cb];B[cc];W[bc])'
  # b.w
  # .b.
  # bbw
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
  tesuji_charm.game_marking.initialize()

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
  setInputSgf '(;SZ[3];AB[aa][ac][bb][ac][bc]AW[cc])'
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
  $pointAt(2, 2).click()
  expected = /TB[\]\[\w]*\[cc]/  # TB, any number of [] and letters, [cc]
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
