################################################################################
#
# Copyright (C) 2011-2014, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
from armoryengine.ArmoryUtils import *
from armoryengine.MultiSigUtils import readLockboxEntryStr, calcLockboxID, \
                                       isBareLockbox, isP2SHLockbox
from armoryengine.Transaction import getTxOutScriptType, getMultisigScriptInfo

#############################################################################
def getScriptForUserString(userStr, wltMap, lboxList):
   """
   NOTE: Just like getDisplayStringForScript(), this used to be in ArmoryQt
   but I can envision that it would be useful for reading user input in a
   context other than the GUI.

   The user has entered a string in one of the following ways:
      
      18cnJQ493jnZn99A3QnHggkl832   (addr str)
      3Hgz4nmKasE32W3drXx719cBnM3   (P2SH str)
      Lockbox[Abcd1234]             (Lockbox: P2SH)
      Lockbox[Bare:Abcd1234]        (Lockbox: Plain Multisig)
      04187322ac7f91a3bb0...        (Plain public key)

   If they enter a lockbox by ID and we don't recognize the ID, we don't
   return anything at all.  Mainly because this is to return the script
   to you and there is no way to know what the script is.

   This returns four values:

      1. The script to which the user was intending to send their funds
      If the script is non-empty
         2. A wallet ID if it is part of one of our wallets (or None)
         3. A lockbox ID if it is part of one of our lockboxes (or None)
         4. An indication of whether the entered string has an address in it

   #4 is irrelevant in most contexts and should be ignored.  It is mainly
   for the getDisplayStringForScript() method, which will show you ID if
   an address string is entered, but will show you the address string instead
   if an ID was entered.
   """

   def getWltIDForScrAddr(scrAddr, walletMap):
      for iterID,iterWlt in walletMap.iteritems():
         if iterWlt.hasScrAddr(scrAddr):
            return iterID
      return None

   # Now try to figure it out
   try:
      userStr = userStr.strip()
      outScript = None
      wltID = None
      lboxID = None
      hasAddrInIt = True

      # Check if this corresponds to a lockbox
      if isBareLockbox(userStr) or isP2SHLockbox(userStr):
         parsedLboxID = readLockboxEntryStr(userStr)
         for iterLbox in lboxList:
            # Search for a lockbox with the same ID
            if iterLbox.uniqueIDB58 == parsedLboxID:
               outScript = iterLbox.binScript
               if isP2SHLockbox(userStr):
                  outScript = script_to_p2sh_script(iterLbox.binScript) 
               lboxID = parsedLboxID
               hasAddrInIt = False
               break
      elif len(userStr) in [66,130]:
         # This might be a public key; if 65 bytes, make sure it's a valid key
         sbdKey = SecureBinaryData(hex_to_binary(userStr))
         if sbdKey.getSize()==33 or (sbdKey.getSize()==65 and \
                     CryptoECDSA().VerifyPublicKeyValid(sbdKey)):
            a160 = sbdKey.getHash160()
            outScript = hash160_to_p2pkhash_script(a160)
            hasAddrInIt = False

            # Check if it's ours
            scrAddr = script_to_scrAddr(outScript)
            wltID = getWltIDForScrAddr(scrAddr, wltMap)
      else:
         scrAddr = addrStr_to_scrAddr(userStr)
         a160 = scrAddr_to_hash160(scrAddr)[1]
         outScript = scrAddr_to_script(scrAddr)
         hasAddrInIt = True

         # Check if it's a wallet scrAddr
         wltID  = getWltIDForScrAddr(scrAddr, wltMap)

         # Check if it's a known P2SH
         for lbox in lboxList:
            if lbox.p2shScrAddr == scrAddr:
               lboxID = lbox.uniqueIDB58
               break

      # Caller might be expecting to see None, instead of '' (empty string)
      wltID  = None if not wltID  else wltID
      lboxID = None if not lboxID else lboxID
      return {'Script': outScript, 
              'WltID':  wltID, 
              'LboxID': lboxID, 
              'ShowID': hasAddrInIt}
   except:
      #LOGEXCEPT('Invalid user string entered')
      return {'Script': None,
              'WltID':  None,
              'LboxID': None,
              'ShowID': None}



################################################################################
def getDisplayStringForScript(binScript, wltMap, lboxList, prefIDOverAddr=True, 
                              maxChars=256, lblTrunc=12, lastTrunc=12):
   """
   NOTE: This was originally in ArmoryQt.py, but we really needed this to be
   more widely accessible.  And it's easier to test when this is in ArmoryUtils.  
   Yes, I realize that it's awkward that we have wltMap {WltID-->Wallet} but
   we have a lboxList [Lbox0, Lbox1, ...].  I will have to standardize the 
   member names and lookup structures.

   We have a script and want to show the user something useful about it.
   We have a couple different display modes, since some formats are space-
   constrained.  For instance, the DlgConfirmSend dialog only has space
   for 34 letters, as it was designed to be showing only an address string.

   This is similar to self.getContribStr, but that method is more focused
   on identifying participants of a multi-sig transaction.  It almost
   works here, but we need one that's more general.

   Consider a 3-of-5 lockbox with ID Abcd1234z and label 
   "My long-term savings super-secure" and p2sh address 2m83zQr9981pmKnrSwa32

                   10        20        30        40        50        60        70
         |         |         |         |         |         |         |         |
   256   Lockbox 3-of-5 "Long-term savings" (2m83zQr9981p...)
   256   Lockbox 3-of-5 "Long-term savings" (Abcd1234z)
    50   Lockbox 3-of-5 "Long-term sa..." (2m83zQr9981p...)
    35   Lockbox 3-of-5 "Long-term savings"
    32   Lockbox 3-of-5 "Long-term sa..."

   256   Wallet "LabelLabelLabelLabelLabelLabel" (1j93CnrAA3xn...)
   256   Wallet "LabelLabelLabelLabelLabelLabel" (Abcd1234z)
    50   Wallet "LabelLabelLa..." (1j93CnrAA3xn...)
    35   Wallet "LabelLabelLa..." 

   So we will always show the type and the label (possibly truncated).  If
   can show the ID or Addr (whichever is preferred) we will
   """

   if maxChars<32:
      LOGERROR('getDisplayStringForScript() req at least 32 bytes output')
      return None

   scriptType = getTxOutScriptType(binScript) 
   scrAddr = script_to_scrAddr(binScript)

   wlt = None
   for iterID,iterWlt in wltMap.iteritems():
      if iterWlt.hasScrAddr(scrAddr):
         wlt = iterWlt
         break

   lbox = None
   if wlt is None:
      searchScrAddr = scrAddr
      if scriptType==CPP_TXOUT_MULTISIG:
         searchScrAddr = script_to_scrAddr(script_to_p2sh_script(binScript))
         
      for iterLbox in lboxList:
         if searchScrAddr == iterLbox.p2shScrAddr:
            lbox = iterLbox
            break


   if wlt is not None:
      strType = 'Wallet'
      strLabel = wlt.labelName
      if not prefIDOverAddr and scriptType in CPP_TXOUT_HAS_ADDRSTR:
         strLast = scrAddr_to_addrStr(scrAddr)
      else:
         strLast = wlt.uniqueIDB58
   elif lbox is not None:
      strType  = 'Lockbox %d-of-%d' % (lbox.M, lbox.N)
      strLabel = lbox.shortName
      if prefIDOverAddr:
         strLast = lbox.uniqueIDB58
      else:
         strLast = scrAddr_to_addrStr(lbox.p2shScrAddr)
   else:
      strType = ''
      strLabel = ''
      strLast = ''


   if len(strType) > 0:
      # We have something to display... do it and return
      lenType  = len(strType)
      lenLabel = len(strLabel) + 3
      lenLast  = len(strLast) + 3
      lenLabelTrunc = min(lenLabel + 3, lblTrunc  + 6)
      lenLastTrunc  = min(lenLast  + 3, lastTrunc + 6)

      dispStr = ''
      if lenType + lenLabel + lenLast <= maxChars:
         dispStr += '%s "%s"' % (strType, strLabel)
         dispStr += (' (%s)' % strLast)  if lenLast>0  else ''
         return dispStr
      elif lenType + lenLabel + lenLastTrunc <= maxChars:
         dispStr += '%s "%s..."' % (strType, strLabel[:lblTrunc])
         dispStr += (' (%s...)' % strLast[:lastTrunc])  if lenLast>0  else ''
         return dispStr
      elif lenType + lenLabelTrunc + lenLastTrunc <= maxChars:
         dispStr += '%s "%s..."' % (strType, strLabel[:lblTrunc])
         dispStr += (' (%s...)' % strLast[:lastTrunc])  if lenLast>0  else ''
         return dispStr
      elif lenType + lenLabel <= maxChars:
         dispStr += '%s "%s"' % (strType, strLabel)
      elif lenType + lenLabelTrunc <= maxChars:
         dispStr += '%s "%s..."' % (strType, strLabel[:lblTrunc])

      return dispStr


   # If we're here, it didn't match any loaded wlt or lockbox
   if scriptType in CPP_TXOUT_HAS_ADDRSTR:
      dispStr = script_to_addrStr(binScript)
      if len(dispStr) > maxChars:
         dispStr = dispStr[:maxChars-3] + '...'
      return dispStr
   elif scriptType == CPP_TXOUT_MULTISIG:
      M,N,a160s,pubs = getMultisigScriptInfo(binScript)
      lbID = calcLockboxID(binScript)
      dispStr = 'Unknown %d-of-%d (%s)' % (M,N,lbID)
      addrStr = script_to_addrStr(script_to_p2sh_script(binScript))
      if len(dispStr) + len(addrStr) + 3 <= maxChars:
         dispStr += ' [%s]' % addrStr
      elif len(dispStr) + lastTrunc + 6 <= maxChars:
         dispStr += ' [%s...]' % addrStr[:lastTrunc]
      return dispStr
   else:
      p2shEquiv = script_to_addrStr(script_to_p2sh_script(binScript))
      dispStr = 'Non-Standard: %s' % p2shEquiv
      if len(dispStr) > maxChars:
         dispStr = dispStr[:maxChars-3] + '...'
      return dispStr

