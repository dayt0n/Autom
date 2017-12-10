import os
import pysftp
import sys
import time
import datetime
import zipfile
import socket

prkey = "/Users/DaytonHasty/.ssh/car_backup_rsa"
end = False
latest = True

def canConnect():
	try:
		socket.setdefaulttimeout(3)
		socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect(("192.168.1.157",56382)) # only backup on home network
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

while not end:
	if not canConnect():
		print("Unable to find backup server, check internet connection. Retrying...")
		time.sleep(3)
		continue
	if not os.path.isfile("data_latest.txt"): # check for past unbacked up files
		print("No data_latest.txt, searching for unbacked up files...")
		latest = False
		foundFiles = False
		files = os.listdir(".")
		for f in files:
			if "data_" in f and f != "data_backup.py":
				print("Found %s, attempting to backup...") % f
				os.rename(f,"data_latest.txt")
				foundFiles = True
				break
		if not foundFiles:
			print("No previous backups remaining, everything seems to be up to date. Exiting...")
			break
	dat = open("data_latest.txt")
	lines = dat.readlines()
	lines = [l.rstrip() for l in lines] # remove newlines
	CANtime = lines[0]
	CANfile = lines[1]
	videoStart = lines[2]
	videoEnd = lines[3]
	if not latest:
		os.rename("output_" + CANtime + ".m4v","output.m4v")
	#SFTP stuff
	srv = pysftp.Connection(host="192.168.1.157",username="carbackup",private_key=prkey,log="/tmp/pysftp.log")
	end = False
	with srv.cd("/home/carbackup/backup"):
		if srv.isfile(CANtime + ".zip"): # file is already there, no need to continue
			print("File aready exists, continuing.")
			continue
	zipName = CANtime + ".zip"
	with zipfile.ZipFile(zipName,"w") as currentZip: # compress because they are big files
		print("zipping files")
		currentZip.write("data_latest.txt")
		currentZip.write("output.m4v")
		currentZip.write(CANfile)
	with srv.cd("/home/carbackup/backup"):
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
		with srv.cd("/home/carbackup/backup"):
			srv.remove(zipName)
		os.rename("data_latest.txt","data_" + CANtime + ".txt")
		os.rename("output.m4v","output_" + CANtime + ".m4v")

		continue
	print("File size match, transfer success")
	print("Cleaning up")
	os.remove("output.m4v")
	os.remove("data_latest.txt")
	os.remove(CANfile)
	dat.close()
	srv.close()
exit(0)