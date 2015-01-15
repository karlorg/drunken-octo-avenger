/* global $, module, test, equal, ok, navigator, tesuji_charm */
(function() {
    "use strict";

    module("Persona");

    test("init function sets request and logout callbacks", function() {
        var request_called = false;
        var logout_called = false;
        var watch_called = false;
        var mock_navigator = {
            id: { logout: function() {
                    logout_called = true;
                }
                , request: function() {
                    request_called = true;
                }
                , watch: function (params) {
                    var pUser = params.loggedInUser;
                    var tUser = tesuji_charm.current_persona_email;
                    ok((tUser === "" && pUser === null) ||
                        (tUser !== "" && pUser === tUser),
                        "n.i.watch passed good loggedInUser");

                    var isFunction = function (functionToCheck) {
                        var getType = {};
                        return functionToCheck && 
                            (getType.toString.call(functionToCheck) ===
                            '[object Function]');
                    };
                    ok(isFunction(params.onlogin),
                        "n.i.watch passed function for onlogin");
                    ok(isFunction(params.onlogout),
                        "n.i.watch passed function for onlogout");

                    watch_called = true;
                }
            }
        };
        equal(watch_called, false);
        tesuji_charm.current_persona_email = "";
        tesuji_charm.persona.initialize(mock_navigator);
        equal(watch_called, true, "navigator.id.watch called");
        tesuji_charm.current_persona_email = "bob@example.com";
        tesuji_charm.persona.initialize(mock_navigator);

        equal(request_called, false);
        equal(logout_called, false);
        $("#persona_login").click();
        equal(request_called, true, "login request called correctly");
        equal(logout_called, false);
        $("#logout").click();
        equal(logout_called, true, "logout callback called correctly");
    });

    module("Basic game page", {
        setup: function() {
            window.tesuji_charm.game_basic.initialize();
        }
    });

    test("clicking an empty point shows a black stone", function() {
        var $point = $("table.goban td").first();
        var $img = $point.find("img").first();
        ok($img.attr("src").indexOf("e.gif") > -1,
           "point is initially empty (e.gif)");
        $point.click();
        ok($img.attr("src").indexOf("e.gif") === -1,
            "after click, no longer empty");
        ok($img.attr("src").indexOf("b.gif") > -1,
            "after click, contains b.gif");
    });

    test("clicking multiple points moves black stone", function() {
        var $point1 = $("table.goban td").first();
        var $point2 = $point1.next();
        $point1.click();
        $point2.click();
        ok($point1.find("img").attr("src").indexOf("e.gif") > -1,
           "first clicked point clear");
        ok($point2.find("img").attr("src").indexOf("b.gif") > -1,
            "second clicked point black");
    });

})();
