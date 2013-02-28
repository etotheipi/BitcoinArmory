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
      procstr = ' '.join(proc.cmdline)
      if name=='':
         return procstr
      else:
         return procstr if procstr==name else False
   except psutil.error.NoSuchProcess:
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
      time.sleep(3)
      for i in range(3):
         if not check_pid(pid):
            print 'Regular TERMINATE succeeded'
            break
         else:
            print 'Regular TERMINATE failed; try again in 1 sec...'
            time.sleep(1)
         print 'Killing process ...'
         os.kill(pid, signal.SIGKILL)
      


# Verify the two PIDs are valid
proc_name_armory   = check_pid(pid_armory)
proc_name_bitcoind = check_pid(pid_bitcoind)

if proc_name_armory:
   print 'ArmoryQt is running in pid=%d (%s)' % (pid_armory, proc_name_armory)
else:
   print 'ArmoryQt IS NOT RUNNING!'


if proc_name_bitcoind:
   print 'bitcoind is running in pid=%d (%s)' % (pid_bitcoind, proc_name_bitcoind)
else:
   print 'bitcoind IS NOT RUNNING!'


while True:
   time.sleep(3)

   if not check_pid(pid_armory, proc_name_armory):
      print 'ArmoryQt died!'
      break

   if not check_pid(pid_bitcoind, proc_name_bitcoind):
      print 'bitcoind disappeared -- guardian exiting'
      exit(0)
   

if check_pid(pid_bitcoind, proc_name_bitcoind):
   kill(pid_bitcoind)



