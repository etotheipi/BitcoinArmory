################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import decimal
import json

from armoryengine.ALL import *


# Some non-twisted json imports from jgarzik's code and his UniversalEncoder
class UniversalEncoder(json.JSONEncoder):
   def default(self, obj):
      if isinstance(obj, decimal.Decimal):
         return float(obj)
      return json.JSONEncoder.default(self, obj)


#############################################################################
def checkArmoryD():
   retVal = True
   sock = socket.socket()

   # Try to create a connection to the Armory server. If an error is thrown,
   # that means the server doesn't exist.
   try:
      # For now, all we want to do is see if the server exists.
      sock = socket.create_connection(('127.0.0.1',getRPCPort()), 0.1);
   except socket.error:
      LOGERROR('No armoryd.py instance is running')
      retVal = False

   # Clean up the socket and return the result.
   sock.close()
   return retVal


#############################################################################
def execute(args):
   # Open the armoryd.conf config file. At present, it's just a username and
   # password (e.g., "frank:abc123").
   '''
   Function that sets up and executes an armoryd command using JSON-RPC.
   '''
   with open(getArmoryDConfFile(), 'r') as f:
      usr,pwd = f.readline().strip().split(':')

   # If the user gave a command, create a connection to the armoryd server
   # and attempt to execute the command.
   if args:
      # Make sure the command is lowercase.
      args[0] = args[0].lower()
      # Create a proxy pointing to the armoryd server.
      proxyobj = ServiceProxy("http://%s:%s@127.0.0.1:%d" % \
                              (usr, pwd, getRPCPort()))
      # Let's try to get everything set up for successful command execution.
      try:
         extraArgs = []
         for arg in ([] if len(args)==1 else args[1:]):
            # It is possible to pass in JSON-formatted data (e.g.,
            # {"myName":"Terry"}). This isn't smart because no armoryd
            # commands can handle them. But, just in case this changes in the
            # future, we'll decode them anyway and let the functions fail on
            # their own terms. "Normal" args, however, will work for now.
            if len(arg) > 0 and arg[0] == '{':
               # JSON input example:  {"Ages":(10.23, 39.21)}
               # json.loads() output: {u'Ages', [10.23, 39.21]}
               extraArgs.append(json.loads(arg))
            else:
               extraArgs.append(arg)
         # Call the user's command (e.g., "getbalance full" ->
         # jsonrpc_getbalance(full)) and print results.
         result = proxyobj.__getattr__(args[0])(*extraArgs)
         if type(result) in (unicode, str):
            print (result)
         else:
            print (json.dumps(result, indent=4, sort_keys=True,
                              cls=UniversalEncoder))
         # If there are any special cases where we wish to do some
         # post-processing on the client side, do it here.
         # For now, no such post-processing is required.
      except Exception as e:
         # stop commands shouldn't print a message
         if args[0] == "stop":
            return
         # The command was bad. Print a message.
         errtype = str(type(e))
         errtype = errtype.replace("<class '",'')
         errtype = errtype.replace("<type '",'')
         errtype = errtype.replace("'>",'')
         errordict = { 'error': {
            'errortype': errtype,
            'jsoncommand': args[0],
            'jsoncommandargs': ([] if len(args)==1 else args[1:]),
            'extrainfo': str(e) if len(e.args)<2 else e.args}}

         print json.dumps( errordict, indent=4, sort_keys=True, cls=UniversalEncoder)
   else:
      raise RuntimeError("nothing to do!")


if __name__ == "__main__":
   initializeOptions()
   initializeLog()
   if checkArmoryD():
      execute(getCommandLineArgs())
   else:
      print ("Couldn't connect to server.\n"
             "It looks like armoryd is not running.\n"
             "Please start armoryd before calling armory-cli.\n")
