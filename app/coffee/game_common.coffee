window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_common ?= {}
game_common = tesuji_charm.game_common


game_common.$pointAt = $pointAt = (x, y) -> $(".row-#{y}.col-#{x}")

game_common.setPointColor = setPointColor = ($td, color) ->
  [filename, stoneclass] = switch color
    when 'empty' then ['e.gif', 'nostone']
    when 'black' then ['b.gif', 'blackstone']
    when 'white' then ['w.gif', 'whitestone']
    when 'blackdead' then ['bdwp.gif', 'blackdead whitescore']
    when 'whitedead' then ['wdbp.gif', 'whitedead blackscore']
    when 'blackscore' then ['bp.gif', 'blackscore nostone']
    when 'whitescore' then ['wp.gif', 'whitescore nostone']
  setImage $td, filename
  setStoneClass $td, stoneclass

setImage = ($td, filename) ->
  $td.find('img').attr 'src', "/static/images/goban/#{filename}"

setStoneClass = ($td, stoneclass) ->
  $td.removeClass('blackstone whitestone nostone
                   blackdead whitedead blackscore whitescore'
  ).addClass(stoneclass)

rowRe = /row-(\d+)/
colRe = /col-(\d+)/

game_common.hasCoordClass = hasCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  return rowRe.test(classStr) and colRe.test(classStr)

game_common.parseCoordClass = parseCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  [_, rowStr] = rowRe.exec classStr
  [_, colStr] = colRe.exec classStr
  return [parseInt(rowStr, 10), parseInt(colStr, 10)]

game_common.readBoardState = readBoardState = ->
  "generate a board state object based on the loaded page contents"
  result = []
  $('.goban td').each ->
    $this = $(this)
    [row, col] = parseCoordClass $this
    result[row] ?= []
    result[row][col] = getStoneColor $this
  return result

getStoneColor = ($point) ->
  return 'black' if $point.hasClass 'blackstone'
  return 'white' if $point.hasClass 'whitestone'
  return 'blackdead' if $point.hasClass 'blackdead'
  return 'whitedead' if $point.hasClass 'whitedead'
  return 'empty'

game_common.updateBoard = updateBoard = (state) ->
  "set the images and classes of the DOM board to match the given state"
  for rowArray, row in state
    for color, col in rowArray
      setPointColor ($pointAt col, row), color
  return

updateBoardChars = (charArray) ->
  for rowString, row in charArray
    for char, col in rowString
      color = switch char
        when "b" then "black"
        when "w" then "white"
        when "." then "empty"
      setPointColor ($pointAt col, row), color
  return

# export for use by tests
game_common._updateBoardChars = updateBoardChars
