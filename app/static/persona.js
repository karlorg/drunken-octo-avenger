/* global window */
(function() {
    "use strict";

    var tesuji_charm;
    if (!window.tesuji_charm) {
        window.tesuji_charm = {};
    }
    tesuji_charm = window.tesuji_charm;

    var persona;
    if (!tesuji_charm.persona) {
        tesuji_charm.persona = {};
    }
    persona = tesuji_charm.persona;

    persona.initialize = function(navigator) {
        var signin_link = $("#persona_login");
        if (signin_link) {
            signin_link.click(function() { navigator.id.request(); });
        }
        var signout_link = $("#logout");
        if (signout_link) {
            signout_link.click(function() { navigator.id.logout(); });
        }

        var loggedInUser = tesuji_charm.current_user_email;
        if (loggedInUser === "") {
            loggedInUser = null;
        }

        navigator.id.watch({
            loggedInUser: loggedInUser,
            onlogin: function(assertion) {
                // A user has logged in! Here you need to:
                // 1. Send the assertion to your backend for verification and
                // to create a session.  2. Update your UI.
                $.ajax({ 
                    type: 'POST',
                    url: '/persona/login', // This is a URL on your website.
                    data: {assertion: assertion},
                    success: function(res, status, xhr) { 
                        window.location.reload();
                    },
                    error: function(xhr, status, err) {
                        navigator.id.logout();
                        // alert("Login failure: " + err);
                    }
                });
            },
            onlogout: function() {
                // A user has logged out! Here you need to:
                // Tear down the user's session by redirecting the user or
                // making a call to your backend.  Also, make sure loggedInUser
                // will get set to null on the next page load.  (That's a
                // literal JavaScript null. Not false, 0, or undefined. null.)
                $.ajax({
                    type: 'POST',
                    url: '/logout', // This is a URL on your website.
                    success: function(res, status, xhr) { 
                        window.location.reload();
                    },
                    error: function(xhr, status, err) {
                        // alert("Logout failure: " + err);
                    }
                });
            },
        });
    };

})();
