# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

go_rules = tesuji_charm.go_rules

initialBoardState = null

$newStone = null
newStoneColor = null

setImage = ($td, filename) ->
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

getStoneClass = ($obj) ->
  classStr = $obj.attr "class"
  return 'blackstone' if classStr.indexOf('blackstone') > -1
  return 'whitestone' if classStr.indexOf('whitestone') > -1
  return ''

readBoardState = ->
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
game_basic._readBoardState = readBoardState

updateBoard = (state) ->
  for row, rowArray of state
    for col, data of rowArray
      $td = $(".row-#{row}.col-#{col}")
      setImage $td, switch data
        when 'empty' then 'e.gif'
        when 'black' then 'b.gif'
        when 'white' then 'w.gif'

# export to enable testing
game_basic._updateBoard = updateBoard

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reloadBoard = ->
  initialBoardState = readBoardState()

game_basic.initialize = ->

  initialBoardState = readBoardState()

  if parseInt($('input#move_no').val()) % 2 is 0
    newStoneColor = 'black'
  else
    newStoneColor = 'white'

  $('button.confirm_button').prop 'disabled', true

  $('table.goban td').click ->
    return unless hasCoordClass $(this)
    [row, col] = parseCoordClass $(this)

    try
      newBoardState = go_rules.getNewState(
        newStoneColor, col, row, initialBoardState)
    catch error
      if error.message is 'illegal move'
        return
      else
        throw error
    updateBoard newBoardState

    $('input#row').val row.toString()
    $('input#column').val col.toString()
    $('button.confirm_button').prop 'disabled', false
