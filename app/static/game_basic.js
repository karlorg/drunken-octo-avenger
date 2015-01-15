/* global window, $ */
(function() {
    "use strict";

    var tesuji_charm;
    if (!window.tesuji_charm) {
        window.tesuji_charm = {};
    }
    tesuji_charm = window.tesuji_charm;

    var game_basic;
    if (!tesuji_charm.game_basic) {
        tesuji_charm.game_basic = {};
    }
    game_basic = tesuji_charm.game_basic;

    var $new_stone = null;
    var new_stone_image_path = null;

    var number_tds = function() {
        var i = 0;
        var j = 0;
        var $row = $('table.goban tr').first();
        while ($row.length > 0) {
            var $cell = $row.find('td').first();
            i = 0;
            while ($cell.length > 0) {
                $cell.data('row', j);
                $cell.data('column', i);
                $cell = $cell.next();
                i += 1;
            }
            $row = $row.next();
            j += 1;
        }
    };

    var set_image = function($td, filename) {
        $td.find("img").attr("src", "static/images/goban/" + filename);
    };

    game_basic.initialize = function() {
        number_tds();

        if (tesuji_charm.move_no % 2 === 0) {
            new_stone_image_path = 'b.gif';
        } else {
            new_stone_image_path = 'w.gif';
        }

        $("table.goban td").click(function () {
            if ($new_stone !== null) {
                set_image($new_stone, "e.gif");
            }
            set_image($(this), new_stone_image_path);
            $new_stone = $(this);
            $('button.confirm_button').prop('disabled', false);
        });

        $('button.confirm_button').prop('disabled', true);

        $('button.confirm_button').click(function () {
            var data =
                { game_no: tesuji_charm.game_no
                , move_no: tesuji_charm.move_no
                , row: $new_stone.data('row')
                , column: $new_stone.data('column')
                };
            $.get(tesuji_charm.game_url, data);
        });
    };

})();
