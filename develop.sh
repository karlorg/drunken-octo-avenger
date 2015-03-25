#! /bin/sh

if [ $# -gt 0 ]
then
VENV=$1
else
VENV=venv
fi

source ../$VENV/bin/activate
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export PATH=$DIR/node_modules/.bin/:$PATH
