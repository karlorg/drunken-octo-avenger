casper.test.begin 'Test the login procedure', 2, (test) ->
  casper.start 'http://localhost:5000', ->
    test.assertTitle 'Go', 'The front page title is the one expected'

  check_no_popups = () -> casper.popups.length is 0

  casper.echo casper.popups.length

  casper.thenClick '#persona_login'
  casper.waitForPopup /persona/
  casper.withPopup /persona/, ->
    test.assertTitleMatch /Persona/i, 'Persona login popup has expected title'
    this.sendKeys '#authentication_email', 'test@mockmyid.com'
    # Slightly annoying we do not have a better way to select the 'next'
    # button, we could try the class "isDesktop isStart isAddressInfo", not
    # quite sure how to write that maybe '.isDesktop isStart isAddressInfo'
    # casper.echo (casper.getPageContent())
    # test.assertExists 'button', 'Button exists on persona page'
    # button = this.evaluate ->
    #           button = document.querySelector 'button:enabled'
    # casper.echo button.className
    test.assertExists 'button:enabled'
    this.echo casper.popups.length
    this.thenClick 'button:enabled'
    this.echo casper.popups.length
    first_popup = casper.popups[0]
    #this.echo (Object.getOwnPropertyNames(first_popup))
    this.echo (first_popup.content)
    this.echo (first_popup.plainText)
    this.thenClick 'button:enabled'
    this.echo casper.popups.length
    this.capture 'log.png'
    test.assertExists '.continue:enabled'
    this.thenClick '.continue:enabled'
    this.capture 'log2.png'
    # this.waitFor check_no_popups


  # casper.waitFor check_no_popups, () -> 
  #  this.reload()
  # this.echo (this.getPageContent())

#                 (() ->
#                this.echo (this.getPageContent())
#                this.reload()
#                this.echo (this.getPageContent())
#                this.waitForSelector '#logout', ->
#                  test.assertExists '#logout', 'Logout button is present'
#                  test.assertDoesntExist '#persona_login', 'No login button as expected')

  casper.then () -> 
    this.echo "I am the roomba queen."
    this.echo casper.popups.length
    test.assertExists '#logout'

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
