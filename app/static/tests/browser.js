// Generated by CoffeeScript 1.9.0
(function() {
  casper.test.begin('Test the login procedure', 1, function(test) {
    casper.start('http://localhost:5000', function() {
      return test.assertTitle('Go', 'The front page title is the one expected');
    });
    casper.on('popup.created', function() {
      return this.echo("url popup created: " + this.getCurrentURL(), "INFO");
    });
    casper.thenClick('#persona_login', function() {
      return this.capture("lol.png");
    });
    casper.waitForPopup(/persona/, function(popup) {
      return this.test.assertTitle('Mozilla Persona');
    });
    return casper.run(function() {
      return test.done();
    });
  });

}).call(this);
