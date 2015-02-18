# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

go_rules = tesuji_charm.go_rules

initial_board_state = null

$new_stone = null
new_stone_color = null

set_image = ($td, filename) ->
  $td.find('img').attr 'src', "/static/images/goban/#{filename}"

rowRe = /row-(\d+)/
colRe = /col-(\d+)/

hasCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  return rowRe.test(classStr) and colRe.test(classStr)

parseCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  [_, rowStr] = rowRe.exec $obj.attr("class")
  [_, colStr] = colRe.exec $obj.attr("class")
  return [parseInt(rowStr, 10), parseInt(colStr, 10)]

hasStoneClass = ($obj) ->
  classStr = $obj.attr "class"
  return true if classStr.indexOf('blackstone') > -1
  return true if classStr.indexOf('whitestone') > -1
  return false

getStoneClass = ($obj) ->
  classStr = $obj.attr "class"
  return 'blackstone' if classStr.indexOf('blackstone') > -1
  return 'whitestone' if classStr.indexOf('whitestone') > -1
  return ''

read_board_state = ->
  # generate a board state object based on the loaded page contents
  result = []
  $('.goban td').each (index) ->
    [row, col] = parseCoordClass $(this)
    result[row] ?= []
    result[row][col] = switch (getStoneClass $(this))
      when 'blackstone' then 'black'
      when 'whitestone' then 'white'
      else 'empty'
  return result

# export to enable testing
game_basic._read_board_state = read_board_state

update_board = (state) ->
  for row, rowArray of state
    for col, data of rowArray
      $td = $(".row-#{row}.col-#{col}")
      set_image $td, switch data
        when 'empty' then 'e.gif'
        when 'black' then 'b.gif'
        when 'white' then 'w.gif'

# export to enable testing
game_basic._update_board = update_board

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reload_board = ->
  initial_board_state = read_board_state()

game_basic.initialize = ->

  initial_board_state = read_board_state()

  if parseInt($('input#move_no').val()) % 2 is 0
    new_stone_color = 'black'
  else
    new_stone_color = 'white'

  $('button.confirm_button').prop 'disabled', true

  $('table.goban td').click ->
    return unless hasCoordClass $(this)
    [row, col] = parseCoordClass $(this)
    return unless go_rules.is_legal(
      new_stone_color, col, row, initial_board_state)

    $old_new_stone = $new_stone
    $new_stone = $(this)

    if $old_new_stone != null
      set_image $old_new_stone, 'e.gif'

    new_board_state = go_rules.get_new_state(
      new_stone_color, col, row, initial_board_state)
    update_board new_board_state

    $('input#row').val row.toString()
    $('input#column').val col.toString()
    $('button.confirm_button').prop 'disabled', false
