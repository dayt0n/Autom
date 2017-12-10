#!/bin/sh
#
# run.sh - shell script to run car <-> Autom system
#
# to be run at startup on dedicated connected computer

unamestr=`uname`
while true; do
	python getData.py
	python data_backup.py
	python idleWait.py
	rc=$?
	if [[ $rc != 0 ]]; then 
		echo "Error in idleWait.py";
		echo $rc;
		if [[ "$unamestr" == 'Linux']]; then
			echo "Shutting down in 10 seconds"
			sleep 10
			poweroff # shutdown w/o sudo
		else
			echo "Exiting"
			exit
		fi
	fi
done