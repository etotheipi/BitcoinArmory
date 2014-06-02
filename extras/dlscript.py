#! /usr/bin/python
import subprocess
import os
from sys import argv

if len(argv)<3:
   print 'Usage:  %s dirToDumpDpkgs <pkg1> <pkg2> ...' % argv[0]
   exit(1)

outDir = argv[1]
pkgs = argv[2:]
if not os.path.exists(outDir):
   os.makedirs(outDir)

cmd = ['apt-get', 'install', '--yes', '--print-uris']
cmd.extend(pkgs)
output = subprocess.check_output(cmd).split('\n')
output = filter(lambda x: x.startswith("'"), output)

dllist  = [out.split()[0][1:-1] for out in output]
filename= [os.path.join(outDir, out.split()[1]) for out in output]
md5list = [out.split()[-1].split(':')[-1] for out in output]

try:
   for dl,fil,md5 in zip(dllist, filename, md5list):
      try:
         subprocess.check_output(['wget', '-O', fil, dl]) 
      except Exception as e:
         print '***Error downloading file:', dl
         print '***Error: ', str(e)
         continue

      out = subprocess.check_output(['md5sum', fil]).split()[0]
      if not out==md5:
         print '***ERROR: MD5sum does not match!' 
         raise
except:
   for f in filename:
      if os.path.exists(f):
         os.remove(f)

