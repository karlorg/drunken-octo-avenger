window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.go_rules ?= {}
go_rules = tesuji_charm.go_rules

go_rules.isLegal = (color, x, y, state) ->
  return state[y][x] is 'empty'

go_rules.getNewState = (color, x, y, state) ->
  newState = $.extend(true, [], state)  # deep copy
  newState[y][x] = color
  return newState
