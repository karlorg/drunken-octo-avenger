window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game ?= {}
exports = tesuji_charm.game


smartgame = tesuji_charm.smartgame
go_rules = tesuji_charm.go_rules


exports.$pointAt = $pointAt = (x, y) -> $(".row-#{y}.col-#{x}")
exports.getInputSgf = getInputSgf = -> $('input#data').val()
exports.setResponseSgf = setResponseSgf = (sgf) ->
  $('#response').val sgf

exports.getBlackPrisoners = -> parseInt($('.prisoners.black').text(), 10)
exports.getWhitePrisoners = -> parseInt($('.prisoners.white').text(), 10)

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

exports.initialize = (sgfObject = null, newStoneColor = null) ->
  sgfObject or= smartgame.parse(getInputSgf() or '(;SZ[19])')

  $('.pass_button').click ->
    newSgfObject = sgfObjectWithMoveAdded sgfObject
    newSgf = smartgame.generate newSgfObject
    setResponseSgf newSgf
    $('#main_form').get(0).submit()

  $('.resume_button').click ->
    newSgfObject = sgfObjectWithResumeAdded sgfObject
    newSgf = smartgame.generate newSgfObject
    setResponseSgf newSgf
    $('#main_form').get(0).submit()

  $('#board').empty()
  reactTop = React.render (React.createElement BoardAreaDom,
                                               initialSgf: getInputSgf()
                                               sgfObject: sgfObject),
                          $('#board')[0]
  return

BoardAreaDom = React.createClass
  getInitialState: ->
    deadStones: null
    proposedMove: null
    viewingMove: null

  isInInitialState: ->
    # not a React method but placed it next to getInitialState for
    # easy visual comparison
    (@state.deadStones is null and
     @state.proposedMove is null and
     @state.viewingMove is null)

  componentWillMount: -> @invalidateCache()
  componentWillUpdate: -> @invalidateCache()
  componentDidMount: -> @updateNonReact()
  componentDidUpdate: -> @updateNonReact()

  render: ->
    {div} = React.DOM
    div {},
        [(React.createElement BoardDom,
                              key: "BoardDom"
                              boardState: @getBoardState()
                              hoverColor: @getHoverColor()
                              clickCallback: @getOnBoardClick()
                              lastPlayed: @getLastPlayed()
                              size: @getSize()),
         (React.createElement NavigationDom,
                              key: "NavigationDom"
                              changeCallback: @onNavigate,
                              resetCallback: @onReset,
                              resetWouldDoNothing: @isInInitialState(),
                              sgfObject: @props.sgfObject,
                              viewingMove: @state.viewingMove),
         (React.createElement ScoreDom,
                              key: "ScoreDom"
                              prisoners: @getPrisoners()
                              scores: @getScores())]

  ## end of React-specific methods, beginning of custom ones

  getHoverColor: ->
    if @getMode().play
      return @getNextColor()
    else
      return null

  getMode: ->
    # return a set of true/false flags indicating different modes we
    # may operate in
    isViewingLatestMove = @state.viewingMove == null or
                          @state.viewingMove == actionCount(@props.sgfObject)
    isOnTurn = tesuji_charm.onTurn and isViewingLatestMove
    showScoring = isPassedTwice @getSgfWithNewMove(), moves: @getMoveToShow()
    scoring = isOnTurn and showScoring
    play = isOnTurn and not showScoring
    return {
      play: play  # ready to accept a new stone
      scoring: scoring  # ready to accept dead stone proposals
      showScoring: showScoring  # show territories and dead stones
    }

  # unlike @state.viewingMove, this takes into account the proposed new stone
  getMoveToShow: ->
    if @state.viewingMove == null \
       then null \
       else if @state.proposedMove \
            then @state.viewingMove + 1 \
            else @state.viewingMove

  getNextColor: -> nextPlayerInSgfObject @props.sgfObject

  getOnBoardClick: ->
    if @getMode().scoring
      return @onBoardClickScoring
    else if @getMode().play
      return @onBoardClickPlay
    else  # not allowing user to make moves/mark dead right now
      return ->

  getSgfWithDeadStones: ->
    sgfObjectWithDeadStones @props.sgfObject, @getBoardState()

  getSgfWithNewMove: ->
    if @state.proposedMove?
      return sgfObjectWithMoveAdded(@props.sgfObject,
                                    @state.proposedMove.color,
                                    @state.proposedMove.x,
                                    @state.proposedMove.y)
    else
      return @props.sgfObject

  getSize: -> parseInt(@props.sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19

  getStateObject: ->
    unless @cache? and @cache.stateObject?
      @getAndCacheStateObject()
    @cache.stateObject

  getAndCacheStateObject: ->
    x = stateFromSgfObject @getSgfWithNewMove(),
                           moves: @getMoveToShow(),
                           scoring: @getMode().showScoring,
                           deadStones: if @getMode().scoring \
                                       then @state.deadStones \
                                       else null
    @cache = {} unless @cache
    @cache.stateObject = x

  getBoardState: -> @getStateObject().boardState
  getLastPlayed: -> @getStateObject().lastPlayed
  getPrisoners: -> @getStateObject().prisoners
  getScores: -> @getStateObject().scores

  invalidateCache: -> @cache = {}

  # on-board-click callback when ready to play a new stone
  onBoardClickPlay: (xy) ->
    return unless isLegalOnSgf @props.sgfObject, @getNextColor(), xy.x, xy.y
    @setState proposedMove:
      color: @getNextColor()
      x: xy.x
      y: xy.y
    return

  # on-board-click callback when ready to mark dead stones
  onBoardClickScoring: (xy) ->
    newDead = getNewDeadForToggledPoint @getBoardState(), xy.x, xy.y
    @setState deadStones: newDead
    return

  onNavigate: (newViewingMove) ->
    @setState
      deadStones: null
      proposedMove: null
      viewingMove: newViewingMove

  onReset: -> @setState @getInitialState()

  updateNonReact: ->
    @updateSubmitButton()
    @updateResponseForm()
    return

  updateSubmitButton: ->
    # enable/disable submit button depending on current state
    if @getMode().scoring
      enabled = true
    else if @getMode().play and @state.proposedMove != null
      enabled = true
    else
      enabled = false
    $('.submit_button').prop 'disabled', not enabled
    return

  updateResponseForm: ->
    if @getMode().play
      setResponseSgf smartgame.generate(@getSgfWithNewMove())
    else if @getMode().scoring
      setResponseSgf smartgame.generate(@getSgfWithDeadStones())
    else
      setResponseSgf @props.initialSgf
    return

BoardDom = React.createClass

  render: ->
    # all we render is a simple div that will have its
    # shouldComponentUpdate always return false, and therefore never
    # be touched by React after initial rendering.  The actual
    # rendering work is done manually, by this object, in our
    # componentDidX methods.
    React.createElement NonReactBoard

  componentDidMount: ->
    @renderGrid()
    @initCurrentStones()
    @renderStones()
    return

  componentDidUpdate: ->
    @renderStones()

  renderGrid: ->
    topVertical = '<div class="board_line board_line_vertical"></div>'
    bottomVertical = '<div class="board_line board_line_vertical
                                  board_line_bottom_vertical"></div>'
    leftHorizontal = '<div class="board_line board_line_horizontal"></div>'
    rightHorizontal = '<div class="board_line board_line_horizontal
                                    board_line_right_horizontal"></div>'

    {size} = @props
    $goban = $('<div>').addClass('goban')
    for j in [0...size]
      $row = $('<div>').addClass('goban-row')
      for i in [0...size]
        $point = $('<div>').addClass("gopoint row-#{j} col-#{i}")
        if j > 0
          $point.append $(topVertical)
        if j < size - 1
          $point.append $(bottomVertical)
        if i > 0
          $point.append $(leftHorizontal)
        if i < size - 1
          $point.append $(rightHorizontal)
        $row.append $point
      $goban.append $row

    $('#non-react-board').append $goban

  initCurrentStones: ->
    # we'll keep a record of what the current board looks like so that we don't
    # have to use expensive DOM queries
    {size} = @props
    @currentStones = (('none' for i in [0...size]) for j in [0...size])

  hasStoneChanged: (x, y, color) ->
    @currentStones[y][x] == @currentStonesCode(color)

  saveCurrentStone: (x, y, color) ->
    @currentStones[y][x] = @currentStonesCode(color)

  currentStonesCode: (color) ->
    # we actually save some extra information besides just color in the
    # current stones map; this function provides a string encoding that
    # information.
    if color is 'empty'
      "#{color} #{@props.hoverColor}"
    else
      color

  renderStones: ->
    for rowArray, row in @props.boardState
      for color, col in rowArray
        @setPointColor col, row, color
    @setLastPlayed()
    return

  setPointColor: (x, y, color) ->
    return if @hasStoneChanged(x, y, color)
    {hoverColor} = @props
    $td = $pointAt x, y
    hoverClass = if @props.hoverColor \
                 then "placement #{hoverColor}" \
                 else ""

    $('.placement', $td).remove()
    $('.stone', $td).remove()
    $('.territory', $td).remove()
    [stoneclass, territoryclass] = switch color
      when 'empty' then [hoverClass, '']
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

    @saveCurrentStone(x, y, color)

  setLastPlayed: ->
    $('.goban .last-played').remove()
    {lastPlayed: {x, y}} = @props
    if x != null and y != null
      $point = $pointAt x, y
      $lp = $('<div>').addClass('last-played')
      $point.append $lp
    return

  oldrender: ->
    # boardState is the complete state to show, with the newly proposed
    # stone included if there is one.  lastPlayed is only used to locate
    # the 'new stone' marker, the stone it refers to should already be in
    # the boardState.
    {size} = @props
    {div} = React.DOM

    div {className: 'goban'},
        for j in [0...size]
          div {key: j, className: 'goban-row'},
              for i in [0...size]
                (div {
                  key: i
                  className: "gopoint row-#{j} col-#{i}"
                  onClick: @onClickForPos(i, j)},
                    (@boardPointDomForPos i, j),
                    (@stoneDomForPos i, j))

  boardPointDomForPos: (i, j) ->
    {size} = @props
    React.createElement BoardPointDom,
                        key: 'point'
                        size: size
                        x: i
                        y: j

  stoneDomForPos: (i, j) ->
    {boardState, hoverColor, lastPlayed} = @props
    color = boardState[j][i]
    isLastPlayed = (i == lastPlayed.x and j == lastPlayed.y)
    React.createElement StoneDom,
                        key: 'stone'
                        color: color
                        hoverColor: hoverColor
                        isLastPlayed: isLastPlayed

  initOnClicks: ->
    # we cache an on-click callback function for each point on the
    # board, so that every time this component updates, the same
    # callback will be used for each point.
    #
    # Without caching, I believe React would see the callback functions
    # changing each time render() was called.  And I can't see a way to have
    # a single callback function and still pass the clicked coordinates back
    # to the listener.
    return if @onClicks?

    # this factory is used to prevent JS from linking i and j to the
    # loop variables instead of their values.
    makeCb = (i, j) =>
      (event) => @props.clickCallback {x: i, y: j}
    {size} = @props
    @onClicks = {}
    for j in [0...size]
      for i in [0...size]
        @onClicks["#{j}-#{i}"] = makeCb i, j
    return

  onClickForPos: (i, j) -> @onClicks["#{j}-#{i}"]

NonReactBoard = React.createClass

  shouldComponentUpdate: -> false

  render: ->
    React.DOM.div {id: 'non-react-board'}

BoardPointDom = React.createClass

  render: ->
    {size, x, y} = @props
    m = @divMakers()
    contents = []
    if y > 0 then contents.push m.topVert()
    if y < size - 1 then contents.push m.botVert()
    if x > 0 then contents.push m.leftHoriz()
    if x < size - 1 then contents.push m.rightHoriz()
    if @isHandicapPoint() then contents.push m.handicapPoint()
    React.DOM.div {}, contents

  shouldComponentUpdate: -> false

  isHandicapPoint: ->
    {size, x: column, y: row} = @props
    switch size
      when 19 then row in [3,9,15] and column in [3,9,15]
      when 13 then (row in [3,9] and column in [3,9]) or row == column == 6
      when 9 then (row in [2,6] and column in [2,6]) or row == column == 4
      else false

  divMakers: ->
    classNames =
      topVert: "board_line board_line_vertical"
      botVert: "board_line board_line_vertical board_line_bottom_vertical"
      leftHoriz: "board_line board_line_horizontal"
      rightHoriz: "board_line board_line_horizontal board_line_right_horizontal"
      handicapPoint: "handicappoint"

    makermaker = (kind, className) ->
      -> React.DOM.div {className: className, key: kind}
    makers = {}
    for own kind, className of classNames
      makers[kind] = makermaker(kind, className)

    makers

StoneDom = React.createClass

  render: ->
    {color, isLastPlayed} = @props
    m = @divMakers()
    contents = switch color
      when 'black' then [m.blackStone()]
      when 'white' then [m.whiteStone()]
      when 'empty' then [m.hover()]
      when 'dame' then [m.dame()]
      when 'blackscore' then [m.blackScore()]
      when 'whitescore' then [m.whiteScore()]
      when 'blackdead' then [m.blackDead(), m.whiteScore()]
      when 'whitedead' then [m.whiteDead(), m.blackScore()]
      else []
    if isLastPlayed
      contents.push m.lastPlayedMarker()
    React.DOM.div {style: {width: '100%', height: '100%'}}, contents

  shouldComponentUpdate: (nextProps) ->
    (@props.color != nextProps.color or
     @props.isLastPlayed != nextProps.isLastPlayed or
     (nextProps.color == 'empty' and
      (@props.hoverColor != nextProps.hoverColor)))

  divMakers: ->
    classNames =
      blackStone: "stone black"
      whiteStone: "stone white"
      dame: "territory neutral"
      blackScore: "territory black"
      whiteScore: "territory white"
      blackDead: "stone black dead"
      whiteDead: "stone white dead"
      lastPlayedMarker: "last-played"
      hover: if @props.hoverColor \
              then "placement #{@props.hoverColor}" \
              else ""

    makermaker = (kind, className) ->
      -> React.DOM.div {className: className, key: kind}
    makers = {}
    for own kind, className of classNames
      makers[kind] = makermaker(kind, className)

    makers

NavigationDom = React.createClass
  render: ->
    {button, div, select} = React.DOM
    div {className: 'board_nav_block'},
        [(select {
           key: 'movelist'
           className: 'move_select'
           onChange: @onSelectChange
           onInput: @onSelectChange
           onKeyUp: @onSelectKeyUp
           value: @getViewingMove()}, @getOptions()),
         (button {
           key: 'resetbutton'
           className: 'reset_button'
           disabled: @props.resetWouldDoNothing
           onClick: @props.resetCallback}, "Reset view to latest move")]

  onSelectChange: (event) ->
    @props.changeCallback parseInt(event.target.value, 10)

  # hack for Firefox, which won't fire change/input event on
  # keyboard updates to select boxes until the focus is removed
  onSelectKeyUp: (event) ->
    event.target.blur()
    event.target.focus()

  getViewingMove: -> @props.viewingMove ? actionCount @props.sgfObject

  getOptions: ->
    makeOption = (optionSpec) ->
      {n, text} = optionSpec
      React.DOM.option {key: n, value: n},
                      ["Move #{n}: #{text}"]

    actionNodes =
      node for node in @props.sgfObject.gameTrees[0].nodes \
                    when isActionNode node

    getActionText = (node) ->
      if node.B?
        return 'B ' + (a1FromSgfTag(node.B) or 'pass')
      else if node.W?
        return 'W ' + (a1FromSgfTag(node.W) or 'pass')
      else if node.TB? or node.TW?
        return 'Mark dead'
      else
        throw new Error "unrecognised action node"

    optionSpecs = [n: 0, text: 'Start'].concat(
      for node, i in actionNodes
        n: i+1, text: getActionText node
    )

    (makeOption o for o in optionSpecs)

ScoreDom = React.createClass
  render: ->
    {prisoners, scores} = @props
    {div, span} = React.DOM
    subDivs = [div {key: "blackpris"},
                   ["Black prisoners: ",
                    span {key: 2, className: "prisoners black"},
                         prisoners.black],
               div {key: "whitepris"},
                   ["White prisoners: ",
                    span {key: 2, className: "prisoners white"},
                         prisoners.white]
              ]

    if scores?
      subDivs.push div {key: "blackscore"},
                       ["Black score: ",
                        span {key: 2, className: "score black"},
                             scores.black]
      subDivs.push div {key: "whitescore"},
                       ["White score: ",
                        span {key: 2, className: "score white"},
                             scores.white]

    div {className: "score_block"}, subDivs

a1FromSgfTag = (tag) ->
  if typeof tag is 'string'
    tag = [tag]
  coordStr = tag[0]
  return '' unless coordStr
  [x, y] = decodeSgfCoord coordStr
  colStr = String.fromCharCode(x + 'a'.charCodeAt(0))
  rowStr = y.toString()
  return "#{colStr}#{rowStr}"

isLegalOnSgf = (sgfObject, color, x, y) ->
  {boardState: previousState} = stateFromSgfObject sgfObject
  try
    go_rules.getNewStateAndCaptures color, x, y, previousState
  catch
    return false
  return true

stateFromSgfObject = (sgfObject, options={}) ->
  "Get a board state and associated info from an SGF object.

  If 'moves' is given as an option, include only that many moves.

  If 'scoring' is given as an option, mark dame and scoring points.

  If 'deadStones' is given as an option, the listed stones should be
  dead.  If null or not given, use the TB and TW nodes in the SGF to
  determine dead stones."
  {moves, scoring, deadStones: deadFromUi} = options
  size = if sgfObject \
         then parseInt(sgfObject.gameTrees[0].nodes[0].SZ, 10) or 19 \
         else 19
  boardState = (('empty' for i in [0...size]) for j in [0...size])
  prisoners = { black: 0, white: 0 }
  moveNo = 0
  for node in sgfObject.gameTrees[0].nodes
    if isActionNode node then moveNo += 1
    break if moves? and moveNo > moves
    if node.AB
      coords = if Array.isArray(node.AB) then node.AB else [node.AB]
      for coordStr in coords
        [x, y] = decodeSgfCoord coordStr
        boardState[y][x] = 'black'
    if node.AW
      coords = if Array.isArray(node.AW) then node.AW else [node.AW]
      for coordStr in coords
        [x, y] = decodeSgfCoord coordStr
        boardState[y][x] = 'white'
    if node.B?
      if node.B == ''
        [x, y] = [null, null]
      else
        [x, y] = decodeSgfCoord node.B
        result = go_rules.getNewStateAndCaptures('black', x, y, boardState,
                                                destructive: true)
        boardState = result.state
        prisoners.black += result.captures.black
        prisoners.white += result.captures.white
    else if node.W?
      if node.W == ''
        [x, y] = [null, null]
      else
        [x, y] = decodeSgfCoord node.W
        result = go_rules.getNewStateAndCaptures('white', x, y, boardState,
                                                destructive: true)
        boardState = result.state
        prisoners.black += result.captures.black
        prisoners.white += result.captures.white
  if scoring
    [x, y] = [null, null]
    deadStones = deadFromUi ?
                 deadStonesFromSgfObject sgfObject, boardState, moves: moves
    for [px, py] in deadStones
      switch boardState[py][px]
        when 'black'
          boardState[py][px] = 'blackdead'
          prisoners.black += 1
        when 'white'
          boardState[py][px] = 'whitedead'
          prisoners.white += 1
    {boardState, prisoners, scores} = scoreState {boardState, prisoners}
  else
    scores = null
  {boardState, lastPlayed: {x, y}, prisoners, scores}

deadStonesFromSgfObject = (sgfObject, state, options={}) ->
  "Read current territories in sgfObject, mark dead stones in `state`
  accordingly, and return an array of points for all dead stones."
  {moves} = options
  nodes = sgfObject.gameTrees[0].nodes
  nodeIndex = if moves? \
              then nodeNoFromActionNo sgfObject, moves \
              else nodes.length - 1
  node = nodes[nodeIndex]
  deadStones = []
  for tag in node.TB or []
    [x, y] = decodeSgfCoord tag
    if state[y][x] == 'white'
      deadStones.push [x, y]
  for tag in node.TW or []
    [x, y] = decodeSgfCoord tag
    if state[y][x] == 'black'
      deadStones.push [x, y]
  deadStones

scoreState = (stateObj) ->
  "given a board state, change its 'empty' points to 'blackscore',
  'whitescore' and 'dame' and return it with prisoner counts and total
  scores"
  {boardState, prisoners} = stateObj

  setRegionScores = (region, color) ->
    for [x, y] in region
      if boardState[y][x] == 'empty'
        boardState[y][x] = color

  for region in getEmptyRegions boardState
    boundary = go_rules.boundingColor region, boardState
    setRegionScores region, switch boundary
      when 'black' then 'blackscore'
      when 'white' then 'whitescore'
      when 'neither' then 'dame'
      else throw new Error "invalid boundary color: '#{boundary}'"

  scores = do ->
    black = prisoners.white
    white = prisoners.black
    for row in boardState
      for point in row
        if point == 'blackscore' or point == 'whitedead' then black += 1
        if point == 'whitescore' or point == 'blackdead' then white += 1
    {black, white}

  {boardState, prisoners, scores}

getEmptyRegions = (state) ->
  regions = []
  # which colors count as empty when detecting regions:
  emptyColors = ['empty', 'blackdead', 'whitedead']
  height = state.length
  width = state[0].length
  done = ((false for i in [0..width]) for j in [0..height])
  for rowArray, row in state
    for color, col in rowArray
      continue if done[row][col]
      if state[row][col] in emptyColors
        region = go_rules.groupPoints col, row, state, emptyColors
        for [x, y] in region
          done[y][x] = true
        regions.push region
  return regions

isActionNode = (node) -> node.B? or node.W? or node.TB? or node.TW?

nodeNoFromActionNo = (sgfObject, actionNo) ->
  "find the node index corresponding to the given action number"
  nodes = sgfObject.gameTrees[0].nodes
  actionsToGo = actionNo
  for node, i in nodes
    if isActionNode(node)
      actionsToGo -= 1
    break if actionsToGo <= 0
  return i

actionCount = (sgfObject) ->
  "Return number of moves (including passes) in sgf object."
  count = 0
  for node in sgfObject.gameTrees[0].nodes
    if isActionNode(node)
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

cloneSgfObject = (sgfObject) ->
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

_lastPassInRun = (nodes) ->
  lastPassSeen = null
  for node in nodes
    if 'B' of node
      if node.B == null or node.B == ''
        lastPassSeen = 'black'
      else
        break
    else if 'W' of node
      if node.W == null or node.W == ''
        lastPassSeen = 'white'
      else
        break
    else
      continue
  if lastPassSeen == null
    throw Error "no passes found before resumption node"
  return lastPassSeen

isPassedTwice = (sgfObject, options={}) ->
  "true iff sgf ends with two successive passes

  if `moves` is given, limit the game to that many moves."
  {moves} = options
  nodes = sgfObject.gameTrees[0].nodes
  nodeIndex = if moves? \
              then nodeNoFromActionNo sgfObject, moves \
              else nodes.length - 1
  isPass = (node) -> node.B == '' or node.W == ''
  hasMoveOrResume = (node) -> (typeof node.B == 'string' and node.B != '') or
                              (typeof node.W == 'string' and node.W != '') or
                              node.TCRESUME?
  passesSeen = 0
  i = nodeIndex
  while i >= 0 and not hasMoveOrResume(nodes[i])
    if isPass(nodes[i])
      passesSeen += 1
    if passesSeen >= 2
      return true
    i -= 1
  return false

sgfObjectWithMoveAdded = (sgfObject, color=null, col=null, row=null) ->
  if col != null and row != null
    coordStr = encodeSgfCoord col, row
  else
    coordStr = ''

  if color == null
    color = nextPlayerInSgfObject sgfObject
  sgfTag = switch color
    when 'black' then 'B'
    when 'white' then 'W'
    else throw Error "invalid new stone color"

  newMove = {}
  newMove[sgfTag] = coordStr

  sgfObjectCopy = cloneSgfObject sgfObject
  nodes = sgfObjectCopy.gameTrees[0].nodes
  if nodes.length == 1 and jQuery.isEmptyObject nodes[0]
    nodes[0] = newMove
  else
    nodes.push newMove

  return sgfObjectCopy

sgfObjectWithDeadStones = (sgfObject, boardState) ->
  tb = []
  tw = []
  height = boardState.length
  width = boardState[0].length
  for y in [0...height]
    for x in [0...width]
      switch boardState[y][x]
        when 'blackscore', 'whitedead'
          tb.push encodeSgfCoord(x, y)
        when 'whitescore', 'blackdead'
          tw.push encodeSgfCoord(x, y)

  newMove = {}
  if tb.length then newMove.TB = tb
  if tw.length then newMove.TW = tw
  sgfObjectCopy = cloneSgfObject sgfObject
  nodes = sgfObjectCopy.gameTrees[0].nodes
  nodes.push newMove

  return sgfObjectCopy

sgfObjectWithResumeAdded = (sgfObject) ->
  newNode = {TCRESUME: ''}
  sgfObjectCopy = cloneSgfObject sgfObject
  nodes = sgfObjectCopy.gameTrees[0].nodes
  nodes.push newNode
  return sgfObjectCopy

# markStonesAround and helpers

getNewDeadForToggledPoint = (state, x, y) ->
  "Return the new set of dead stones resulting from toggling the
  life/death status of the stone at (x, y) and all friendly stones in
  the region (ie. the area bounded by unfriendly stones).  If killing
  stones, also revive surrounding enemy stones.

  Changes `state` as a side effect (at time of writing this doesn't
  matter for our callers)."
  markStonesAround state, x, y
  dead = []
  for row, j in state
    for point, i in row
      if point == 'blackdead' or point == 'whitedead'
        dead.push [i, j]
  dead

markStonesAround = (state, x, y) ->
  "Toggle the life/death status of the given point and all friendly stones in
  the region (ie. the area bounded by unfriendly stones).  If killing stones,
  also revive surrounding enemy stones."
  color = state[y][x]
  return if color == 'empty'
  isKilling = color in ['black', 'white']
  # we're assuming here that the region never contains both live and dead
  # stones of the same color, as the interface should not allow this to happen
  region = go_rules.groupPoints(
    x, y, state,
    # list of colors to include in 'group'
    ['empty', 'dame', 'blackscore', 'whitescore', color])
  togglePoints state, region
  if isKilling
    reviveAroundRegion state, region
  return

reviveAroundRegion = (state, region) ->
  "Revive all dead groups touching, but not in, the given region; together with
  friendly stones in their own regions."
  height = state.length
  width = state[0].length
  ignore = ((false for i in [0..width]) for j in [0..height])
  for [x, y] in region
    ignore[y][x] = true

  for [x, y] in region
    for [xn, yn] in go_rules.neighboringPoints x, y, state
      continue if ignore[yn][xn]
      ignore[yn][xn] = true
      neighborColor = state[yn][xn]
      if neighborColor in ['blackdead', 'whitedead']
        neighborRegion = go_rules.groupPoints(
          xn, yn, state,
          # list of colors to include in 'group'
          ['empty', 'dame', 'blackscore', 'whitescore', neighborColor])
        togglePoints state, neighborRegion
        for [xg, yg] in neighborRegion
          ignore[yg][xg] = true
  return

togglePoints = (state, points) ->
  "Among the given points, mark live stones as dead and dead stones as alive."
  for [x, y] in points
    color = state[y][x]
    continue if color == 'empty'
    newColor = switch color
      when 'black' then 'blackdead'
      when 'white' then 'whitedead'
      when 'blackdead' then 'black'
      when 'whitedead' then 'white'
      else null
    if newColor
      state[y][x] = newColor
  return

# end markStonesAround
