import sys
import psutil
import time
import platform
import os
import signal

opsys = platform.system()
OS_WINDOWS = 'win32'  in opsys.lower() or 'windows' in opsys.lower()

try:
   pid_armory   = int(sys.argv[1])
   pid_bitcoind = int(sys.argv[2])
except:
   print 'USAGE: %d armorypid bitcoindpid' % argv[0]
   exit(0)


def check_pid(pid, name=''):
   try:
      proc = psutil.Process(pid)
      if name=='':
         return True
      else:
         for arg in proc.cmdline:
            if name.lower() in arg.lower():
               return True
   except psutil.error.NoSuchProcess:
      pass

   return False


def kill(pid):
   if OS_WINDOWS:
      #import ctypes
      #k32 = ctypes.windll.kernel32
      #handle = k32.OpenProcess(1,0,pid)
      #return (0 != k32.TerminateProcess(handle,0))
      os.kill(pid, signal.CTRL_C_EVENT)
   else:
      os.kill(pid, signal.SIGTERM)
      for i in range(3):
         if not check_pid(pid)
            print 'Regular TERMINATE succeeded'
            break
         else:
            print 'Regular TERMINATE failedi; try again in 1 sec...'
            time.sleep(1)
         print 'Killing process ...'
         os.kill(pid, signal.SIGKILL)
      


# Verify the two PIDs are valid
print 'ArmoryQt is running:', check_pid(pid_armory,   'armoryqt')
print 'bitcoind is running:', check_pid(pid_bitcoind, 'bitcoind')


while True:
   time.sleep(3)
   if not check_pid(pid_armory, 'armoryqt'):
      print 'ArmoryQt died!'
      break
   

if check_pid(pid_bitcoind, 'bitcoind'):
   kill(pid_bitcoind)
