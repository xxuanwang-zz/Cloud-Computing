#!/bin/bash -x

if (( $# < 2 )); then
    echo "./restore-student-repo-cicd.sh <studentName> <assignmentName>"
    exit 0
fi

dirName=$1
assignmentName=$2

currentdir=`pwd`

cd $dirName/$assignmentName

gitcommit=`git log --pretty=oneline | grep -v good-application | grep -v bad-application| grep -v Original | grep -v Merge | awk '{print $1}' | head -1`

echo "Checkout commit:$gitcommit"

git checkout $gitcommit

cp application.py application.py.orig

more application.py

git checkout master

cp application.py.orig application.py

git add application.py

git commit -m "Restoring Original application.py"

git push origin master

cd $currentdir
