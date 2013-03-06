from sys import argv, path
path.append('..')
path.append('.')

from armoryengine import *

with open(argv[1], 'rb') as f:
   f.seek(long(argv[2]))
   k = f.read(1024)

   pprintHex( binary_to_hex(k))

