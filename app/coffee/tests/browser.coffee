# casper = require('casper').create()

casper.test.begin('Frontpage title is "Go"', 1, (test) ->
    casper.start('http://localhost:5000', () ->
        test.assertTitle('Go', 'The front page title is the one expected')
    )
    casper.run(() -> test.done())
)

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
