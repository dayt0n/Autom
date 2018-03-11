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

def canConnect(server,portNum):
	try:
		socket.setdefaulttimeout(3)
		socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((server,portNum))
		return True
	except Exception as ex:
		return False

def checkForUpdates():
	print("Checking for updates...")
	if not canConnect("8.8.8.8",53): # google DNS
		print("Unable to connect to the internet")
		return False
	os.chdir("..")
	subprocess.call(["git", "pull"])

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
	try:
		dev.ser.write('S6\r'.encode())
	except:
		print("Cannot write to bus")
		checkForUpdates()
		print("Shutting down...")
		subprocess.call(["sudo", "shutdown", "-h", "now"])
		exit(0)
try:
	dev.start()
except:
	print("Cannot start device")
	checkForUpdates()
	print("Shutting down...")
	subprocess.call(["sudo", "shutdown", "-h", "now"])
	exit(0)
delay = 0
canEngineStillGoing = False
while True:
	startTime = time.time()
	if time.time() > (startTime + 2) and not canEngineStillGoing: # engine stops sending out messages after a while
		# engine also sends multiple messages per second, so if there are none in two seconds, that means it has officially stopped responding
		print("Engine no longer sending out messages on the CAN bus")
		checkForUpdates()
		print("Shutting down...")
		subprocess.call(["sudo", "shutdown", "-h", "now"])
		exit(0)
	try:
		frame = dev.recv(timeout=1)
	except:
		print("CAN data read failed")
		checkForUpdates()
		print("Attempting to shut down...")
		subprocess.call(["sudo", "shutdown", "-h", "now"])
		exit(0)
	if frame.arb_id == 0xC9 and frame.data[0] != 0x0:
		print("Engine started, beginning data connection")
		break
	elif frame.arb_id == 0xC9 and frame.data[0] == 0x0 and delay < 5:
		canEngineStillGoing = True
		delay += 1
		print("Engine still off (%d/5)" % delay)
		time.sleep(5) # sleep for 5 seconds as not to plague the car with requests
	elif frame.arb_id == 0xC9 and frame.data[0] == 0x0 and delay >= 5:
		if sys.platform == "linux" or sys.platform == "linux2":
			dev.stop()
			checkForUpdates()
			print("Attempting to shutdown...")
			subprocess.call(["sudo", "shutdown", "-h", "now"]) # you should use `sudo vidsudo` and set your username to use sudo w/o password
			exit(0)
		if sys.platform == "darwin":
			dev.stop()
			checkForUpdates()
			subprocess.call(['osascript','-e','tell app "system events" to shut down'])
			exit(0)
dev.stop()
time.sleep(20) # we don't want to connect/disconnect too fast or else we will get a lot of error messages, possibly disabling the vehicle
exit(0)