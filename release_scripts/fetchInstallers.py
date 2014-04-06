import subprocess
import os
import time
import sys
import shutil
import ast
from release_utils import execAndWait

verStr   = sys.argv[1]
typeStr  = sys.argv[2]
localDir = sys.argv[3]



def doFetch():

   fetchList = ast.literal_eval(open('fetchlist.txt','r').read().strip())

   if os.path.exists(localDir):
      shutil.rmtree(localDir)
   os.mkdir(localDir)


   for cmd,cplist in fetchList.iteritems():
      if cmd=='cp':
         for src,dst in cplist:
            src_ = src%verStr
            dst_ = os.path.join(localDir, dst%(verStr,typeStr))
            print 'Copying: %s --> %s' % (src_,dst_)
            shutil.copy(src_,dst_)
      if cmd=='scp':
         for usr,ip,port,path,rllist in cplist:
            for rem,loc in rllist:
            
               remotePath = os.path.join(path, rem%verStr)
               hostPath = '%s@%s:%s' % (usr,ip,remotePath)
               localPath  = os.path.join(localDir, loc % (verStr,typeStr))
         
               cmdList = ['scp', '-P', str(port), hostPath, localPath]
               #print ' '.join(cmdList)
               execAndWait(cmdList)
      

