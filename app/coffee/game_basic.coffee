# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

$new_stone = null
new_stone_image_path = null

number_tds = ->
  j = 0
  $row = $('table.goban tr').first()
  while $row.length > 0
    i = 0
    $cell = $row.find('td').first()
    while $cell.length > 0
      $cell.data 'row', j
      $cell.data 'column', i
      $cell = $cell.next()
      i += 1
    $row = $row.next()
    j += 1

set_image = ($td, filename) ->
  $td.find('img').attr 'src', "static/images/goban/#{filename}"

game_basic.initialize = ->
  number_tds()

  if tesuji_charm.move_no % 2 == 0
    new_stone_image_path = 'b.gif'
  else
    new_stone_image_path = 'w.gif'

  $('table.goban td').click ->
    if $new_stone != null
      set_image $new_stone, 'e.gif'
    set_image $(this), new_stone_image_path
    $new_stone = $(this)
    $('button.confirm_button').prop 'disabled', false

  $('button.confirm_button').prop 'disabled', true

  $('button.confirm_button').click ->
    data =
      game_no: tesuji_charm.game_no
      move_no: tesuji_charm.move_no
      row: $new_stone.data 'row'
      column: $new_stone.data 'column'
    $.get tesuji_charm.game_url, data
