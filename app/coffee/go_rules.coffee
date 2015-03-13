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

neighboringPoints = (x, y, state) ->
  [x0, y0] \
    for [x0, y0] in [ [x, y-1], [x+1, y], [x, y+1], [x-1, y] ] \
    when state[y0] isnt undefined and state[y0][x0] isnt undefined

# export for testing
go_rules._neighbouringPoints = neighboringPoints

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

groupPoints = (x, y, state) ->
  groupPointsInternal = (x, y, state, seen) ->
    color = state[y][x]
    result = [[x, y]]
    for [xn, yn] in neighboringPoints(x, y, state)
      if state[yn][xn] is color and "#{xn} #{yn}" not in seen
        result = result.concat(groupPointsInternal(
          xn, yn, state, seen.concat("#{x} #{y}")))
    return result
  groupPointsInternal(x, y, state, [])

# export for testing
go_rules._groupPoints = groupPoints
