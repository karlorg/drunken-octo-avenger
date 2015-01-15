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

    var set_image = function($td, filename) {
        $td.find("img").attr("src", "static/images/goban/" + filename);
    };

    game_basic.initialize = function() {
        $("table.goban td").click(function () {
            if ($new_stone !== null) {
                set_image($new_stone, "e.gif");
            }
            set_image($(this), "b.gif");
            $new_stone = $(this);
        });
    };

})();
