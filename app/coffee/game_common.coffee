window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_common ?= {}
game_common = tesuji_charm.game_common


smartgame = tesuji_charm.smartgame
go_rules = tesuji_charm.go_rules


game_common.$pointAt = $pointAt = (x, y) -> $(".row-#{y}.col-#{x}")

# setPointColor and helpers

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

# end of setPointColor helpers

game_common.colorFromDom = colorFromDom = ($point) ->
  "return the color of the given point based on the DOM status"
  if $point.hasClass 'blackstone' then return 'black'
  if $point.hasClass 'whitestone' then return 'white'
  if $point.hasClass 'blackdead' then return 'blackdead'
  if $point.hasClass 'whitedead' then return 'whitedead'
  return 'empty'

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
    result[row][col] = colorFromDom $this
  return result

game_common.updateBoard = updateBoard = (state) ->
  "set the images and classes of the DOM board to match the given state"
  for rowArray, row in state
    for color, col in rowArray
      setPointColor ($pointAt col, row), color
  return

game_common.initialize = (sgf_object) ->
  $('.goban').remove()
  $('#content').append '<table class="goban"></table>'

  unless sgf_object
    if $('input#data').val() != ''
      sgf_object = smartgame.parse $('input#data').val()

  size = if sgf_object \
         then parseInt(sgf_object.gameTrees[0].nodes[0].SZ) or 19 \
         else 19

  for j in [0...size]
    $tr = $('<tr/>')
    $('.goban').append $tr
    for i in [0...size]
      $td = $("<td class='row-#{j} col-#{i} nostone' />")
      $tr.append $td

  if $('input#data').val() != ''
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
  cloneObjectRecursive = (subObject, parent) ->
    result = {}
    for own k, v of subObject
      if k == 'parent'
        result[k] = parent
      else if Array.isArray v
        result[k] = cloneArrayRecursive v
      else if v == Object(v)
        result[k] = cloneObjectRecursive v, result
      else
        result[k] = v
    return result
  cloneArrayRecursive = (subArray) ->
    result = []
    for v in subArray
      if Array.isArray v
        result.push cloneArrayRecursive(v)
      else if v == Object(v)
        result.push cloneObjectRecursive(v, result)
      else
        result.push v
    return result
  return cloneObjectRecursive sgfObject, null
