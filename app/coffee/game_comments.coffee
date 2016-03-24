window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.game ?= {}
exports = tesuji_charm.game

exports.receive_game_comments = receive_game_comments = (data, black_user, white_user) ->
  $('.chat-comment').remove()
  moments = data['moments']
  for comment in moments
    speaker = comment['speaker']
    speaker_color = if speaker == black_user then 'black' else\
                    if speaker == white_user then 'white' else 'anonymous'
    content = comment['content']
    comment_li = "<li class=\"chat-comment chat-comment-#{speaker_color} list-group-item\">
                      #{speaker}: #{content}</li>"
    $(".chat-comments").append comment_li
  $("#refreshing-comments").hide()
  $('.chat-comments').scrollTop($('.chat-comments')[0].scrollHeight)


exports.refresh_game_comments = (game_id, black_user, white_user) ->
  $("#refreshing-comments").show()
  posting = $.post '/grab_game_comments', game_id: game_id
  posting.done (data) ->
    receive_game_comments data, black_user, white_user
  posting.fail (data) ->
    $("#refreshing-comments").text "Error: Could not contact server."
