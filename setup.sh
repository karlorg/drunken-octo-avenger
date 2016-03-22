#! /bin/sh

# If the first argument is there it will be the python version
if [ $# -gt 0 ]
then
PYTHONVERSION=$1
else
PYTHONVERSION=3.4
fi

# If there is a second argument it is the directory to create the
# virtual environment in.
if [ $# -gt 1 ]
then
    VENV="../$2"
else
    VENV="../venv$PYTHONVERSION"
fi

REQUIREMENTS=requirements.txt
PYVENV="virtualenv -p python${PYTHONVERSION}"


# Finally we can go about creating the virtual environment and installing
# all of the dependencies.
${PYVENV} ${VENV}

# This will activate the python virtual environment as well as add the
# node_modules/ directory to the path so that we can use the node stuff that
# we install, such as coffee-script.
source develop.sh ${VENV}

# Then we have to install the python requirements.
pip install -r ${REQUIREMENTS}


# This essentially writes a small sitecustomize.py file into the virtual
# environment, this is required for coverage to work with subprocesses.
SITECUSTOMIZE="${VENV}/lib/python${PYTHONVERSION}/site-packages/sitecustomize.py"
echo import coverage >> ${SITECUSTOMIZE}
echo "coverage.process_startup()" >> ${SITECUSTOMIZE}

# Finally we have to install the node modules that we require, so for this
# you will need to have 'npm' installed.
npm install coffee-script
echo "To run the tests you will need to run 'npm install casperjs'"
