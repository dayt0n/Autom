# data_backup.py - sync times for video/CAN data and then upload to server
#
# by dayt0n 2017
#
import os
import getpass
import pysftp
import sys
import time
import datetime
import zipfile
import socket
import configparser
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import bz2
import csv

def changeLineInFile(fileLocation,lineNumber,string):
	file = open(fileLocation)
	lines = file.readlines()
	file.close()
	lines = [l.rstrip() for l in lines]
	lines[lineNumber] = string
	os.remove(fileLocation)
	newfile = open(fileLocation,"wb")
	for l in lines:
		newfile.write(l + "\n")
	newfile.close()

def hasExternalStorage():
	login = getpass.getuser()
	medias = os.listdir("/media/"+login+"/")
	if len(medias) == 0:
		return False
	else:
		return str("/media/" + login + "/" + medias[0])

def hasExternalServerStorage(srv):
	with srv.cd("/media/"):
		if srv.isdir(user):
			devs = srv.listdir()
			if len(devs) == 0:
				return False
			else:
				return str("/media/" + user + "/" + devs[0])
		else:
			return False

def canConnect():
	try:
		socket.setdefaulttimeout(5)
		socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((server,portNum)) # only backup on home network
		return True
	except Exception as ex:
		return False

def checkFileTransfer(srv,zipName):
	osattr = os.stat(zipName)
	val = True
	with srv.cd("/home/carbackup/backup"):
		attr = srv.stat(zipName)
		print("Local: %d Remote: %d") % (osattr.st_size,attr.st_size)
		if attr.st_size != osattr.st_size and os.st_size != 0:
			val = False
	return val

config = configparser.ConfigParser()
config.read('config.cfg')

prkey = config.get('SFTP','prkey')
server = config.get('SFTP','server')
user = config.get('SFTP','user')
portNum = int(config.get('SFTP','portNum'))
ifPassword = config.get('SFTP','ifPassword')
sshPass = config.get('SFTP',"sshPass")
if ifPassword == "false":
	ifPassword = False
else:
	ifPassword = True

end = False
latest = True
connectTimeout = 0
extStorage = hasExternalStorage()
if extStorage:
	os.chdir(extStorage)
while not end:
	if not canConnect():
		if connectTimeout >= 40: # wait two minutes
			print("Connection no where near by, quitting...")
			exit(0)
		print("Unable to find backup server, check internet connection. Retrying...")
		time.sleep(3)
		connectTimeout += 1
		continue
	if not os.path.isfile("data_latest.txt"): # check for past unbacked up files
		print("No data_latest.txt, searching for unbacked up files...")
		latest = False
		foundFiles = False
		files = os.listdir(".")
		for f in files:
			if "data_" in f and f != "data_backup.py":
				print("Found %s, attempting to backup...") % f
				if f != "data_.txt": # for some reason sometimes data files look like this and are empty
					os.rename(f,"data_latest.txt")
					foundFiles = True
					break
				else:
					os.remove(f)
		if not foundFiles:
			print("No previous backups remaining, everything seems to be up to date. Exiting...")
			break
	# sync video and CAN data time
	dat = open("data_latest.txt")
	lines = dat.readlines()
	lines = [l.rstrip() for l in lines] # remove newlines
	CANtime = lines[0]
	CANfile = lines[1]
	vidStart = float(lines[2])
	vidEnd = float(lines[3])
	if not latest:
		os.rename("output_" + CANtime + ".m4v","output.m4v")
	dat.close()
	fileobj = open(CANfile,"rb")
	signature = fileobj.read(4)
	fileobj.close()
	if signature[:3] == b'BZh': # it is bz2
		print("Detected bz2 compressed file, uncompressing CAN data...")
		compressed = bz2.BZ2File(CANfile,"rb")
		uncompressed = open("uncompressed.csv","wb")
		lineCount = -1
		try:
			rawbz2 = compressed.read()
			uncompressed.write(rawbz2)
		except (EOFError): # fix issue in case of abrupt stop in CAN data
			print("Unexpected EOF, attempting to fix issue... This might take a while... (YOU WILL LOSE DATA NEAR END OF FILE AND VIDEO)")
			uncompressed.close()
			compressed.close()
			compressed = bz2.BZ2File(CANfile,"rb") # restart line iteration
			try:
				while True:
					wholebz2 = compressed.readline()
					lineCount += 1
			except (EOFError):
				pass
			compressed.close()
			compressed = bz2.BZ2File(CANfile,"rb") # restart line iteration
			os.remove("uncompressed.csv")
			uncompressed = open("uncompressed.csv","wb")
			#lineCount -= 1
			for i in range(0,lineCount):
			 	wholebz2 = compressed.readline()
			 	uncompressed.write(wholebz2)
		uncompressed.close()
		compressed.close()
		os.remove(CANfile)
		os.rename("uncompressed.csv",CANfile)
	print("Reading %s..." % CANfile)
	os.rename(CANfile,"working.csv")
	file = open("working.csv")
	read = csv.reader(file,delimiter=",",quoting=csv.QUOTE_MINIMAL,lineterminator="\n")
	# get second line
	line = read.next()
	line = read.next()
	CANstart = float(line[0])
	iterations = 2
	if CANstart != vidStart:
		while CANstart < vidStart:
			iterations += 1
			CANstart = float((read.next())[0])
	# get CANend
	CANend = 0
	while True:
		try: 
			CANend = float((read.next())[0]) # read until EOF
		except:
			break
	print("CAN end: %f" % CANend)

	print("CAN start: %f\nVideo start: %f after %d iterations" % (CANstart,vidStart,iterations))
	if CANstart != vidStart:
		print("Time mismatch, CANstart doesn't match vidStart. Fixing...")
		if CANstart > vidStart:
			print("Shaving beginning of video to match CAN data...")
			secondsToShave = CANstart - vidStart
			vidLength = vidEnd - vidStart
			vidStart += secondsToShave
			ffmpeg_extract_subclip("output.m4v",secondsToShave,vidLength,targetname="shaved.m4v")
			changeLineInFile("data_latest.txt",2,str(vidStart))
			os.remove("output.m4v")
			os.rename("shaved.m4v","output.m4v")
	newFile = bz2.BZ2File(CANfile,"wb") # re-compress
	file.close()
	file = open("working.csv")
	CANlines = file.readlines()
	file.close()
	file = open("working.csv")
	secondRead = csv.reader(file,delimiter=",",quoting=csv.QUOTE_MINIMAL,lineterminator="\n")
	newFile.write(CANlines[0]) # write labels
	if iterations > 2:
		newIterations = iterations - 1
	elif iterations == 2:
		newIterations = 1 # this SHOULD work (?)
	elif iterations < 2:
		print("Error in counting iterations until video")
		sys.exit(-1)
	else:
		print("Error in iterations")
		sys.exit(-1)
	vidIterationsCAN = 0
	CANstopWrite = len(CANlines)
	if vidEnd != CANend:
		if vidEnd < CANend: # modify CAN file
			while CANend < vidEnd:
				vidIterationsCAN += 1
				CANend = float(secondRead.next()[0])
			if CANend == vidEnd:
				print("CANend and vidEnd match on line %d at %f" % (vidIterationsCAN,CANend))
				CANstopWrite = vidIterationsCAN
			else:
				print("ERROR: CANend: %f | vidEnd: %f" % (CANend,vidEnd))
		elif vidEnd > CANend: # modify video
			vidEnd -= (vidEnd - CANend)
			vidLength = vidEnd - vidStart
			ffmpeg_extract_subclip("output.m4v",0,vidLength,targetname="shaved.m4v")
			os.remove("output.m4v")
			os.rename("shaved.m4v","output.m4v")
			changeLineInFile("data_latest.txt",3,str(vidEnd))
			if vidEnd == CANend:
				print("Successfully trimmed video")
			else:
				print("Error determining trim for video")
		else:
			print("Error in comparing vidEnd and CANend")
			sys.exit(-1)
	else:
		print("CANend and vidEnd already match")
	print("Writing to new CAN file...")
	for i in range(newIterations,CANstopWrite):
		newFile.write(CANlines[i]) # write revalvent bit
	os.remove("working.csv")
	newFile.close()
	file.close()
	# start backup process
	#
	# SFTP stuff
	print("Initializing server connection")
	cnopts = pysftp.CnOpts()
	cnopts.hostkeys = None
	if ifPassword:
		srv = pysftp.Connection(host=server,username=user,password=sshPass,log="/tmp/pysftp.log",port=portNum,cnopts=cnopts)
	else:
		srv = pysftp.Connection(host=server,username=user,private_key=prkey,log="/tmp/pysftp.log",port=portNum,cnopts=cnopts)
	end = False
	serverMedia = hasExternalServerStorage(srv)
	if serverMedia:
		serverCD = "/media/" + user + "/" + serverMedia
	else:
		serverCD = "/home/" + user
	with srv.cd(serverCD):
		if not srv.isdir("backup"):
			srv.mkdir("backup")
	serverCD += "/backup"
	with srv.cd(serverCD):
		if srv.isfile(CANtime + ".zip"): # file is already there, no need to continue
			print("File aready exists, continuing.")
			continue
	zipName = CANtime + ".zip"
	with zipfile.ZipFile(zipName,"w") as currentZip: # compress because they are big files
		print("zipping files")
		currentZip.write("data_latest.txt")
		currentZip.write("output.m4v")
		currentZip.write(CANfile)
	with srv.cd(serverCD):
		print("uploading zip file")
		if not srv.put(zipName,preserve_mtime=True):
			print("Error uploading, deleting zip...")
			os.remove(zipName)
			continue
		else:
			print("done uploading")
	didTransfer = checkFileTransfer(srv,zipName)
	os.remove(zipName)
	if didTransfer == False:
		print("File mismatch, deleting...")
		with srv.cd(serverCD):
			srv.remove(zipName)
		os.rename("data_latest.txt","data_" + CANtime + ".txt")
		os.rename("output.m4v","output_" + CANtime + ".m4v")

		continue
	print("File size match, transfer success")
	print("Cleaning up")
	os.remove("output.m4v")
	os.remove("data_latest.txt")
	os.remove(CANfile)
	srv.close()
# final cleanup
remainingFiles = os.listdir(".")
if len(remainingFiles) != 0:
	if len(remainingFiles) == 1:
		if remainingFiles[0] != ".Trashes":
			os.remove(remainingFiles[0])
	else:
		for f in remainingFiles:
			os.remove(f)
exit(0)