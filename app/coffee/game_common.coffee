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

game_common.getBlackPrisoners = -> parseInt($('.prisoners.black').text(), 10)
game_common.getWhitePrisoners = -> parseInt($('.prisoners.white').text(), 10)
game_common.setBlackPrisoners = setBlackPrisoners = (count) ->
  $('.prisoners.black').text count
game_common.setWhitePrisoners = setWhitePrisoners = (count) ->
  $('.prisoners.white').text count

# setPointColor and helpers

game_common.setPointColor = setPointColor = ($td, color) ->
  $('.stone', $td).remove()
  $('.territory', $td).remove()
  [stoneclass, territoryclass] = switch color
    when 'empty' then ['', '']
    when 'dame' then ['', 'territory neutral']
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

game_common.setLastPlayed = setLastPlayed = ($point) ->
  $('.goban .last-played').remove()
  lastPlayedElement = document.createElement 'div'
  lastPlayedElement.className = 'last-played'
  $point.append lastPlayedElement

removeLastPlayed = ->
  $('.goban .last-played').remove()

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
  return [parseInt(colStr, 10), parseInt(rowStr, 10)]

game_common.readBoardState = readBoardState = ->
  "generate a board state object based on the loaded page contents"
  result = []
  $('.goban .gopoint').each ->
    $this = $(this)
    [col, row] = parseCoordClass $this
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
    else false

game_common.initialize = (sgfObject = null, newStoneColor = null) ->
  sgfObject or= smartgame.parse(getInputSgf() or '(;SZ[19])')
  size = parseInt(sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19

  $scoreBlock = createScoringDom()
  $navBlock = createNavigationDom sgfObject
  $('#board').empty()
  React.render (React.createElement BoardDom, size: size,
                                              sgfObject: sgfObject),
               $('#board')[0]
  $('#board').append($elem) for $elem in [$navBlock, $scoreBlock]
  # setupState sgfObject
  return

BoardDom = React.createClass
  render: ->
    sgfObject = smartgame.parse(getInputSgf() or '(;SZ[19])')
    {boardState, lastPlayed, prisoners} = stateFromSgfObject sgfObject

    {div} = React.DOM
    topVert = div {className: "board_line board_line_vertical"}
    botVert = div {className: "board_line board_line_vertical
                               board_line_bottom_vertical"}
    leftHoriz = div {className: "board_line board_line_horizontal"}
    rightHoriz = div {className: "board_line board_line_horizontal
                                  board_line_right_horizontal"}
    handicapPoint = div {className: "handicappoint" }
    blackStone = div {className: "stone black"}
    whiteStone = div {className: "stone white"}

    size = this.props.size

    boardDivsForPos = (i, j) ->
      result = []
      if j > 0 then result.push topVert
      if j < size - 1 then result.push botVert
      if i > 0 then result.push leftHoriz
      if i < size - 1 then result.push rightHoriz
      if isHandicapPoint(size, j, i) then result.push handicapPoint
      result

    stoneDivsForPos = (i, j) ->
      switch boardState[j][i]
        when 'black' then [blackStone]
        when 'white' then [whiteStone]
        else []

    div {className: 'goban'},
        for j in [0...size]
          div {className: 'goban-row'},
              for i in [0...size]
                div {className: "gopoint row-#{j} col-#{i}"},
                    (boardDivsForPos i, j),
                    (stoneDivsForPos i, j)

createScoringDom = ->
  $scoreBlock = $('<div class="score_block"></div>')
  $scoreBlock.append ('<div>Black prisoners: ' +
    '<span class="prisoners black"></span></div>')
  $scoreBlock.append ('<div>White prisoners: ' +
    '<span class="prisoners white"></span></div>')
  $scoreBlock


# move navigation ====================================================

_moveNoListeners = []

game_common.onViewMoveNo = (callback) ->
  _moveNoListeners.push callback
  callback

game_common.offViewMoveNo = ->
  "Clear all view move no listeners.

  We need this for testing, where initialise() functions get called in many
  test cases, so we must clean up listeners after each test."
  _moveNoListeners = []

_isViewingLatestMove = false
_viewingMoveNo = 0

game_common.isViewingLatestMove = -> _isViewingLatestMove
game_common.viewingMoveNo = -> _viewingMoveNo

createNavigationDom = (sgfObject) ->
  maxMoves =  null

  $navBlock = $('<div class="board_nav_block"></div>')
  $select = $('<select class="move_select"/>')
  do ->
    moveNo = 0
    options = [n: 0, text: 'Start']
    for node in sgfObject.gameTrees[0].nodes
      if node.B?
        moveNo += 1
        options.push n: moveNo, text: 'B ' + (a1FromSgfTag(node.B) or 'pass')
      else if node.W?
        moveNo += 1
        options.push n: moveNo, text: 'W ' + (a1FromSgfTag(node.W) or 'pass')
      else if node.TB? or node.TW?
        moveNo += 1
        options.push n: moveNo, text: 'Mark dead'
    maxMoves = moveNo
    _viewingMoveNo = moveNo
    for option in options
      $select.append(
        "<option value=#{option.n}>" +
        "Move #{option.n}: #{option.text}" +
        "</option>")
  $select.find('option:last-child').attr('selected', true)

  # hack for Firefox; it won't respond to moving through the list with
  # arrow keys until it sees an onblur event
  $select.on 'keyup', (e) ->
    e.target.blur()
    e.target.focus()

  _isViewingLatestMove = true
  do ->
    $select.on 'change input', ->
      # filter events to ensure we only update as necessary
      val = parseInt($(this).val(), 10)
      return if _viewingMoveNo == val
      _viewingMoveNo = val
      _isViewingLatestMove = val == maxMoves
      setupState sgfObject, moves: val
      # notify listeners
      cb() for cb in _moveNoListeners

  $navBlock.append $select
  $navBlock

a1FromSgfTag = (tag) ->
  if typeof tag is 'string'
    tag = [tag]
  coordStr = tag[0]
  return '' unless coordStr
  [x, y] = decodeSgfCoord coordStr
  colStr = String.fromCharCode(x + 'a'.charCodeAt(0))
  rowStr = y.toString()
  return "#{colStr}#{rowStr}"

# end of move navigation =============================================


setupState = (sgfObject, options={}) ->
  "Update the DOM board to match the given SGF object.

  If 'moves' is given as an option, include only that many moves."
  {boardState, lastPlayed, prisoners} = stateFromSgfObject sgfObject, options
  updateBoard board_state
  if lastPlayed.x? and lastPlayed.y?
    setLastPlayed ($pointAt lastPlayed.x, lastPlayed.y)
  else
    removeLastPlayed()

  setBlackPrisoners prisoners.black
  setWhitePrisoners prisoners.white
  return

stateFromSgfObject = (sgfObject, options={}) ->
  "Get a board state and associated info from an SGF object.

  If 'moves' is given as an option, include only that many moves."
  {moves} = options
  size = if sgfObject \
         then parseInt(sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19 \
         else 19
  board_state = (('empty' for i in [0...size]) for j in [0...size])
  prisoners = { black: 0, white: 0 }
  moveNo = 0
  for node in sgfObject.gameTrees[0].nodes
    break if moves? and moveNo >= moves
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
    if node.B
      moveNo += 1
      [x, y] = decodeSgfCoord node.B
      result = go_rules.getNewStateAndCaptures('black', x, y, board_state)
      board_state = result.state
      prisoners.black += result.captures.black
      prisoners.white += result.captures.white
    if node.W
      moveNo += 1
      [x, y] = decodeSgfCoord node.W
      result = go_rules.getNewStateAndCaptures('white', x, y, board_state)
      board_state = result.state
      prisoners.black += result.captures.black
      prisoners.white += result.captures.white
  {boardState: board_state, lastPlayed: [x, y], prisoners: prisoners}


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
