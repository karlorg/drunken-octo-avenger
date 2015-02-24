page = require('webpage').create()
check_status = (status) ->
    console.log("Status: " + status)
    phantom.exit()
    

page.open('http://localhost:5000', check_status)
