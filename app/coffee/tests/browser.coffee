casper.test.begin 'Test the login procedure', 2, (test) ->
  casper.start 'http://localhost:5000', ->
    test.assertTitle 'Go', 'The front page title is the one expected'

  casper.thenClick '#persona_login'
  casper.waitForPopup /persona/
  casper.withPopup /persona/, ->
    test.assertTitleMatch /Persona/i, 'Persona login popup has expected title'
    this.sendKeys '#authentication_email', 'test@mockmyid.com'
    # Slightly annoying we do not have an better way to select the 'next'
    # button, we could try the class "isDesktop isStart isAddressInfo", not
    # quite sure how to write that maybe '.isDesktop isStart isAddressInfo'
    this.click 'button'

  casper.run ->
    test.done()

# @fill "form[action='/search']", q: "casperjs", true

# casper.then ->
  # aggregate results for the 'casperjs' search
#   links = @evaluate getLinks
  # search for 'phantomjs' from google form
#   @fill "form[action='/search']", q: "phantomjs", true

# casper.then ->
  # concat results for the 'phantomjs' search
#   links = links.concat @evaluate(getLinks)

# casper.run ->
  # display results
#  @echo links.length + " links found:"
#  @echo(" - " + links.join("\n - ")).exit()
