window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.go_rules ?= {}
go_rules = tesuji_charm.go_rules

go_rules.getNewState = (color, x, y, state) ->
  # given a color stone to play at (x,y), return the new board state
  if state[y][x] isnt 'empty'
    throw Error 'illegal move'
  newState = $.extend(true, [], state)  # deep copy
  newState[y][x] = color

  # process captures
  for [xn, yn] in neighboringPoints(x, y, newState)
    if newState[yn][xn] is enemyColor(color)
      if countLiberties(xn, yn, newState) is 0
        for [xg, yg] in groupPoints(xn, yn, newState)
          newState[yg][xg] = 'empty'

  if countLiberties(x, y, newState) is 0
    throw Error 'illegal move'
  return newState

go_rules.groupPoints = groupPoints = (x, y, state, colors=null) ->
  "Return a list of points in the group around (x, y) from `state`, whether
  black, white, or empty."
  if colors == null
    colors = [state[y][x]]
  done = []
  doneState = (('none' for w in [0..state[0].length]) \
               for h in [0..state.length])
  new_ = [[x, y]]
  doneState[y][x] = 'new'
  while true
    if new_.length is 0
      return done
    [x0, y0] = new_.pop()
    done.push [x0, y0]
    doneState[y0][x0] = 'done'
    for [xn, yn] in neighboringPoints(x0, y0, state)
      if state[yn][xn] in colors and
         doneState[yn][xn] is 'none'
        new_.push [xn, yn]
        doneState[yn][xn] = 'new'

go_rules.boundingColor = (region, state) ->
  "Return the color surrounding the empty region, or 'neither' if boundary is
  mixed."
  seen = 'none'
  for [x, y] in region
    for [x0, y0] in neighboringPoints x, y, state
      point = state[y0][x0]
      if point in ['empty', 'blackdead', 'whitedead']
        continue
      else if seen is 'none'
        seen = point
        continue
      else if seen isnt point
        return 'neither'
  if seen is 'none'
    seen = 'neither'
  return seen

go_rules.neighboringPoints = neighboringPoints = (x, y, state) ->
  [x0, y0] \
    for [x0, y0] in [ [x, y-1], [x+1, y], [x, y+1], [x-1, y] ] \
    when state[y0] isnt undefined and state[y0][x0] isnt undefined

# ============================================================================
# helper functions

enemyColor = (color) -> switch color
  when 'black' then 'white'
  when 'white' then 'black'
  else throw Error("#{color} has no enemy color")

countLiberties = (x, y, state) ->
  libertiesOfPoint = (x, y, state) ->
    color = state[y][x]
    result = []
    for [xn, yn] in neighboringPoints(x, y, state)
      if state[yn][xn] is 'empty'
        result.push("#{xn} #{yn}")
    return result
  liberties = []
  for [xg, yg] in groupPoints(x, y, state)
    for liberty in libertiesOfPoint(xg, yg, state)
      if liberty not in liberties
        liberties.push(liberty)
  return liberties.length

# export for testing
go_rules._countLiberties = countLiberties
