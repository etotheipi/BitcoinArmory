import sys
import psutil
import time

try:
   pid_armory   = int(sys.argv[1])
   pid_bitcoind = int(sys.argv[2])
except:
   print 'USAGE: %d armorypid bitcoindpid' % argv[0]
   exit(0)


def check_pid(pid, name):
   try:
      proc = psutil.Process(pid)
      for arg in proc.cmdline:
         if name.lower() in arg.lower():
            return True
   except psutil.error.NoSuchProcess:
      pass

   return False


# Verify the two PIDs are valid
print 'ArmoryQt is running:', check_pid(pid_armory,   'armoryqt')
print 'bitcoind is running:', check_pid(pid_bitcoind, 'bitcoind')


while True:
   time.sleep(3)
   if not check_pid(pid_armory, 'armoryqt'):
      print 'ArmoryQt died!'
      break
   

if check_pid(pid_bitcoind, 'bitcoind'):
   psutil.kill(pid_bitcoind)
