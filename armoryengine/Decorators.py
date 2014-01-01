################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
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
from armoryengine.ArmoryUtils import LOGWARN, LOGERROR


import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

def send_email(send_from, send_to, subject, text):
   if not type(send_to) == list:
      raise AssertionError
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
   mailServer.login('armorynotify@gmail.com', 'Notification')
   mailServer.sendmail(send_from, send_to, msg.as_string())
   mailServer.close()

def EmailOutput(func, send_from='armorynotify@gmail.com',
                 send_to=['andy@bitcoinarmory.com'], subject='Armory Output'):
   def inner(*args, **kwargs):
      ret = func(*args, **kwargs)
      if ret:
         send_email(send_from, send_to, subject, ret)
      return ret
   return inner








