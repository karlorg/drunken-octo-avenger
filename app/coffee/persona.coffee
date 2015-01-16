window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.persona ?= {}
persona = tesuji_charm.persona

persona.initialize = (navigator) ->
  signin_link = $('#persona_login')
  if signin_link.length > 0
    signin_link.click -> navigator.id.request()
  signout_link = $('#logout')
  if signout_link.length > 0
    signout_link.click -> navigator.id.logout()

  logged_in_user = tesuji_charm.current_persona_email
  if logged_in_user == ''
    logged_in_user = null

  navigator.id.watch {
    loggedInUser: logged_in_user
    onlogin: (assertion) ->
      $.ajax {
        type: 'POST'
        url: '/persona/login'
        data: {assertion: assertion}
        success: (res, status, xhr) -> window.location.reload()
        error: (xhr, status, err) -> navigator.id.logout()
      }
    onlogout: ->
      $.ajax {
        type: 'POST'
        url: '/logout'
        success: (res, status, xhr) -> window.location.reload()
        error: (xhr, status, err) -> undefined
      }
  }
