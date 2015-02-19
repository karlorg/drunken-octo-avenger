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


module 'Basic game page',
  setup: ->
    $('input#move_no').val "0"
    $('input#row').val ""
    $('input#column').val ""
    tesuji_charm.game_basic.initialize()

test 'clicking multiple points moves black stone', ->
  $point1 = $('td.row-0.col-0').first()
  $img1 = $point1.find('img').first()
  $point2 = $('td.row-2.col-1').first()
  $img2 = $point2.find('img').first()

  ok $img1.attr('src').indexOf('e.gif') > -1,
    'first point is initially empty (e.gif)'
  $point1.click()
  ok $img1.attr('src').indexOf('e.gif') is -1,
    'after click, no longer empty'
  ok $img1.attr('src').indexOf('b.gif') > -1,
    'after click, contains b.gif'
  $point2.click()
  ok $img1.attr('src').indexOf('e.gif') > -1,
    'after second click, first clicked point clear'
  ok $img2.attr('src').indexOf('b.gif') > -1,
    'after second click, second clicked point black'

test 'clicking multiple points updates hidden form', ->
  $point1 = $('td.row-0.col-0').first()
  $point2 = $('td.row-2.col-1').first()
  $row = $('input#row')
  $column = $('input#column')

  $point1.click()
  equal $row.val(), "0", "first stone sets correct row"
  equal $column.val(), "0", "first stone sets correct column"
  $point2.click()
  equal $row.val(), "2", "second stone sets correct row"
  equal $column.val(), "1", "second stone sets correct column"

test 'Confirm button disabled until stone placed', ->
  $button = $('button.confirm_button')
  equal $button.prop('disabled'), true,
    'starts out disabled'
  $('table.goban td').first().click()
  equal $button.prop('disabled'), false,
    'enabled after stone placed'

test "clicking a pre-existing stone does nothing", (assert) ->
  $point = $('.row-1.col-1')
  $img = $point.find('img')
  $point.addClass('whitestone')
  tesuji_charm.game_basic._reloadBoard()
  # test
  $point.click()
  assert.ok $img.attr('src').indexOf('b.gif') == -1,
    "point has not become black"
  assert.notEqual $('input#row').val(), "1", "row not set"
  assert.notEqual $('input#column').val(), "1", "column not set"

test "captured stones are removed from the board", (assert) ->
  # place existing stones
  $('.row-0.col-1').addClass "blackstone"
  $('.row-0.col-1 img').attr 'src', '/static/images/goban/b.gif'
  $('.row-0.col-0').addClass "whitestone"
  $('.row-0.col-0 img').attr 'src', '/static/images/goban/w.gif'
  tesuji_charm.game_basic._reloadBoard()
  # now make the capture
  $('.row-1.col-0').click()
  # corner should be blank now
  assert.ok $('.row-0.col-0 img').attr('src').indexOf('e.gif') > -1,
    "#{$('.row-0.col-0 img').attr('src')}"

test "helper function readBoardState", (assert) ->
  # place existing stones
  $('.row-0.col-1').addClass "blackstone"
  $('.row-0.col-0').addClass "whitestone"
  # test
  expected = [
    ['white', 'black', 'empty']
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
  ]
  assert.deepEqual tesuji_charm.game_basic._readBoardState(), expected

test "helper function updateBoard", (assert) ->
  tesuji_charm.game_basic._updateBoard [
    ['empty', 'black', 'empty']
    ['black', 'white', 'empty']
    ['empty', 'black', 'empty']
  ]
  assert.ok $('.row-0.col-1 img').attr('src').indexOf('b.gif') > -1
  assert.ok $('.row-1.col-1 img').attr('src').indexOf('w.gif') > -1
  assert.ok $('.row-1.col-2 img').attr('src').indexOf('e.gif') > -1
  tesuji_charm.game_basic._updateBoard [
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
  ]
  assert.ok $('.row-0.col-1 img').attr('src').indexOf('e.gif') > -1
  assert.ok $('.row-1.col-1 img').attr('src').indexOf('e.gif') > -1


module 'Go rules'

go_rules = tesuji_charm.go_rules

test "playing on an existing stone is illegal", (assert) ->
  board = [ ['empty', 'black'], ['empty', 'empty'] ]
  assert.equal go_rules.isLegal('white', 0, 1, board), true
  assert.equal go_rules.isLegal('white', 1, 0, board), false

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

test "helper function neighboringPoints", (assert) ->
  board = [
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
    ['empty', 'empty', 'empty']
  ]
  assert.equal(go_rules._neighbouringPoints(0, 0, board).length, 2)
  assert.equal(go_rules._neighbouringPoints(1, 0, board).length, 3)
  assert.equal(go_rules._neighbouringPoints(1, 1, board).length, 4)

test "helper function countLiberties", (assert) ->
  board = [
    ['black', 'empty', 'black']
    ['empty', 'black', 'white']
    ['empty', 'empty', 'empty']
  ]
  assert.equal(go_rules._countLiberties(0, 0, board), 2)
  assert.equal(go_rules._countLiberties(1, 1, board), 3)
  assert.equal(go_rules._countLiberties(2, 1, board), 1)
