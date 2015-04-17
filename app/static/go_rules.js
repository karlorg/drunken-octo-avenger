// Generated by CoffeeScript 1.9.1
(function() {
  var countLiberties, enemyColor, go_rules, groupPoints, neighboringPoints, tesuji_charm,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  if (window.tesuji_charm == null) {
    window.tesuji_charm = {};
  }

  tesuji_charm = window.tesuji_charm;

  if (tesuji_charm.go_rules == null) {
    tesuji_charm.go_rules = {};
  }

  go_rules = tesuji_charm.go_rules;

  go_rules.getNewState = function(color, x, y, state) {
    var i, j, len, len1, newState, ref, ref1, ref2, ref3, xg, xn, yg, yn;
    if (state[y][x] !== 'empty') {
      throw Error('illegal move');
    }
    newState = $.extend(true, [], state);
    newState[y][x] = color;
    ref = neighboringPoints(x, y, newState);
    for (i = 0, len = ref.length; i < len; i++) {
      ref1 = ref[i], xn = ref1[0], yn = ref1[1];
      if (newState[yn][xn] === enemyColor(color)) {
        if (countLiberties(xn, yn, newState) === 0) {
          ref2 = groupPoints(xn, yn, newState);
          for (j = 0, len1 = ref2.length; j < len1; j++) {
            ref3 = ref2[j], xg = ref3[0], yg = ref3[1];
            newState[yg][xg] = 'empty';
          }
        }
      }
    }
    if (countLiberties(x, y, newState) === 0) {
      throw Error('illegal move');
    }
    return newState;
  };

  go_rules.boundingColor = function(x, y, state) {
    "Return the color surrounding the empty area around (x, y), or 'neither' if boundary is mixed.";
    var area, i, j, len, len1, point, ref, ref1, ref2, seen, x0, y0;
    area = groupPoints(x, y, state);
    seen = 'none';
    for (i = 0, len = area.length; i < len; i++) {
      ref = area[i], x = ref[0], y = ref[1];
      ref1 = neighboringPoints(x, y, state);
      for (j = 0, len1 = ref1.length; j < len1; j++) {
        ref2 = ref1[j], x0 = ref2[0], y0 = ref2[1];
        point = state[y0][x0];
        if (point === 'empty') {
          continue;
        } else if (seen === 'none') {
          seen = point;
          continue;
        } else if (seen !== point) {
          return 'neither';
        }
      }
    }
    if (seen === 'none') {
      seen = 'neither';
    }
    return seen;
  };

  neighboringPoints = function(x, y, state) {
    var i, len, ref, ref1, results, x0, y0;
    ref = [[x, y - 1], [x + 1, y], [x, y + 1], [x - 1, y]];
    results = [];
    for (i = 0, len = ref.length; i < len; i++) {
      ref1 = ref[i], x0 = ref1[0], y0 = ref1[1];
      if (state[y0] !== void 0 && state[y0][x0] !== void 0) {
        results.push([x0, y0]);
      }
    }
    return results;
  };

  go_rules._neighbouringPoints = neighboringPoints;

  enemyColor = function(color) {
    switch (color) {
      case 'black':
        return 'white';
      case 'white':
        return 'black';
      default:
        throw Error(color + " has no enemy color");
    }
  };

  countLiberties = function(x, y, state) {
    var i, j, len, len1, liberties, libertiesOfPoint, liberty, ref, ref1, ref2, xg, yg;
    libertiesOfPoint = function(x, y, state) {
      var color, i, len, ref, ref1, result, xn, yn;
      color = state[y][x];
      result = [];
      ref = neighboringPoints(x, y, state);
      for (i = 0, len = ref.length; i < len; i++) {
        ref1 = ref[i], xn = ref1[0], yn = ref1[1];
        if (state[yn][xn] === 'empty') {
          result.push(xn + " " + yn);
        }
      }
      return result;
    };
    liberties = [];
    ref = groupPoints(x, y, state);
    for (i = 0, len = ref.length; i < len; i++) {
      ref1 = ref[i], xg = ref1[0], yg = ref1[1];
      ref2 = libertiesOfPoint(xg, yg, state);
      for (j = 0, len1 = ref2.length; j < len1; j++) {
        liberty = ref2[j];
        if (indexOf.call(liberties, liberty) < 0) {
          liberties.push(liberty);
        }
      }
    }
    return liberties.length;
  };

  go_rules._countLiberties = countLiberties;

  groupPoints = function(x, y, state) {
    "Return a list of points in the group around (x, y) from `state`, whether black, white, or empty.";
    var groupPointsInternal;
    groupPointsInternal = function(x, y, state, seen) {
      var color, i, len, ref, ref1, ref2, result, xn, yn;
      color = state[y][x];
      result = [[x, y]];
      ref = neighboringPoints(x, y, state);
      for (i = 0, len = ref.length; i < len; i++) {
        ref1 = ref[i], xn = ref1[0], yn = ref1[1];
        if (state[yn][xn] === color && (ref2 = xn + " " + yn, indexOf.call(seen, ref2) < 0)) {
          result = result.concat(groupPointsInternal(xn, yn, state, seen.concat(x + " " + y)));
        }
      }
      return result;
    };
    return groupPointsInternal(x, y, state, []);
  };

  go_rules._groupPoints = groupPoints;

}).call(this);
