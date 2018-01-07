# idleWait.py - allow grace period after engine shutdown incase of quick car restart
#
# by dayt0n 2017
#
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
print("Connecting to %s") % serialDev
dev = cantact.CantactDev(serialDev)
if not dev:
	print("Error in connecting to %s, exiting") % serialDev
	exit(-1)
dev.set_bitrate(500000)
if sys.platform == "linux" or sys.platform == "linux2":
	dev.ser.write('S6\r'.encode())
dev.start()
minutes = 0
while True:
	frame = dev.recv()
	if frame.arb_id == 0xC9 and frame.data[0] != 0x0:
		print("Engine started, beginning data connection")
		break
	elif frame.arb_id == 0xC9 and frame.data[0] == 0x0 and minutes < 5:
		minutes += 1
		time.sleep(60) # sleep for two minutes as not to plague the car with requests
	elif frame.arb_id == 0xC9 and frame.data[0] == 0x0 and minutes >= 5:
		# shut down computer w/o root priviledges (ConsoleKit runs as root, so just need to hijack it)
		if sys.platform == "linux" or sys.platform == "linux2":
			dev.stop()
			subprocess.call(["sudo", "shutdown", "-h", "now"]) # you should use `sudo vidsudo` and set your username to use sudo w/o password
			exit(0)
		if sys.platform == "darwin":
			dev.stop()
			subprocess.call(['osascript','-e','tell app "system events" to shut down'])
			exit(0)
dev.stop()
exit(0)