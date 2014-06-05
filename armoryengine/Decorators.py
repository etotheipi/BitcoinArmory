################################################################################
#
# Copyright (C) 2011-2014, Armory Technologies, Inc.                         
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  20 November, 2011
#
################################################################################

from armoryengine.ArmoryUtils import send_email
import functools

# Following this pattern to allow arguments to be passed to this decorator:
# http://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
def EmailOutput(send_from, server, password, send_to, subject='Armory Output'):
   def ActualEmailOutputDecorator(func):
      @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
      def wrapper(*args, **kwargs):
         ret = func(*args, **kwargs)  # Run dec'd func before sending e-mail
         if ret and send_from and server and password and send_to:
            send_email(send_from, server, password, send_to, subject, ret)
         return ret
      return wrapper

   return ActualEmailOutputDecorator
