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

################################################################################
#
# Note that, for now, the code ONLY supports sending e-mails from a GMail
# account.
#
################################################################################

from armoryengine.ArmoryUtils import LOGWARN, LOGERROR
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

import smtplib
import os
import functools

def send_email(send_from, password, send_to, subject, text):
   # smtp.sendmail() requires a list of recipients. If we didn't get a list,
   # create one.
   if not type(send_to) == list:
      send_to = [send_to]
      
   msg = MIMEMultipart()
   msg['From'] = send_from
   msg['To'] = COMMASPACE.join(send_to)
   msg['Date'] = formatdate(localtime=True)
   msg['Subject'] = subject
   msg.attach(MIMEText(text))
   mailServer = smtplib.SMTP('smtp.gmail.com', 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(send_from, password)
   mailServer.sendmail(send_from, send_to, msg.as_string())
   mailServer.close()

# Following this pattern to allow arguments to be passed to this decorator:
# http://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
def EmailOutput(send_from, password, send_to, subject='Armory Output'):
   def ActualEmailOutputDecorator(func):
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
         ret = func(*args, **kwargs)
         if ret and send_from and password and send_to:
            send_email(send_from, password, send_to, subject, ret)
         return ret
      return wrapper

   return ActualEmailOutputDecorator
