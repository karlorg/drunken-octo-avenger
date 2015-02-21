window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.persona ?= {}
persona = tesuji_charm.persona

persona.initialize = (navigator) ->
  signinLink = $('#persona_login')
  if signinLink.length > 0
    signinLink.click -> navigator.id.request()
  signoutLink = $('#logout')
  if signoutLink.length > 0
    signoutLink.click -> navigator.id.logout()

  loggedInUser = tesuji_charm.currentPersonaEmail
  if loggedInUser == ''
    loggedInUser = null

  navigator.id.watch {
    loggedInUser: loggedInUser
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
