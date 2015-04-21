# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

# 'imports'

game_common = tesuji_charm.game_common
go_rules = tesuji_charm.go_rules


# module variables

initialBoardState = null
newStoneColor = null

game_basic.initialize = ->

  initialBoardState = game_common.readBoardState()

  if parseInt($('input#move_no').val()) % 2 is 0
    newStoneColor = 'black'
  else
    newStoneColor = 'white'

  $('button.confirm_button').prop 'disabled', true

  $('table.goban td').click ->
    return unless game_common.hasCoordClass $(this)
    [row, col] = game_common.parseCoordClass $(this)

    try
      newBoardState = go_rules.getNewState(
        newStoneColor, col, row, initialBoardState)
    catch error
      if error.message is 'illegal move'
        return
      else
        throw error
    game_common.updateBoard newBoardState

    $('input#row').val row.toString()
    $('input#column').val col.toString()
    $('button.confirm_button').prop 'disabled', false

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reloadBoard = ->
  initialBoardState = game_common.readBoardState()
