from armoryengine import *
from sys import argv

with open(argv[1], 'rb') as f:
   f.seek(long(argv[2]))
   k = f.read(1024)

   pprintHex( binary_to_hex(k))

