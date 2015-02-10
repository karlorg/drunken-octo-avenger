#! /bin/sh

TEST_COMMAND="python manage.py test_all"

if [ "$1" == "coverage" ]
then
TEST_COMMAND="python manage.py coverage"
fi

if [ "$1" == "quick" ]
then
TEST_COMMAND="python manage.py test_module app.tests.test"
fi

echo $TEST_COMMAND

test_python(){
    rm -fr ../testvenv$1
    source setup.sh $1 testvenv$1
    $TEST_COMMAND
    deactivate
}

test_python 3.4
test_python 2.7
