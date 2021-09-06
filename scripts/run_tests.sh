#!/usr/bin/env bash

source ./scripts/set_env.sh

eval "python -m coverage run -m unittest discover -v --failfast ./tests"
TEST_OUTPUT=$?

eval "python -m coverage report -m --omit="tests/*,/layers/google.*""

coverage-badge -o ./static/images/coverage-badge.svg -f

echo "TEST_OUTPUT:" $TEST_OUTPUT
exit $TEST_OUTPUT