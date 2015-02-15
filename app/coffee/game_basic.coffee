# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

$new_stone = null
new_stone_image_path = null

set_image = ($a, filename) ->
  $a.find('img').attr 'src', "static/images/goban/#{filename}"

coordFromChr = (chr) -> chr.charCodeAt(0) - 'a'.charCodeAt(0)

coordRe = /coord-(\w)(\w)/

hasCoordClass = ($obj) -> coordRe.test $obj.attr("class")

parseCoordClass = ($obj) ->
  [_, rowStr, colStr] = coordRe.exec $obj.attr("class")
  return [coordFromChr(rowStr), coordFromChr(colStr)]

game_basic.initialize = ->

  if parseInt($('input#move_no').val()) % 2 == 0
    new_stone_image_path = 'b.gif'
  else
    new_stone_image_path = 'w.gif'

  $('button.confirm_button').prop 'disabled', true

  $('table.goban a').click ->
    return unless hasCoordClass $(this)

    $old_new_stone = $new_stone
    $new_stone = $(this)

    if $old_new_stone != null
      set_image $old_new_stone, 'e.gif'

    set_image $new_stone, new_stone_image_path
    [row, col] = parseCoordClass $new_stone
    $('input#row').val row.toString()
    $('input#column').val col.toString()
    $('button.confirm_button').prop 'disabled', false
