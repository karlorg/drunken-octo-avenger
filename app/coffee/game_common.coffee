window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_common ?= {}
game_common = tesuji_charm.game_common


setImage = ($td, filename) ->
  $td.find('img').attr 'src', "/static/images/goban/#{filename}"

setStoneClass = ($td, stoneclass) ->
  $td.removeClass('blackstone whitestone nostone
                   blackdead whitedead blackscore whitescore'
  ).addClass(stoneclass)

setPointColor = ($td, color) ->
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

game_common.setPointColor = setPointColor

$pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
game_common.$pointAt = $pointAt


rowRe = /row-(\d+)/
colRe = /col-(\d+)/

hasCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  return rowRe.test(classStr) and colRe.test(classStr)

game_common.hasCoordClass = hasCoordClass

parseCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  [_, rowStr] = rowRe.exec $obj.attr("class")
  [_, colStr] = colRe.exec $obj.attr("class")
  return [parseInt(rowStr, 10), parseInt(colStr, 10)]

game_common.parseCoordClass = parseCoordClass

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
game_common.readBoardState = readBoardState

updateBoard = (state) ->
  for row, rowArray of state
    for col, data of rowArray
      $td = $pointAt col, row
      setPointColor $td, data

game_common.updateBoard = updateBoard

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
game_common._updateBoardChars = updateBoardChars
