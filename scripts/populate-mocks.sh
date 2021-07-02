#!/bin/bash

COURSES=( "TEST_NBGRADER" "BIPN162_S120_A00" "COGS108_SP21_A00" "CSE284_SP21_A00")

if [ $# -eq 0 ]
  then
    echo "Please supply a username to its-dsmlp-fs01"
    exit 1
fi

for course in "${COURSES[@]}"; do
  mkdir -p mocks/$course/grader
  scp -r $1@its-dsmlp-fs01:/export/nbgrader/dsmlp/$course/grader/gradebook.db ./mocks/$course/grader
done