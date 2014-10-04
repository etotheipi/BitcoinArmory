import os
import subprocess
import time


def setEnv(var, val):
   print 'Setting environment var: $%s to %s' % (var,val)
   os.environ[str(var)] = str(val)


def popen(cmdList, cwd=None):
   print '*'*80
   print 'Executing: "%s"' % ' '.join(cmdList)
   proc = subprocess.Popen(cmdList, cwd=cwd)
   while proc.poll() is None:
      time.sleep(1)
   print 'Done with: "%s"' % ' '.join(cmdList)
   print '*'*80


verStr = ''
for line in open('armoryengine/ArmoryUtils.py','r').readlines():
   if line.startswith('BTCARMORY_VERSION'):
      c0 = line.find('(')+1
      c1 = line.find(')')
      vquad = [int(istr.strip()) for istr in line[c0:c1].split(',')]
      verStr = '%d.%02d' % tuple(vquad[:2])
      if (vquad[2] > 0 or vquad[3] > 0):
         verStr += '.%d' % vquad[2]
      if vquad[3] > 0:
         verStr += '.%d' % vquad[3]
      break

print 'Armory version:', verStr 
instDir = 'armory_%s_raspbian-armhf' % verStr
targz   = '../' + instDir + '.tar.gz'
os.makedirs(instDir)

popen(['make', 'CXX=/home/alan/x-tools/arm-unknown-linux-gnueabi/bin/arm-unknown-linux-gnueabi-g++'])
popen(['make', 'install', 'DESTDIR=%s'%instDir])
popen(['tar','-zcf', targz, 'usr'], cwd=instDir)


