window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.go_rules ?= {}
go_rules = tesuji_charm.go_rules

go_rules.isLegal = (color, x, y, state) ->
  return state[y][x] is 'empty'

go_rules.getNewState = (color, x, y, state) ->
  # given a color stone to play at (x,y), return the new board state
  newState = $.extend(true, [], state)  # deep copy
  newState[y][x] = color
  for [xn, yn] in neighboringPoints(x, y, newState)
    if newState[yn][xn] is enemyColor(color)
      if countLiberties(xn, yn, newState) is 0
        newState[yn][xn] = 'empty'
  return newState

neighboringPoints = (x, y, state) ->
  [x0, y0] \
    for [x0, y0] in [ [x, y-1], [x+1, y], [x, y+1], [x-1, y] ] \
    when state[y0] isnt undefined and state[y0][x0] isnt undefined

enemyColor = (color) -> switch color
  when 'black' then 'white'
  when 'white' then 'black'
  else throw Error("#{color} has no enemy color")

countLiberties = (x, y, state) ->
  count = 0
  for [xn, yn] in neighboringPoints(x, y, state)
    if state[yn][xn] is 'empty'
      count += 1
  return count
