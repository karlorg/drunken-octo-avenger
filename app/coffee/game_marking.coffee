window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_marking ?= {}
game_marking = tesuji_charm.game_marking

# 'imports'

game_common = tesuji_charm.game_common
$pointAt = game_common.$pointAt

go_rules = tesuji_charm.go_rules


clearScores = ->
  "remove score classes from board in the DOM"
  $('.goban td').removeClass('blackscore whitescore')

setupScoring = ->
  state = game_common.readBoardState()
  clearScores()
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
  for row, rowArray of state
    row = parseInt row, 10
    for col, color of rowArray
      col = parseInt col, 10
      continue if done[row][col]
      if state[row][col] == 'empty'
        # TODO: make _groupPoints public or change this
        region = go_rules._groupPoints col, row, state
        for [x, y] in region
          done[y][x] = true
        regions.push region
  return regions

setRegionScores = (region, scoreColor) ->
  for [x, y] in region
    $point = $pointAt x, y
    if $point.hasClass 'blackdead'
      newColor = 'blackdead'
    else if $point.hasClass 'whitedead'
      newColor = 'whitedead'
    else
      newColor = scoreColor
    game_common.setPointColor $point, newColor
  return

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
    # TODO: make _groupPoints public or change this
    for [x, y] in go_rules._groupPoints col, row, game_common.readBoardState()
      game_common.setPointColor $pointAt(x, y), newColor
    setupScoring()
