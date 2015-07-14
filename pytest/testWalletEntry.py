###############################################################################
#                                                                             #
#Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
#Distributed under the GNU Affero General Public License (AGPL v3)            #
#See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                             #
###############################################################################

import sys
sys.path.append('..')
import unittest

from armoryengine.ALL import *
from armoryengine.BitSet import BitSet

from testArmoryWallet import MockSerializableObject

WALLET_VERSION_BIN = hex_to_binary('002d3101')

# This disables RSEC for all WalletEntry objects.  This causes it to stop
# checking RSEC codes on all entries, and writes all \x00 bytes when creating.
WalletEntry.DisableRSEC()


MSO_FILECODE   = 'MOCKOBJ_'
MSO_ENTRY_ID   = '\x01'+'\x33'*20
MSO_FLAGS_REG  = '\x00\x00'
MSO_FLAGS_DEL  = '\x80\x00'
MSO_PARSCRADDR = '\x05'+'\x11'*20
MSO_PAYLOAD    = '\xaf'*5

FAKE_KDF_ID  = '\x42'*8
FAKE_EKEY_ID = '\x9e'*8

###############################################################################
class MockWalletFile(object):
   def __init__(self):
      self.ekeyMap = {}

   def doFileOperation(*args, **kwargs):
      pass

   def getName(self):
      return 'MockWalletFile'



###############################################################################
def skipFlagExists():
   if os.path.exists('skipmosttests.flag'):
      print '*'*80
      print 'SKIPPING MOST TESTS.  REMOVE skipMostTests.flag TO REENABLE'
      print '*'*80
      return True
   else:
      return False


###############################################################################
class WalletEntryTests(unittest.TestCase):

   def setUp(self):
      useMainnet()

   #############################################################################
   def testInit(self):
      # Default constructor
      we = WalletEntry()
      self.assertEqual(we.wltFileRef, None)
      self.assertEqual(we.wltByteLoc, None)
      self.assertEqual(we.wltEntrySz, None)
      self.assertEqual(we.isRequired, False)
      self.assertEqual(we.wltParentID, None)
      self.assertEqual(we.outerCrypt.serialize(), ArmoryCryptInfo(None).serialize())
      self.assertEqual(we.serPayload, None)
      self.assertEqual(we.defaultPad, 256)

      #self.assertEqual(we.flagBitset.toBitString(), '0'*16)

      self.assertEqual(we.wltParentRef, None)
      self.assertEqual(we.wltChildRefs, [])
      self.assertEqual(we.outerEkeyRef, None)

      self.assertEqual(we.isOpaque,        False)
      self.assertEqual(we.isUnrecognized,  False)
      self.assertEqual(we.isUnrecoverable, False)
      self.assertEqual(we.isDeleted,       False)
      self.assertEqual(we.isDisabled,      False)
      self.assertEqual(we.needFsync,       False)


      # Init with all args supplied
      mockWlt = MockWalletFile()
      we = WalletEntry(mockWlt, 10, 10, True, MSO_PARSCRADDR,
                       ArmoryCryptInfo(None), None, MSO_PAYLOAD, 128)

      self.assertEqual(we.wltFileRef.getName(), 'MockWalletFile')
      self.assertEqual(we.wltByteLoc, 10)
      self.assertEqual(we.wltEntrySz, 10)
      self.assertEqual(we.isRequired, True)
      self.assertEqual(we.wltParentID, MSO_PARSCRADDR)
      self.assertEqual(we.outerCrypt.serialize(), ArmoryCryptInfo(None).serialize())
      self.assertEqual(we.serPayload, MSO_PAYLOAD)
      self.assertEqual(we.defaultPad, 128)

      #self.assertEqual(we.flagBitset.toBitString(), '0'*16)

      self.assertEqual(we.wltParentRef, None)
      self.assertEqual(we.wltChildRefs, [])
      self.assertEqual(we.outerEkeyRef, None)

      self.assertEqual(we.isOpaque,        False)
      self.assertEqual(we.isUnrecognized,  False)
      self.assertEqual(we.isUnrecoverable, False)
      self.assertEqual(we.isDeleted,       False)
      self.assertEqual(we.isDisabled,      False)
      self.assertEqual(we.needFsync,       False)


   #############################################################################
   def testSerializeDeleted(self):
      for testSize in [20, 53, 127, 128, 245, 246, 247, 255, 256, 257, 512]:
         we = WalletEntry.CreateDeletedEntry(testSize)
         ser = we.serializeEntry()
         self.assertEqual(len(ser), testSize)

         expected = BinaryPacker()
         expected.put(BINARY_CHUNK, WALLET_VERSION_BIN, 4)
         expected.put(BINARY_CHUNK, MSO_FLAGS_DEL, 2)
         expected.put(UINT32,       testSize-10)
         expected.put(BINARY_CHUNK, '\x00'*(testSize-10))
         self.assertEqual(binary_to_hex(ser), binary_to_hex(expected.getBinaryString()))


   #############################################################################
   def testUnserializeDeleted(self):
      mockWlt = MockWalletFile()

      for testSize in [20, 53, 127, 128, 245, 246, 247, 255, 256, 257, 512]:
         expected = BinaryPacker()
         expected.put(BINARY_CHUNK, WALLET_VERSION_BIN, 4)
         expected.put(BINARY_CHUNK, MSO_FLAGS_DEL, 2)
         expected.put(UINT32,       testSize-10)
         expected.put(BINARY_CHUNK, '\x00'*(testSize-10))
         delData = expected.getBinaryString()

         we = WalletEntry.UnserializeEntry(delData, mockWlt, 20)

         self.assertTrue(we.isDeleted)
         self.assertEqual(we.wltEntrySz, testSize)
         self.assertEqual(we.serializeEntry(), delData)
         self.assertEqual(we.wltFileRef.getName(), 'MockWalletFile')
         self.assertEqual(we.wltByteLoc, 20)

         delData = delData[:12] + '\x01' + delData[13:]
         self.assertRaises(UnserializeError, WalletEntry.UnserializeEntry, delData, mockWlt, 20)

   #############################################################################
   def testSerializeObj(self):
      # For reference, a payload with a 20-byte ID will have:
      #    FILECODE(8) + flags(2) + EntryID(1+21) + SerObj(VI+N)
      
      for pad in [1, 16, 64, 256, 1024]:
         for testSize in [0, 20, 53, 221, 222, 223, 224, 255, 256]:
            data = '\x9f'*testSize
            mso = MockSerializableObject(data)
            mso.wltParentID = MSO_PARSCRADDR
            mso.defaultPad = pad
            serCompute = mso.serialize()
            serExpect = packVarInt(testSize)[0] + data
            self.assertEqual(serCompute, serExpect)

            bpInner = BinaryPacker()
            bpInner.put(BINARY_CHUNK,  MSO_FILECODE)
            bpInner.put(BINARY_CHUNK,  MSO_FLAGS_REG)
            bpInner.put(VAR_STR,       MSO_ENTRY_ID)
            bpInner.put(VAR_STR,       serExpect)
            innerStr = bpInner.getBinaryString()
            innerStr = padString(innerStr, mso.defaultPad)

            bpOuter = BinaryPacker()
            bpOuter.put(UINT32,       getVersionInt(ARMORY_WALLET_VERSION)) 
            bpOuter.put(BITSET,       BitSet(16), 2)
            bpOuter.put(VAR_STR,      MSO_PARSCRADDR)
            bpOuter.put(BINARY_CHUNK, ArmoryCryptInfo(None).serialize())
            bpOuter.put(VAR_STR,      innerStr)
            bpOuter.put(VAR_STR,      '\x00'*16)
            weSerExpect = bpOuter.getBinaryString()

            weSerCompute = mso.serializeEntry()

            #pprintDiff(weSerCompute, weSerExpect)

            self.assertEqual(len(weSerCompute), len(weSerExpect))
            self.assertEqual(weSerCompute, weSerExpect)
   
      
   #############################################################################
   def testSerUnserRT(self):
      # For reference, a payload with a 21-byte ID will have:
      #    FILECODE(8) + flags(2) + EntryID(1+21) + SerObj(VI+N)
      
      mockWlt = MockWalletFile()
      for pad in [1, 16, 64, 256, 1024]:
         for testSize in [0, 20, 53, 221, 222, 223, 224, 255, 256]:
            data = '\x9f'*testSize
            mso = MockSerializableObject(data)
            mso.wltParentID = MSO_PARSCRADDR
            mso.defaultPad = pad
            serExpect = packVarInt(testSize)[0] + data

            bpInner = BinaryPacker()
            bpInner.put(BINARY_CHUNK,  MSO_FILECODE)
            bpInner.put(BINARY_CHUNK,  MSO_FLAGS_REG)
            bpInner.put(VAR_STR,       MSO_ENTRY_ID)
            bpInner.put(VAR_STR,       serExpect)
            innerStr = bpInner.getBinaryString()
            innerStr = padString(innerStr, mso.defaultPad)

            bpOuter = BinaryPacker()
            bpOuter.put(UINT32,       getVersionInt(ARMORY_WALLET_VERSION)) 
            bpOuter.put(BITSET,       BitSet(16), 2)
            bpOuter.put(VAR_STR,      MSO_PARSCRADDR)
            bpOuter.put(BINARY_CHUNK, ArmoryCryptInfo(None).serialize())
            bpOuter.put(VAR_STR,      innerStr)
            bpOuter.put(VAR_STR,      '\x00'*16)
            weSerExpect = bpOuter.getBinaryString()

   
            # First pass uses expected serialization, second pass uses the 
            # output of .serializeEntry()
            for i in range(2):
               mso = WalletEntry.UnserializeEntry(weSerExpect, mockWlt, 0)

               self.assertEqual(type(mso), MockSerializableObject)
               self.assertEqual(mso.wltFileRef.getName(), 'MockWalletFile')
               self.assertEqual(mso.wltByteLoc, 0)
               self.assertTrue(testSize < mso.wltEntrySz)
               self.assertEqual(mso.isRequired, False)
               self.assertEqual(mso.wltParentID, MSO_PARSCRADDR)
               self.assertEqual(mso.outerCrypt.serialize(), ArmoryCryptInfo(None).serialize())
               self.assertEqual(mso.defaultPad, 256)  

               if pad==256: 
                  # NOTE:     
                  #    The Round-trip test is not perfect, b/c serialization
                  #    requires an unrecorded padding value in it.
                  #    Since the loop mods the padding, the UnserializeEntry
                  #    call has no way to know how what the unserialized 
                  #    padding is.  As such, we can only do a perfect R/T
                  #    test if the padding on ser is equal to the default (256)
                  self.assertEqual(mso.serPayload, innerStr)

               self.assertEqual(mso.wltParentRef, None)
               self.assertEqual(mso.wltChildRefs, [])
               self.assertEqual(mso.outerEkeyRef, None)

               self.assertEqual(mso.isOpaque,        False)
               self.assertEqual(mso.isUnrecognized,  False)
               self.assertEqual(mso.isUnrecoverable, False)
               self.assertEqual(mso.isDeleted,       False)
               self.assertEqual(mso.isDisabled,      False)
               self.assertEqual(mso.needFsync,       False)
               weSerExpect = mso.serializeEntry()


            # Might as well check whether it deletes, properly too
            serDelete = mso.serializeEntry(doDelete=True)
            delExpect = WalletEntry.CreateDeletedEntry(len(weSerExpect))
            self.assertEqual(serDelete, delExpect.serializeEntry())



   #############################################################################
   def testUnrecog(self):
      # For reference, a payload with a 21-byte ID will have:
      #    FILECODE(8) + flags(2) + EntryID(1+21) + SerObj(VI+N)
      
      mockWlt = MockWalletFile()
      for pad in [1, 16, 64, 256, 1024]:
         for testSize in [0, 20, 53, 221, 222, 223, 224, 255, 256]:
            data = '\x9f'*testSize
            mso = MockSerializableObject(data)
            mso.wltParentID = MSO_PARSCRADDR
            mso.defaultPad = pad
            serExpect = packVarInt(testSize)[0] + data

            bpInner = BinaryPacker()
            bpInner.put(BINARY_CHUNK,  'UNRECOG_')
            bpInner.put(BINARY_CHUNK,  MSO_FLAGS_REG)
            bpInner.put(VAR_STR,       MSO_ENTRY_ID)
            bpInner.put(VAR_STR,       serExpect)
            innerStr = bpInner.getBinaryString()
            innerStr = padString(innerStr, mso.defaultPad)

            bpOuter = BinaryPacker()
            bpOuter.put(UINT32,       getVersionInt(ARMORY_WALLET_VERSION)) 
            bpOuter.put(BITSET,       BitSet(16), 2)
            bpOuter.put(VAR_STR,      MSO_PARSCRADDR)
            bpOuter.put(BINARY_CHUNK, ArmoryCryptInfo(None).serialize())
            bpOuter.put(VAR_STR,      innerStr)
            bpOuter.put(VAR_STR,      '\x00'*16)
            weSerExpect = bpOuter.getBinaryString()

   
            mso = WalletEntry.UnserializeEntry(weSerExpect, mockWlt, 0)

            self.assertEqual(mso.__class__, WalletEntry)
            self.assertTrue(mso.isUnrecognized)
            self.assertEqual(mso.serPayload, innerStr)
            self.assertEqual(mso.wltParentID, MSO_PARSCRADDR)
            
            serDelete = mso.serializeEntry(doDelete=True)
            delExpect = WalletEntry.CreateDeletedEntry(len(serDelete))
            self.assertEqual(serDelete, delExpect.serializeEntry())
            

   #############################################################################
   def testOpaque(self):
      mockWlt = MockWalletFile()
      AciObject = ArmoryCryptInfo(FAKE_KDF_ID, 'AE256CBC', FAKE_EKEY_ID, 'PUBKEY20')
      for pad in [1, 16, 64, 256, 1024]:
         for testSize in [0, 20, 53, 221, 222, 223, 224, 255, 256]:
            data = '\x9f'*testSize
            mso = MockSerializableObject(data)
            mso.wltParentID = MSO_PARSCRADDR
            mso.defaultPad = pad
            serExpect = packVarInt(testSize)[0] + data

            bpInner = BinaryPacker()
            bpInner.put(BINARY_CHUNK,  'UNRECOG_')
            bpInner.put(BINARY_CHUNK,  MSO_FLAGS_REG)
            bpInner.put(VAR_STR,       MSO_ENTRY_ID)
            bpInner.put(VAR_STR,       serExpect)
            innerStr = bpInner.getBinaryString()
            innerStr = padString(innerStr, mso.defaultPad)

            bpOuter = BinaryPacker()
            bpOuter.put(UINT32,       getVersionInt(ARMORY_WALLET_VERSION)) 
            bpOuter.put(BITSET,       BitSet(16), 2)
            bpOuter.put(VAR_STR,      MSO_PARSCRADDR)
            bpOuter.put(BINARY_CHUNK, AciObject.serialize())
            bpOuter.put(VAR_STR,      innerStr)
            bpOuter.put(VAR_STR,      '\x00'*16)
            weSerExpect = bpOuter.getBinaryString()

   
            mso = WalletEntry.UnserializeEntry(weSerExpect, mockWlt, 0)
            self.assertTrue(mso.isOpaque)
            self.assertEqual(mso.wltParentID, MSO_PARSCRADDR)
                  
            # Test that we can delete opaque objects
            serDelete = mso.serializeEntry(doDelete=True)
            delExpect = WalletEntry.CreateDeletedEntry(len(serDelete))
            self.assertEqual(serDelete, delExpect.serializeEntry())


