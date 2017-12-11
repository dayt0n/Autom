#!/bin/sh
#
# run.sh - shell script to run car <-> Autom system
#
# to be run at startup on dedicated connected computer

counter=0
cd $(dirname $0)
unamestr=`uname`
echo "Allowing device time to be free"
sleep 22 # wait for device to intialize
while true; do
	python getData.py
	python data_backup.py
	python idleWait.py
	rc=$?
	if [ $rc != 0 ]; then
		counter=$((counter+1))
		sleep 5
		if [ "$counter" -gt 2 ]; then
			echo "Error in idleWait.py";
			echo $rc;
			echo "Exiting";
			exit;
		fi
	fi
done