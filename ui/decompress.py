# decompress.py - a small utility to decompress bz2 files because calling bunzip from system() or using libbzip2 doesn't work for some reason
#
# for use in automui

import sys
import bz2

if len(sys.argv) < 3:
	print("Incorrect usage\nusage: %s <bz2 file> <output>")
	exit(-1);
infile = sys.argv[1];
out = sys.argv[2];
fileobj = open(infile,"rb")
signature = fileobj.read(4)
fileobj.close()
if signature[:3] == b'BZh':
	compressed = bz2.BZ2File(infile,"rb")
	uncompressed = open(out,"wb");
	rawbz2 = compressed.read()
	uncompressed.write(rawbz2)
	uncompressed.close()
	compressed.close()