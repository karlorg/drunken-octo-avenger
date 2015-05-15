// Generated by CoffeeScript 1.9.0
(function() {
  var game_basic, game_common, go_rules, initialBoardState, newStoneColor, nextPlayerInSgfObject, smartgame, tesuji_charm;

  if (window.tesuji_charm == null) {
    window.tesuji_charm = {};
  }

  tesuji_charm = window.tesuji_charm;

  if (tesuji_charm.game_basic == null) {
    tesuji_charm.game_basic = {};
  }

  game_basic = tesuji_charm.game_basic;

  smartgame = tesuji_charm.smartgame;

  game_common = tesuji_charm.game_common;

  go_rules = tesuji_charm.go_rules;

  initialBoardState = null;

  newStoneColor = null;

  game_basic.initialize = function() {
    var sgf_object;
    if ($('input#data').val()) {
      sgf_object = smartgame.parse($('input#data').val());
    } else {
      sgf_object = smartgame.parse('(;)');
    }
    game_common.initialize(sgf_object);
    initialBoardState = game_common.readBoardState();
    newStoneColor = nextPlayerInSgfObject(sgf_object);
    $('button.confirm_button').prop('disabled', true);
    return $('table.goban td').click(function() {
      var col, error, newBoardState, row, _ref;
      if (!game_common.hasCoordClass($(this))) {
        return;
      }
      _ref = game_common.parseCoordClass($(this)), row = _ref[0], col = _ref[1];
      try {
        newBoardState = go_rules.getNewState(newStoneColor, col, row, initialBoardState);
      } catch (_error) {
        error = _error;
        if (error.message === 'illegal move') {
          return;
        } else {
          throw error;
        }
      }
      game_common.updateBoard(newBoardState);
      $('input#row').val(row.toString());
      $('input#column').val(col.toString());
      return $('button.confirm_button').prop('disabled', false);
    });
  };

  game_basic._reloadBoard = function() {
    return initialBoardState = game_common.readBoardState();
  };

  nextPlayerInSgfObject = function(sgf_object) {
    var node, nodes, _i, _len, _ref;
    nodes = sgf_object.gameTrees[0].nodes;
    _ref = nodes.slice(0).reverse();
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      node = _ref[_i];
      if (node.B) {
        return 'white';
      } else if (node.W) {
        return 'black';
      }
    }
    return 'black';
  };

}).call(this);
