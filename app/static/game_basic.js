// Generated by CoffeeScript 1.9.0
(function() {
  var $new_stone, game_basic, new_stone_image_path, number_tds, set_image, tesuji_charm;

  if (window.tesuji_charm == null) {
    window.tesuji_charm = {};
  }

  tesuji_charm = window.tesuji_charm;

  if (tesuji_charm.game_basic == null) {
    tesuji_charm.game_basic = {};
  }

  game_basic = tesuji_charm.game_basic;

  $new_stone = null;

  new_stone_image_path = null;

  number_tds = function() {
    var $cell, $row, i, j, _results;
    j = 0;
    $row = $('table.goban tr').first();
    _results = [];
    while ($row.length > 0) {
      i = 0;
      $cell = $row.find('td').first();
      while ($cell.length > 0) {
        $cell.data('row', j);
        $cell.data('column', i);
        $cell = $cell.next();
        i += 1;
      }
      $row = $row.next();
      _results.push(j += 1);
    }
    return _results;
  };

  set_image = function($td, filename) {
    return $td.find('img').attr('src', "static/images/goban/" + filename);
  };

  game_basic.initialize = function() {
    number_tds();
    if (tesuji_charm.move_no % 2 === 0) {
      new_stone_image_path = 'b.gif';
    } else {
      new_stone_image_path = 'w.gif';
    }
    $('table.goban td').click(function() {
      if ($new_stone !== null) {
        set_image($new_stone, 'e.gif');
      }
      set_image($(this), new_stone_image_path);
      $new_stone = $(this);
      return $('button.confirm_button').prop('disabled', false);
    });
    $('button.confirm_button').prop('disabled', true);
    return $('button.confirm_button').click(function() {
      var data;
      data = {
        game_no: tesuji_charm.game_no,
        move_no: tesuji_charm.move_no,
        row: $new_stone.data('row'),
        column: $new_stone.data('column')
      };
      return $.post(tesuji_charm.playstone_url, data);
    });
  };

}).call(this);
