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
    markStonesAround col, row
    setupScoring()

# setupScoring and its helpers

setupScoring = ->
  "set/remove scoring classes on the DOM based on current live/dead state of
  all stones"
  state = game_common.readBoardState()
  for region in getEmptyRegions state
    [col, row] = region[0]
    boundary = go_rules.boundingColor region, state
    setRegionScores region, switch boundary
      when 'black' then 'blackscore'
      when 'white' then 'whitescore'
      when 'neither' then 'empty'
      else throw new Error "invalid boundary color: '#{boundary}'"
  return  # explicit return so Coffee won't accumulate results of the `for`

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

setRegionScores = (region, scoreColor) ->
  for [x, y] in region
    $point = $pointAt x, y
    if game_common.colorFromDom($point) == 'empty'
      game_common.setPointColor $point, scoreColor
  return

# markStonesAround and its helpers

markStonesAround = (x, y) ->
  "Toggle the life/death status of the given point and all friendly stones in
  the region (ie. the area bounded by unfriendly stones).

  We don't trigger scoring recalculation here, that's for the caller to do."
  color = game_common.colorFromDom $pointAt(x, y)
  return if color == 'empty'
  state = game_common.readBoardState()
  # we're assuming here that the region never contains both live and dead
  # stones of the same color, as the interface should not allow this to happen
  region = go_rules.groupPoints(
    x, y, state,
    ['empty', color])  # list of colors to include in 'group'
  toggleRegion region
  return

toggleRegion = (region) ->
  "In the given region, mark live stones as dead and dead stones as alive."
  for [x, y] in region
    $point = $pointAt x, y
    color = game_common.colorFromDom $point
    continue if color == 'empty'
    newColor = switch color
      when 'black' then 'blackdead'
      when 'white' then 'whitedead'
      when 'blackdead' then 'black'
      when 'whitedead' then 'white'
      else null
    if newColor
      game_common.setPointColor $point, newColor
  return
