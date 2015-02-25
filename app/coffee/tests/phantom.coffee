click = (element) ->
    ev = document.createEvent("MouseEvent")
    ev.initMouseEvent("click",
                      true, # bubble
                      true, # cancelable
                      window, null,
                      0, 0, 0, 0, # coordinates
                      false, false, false, false, # modifier keys
                      0, # left
                      null)
    element.dispatchEvent(ev)


page = require('webpage').create()
print_title = (status) ->
    title = page.evaluate(() -> document.title)
    console.log(title)
check_status = (status) ->
    console.log("Status: " + status)
    get_login_link = () -> document.getElementById('persona_login')
    login_link = page.evaluate(get_login_link)
    click(login_link)
    phantom.exit()
    

page.open('http://localhost:5000', check_status)
