# needs root

* python 3.4 (3.2 not good, 3.3 unknown) or 2.7
* virtualenv installed (`pip3 install virtualenv`)
* user account for non-root operations
* running a web server
* web server reverse proxys requests for sites
* web server aliases requests for /static/ to appropiate dir
* wsgi server running, hopefully managed by sysvinit, upstart etc.

# doesn't need root

* `.ssh/authorized_keys` has keys of machines that may auto-deploy here
* site root dir `~/sites/[SITENAME]/`, call this `[ROOT]`
* clone repo to `[ROOT]/repo`
* make virtualenv in `[ROOT]/virtualenv`
* install `p3reqs.txt` or `requirements.txt` into virtualenv using `pip -r`
* generate new secret key in `config.py`
* disable DEBUG in `config.py`
* replace `localhost` with correct hostname in `config.py`
* update database version -- need migration tool!  For now can use `python
  db_remake.py` to clobber the old db as needed
