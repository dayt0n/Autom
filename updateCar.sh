# updateCar.sh - script to update the software over SSH

if [ $(pgrep -f run.sh) ]; then # kill run.sh to initiate update if it is running
	PID=`pgrep -f run.sh`
	kill -9 $PID
fi

wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "Device is online, attempting update..."
    git pull
else
    echo "Device is offline"
fi
