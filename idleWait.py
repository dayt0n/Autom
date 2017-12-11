import os
import sys
from pyvit import can
from pyvit.hw import cantact
import time
import subprocess

if len(sys.argv) > 1:
	if sys.argv[2] == "-h" or sys.argv[2] == "--help":
		print("usage: %s [/dev/cu.*]") % sys.argv[0]
		exit(0)
serialDev = ""
if len(sys.argv) == 1:
	# autodetect mode on, attempting to find serial device...
	while True:
		devList = os.listdir("/dev/")
		devCount = 0
		for f in devList:
			if sys.platform == "linux" or sys.platform == "linux2":
				if "ttyACM" in f:
					devCount += 1
					serialDev = "/dev/" + f
			elif sys.platform == "darwin":
				if "tty.usbmodem" in f:
					devCount += 1
					serialDev = "/dev/" + f
		if devCount == 0:
			print("Unable to locate a serial device")
			time.sleep(3)
			continue
		elif devCount == 1:
			print("Using device %s") % serialDev
			break
		elif devCount > 1:
			print("Multiple serial devices plugged, in. Please remove any extraneous devices.")
			time.sleep(3)
			continue
else:
	serialDev = sys.argv[1]
# must wait for device to be free
while True:
	proc = subprocess.Popen('lsof | grep ' + serialDev, stdout=subprocess.PIPE)
	tmp = proc.stdout.read()
	if "Modem" in tmp:
		sleep(5)
		continue
	else:
		break
print("Connecting to %s") % serialDev
dev = cantact.CantactDev(serialDev)
if not dev:
	print("Error in connecting to %s, exiting") % serialDev
	exit(-1)
dev.set_bitrate(500000)
if sys.platform == "linux" or sys.platform == "linux2":
	dev.ser.write('S6\r'.encode())
dev.start()
while True:
	frame = dev.recv()
	if frame.arb_id == 0xC9 and frame.data[0] != 0x0:
		print("Engine started, beginning data connection")
		break
	time.sleep(120) # sleep for two minutes as not to plague the car with requests
dev.stop()
exit(0)