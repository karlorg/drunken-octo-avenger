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

setStoneClass = ($td, stoneclass) ->
  $td.removeClass('blackstone whitestone nostone').addClass(stoneclass)

setPointColor = ($td, color) ->
  [filename, stoneclass] = switch color
    when 'empty' then ['e.gif', 'nostone']
    when 'black' then ['b.gif', 'blackstone']
    when 'white' then ['w.gif', 'whitestone']
  setImage $td, filename
  setStoneClass $td, stoneclass


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
      setPointColor $td, data

# export to enable testing
game_basic._updateBoard = updateBoard

updateBoardChars = (charArray) ->
  for row, rowString of charArray
    for col, char of rowString
      color = switch char
        when "b" then "black"
        when "w" then "white"
        when "." then "empty"
      $td = $(".row-#{row}.col-#{col}")
      setPointColor $td, color

# export for use by tests
game_basic._updateBoardChars = updateBoardChars

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reloadBoard = ->
  initialBoardState = readBoardState()

setupScoring = ->
  for row, rowArray of initialBoardState
    row = parseInt row, 10
    for col, state of rowArray
      col = parseInt col, 10
      $td = $(".row-#{row}.col-#{col}")
      continue if $td.hasClass 'blackscore'
      continue if $td.hasClass 'whitescore'
      continue unless state is 'empty'
      boundary = go_rules.boundingColor col, row, initialBoardState
      continue if boundary is 'neither'
      class_ = switch boundary
        when 'black' then 'blackscore'
        when 'white' then 'whitescore'
      for [x, y] in go_rules._groupPoints col, row, initialBoardState
        $td.addClass class_
  return

game_basic.initialize = ->

  initialBoardState = readBoardState()

  if parseInt($('input#move_no').val()) % 2 is 0
    newStoneColor = 'black'
  else
    newStoneColor = 'white'

  $('button.confirm_button').prop 'disabled', true

  if $('.with_scoring').length
    setupScoring()

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
