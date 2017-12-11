#!/bin/sh
#
# run.sh - shell script to run car <-> Autom system
#
# to be run at startup on dedicated connected computer

cd $(dirname $0)
unamestr=`uname`
while true; do
	python getData.py
	python data_backup.py
	python idleWait.py
	rc=$?
	if [ $rc != 0 ]; then 
		echo "Error in idleWait.py";
		echo $rc;
		echo "Exiting";
		exit;
	fi
done