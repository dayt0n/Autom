import os
import pysftp
import sys
import time
import datetime
import zipfile

prkey = "/Users/DaytonHasty/.ssh/car_backup_rsa"

dat = open("data_latest.txt")
lines = dat.readlines()
lines = [l.rstrip() for l in lines] # remove newlines
CANtime = lines[0]
CANfile = lines[1]
videoStart = lines[2]
videoEnd = lines[3]

#SFTP stuff
srv = pysftp.Connection(host="192.168.1.157",username="carbackup",private_key=prkey,log="/tmp/pysftp.log")
end = False
with srv.cd("/home/carbackup/backup"):
	if srv.isfile(CANtime + ".zip"): # file is already there, no need to continue
		print("File aready exists, exiting.")
		end = True
if end:
	srv.close()
	sys.exit()
zipName = CANtime + ".zip"
with zipfile.ZipFile(zipName,"w") as currentZip: # compress because they are big files
	print("zipping files")
	currentZip.write("data_latest.txt")
	currentZip.write("output.m4v")
	currentZip.write(CANfile)
with srv.cd("/home/carbackup/backup"):
	print("uploading zip file")
	if not srv.put(zipName,preserve_mtime=True):
		print("Error uploading, archiving...")
		"""

		TODO


		"""
	else:
		print("done uploading")
print("Cleaning up")
"""

TODO


"""
print("Exiting...")
srv.close()
