# one-time root config

Needs root -- needs to be done manually, but only one time.

* python 3.4 (3.2 not good, 3.3 unknown) or 2.7
* virtualenv installed (`pip3 install virtualenv`)
* user account for non-root operations, which will host the site code under its
  home directory (the directory structure will be created by the fabric script,
  see below)
* running a web server
* web server reverse proxys requests for sites
  - there's a template for an nginx `sites-available` site config file in this
    directory; replace `{DOMAIN}` and `{USER}` with the correct values.  (I'm
    new to nginx myself, so it's far from guaranteed.  Can someone check me?)
* web server aliases requests for `/static/` to appropiate dir
* sysvinit/upstart/whatever configured to keep wsgi server running
  - there's a sysvinit template in this directory, replace `{DOMAIN}` and
    `{USER}`

# code deployment

This is now handled by the fabfile in the deployment directory.  cd there and
run

    fab deploy:host=[USERNAME]@[HOSTNAME]
