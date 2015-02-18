module 'Persona'

test 'init function sets request and logout callbacks', ->
  request_called = false
  logout_called = false
  watch_called = false
  mock_navigator =
    id:
      logout: -> logout_called = true
      request: -> request_called = true
      watch: (params) ->
        p_user = params.loggedInUser
        t_user = tesuji_charm.current_persona_email
        ok(
          (t_user == '' and p_user == null) or
          (t_user != '' and p_user == t_user),
            'navigator.id.watch passed good loggedInUser')
        ok typeof params.onlogin is 'function',
          'navigator.id.watch passed function for onlogin'
        ok typeof params.onlogout is 'function',
          'navigator.id.watch passed function for onlogout'
        watch_called = true
  # main test sequence begins here
  equal watch_called, false
  tesuji_charm.current_persona_email = ''
  tesuji_charm.persona.initialize mock_navigator
  equal watch_called, true, 'navigator.id.watch called'
  tesuji_charm.current_persona_email = 'bob@example.com'
  tesuji_charm.persona.initialize mock_navigator

  equal request_called, false
  equal logout_called, false
  $('#persona_login').click()
  equal request_called, true, 'login request called correctly'
  equal logout_called, false
  $('#logout').click()
  equal logout_called, true, 'logout callback called correctly'


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
  # indicate a pre-existing stone with a class
  $point.addClass('whitestone')
  $point.click()
  assert.ok $img.attr('src').indexOf('b.gif') == -1,
    "point has not become black"
  assert.notEqual $('input#row').val(), "1", "row not set"
  assert.notEqual $('input#column').val(), "1", "column not set"
