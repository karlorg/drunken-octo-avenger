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
  $td.removeClass('blackstone whitestone nostone
                   blackdead').addClass(stoneclass)

setPointColor = ($td, color) ->
  [filename, stoneclass] = switch color
    when 'empty' then ['e.gif', 'nostone']
    when 'black' then ['b.gif', 'blackstone']
    when 'white' then ['w.gif', 'whitestone']
    when 'blackdead' then ['bdwp.gif', 'blackdead']
  setImage $td, filename
  setStoneClass $td, stoneclass

$pointAt = (x, y) -> $(".row-#{y}.col-#{x}")


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
      $td = $pointAt col, row
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
      $td = $pointAt col, row
      setPointColor $td, color

# export for use by tests
game_basic._updateBoardChars = updateBoardChars

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reloadBoard = ->
  initialBoardState = readBoardState()

setupScoring = ->
  state = readBoardState()
  clearScores state
  for row, rowArray of state
    row = parseInt row, 10
    for col, color of rowArray
      col = parseInt col, 10
      $td = $pointAt col, row
      continue if $td.hasClass 'blackscore'
      continue if $td.hasClass 'whitescore'
      continue if ($td.hasClass 'blackstone') or ($td.hasClass 'whitestone')
      boundary = go_rules.boundingColor col, row, state
      continue if boundary is 'neither'
      class_ = switch boundary
        when 'black' then 'blackscore'
        when 'white' then 'whitescore'
      # TODO: either make groupPoints public, or move this functionality into
      # go_rules
      for [x, y] in go_rules._groupPoints col, row, state
        $td.addClass class_
  return

clearScores = (state) ->
  "remove score classes from board with dimensions taken from `state`"
  for row, rowArray of state
    for col, _ of rowArray
      $td = $pointAt col, row
      $td.removeClass 'blackscore'
      $td.removeClass 'whitescore'

normalClickFunc = ->
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

markingClickFunc = ->
  return unless hasCoordClass $(this)
  [row, col] = parseCoordClass $(this)
  $point = $pointAt col, row
  if $point.hasClass('blackstone')
    newColor = 'blackdead'
  else if $point.hasClass('whitestone')
    newColor = 'whitedead'
  else
    return
  for [x, y] in go_rules._groupPoints col, row, readBoardState()
    setPointColor $pointAt(x, y), newColor
  setupScoring()

game_basic.initialize = ->

  initialBoardState = readBoardState()

  if parseInt($('input#move_no').val()) % 2 is 0
    newStoneColor = 'black'
  else
    newStoneColor = 'white'

  $('button.confirm_button').prop 'disabled', true

  if $('.with_scoring').length
    setupScoring()

  if not $('.with_scoring').length
    $('table.goban td').click normalClickFunc
  else
    $('table.goban td').click markingClickFunc
