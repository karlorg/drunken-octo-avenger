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

game_common.initialize = ->
  $('.goban').remove()
  $('#content').append '<table class="goban"></table>'
  for j in [0..18]
    $tr = $('<tr/>')
    $('.goban').append $tr
    for i in [0..18]
      $td = $("<td class='row-#{j} col-#{i} nostone' />")
      $tr.append $td
  if $('input#data').val() != ''
    sgf_object = smartgame.parse $('input#data').val()
    board_state = (('empty' for i in [0..18]) for j in [0..18])
    for node in sgf_object.gameTrees[0].nodes
      if node.B
        x = node.B.charCodeAt(0) - 'a'.charCodeAt(0)
        y = node.B.charCodeAt(1) - 'a'.charCodeAt(0)
        board_state = go_rules.getNewState 'black', x, y, board_state
      if node.W
        x = node.W.charCodeAt(0) - 'a'.charCodeAt(0)
        y = node.W.charCodeAt(1) - 'a'.charCodeAt(0)
        board_state = go_rules.getNewState 'white', x, y, board_state
    updateBoard board_state
  return
