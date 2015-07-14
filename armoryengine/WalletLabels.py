################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from ArmoryUtils import *
from BinaryPacker import BinaryPacker, makeBinaryUnpacker
from WalletEntry import WalletEntry


################################################################################
class ScrAddrLabel(WalletEntry):

   FILECODE = 'ADDRLABL'

   #############################################################################
   def __init__(self):
      super(ScrAddrLabel, self).__init__()
      self.scrAddr = None
      self.label   = None
      self.akpRef  = None

   #############################################################################
   def initialize(self, scrAddrStr=None, lbl=None):
      self.scrAddr = scrAddrStr
      self.label   = toUnicode(lbl)


   #############################################################################
   def serialize(self):
      if self.scrAddr is None:
         raise UninitializedError('AddrLabel not initialized')

      bp = BinaryPacker()
      bp.put(VAR_STR,     self.scrAddr)
      bp.put(VAR_UNICODE, self.label)
      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, theStr):
      bu = makeBinaryUnpacker(theStr)
      scraddr = bu.get(VAR_STR)
      lbl     = bu.get(VAR_UNICODE)
      self.initialize(scraddr, lbl)
      return self

   #############################################################################
   def linkWalletEntries(self, wltRef):
      akp = wltRef.masterScrAddrMap.get(self.scrAddr)
      if akp:
         self.akpRef = akp
         akp.scrAddrLabelRef = self

   #############################################################################
   def pprintOneLineStr(self, indent=0):
      return '%s%s: "%s"' % (' '*indent, scrAddr_to_addrStr(self.scrAddr),
                             self.label[:32])


################################################################################
class ScrAddrDesc(WalletEntry):

   FILECODE = 'ADDRDESC'

   #############################################################################
   def __init__(self):
      super(ScrAddrDesc, self).__init__()
      self.scrAddr = None
      self.description   = None
      self.akpRef  = None

   #############################################################################
   def initialize(self, scrAddrStr=None, desc=None):
      self.scrAddr     = scrAddrStr
      self.description = toUnicode(desc)


   #############################################################################
   def serialize(self):
      if self.scrAddr is None:
         raise UninitializedError('AddrDesc not initialized')

      bp = BinaryPacker()
      bp.put(VAR_STR,     self.scrAddr)
      bp.put(VAR_UNICODE, self.description)
      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, theStr):
      bu = makeBinaryUnpacker(theStr)
      scraddr = bu.get(VAR_STR)
      desc    = bu.get(VAR_UNICODE)
      self.initialize(scraddr, desc)
      return self

   #############################################################################
   def linkWalletEntries(self, wltRef):
      akp = wltRef.masterScrAddrMap.get(self.scrAddr)
      if akp:
         self.akpRef = akp
         akp.scrAddrDescRef = self

   #############################################################################
   def pprintOneLineStr(self, indent=0):
      return '%s%s: "%s"' % (' '*indent, scrAddr_to_addrStr(self.scrAddr),
                             self.description[:32])


################################################################################
class TxLabel(WalletEntry):

   FILECODE = 'TXLABEL_'

   #############################################################################
   def __init__(self):
      super(TxLabel, self).__init__()
      self.txidFull = ''
      self.txidMall = ''
      self.uComment = u''

   #############################################################################
   def initialize(self, txidFull, txidMall, comment):
      """
      "Mall" refers to malleability-resistant.  This isn't just for
      transactions that have been "mall"ed after broadcast, but for
      offline and multi-sig transactions that haven't been signed yet,
      for which we don't have the full ID.  The user may set the comment
      when creating the tx, and we want Armory to later associate
      that comment with the final transaction.  For each transaction
      in the ledger, we will look for both the "Full" and "Mall" version
      of the transaction ID (if available).
      """
      self.txidFull =   '' if txidFull is None else txidFull[:]
      self.txidMall =   '' if txidMall is None else txidMall[:]
      self.uComment  = u'' if comment  is None else toUnicode(comment)

   #############################################################################
   def serialize(self):
      if len(self.txidFull) + len(self.txidMall) == 0:
         raise UninitializedError('Tx label is not associated with any tx')

      bp = BinaryPacker()
      bp.put(VAR_STR,      self.txidFull)
      bp.put(VAR_STR,      self.txidMall)
      bp.put(VAR_UNICODE,  self.uComment)
      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, theStr):
      bu = makeBinaryUnpacker(theStr)
      self.txidFull = bu.get(VAR_STR)
      self.txidMall = bu.get(VAR_STR)
      self.uComment = bu.get(VAR_UNICODE)
      return self

   #############################################################################
   def linkWalletEntries(self, wltRef):
      pass

   #############################################################################
   def pprintOneLine(self, indent=0):
      if self.txidFull:
         idStr = binary_to_hex(self.txidFull) + ' '
      else:
         if not self.txidMall:
            raise KeyDataError('No txid specified for TxLabel')
         else:
            idStr = binary_to_hex(self.txidMall) + '*'

      print '%s%s: "%s"' % (' '*indent, idStr, self.uComment[:32])
