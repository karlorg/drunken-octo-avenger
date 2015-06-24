# Javascript controlling the 'basic' interface used to select a move on a game
# display page (as opposed to more complex interfaces that may be used for
# conditional move selection etc.)

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_basic ?= {}
game_basic = tesuji_charm.game_basic

# 'imports'

smartgame = tesuji_charm.smartgame
game_common = tesuji_charm.game_common
getInputSgf = game_common.getInputSgf
setResponseSgf = game_common.setResponseSgf
go_rules = tesuji_charm.go_rules


# module variables

initialBoardState = null
newStoneColor = null

game_basic.initialize = ->

  if getInputSgf()
    sgfObject = smartgame.parse getInputSgf()
  else
    sgfObject = smartgame.parse '(;)'

  newStoneColor = nextPlayerInSgfObject sgfObject

  game_common.initialize(sgfObject, newStoneColor)
  initialBoardState = game_common.readBoardState()

  $('button.confirm_button').prop 'disabled', true

  $('.goban .gopoint').click ->
    return unless game_common.hasCoordClass $(this)
    [row, col] = game_common.parseCoordClass $(this)

    try
      newBoardState = go_rules.getNewState(
        newStoneColor, col, row, initialBoardState)
    catch error
      if error.message is 'illegal move'
        return
      else
        throw error
    game_common.updateBoard newBoardState

    newSgfObject = sgfObjectWithMoveAdded sgfObject, col, row
    setResponseSgf smartgame.generate(newSgfObject)

    $('button.confirm_button').prop 'disabled', false

  $('.pass_button').click ->
    passSgfObject = sgfObjectWithMoveAdded sgfObject
    setResponseSgf smartgame.generate(passSgfObject)
    $('#main_form').get(0).submit()

# to facilitate testing, export a function to reload our internal state from
# the page
game_basic._reloadBoard = ->
  initialBoardState = game_common.readBoardState()

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

_lastPassInRun = (reversedNodes) ->
  lastPass = null
  for node in reversedNodes
    if 'B' of node
      if node.B
        return lastPass
      else
        lastPass = 'black'
    else if 'W' of node
      if node.W
        return lastPass
      else
        lastPass = 'white'
  unless lastPass
    throw new Error("no pass found before TCRESUME")
  return lastPass

sgfObjectWithMoveAdded = (sgfObject, col=null, row=null) ->
  if col != null and row != null
    coordStr = game_common.encodeSgfCoord col, row
  else
    coordStr = ''

  sgfTag = switch newStoneColor
    when 'black' then 'B'
    when 'white' then 'W'
    else throw Error "invalid new stone color"

  newMove = {}
  newMove[sgfTag] = coordStr

  sgfObjectCopy = game_common.cloneSgfObject sgfObject
  nodes = sgfObjectCopy.gameTrees[0].nodes
  if nodes.length == 1 and jQuery.isEmptyObject nodes[0]
    nodes[0] = newMove
  else
    nodes.push newMove

  return sgfObjectCopy
