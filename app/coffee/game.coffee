window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game ?= {}
exports = tesuji_charm.game


smartgame = tesuji_charm.smartgame
go_rules = tesuji_charm.go_rules


exports.$pointAt = $pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
exports.getInputSgf = getInputSgf = -> $('input#data').val()
# exports.setResponseSgf = setResponseSgf = (sgf) ->
  # $('#response').val sgf

exports.getBlackPrisoners = -> parseInt($('.prisoners.black').text(), 10)
exports.getWhitePrisoners = -> parseInt($('.prisoners.white').text(), 10)

###
# setPointColor and helpers

exports.setPointColor = setPointColor = ($td, color) ->
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

exports.setLastPlayed = setLastPlayed = ($point) ->
  $('.goban .last-played').remove()
  lastPlayedElement = document.createElement 'div'
  lastPlayedElement.className = 'last-played'
  $point.append lastPlayedElement

removeLastPlayed = ->
  $('.goban .last-played').remove()

# end of setPointColor helpers
###

exports.contains_selector = contains_selector = ($context, selector) ->
  "A helper function returns true if the given element/context contains an
   element that satisfies the selector."
  return ($context.find selector).length > 0

exports.colorFromDom = colorFromDom = ($point) ->
  "return the color of the given point based on the DOM status"
  # We do the dead ones first because a dead stone would still satisfy the
  # test for a white/black stone.
  if contains_selector $point, '.stone.black.dead' then return 'blackdead'
  if contains_selector $point, '.stone.white.dead' then return 'whitedead'
  if contains_selector $point, '.stone.black' then return 'black'
  if contains_selector $point, '.stone.white' then return 'white'
  if not (contains_selector $point, '.stone') then return 'empty'
  return null

exports.isBlackScore = ($point) ->
  return contains_selector $point, '.territory.black'

exports.isWhiteScore = ($point) ->
  return contains_selector $point, '.territory.white'

rowRe = /row-(\d+)/
colRe = /col-(\d+)/

exports.hasCoordClass = hasCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  return rowRe.test(classStr) and colRe.test(classStr)

exports.parseCoordClass = parseCoordClass = ($obj) ->
  classStr = $obj.attr "class"
  [_, rowStr] = rowRe.exec classStr
  [_, colStr] = colRe.exec classStr
  return [parseInt(colStr, 10), parseInt(rowStr, 10)]

exports.readBoardState = readBoardState = ->
  "generate a board state object based on the loaded page contents"
  result = []
  $('.goban .gopoint').each ->
    $this = $(this)
    [col, row] = parseCoordClass $this
    result[row] ?= []
    result[row][col] = colorFromDom $this
  return result

isHandicapPoint = (size, row, column) ->
  switch size
    when 19 then row in [3,9,15] and column in [3,9,15]
    when 13 then (row in [3,9] and column in [3,9]) or row == column == 6
    when 9 then (row in [2,6] and column in [2,6]) or row == column == 4
    else false

exports.initialize = (sgfObject = null, newStoneColor = null) ->
  sgfObject or= smartgame.parse(getInputSgf() or '(;SZ[19])')
  size = parseInt(sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19

  $('#board').empty()
  reactTop = React.render (React.createElement BoardAreaDom,
                                               {sgfObject: sgfObject}),
                          $('#board')[0]
  return

BoardAreaDom = React.createClass
  getInitialState: ->
    proposedMove: null
    viewingMove: null

  onNavigate: (newViewingMove) ->
    @setState
      proposedMove: null
      viewingMove: newViewingMove

  render: ->
    objState = stateFromSgfObject @props.sgfObject, moves: @state.viewingMove
    {boardState, lastPlayed, prisoners} = objState
    size = parseInt(@props.sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19

    if (tesuji_charm.onTurn and \
        (@state.viewingMove == null or \
         @state.viewingMove == moveCount(@props.sgfObject)))
      nextColor = nextPlayerInSgfObject @props.sgfObject
      onPlaceStone = (xy) =>
        @setState proposedMove:
          color: nextColor
          x: xy.x
          y: xy.y
    else
      onPlaceStone = ->

    {div} = React.DOM
    div {},
        [(React.createElement BoardDom,
                              boardState: boardState
                              placeStoneCallback: onPlaceStone
                              proposedMove: @state.proposedMove
                              lastPlayed: lastPlayed
                              size: size),
         (React.createElement NavigationDom,
                              changeCallback: @onNavigate,
                              sgfObject: @props.sgfObject,
                              viewingMove: @state.viewingMove),
         (React.createElement ScoreDom, prisoners: prisoners)]

BoardDom = React.createClass
  render: ->
    {boardState, lastPlayed, proposedMove, size} = @props

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
    lastPlayedMarker = div {className: "last-played"}

    boardDivsForPos = (i, j) ->
      result = []
      if j > 0 then result.push topVert
      if j < size - 1 then result.push botVert
      if i > 0 then result.push leftHoriz
      if i < size - 1 then result.push rightHoriz
      if isHandicapPoint(size, j, i) then result.push handicapPoint
      result

    stoneDivsForPos = (i, j) ->
      color = boardState[j][i]
      if proposedMove?
        _lastPlayed = proposedMove
        if proposedMove.x == i and proposedMove.y == j
          color = proposedMove.color
      else
        _lastPlayed = lastPlayed
      result = switch color
        when 'black' then [blackStone]
        when 'white' then [whiteStone]
        else []
      if i == _lastPlayed.x and j == _lastPlayed.y
        result.push lastPlayedMarker
      result

    onClickForPos = (i, j) => (event) =>
      @props.placeStoneCallback {
        x: i
        y: j
      }

    div {className: 'goban'},
        for j in [0...size]
          div {className: 'goban-row'},
              for i in [0...size]
                (div {
                  className: "gopoint row-#{j} col-#{i}"
                  onClick: onClickForPos(i, j)},
                    (boardDivsForPos i, j),
                    (stoneDivsForPos i, j))

NavigationDom = React.createClass
  render: ->
    {sgfObject, viewingMove} = @props

    options = [n: 0, text: 'Start']
    maxMoves = null
    do ->
      moveNo = 0
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

    reactOption = (option) ->
      {n, text} = option
      React.DOM.option {key: n, value: n},
                       ["Move #{n}: #{text}"]

    onChange = (event) =>
      @props.changeCallback parseInt(event.target.value, 10)

    # hack for Firefox, which won't fire change/input event on
    # keyboard updates to select boxes until the focus is removed
    onKeyUp = (event) ->
      event.target.blur()
      event.target.focus()

    {div, select} = React.DOM
    div {className: 'board_nav_block'},
        (select {
          className: 'move_select',
          onChange: onChange
          onInput: onChange
          onKeyUp: onKeyUp
          value: viewingMove ? maxMoves},
                (reactOption o for o in options))

ScoreDom = React.createClass
  render: ->
    prisoners = @props.prisoners
    {div, span} = React.DOM
    div {className: "score_block"},
        [div {}, ["Black prisoners: ",
                  span {className: "prisoners black"}, prisoners.black],
         div {}, ["White prisoners: ",
                  span {className: "prisoners white"}, prisoners.white]]


# move navigation ====================================================

_moveNoListeners = []

exports.onViewMoveNo = (callback) ->
  # _moveNoListeners.push callback
  callback

exports.offViewMoveNo = ->
  "Clear all view move no listeners.

  We need this for testing, where initialise() functions get called in many
  test cases, so we must clean up listeners after each test."
  _moveNoListeners = []

_isViewingLatestMove = false
_viewingMoveNo = 0

exports.isViewingLatestMove = -> _isViewingLatestMove
exports.viewingMoveNo = -> _viewingMoveNo

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
  {boardState: board_state, lastPlayed: {x, y}, prisoners: prisoners}

moveCount = (sgfObject) ->
  "Return number of moves (including passes) in sgf object."
  count = 0
  for node in sgfObject.gameTrees[0].nodes
    if node.B or node.W
      count += 1
  count


aCode = 'a'.charCodeAt(0)

exports.decodeSgfCoord = decodeSgfCoord = (coordStr) ->
  x = coordStr.charCodeAt(0) - aCode
  y = coordStr.charCodeAt(1) - aCode
  return [x, y]

exports.encodeSgfCoord = encodeSgfCoord = (x, y) ->
  encodedX = String.fromCharCode(aCode + x)
  encodedY = String.fromCharCode(aCode + y)
  return encodedX + encodedY

exports.cloneSgfObject = (sgfObject) ->
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

nextPlayerInSgfObject = (sgfObject) ->
  nodes = sgfObject.gameTrees[0].nodes
  reversedNodes = nodes.slice(0).reverse()  # slice(0) copies
  for node, index in reversedNodes
    if 'B' of node
      return 'white'
    else if 'W' of node
      return 'black'
    else if 'TCRESUME' of node
      # next to move is the first to pass before this resumption
      return _lastPassInRun reversedNodes.slice(index + 1)
  return 'black'
