window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_common ?= {}
game_common = tesuji_charm.game_common


smartgame = tesuji_charm.smartgame
go_rules = tesuji_charm.go_rules


game_common.$pointAt = $pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
game_common.getInputSgf = getInputSgf = -> $('input#data').val()
game_common.setResponseSgf = setResponseSgf = (sgf) ->
  $('#response').val sgf

# setPointColor and helpers

game_common.setPointColor = setPointColor = ($td, color) ->
  $('.stone', $td).remove()
  $('.territory', $td).remove()
  [stoneclass, territoryclass] = switch color
    when 'empty' then ['', '']
    when 'black' then ['stone black', '']
    when 'white' then ['stone white', '']
    when 'blackdead' then ['stone black dead', 'territory white']
    when 'whitedead' then ['stone white dead', 'territory black']
    when 'blackscore' then ['', 'territory black']
    when 'whitescore' then ['', 'territory white']
  if stoneclass
    stoneElement = document.createElement 'div'
    stoneElement.className = stoneclass
    $td.append stoneElement
  if territoryclass
    territoryElement = document.createElement 'div'
    territoryElement.className = territoryclass
    $td.append territoryElement


# end of setPointColor helpers

game_common.contains_selector = contains_selector = ($context, selector) ->
  "A helper function returns true if the given element/context contains an
   element that satisfies the selector."
  return ($context.find selector).length > 0

game_common.colorFromDom = colorFromDom = ($point) ->
  "return the color of the given point based on the DOM status"
  # We do the dead ones first because a dead stone would still satisfy the
  # test for a white/black stone.
  if contains_selector $point, '.stone.black.dead' then return 'blackdead'
  if contains_selector $point, '.stone.white.dead' then return 'whitedead'
  if contains_selector $point, '.stone.black' then return 'black'
  if contains_selector $point, '.stone.white' then return 'white'
  if not (contains_selector $point, '.stone') then return 'empty'
  return null

game_common.isBlackScore = ($point) ->
  return contains_selector $point, '.territory.black'

game_common.isWhiteScore = ($point) ->
  return contains_selector $point, '.territory.white'

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
  $('.goban .gopoint').each ->
    $this = $(this)
    [row, col] = parseCoordClass $this
    result[row] ?= []
    result[row][col] = colorFromDom $this
  return result

game_common.updateBoard = updateBoard = (state) ->
  "set the images and classes of the DOM board to match the given state"
  for rowArray, row in state
    for color, col in rowArray
      setPointColor ($pointAt col, row), color
  return

isHandicapPoint = (size, row, column) ->
  switch size
    when 19 then row in [3,9,15] and column in [3,9,15]
    when 13 then (row in [3,9] and column in [3,9]) or row == column == 6
    when 9 then (row in [2,6] and column in [2,6]) or row == column == 4

game_common.initialize = (sgf_object, newStoneColor) ->
  $('.goban').remove()
  $('#content').append '<div class="goban"></div>'

  unless sgf_object
    if getInputSgf() != ''
      sgf_object = smartgame.parse getInputSgf()

  size = if sgf_object \
         then parseInt(sgf_object.gameTrees[0].nodes[0].SZ) or 19 \
         else 19

  top_vertical = '<div class="board_line board_line_vertical"></div>'
  bottom_vertical = '<div class="board_line board_line_vertical
                                 board_line_bottom_vertical"></div>'
  left_horizontal = '<div class="board_line board_line_horizontal"></div>'
  right_horizontal = '<div class="board_line board_line_horizontal
                                  board_line_right_horizontal"></div>'
  placement = "<div class='placement " + newStoneColor + "'></div>"


  tableContentsStr = ''
  for j in [0...size]
    row_element = "<div class='goban-row'>"
    for i in [0...size]
      point_element = "<div class='gopoint row-#{j} col-#{i}'>"
      if j > 0
        point_element += top_vertical
      if j < size - 1
        point_element += bottom_vertical
      if i > 0
        point_element += left_horizontal
      if i < size - 1
        point_element += right_horizontal
      if isHandicapPoint(size, j, i)
        point_element += "<div class='handicappoint'></div>"
      point_element += placement
      point_element += "</div>"
      row_element += point_element
    row_element += "</div>"
    tableContentsStr += row_element
  $('.goban').append tableContentsStr

  if getInputSgf() != ''
    board_state = (('empty' for i in [0...size]) for j in [0...size])
    for node in sgf_object.gameTrees[0].nodes
      if node.B
        [x, y] = decodeSgfCoord node.B
        board_state = go_rules.getNewState 'black', x, y, board_state
      if node.W
        [x, y] = decodeSgfCoord node.W
        board_state = go_rules.getNewState 'white', x, y, board_state
      if node.AB
        coords = if Array.isArray(node.AB) then node.AB else [node.AB]
        for coordStr in coords
          [x, y] = decodeSgfCoord coordStr
          board_state[y][x] = 'black'
      if node.AW
        coords = if Array.isArray(node.AW) then node.AW else [node.AW]
        for coordStr in coords
          [x, y] = decodeSgfCoord coordStr
          board_state[y][x] = 'white'
    updateBoard board_state

  return

aCode = 'a'.charCodeAt(0)

game_common.decodeSgfCoord = decodeSgfCoord = (coordStr) ->
  x = coordStr.charCodeAt(0) - aCode
  y = coordStr.charCodeAt(1) - aCode
  return [x, y]

game_common.encodeSgfCoord = encodeSgfCoord = (x, y) ->
  encodedX = String.fromCharCode(aCode + x)
  encodedY = String.fromCharCode(aCode + y)
  return encodedX + encodedY

game_common.cloneSgfObject = (sgfObject) ->
  "The trick here is that 'parent' attributes must be replaced with the parent
  in the new copy instead of pointing to the old one."
  getClone = (v, self, k=null, parent=null) -> switch
    when k == 'parent' then parent
    when Array.isArray v then cloneArrayRecursive v
    when v == Object(v) then cloneObjectRecursive v, self
    else v
  cloneObjectRecursive = (subObject, parent) ->
    result = {}
    for own k, v of subObject
      result[k] = getClone(v, result, k, parent)
    return result
  cloneArrayRecursive = (subArray) ->
    result = []
    for v in subArray
      result.push getClone(v, result)
    return result
  return cloneObjectRecursive sgfObject, null
