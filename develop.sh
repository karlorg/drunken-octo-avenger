#! /bin/sh

# We set the virtual environment, first if it is specified on the command
# line, then we assume that is correct.
if [ $# -gt 0 ]
then
VENV=$1
else
    # If it is not specified on the command line we check for the existance
    # of a ../venv3.4 directory, if that exists we set that as the virtual
    # environment otherwise we complain and exit.
    if [ -d "../venv3.4" ]
    then
    VENV=../venv3.4
    else
        echo "I don't know where your virtual environment is"
        echo "Perhaps you need to run setup.sh?"
        echo "Otherwise please specify your venv"
        return 1
    fi
fi

source $VENV/bin/activate
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export PATH=$DIR/node_modules/.bin/:$PATH
