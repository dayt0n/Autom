# getData.py - record video and CAN bus data from a supported vehicle
#
# by dayt0n 2017
#
import os
import sys
import getpass
from pyvit import can
from pyvit.hw import cantact
import time
import datetime
import subprocess
import csv
import threading
import cv2
import bz2
import configparser

end = False

def get_image(camera):
	retval, im = camera.read()
	return im

def hasExternalStorage():
	login = getpass.getuser()
	medias = os.listdir("/media/"+login+"/")
	if len(medias) == 0:
		return False
	else:
		return str("/media/" + login + "/" + medias[0])

def vision(datfile,lastDat):
	global end
	cv2.namedWindow("visiond")
	vc = cv2.VideoCapture(0)
	fps = vc.get(cv2.CAP_PROP_FPS)
	vc.set(cv2.CAP_PROP_GAIN,0) # attempt to fix nighttime issues
	if not fps:
		print("Error getting fps, sticking with fifteen.")
		fps = 15.0
	else:
		print("got fps: %d" % fps)
	delay = int(1000 / (int(fps)))
	frame_width = int(vc.get(3))
	frame_height = int(vc.get(4))
	if os.path.isfile("output.m4v"): # check for remnants of last video and handle it
		with open(lastDat,"r") as f:
			firstLine = f.readline().rstrip()
		os.rename("output.m4v","output_" + firstLine + ".m4v")
	fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
	out = cv2.VideoWriter('output.m4v',fourcc,fps,(frame_width,frame_height))
	datfile.write(str(time.time()) + "\n") # write begin time
	print("Started video service")
	while(vc.isOpened()):
		if end == True:
			break
		rval,frame = vc.read()
		if rval == True:
			frame = cv2.resize(frame,(frame_width,frame_height))
			out.write(frame)
			cv2.imshow("visiond",frame)
			key = cv2.waitKey(delay)
			if key == 27:
				end = True
				break
		else:
			continue
	datfile.write(str(time.time()) + "\n") # write end time
	vc.release()
	out.release()
	cv2.destroyWindow("visiond")

class myThread(threading.Thread):
	def __init__(self,datfile,lastDat):
		threading.Thread.__init__(self)
		self.datfile = datfile
		self.lastDat = lastDat
	def run(self):
		print("Starting video service...")
		vision(self.datfile,lastDat)
		print("Stopping video service...")


if len(sys.argv) > 1:
	if sys.argv[2] == "-h" or sys.argv[2] == "--help":
		print("usage: %s [/dev/cu.*]") % sys.argv[0]
		exit(0)

config = configparser.ConfigParser()
config.read('config.cfg')
vehicle = config.get('DRIVE','vehicle')
if vehicle == "CHEVY VOLT":
	GEAR_SHIFT = 0x135 # ID for GEAR_SHIFT
	DRIVE = 0x02
	SHIFT_PLACE = 0x0 # place is byte in data like this: { [here] [~] [~] [~] [~] [~] [~] [~] }
	ENGINE_STATUS = 0xC9
	ENGINE_OFF = 0x0
	ENGINE_OFF_PLACE = 0x0
else:
	print("Vehicle not supported, exiting...")
	exit(0)
# more options to come in the future

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
dev.set_bitrate(500000)
if sys.platform == "linux" or sys.platform == "linux2": # b/c SocketCAN
	dev.ser.write('S6\r'.encode())
drive = False
if sys.platform == "linux" or sys.platform == "linux2":
	hasDevice = hasExternalStorage()
	if hasDevice:
		os.chdir(hasDevice)
dev.start()
while not drive:
	try:
		frame = dev.recv()
	except (KeyboardInterrupt,SystemExit):
		print("Exiting...")
		dev.stop()
		sys.exit()
	except:
		print("exception, trying again")
		time.sleep(2)
		continue
	if frame.arb_id == GEAR_SHIFT and frame.data[SHIFT_PLACE] != DRIVE: # this also works as a check to see if the car is actually on before you do anything
		print("Waiting for car to shift to drive")
	elif frame.arb_id == GEAR_SHIFT and frame.data[SHIFT_PLACE] == DRIVE:
		print("Drive detected, continuing...")
		drive = True
lastDat = "data_latest.txt"
if os.path.isfile("data_latest.txt"): # check for remnants of last data backup info and handle it
	with open("data_latest.txt","r") as f:
		firstLine = f.readline().rstrip()
	lastDat = "data_" + firstLine + ".txt"
	os.rename("data_latest.txt",lastDat)

latestDat = open("data_latest.txt","w")
thisTime = str(datetime.datetime.now())
thisTime = thisTime.replace(" ","_") # replace spaces with underscores for better navigation
thisTime = thisTime.replace("/","-") # same with forward slashes
thisTime = thisTime.replace(":","-")
latestDat.write(thisTime + "\n") # let backup service know start time
filename = "CAN_" + thisTime + ".csv"
latestDat.write(filename + "\n") # let backup service know latest file
file = bz2.BZ2File(filename,"wb")
writer = csv.writer(file,delimiter=",",quotechar=" ",quoting=csv.QUOTE_MINIMAL,lineterminator='\n')
writer.writerow(['Time','ID','DLC','Data'])
print("Collecting data in " + filename + "...")
vidThread = myThread(latestDat,lastDat)
vidThread.start() # start videoing
engineOffCounter = 0
while not end:
	try:
		frame = dev.recv()
		writer.writerow([str(time.time()),frame.arb_id,frame.dlc,str(frame.data)])
		if frame.arb_id == ENGINE_STATUS and frame.data[ENGINE_OFF_PLACE] == ENGINE_OFF: # engine has turned off, time to wrap things up...
			engineOffCounter += 1
			print("Detected engine off signal (%d/20) at %s" % (engineOffCounter,str(time.time()))) # added because in cold temperatures engine cuts on/off
			# in the future, probably need to add a timing mechanism instead of a counter
			if engineOffCounter == 20:
				end = True
				break
	except (KeyboardInterrupt,SystemExit):
		end = True
		break
print("Exiting...")
vidThread.join()
file.close()
latestDat.close()
dev.stop()
exit(0)