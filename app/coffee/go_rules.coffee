window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.go_rules ?= {}
go_rules = tesuji_charm.go_rules

go_rules.is_legal = (color, x, y, state) ->
  return state[y][x] is 'empty'

go_rules.get_new_state = (color, x, y, state) ->
  new_state = $.extend(true, [], state)  # deep copy
  new_state[y][x] = color
  return new_state
