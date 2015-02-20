// Generated by CoffeeScript 1.9.0
(function() {
  var $newStone, colRe, game_basic, getStoneClass, go_rules, hasCoordClass, initialBoardState, newStoneColor, parseCoordClass, readBoardState, rowRe, setImage, tesuji_charm, updateBoard;

  if (window.tesuji_charm == null) {
    window.tesuji_charm = {};
  }

  tesuji_charm = window.tesuji_charm;

  if (tesuji_charm.game_basic == null) {
    tesuji_charm.game_basic = {};
  }

  game_basic = tesuji_charm.game_basic;

  go_rules = tesuji_charm.go_rules;

  initialBoardState = null;

  $newStone = null;

  newStoneColor = null;

  setImage = function($td, filename) {
    return $td.find('img').attr('src', "/static/images/goban/" + filename);
  };

  rowRe = /row-(\d+)/;

  colRe = /col-(\d+)/;

  hasCoordClass = function($obj) {
    var classStr;
    classStr = $obj.attr("class");
    return rowRe.test(classStr) && colRe.test(classStr);
  };

  parseCoordClass = function($obj) {
    var classStr, colStr, rowStr, _, _ref, _ref1;
    classStr = $obj.attr("class");
    _ref = rowRe.exec($obj.attr("class")), _ = _ref[0], rowStr = _ref[1];
    _ref1 = colRe.exec($obj.attr("class")), _ = _ref1[0], colStr = _ref1[1];
    return [parseInt(rowStr, 10), parseInt(colStr, 10)];
  };

  getStoneClass = function($obj) {
    var classStr;
    classStr = $obj.attr("class");
    if (classStr.indexOf('blackstone') > -1) {
      return 'blackstone';
    }
    if (classStr.indexOf('whitestone') > -1) {
      return 'whitestone';
    }
    return '';
  };

  readBoardState = function() {
    var result;
    result = [];
    $('.goban td').each(function(index) {
      var col, row, _ref;
      _ref = parseCoordClass($(this)), row = _ref[0], col = _ref[1];
      if (result[row] == null) {
        result[row] = [];
      }
      return result[row][col] = (function() {
        switch (getStoneClass($(this))) {
          case 'blackstone':
            return 'black';
          case 'whitestone':
            return 'white';
          default:
            return 'empty';
        }
      }).call(this);
    });
    return result;
  };

  game_basic._readBoardState = readBoardState;

  updateBoard = function(state) {
    var $td, col, data, row, rowArray, _results;
    _results = [];
    for (row in state) {
      rowArray = state[row];
      _results.push((function() {
        var _results1;
        _results1 = [];
        for (col in rowArray) {
          data = rowArray[col];
          $td = $(".row-" + row + ".col-" + col);
          _results1.push(setImage($td, (function() {
            switch (data) {
              case 'empty':
                return 'e.gif';
              case 'black':
                return 'b.gif';
              case 'white':
                return 'w.gif';
            }
          })()));
        }
        return _results1;
      })());
    }
    return _results;
  };

  game_basic._updateBoard = updateBoard;

  game_basic._reloadBoard = function() {
    return initialBoardState = readBoardState();
  };

  game_basic.initialize = function() {
    initialBoardState = readBoardState();
    if (parseInt($('input#move_no').val()) % 2 === 0) {
      newStoneColor = 'black';
    } else {
      newStoneColor = 'white';
    }
    $('button.confirm_button').prop('disabled', true);
    return $('table.goban td').click(function() {
      var col, error, newBoardState, row, _ref;
      if (!hasCoordClass($(this))) {
        return;
      }
      _ref = parseCoordClass($(this)), row = _ref[0], col = _ref[1];
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
      updateBoard(newBoardState);
      $('input#row').val(row.toString());
      $('input#column').val(col.toString());
      return $('button.confirm_button').prop('disabled', false);
    });
  };

}).call(this);
