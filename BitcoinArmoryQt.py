#! /usr/bin/python
################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    BitcoinArmory          (https://github.com/etotheipi/BitcoinArmory)
# Author:     Alan Reiner
# Orig Date:  20 November, 2011
# Descr:      This file serves as an engine for python-based Bitcoin software.
#             I forked this from my own project -- PyBtcEngine -- because I
#             I needed to start including/rewriting code to use CppBlockUtils
#             but did not want to break the pure-python-ness of PyBtcEngine.
#             If you are interested in in a pure-python set of bitcoin utils
#             please go checkout the PyBtcEngine github project.
#
#
################################################################################

import hashlib
import random
import time
import os
import sys
import shutil
import math
from datetime import datetime

# 8000 lines of python to help us out...
from btcarmoryengine import *

# All the twisted/networking functionality
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred

# This is an amazing trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

TXTBL = enum("Status", "Date", "Direction", "Address", "Amount")


SETTINGS = None
wallets = []


'''
class HeaderDataModel(QAbstractTableModel):
   def __init__(self):
      super(HeaderDataModel, self).__init__()
      self.bdm = BlockDataManager().getBDM()

   def rowCount(self, index=QModelIndex()):

   def columnCount(self, index=QModelIndex()):

   def data(self, index, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if col== HEAD_DATE: return QVariant(someStr)
      elif role==Qt.TextAlignmentRole:
         if col in (HEAD_BLKNUM, HEAD_DIFF, HEAD_NUMTX, HEAD_BTC):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,235,255) )
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( headColLabels[section] )
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
'''


if __name__ == '__main__':
 
   import optparse
   parser = optparse.OptionParser(usage="%prog [options]\n")
   parser.add_option("--host", dest="host", default="127.0.0.1",
                     help="IP/hostname to connect to (default: %default)")
   parser.add_option("--port", dest="port", default="8333", type="int",
                     help="port to connect to (default: %default)")
   parser.add_option("--optionsPath", dest="optpath", default=SETTINGS_PATH, type="str",
                     help="location of your settings file")
   parser.add_option("--verbose", dest="verbose", action="store_true", default=False,
                     help="Print all messages sent/received")
   #parser.add_option("--testnet", dest="testnet", action="store_true", default=False,
                     #help="Speak testnet protocol")

   (options, args) = parser.parse_args()

   SETTINGS = SettingsFile(options.optpath)

   print 'Loading wallets...'
   for root,subs,files in os.walk(ARMORY_HOME_DIR):
      for f in files:
         if f.startswith('armory_') and f.endswith('.wallet') and \
            not f.endswith('backup.wallet') and not ('unsuccessful' in f):
               try:
                  fpath = os.path.join(root, f)
                  wallets.append( PyBtcWallet().readWalletFile(fpath))
               except:
                  pass

   passphrase = SecureBinaryData("This is my super-secret passphrase no one would ever guess!")
   print 'Number of wallets:', len(wallets)
   for wlt in wallets:
      print '   Wallet:', wlt.wltUniqueIDB58,
      print '"'+wlt.labelName+'"',
      print '(Encrypted)' if wlt.useEncryption else '(Not Encrypted)'
      wlt.unlock(securePassphrase=passphrase)



   

   exit(0)
   app = QApplication(sys.argv)
   import qt4reactor
   qt4reactor.install()




