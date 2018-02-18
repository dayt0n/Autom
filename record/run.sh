#!/bin/sh
#
# run.sh - shell script to run car <-> Autom system
#
# to be run at startup on dedicated connected computer
#
# by dayt0n 2017

counter=0
cd $(dirname $0)
currentDate=`date +%Y-%m-%d`
oldDate=`date --date="10 days ago" +%Y-%m-%d`
if [ -f record.log ]; then
	if grep -Fxq $oldDate record.log; then
		# only keep logs of past 10 days
		sed -n -E -e '/$oldDate/,$ p' record.log | sed '1 d'
	fi
fi
echo $currentDate >> record.log
unamestr=`uname`
echo "Allowing device time to be free"
sleep 22 # wait for device to intialize
echo "Applying video settings"
v4l2-ctl -d /dev/video0 -c exposure_auto=1 -c exposure_absolute=5
while true; do
	stdbuf -oL python getData.py 2>&1 | tee -a record.log
	stdbuf -oL python data_backup.py 2>&1 | tee -a record.log
	stdbuf -oL python idleWait.py 2>&1 | tee -a record.log
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