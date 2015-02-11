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
    VENV="../tmpvenv"
fi

# Creating a virtual environment and which requirements file to use depends
# upon which version of python we are using.
if [ $(echo "$PYTHONVERSION < 3.0" | bc) -ne 0 ] 
then
    PYVENV=virtualenv
    REQUIREMENTS=requirements.txt
else
    PYVENV=pyvenv
    REQUIREMENTS=p3req.txt
fi

# Finally we can go about creating the virtual environment and installing
# all of the dependencies.
${PYVENV} ${VENV}
source ${VENV}/bin/activate

# This essentially writes a small sitecustomize.py file into the virtual
# environment, this is required for coverage to work with subprocesses.
SITECUSTOMIZE="${VENV}/lib/python${PYTHONVERSION}/site-packages/sitecustomize.py"
echo import coverage >> ${SITECUSTOMIZE}
echo "coverage.process_startup()" >> ${SITECUSTOMIZE}
pip install -r ${REQUIREMENTS}
