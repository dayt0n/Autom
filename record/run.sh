#!/bin/sh
#
# run.sh - shell script to run car <-> Autom system
#
# to be run at startup on dedicated connected computer
#
# by dayt0n 2017

counter=0
cd $(dirname $0)
$currentDate=`date +%Y-%m-%d`
$oldDate=`date -v -10d +%Y-%m-%d`
if [ -f record.log]; then
	if grep -Fxq $oldDate record.log; then
		# only keep logs of past 10 days
		sed -n -E -e '/$oldDate/,$ p' record.log | sed '1 d'
	fi
fi
echo $currentDate > record.log
unamestr=`uname`
echo "Allowing device time to be free"
sleep 22 # wait for device to intialize
while true; do
	python getData.py 2>&1 | tee -a record.log
	python data_backup.py 2>&1 | tee -a record.log
	python idleWait.py 2>&1 | tee -a record.log
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