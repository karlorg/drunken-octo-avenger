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
    test_result=$?
    deactivate
    rm -fr ../testvenv$1
    return $test_result
}

test_series() {
    for version in "$@"
    do
        test_python $version
        if [[ $? != 0 ]]
        then
            echo Tests failed for Python ${PYTHONVERSION}
            return 1
        fi
    done
}

test_series 3.4 2.7
