window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_marking ?= {}
game_marking = tesuji_charm.game_marking

# 'imports'

game_common = tesuji_charm.game_common
$pointAt = game_common.$pointAt

go_rules = tesuji_charm.go_rules


game_marking.initialize = ->
  setupScoring()

  $('table.goban td').click ->
    return unless game_common.hasCoordClass $(this)
    [row, col] = game_common.parseCoordClass $(this)
    $point = $pointAt col, row
    if $point.hasClass('blackstone')
      newColor = 'blackdead'
    else if $point.hasClass('whitestone')
      newColor = 'whitedead'
    else
      return
    for [x, y] in go_rules.groupPoints col, row, game_common.readBoardState()
      game_common.setPointColor $pointAt(x, y), newColor
    setupScoring()

setupScoring = ->
  state = game_common.readBoardState()
  for region in getEmptyRegions state
    [col, row] = region[0]
    boundary = go_rules.boundingColor col, row, state
    if boundary != 'neither'
      setRegionScores region, switch boundary
        when 'black' then 'blackscore'
        when 'white' then 'whitescore'
  return  # explicit return so Coffee won't accumulate results of the `for`

getEmptyRegions = (state) ->
  regions = []
  height = state.length
  width = state[0].length
  done = ((false for i in [0..width]) for j in [0..height])
  for rowArray, row in state
    for color, col in rowArray
      continue if done[row][col]
      if state[row][col] == 'empty'
        region = go_rules.groupPoints col, row, state
        for [x, y] in region
          done[y][x] = true
        regions.push region
  return regions

setRegionScores = (region, scoreColor) ->
  for [x, y] in region
    $point = $pointAt x, y
    if $point.hasClass 'nostone'
      game_common.setPointColor $point, scoreColor
  return
