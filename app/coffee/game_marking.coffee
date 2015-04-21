window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game_marking ?= {}
game_marking = tesuji_charm.game_marking

# 'imports'

game_common = tesuji_charm.game_common
$pointAt = game_common.$pointAt

go_rules = tesuji_charm.go_rules


setupScoring = ->
  state = game_common.readBoardState()
  clearScores state
  for row, rowArray of state
    row = parseInt row, 10
    for col, color of rowArray
      col = parseInt col, 10
      $td = $pointAt col, row
      continue if $td.hasClass 'blackscore'
      continue if $td.hasClass 'whitescore'
      continue if ($td.hasClass 'blackstone') or ($td.hasClass 'whitestone')
      boundary = go_rules.boundingColor col, row, state
      continue if boundary is 'neither'
      scoreColor = switch boundary
        when 'black' then 'blackscore'
        when 'white' then 'whitescore'
      # TODO: either make groupPoints public, or move this functionality into
      # go_rules
      for [x, y] in go_rules._groupPoints col, row, state
        $td0 = $pointAt(x, y)
        if $td0.hasClass('blackdead')
          game_common.setPointColor $td0, 'blackdead'
        else if $td0.hasClass('whitedead')
          game_common.setPointColor $td0, 'whitedead'
        else
          game_common.setPointColor $td0, scoreColor
  return  # explicit return so Coffee won't accumulate results of the `for`

clearScores = (state) ->
  "remove score classes from board with dimensions taken from `state`"
  for row, rowArray of state
    for col, _ of rowArray
      $td = $pointAt col, row
      $td.removeClass 'blackscore'
      $td.removeClass 'whitescore'

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
    for [x, y] in go_rules._groupPoints col, row, game_common.readBoardState()
      game_common.setPointColor $pointAt(x, y), newColor
    setupScoring()
