#######################################################################################################
#
# Inconsistencies found in the DB map (https://dl.dropboxusercontent.com/u/1139081/BitcoinImg/armory_db_keyvalue_maps.png) as compared to the actual DB:
#
# In leveldb_headers:
# StoredDBInfo (Key '\0'):
#    The value is 48 bytes long isntead of the 44 announced. Magic byte and Top block height are in their expected position
#
# In leveldb_blkdata
# StoredTx:
#    Locktime at the end of the TxIns, remember to it away from there and pad at the end of TxOuts to proper unserialization
#
# StoredTxOut:
#    No spendness data appended at the end of each txout (yet)
#
#######################################################################################################

import os
import struct

from armoryengine.ArmoryUtils import ARMORY_HOME_DIR, unpackVarInt
from armoryengine.Block import PyBlockHeader
from armoryengine.Transaction import PyTx
import leveldb


#dbheaders_path = '/home/goat/.armory/databases/leveldb_headers'
#dbblkdata_path = '/home/goat/.armory/databases/leveldb_blkdata'
dbheaders_path = os.path.join(ARMORY_HOME_DIR, 'databases', 'leveldb_headers')
dbblkdata_path = os.path.join(ARMORY_HOME_DIR, 'databases', 'leveldb_blkdata')

########################################################################################################
# front end class, implements the db parsing and querying methods.
# opens DB on instantiation
########################################################################################################
class ArmoryDB:
   dbheaders = None
   dbblkdata = None

   def __init__(self):
      if(ArmoryDB.dbheaders==None):
         ArmoryDB.dbheaders = leveldb.LevelDB(dbheaders_path)
         ArmoryDB.dbblkdata = leveldb.LevelDB(dbblkdata_path)

   ####################################################################################################
   # parses block headers db
   # return a DBstatus object
   ####################################################################################################
   def getDBStatus(self):

      rtStat = DBstatus()
      rtStat.TopBlockInHeadersDB = self.getTopBlockInHeadersDB()
      rtStat.TopBlockInBlkDataDB = self.getTopBlockInBlkDataDB()
      
      headstart = '\x0200000000'
      headers = ArmoryDB.dbheaders.RangeIter(key_from = headstart, key_to = None, include_value = True)

      i = 0
      rtStat.nMissingHeight = 0
      rtStat.nDupHeight = 0
      rtStat.MissingHeight = []
      rtStat.DupHeight = []
        
      for (key, value) in headers:

          height = struct.pack('I', key[1:5])
          if(height!=i):
             rtStat.nMissingHeight = rtStat.nMissingHeight +1
             rtStat.MissingHeight.append(height)

          nDups = struct.pack('B', value[0:1])
          if (nDups>1):
             rtStat.nDupHeight = rtStat.nDupHeight +1
             rtStat.DupHeight.append(height)
             
          i = i+1;

      return rtStat


   ###################################################################################################
   # fetch headers functions
   ###################################################################################################
   def getAllHeadersAtHeight(self, height):

      key = '\x02'
      keybody = struct.pack('>I', height)
      key = key +keybody
      
      try:
         headers = ArmoryDB.dbheaders.Get(key)
      except:
         return None
      nheaders = struct.unpack_from('B', headers)

      tlength = 1 +33*nheaders[0]
      pos=1
      BlockHeaderList = []
      while(pos<tlength):
         blkkey = '\x01' + headers[pos+1:pos+33]
         val = ArmoryDB.dbheaders.Get(blkkey)
         rtBlock = PyBlockHeader()
         rtBlock.unserialize(val)
         BlockHeaderList.append(rtBlock)
         
         pos = pos+33;

      return BlockHeaderList

   ########
   def getMainHeaderAtHeight(self, height):

      key = '\x02'
      keybody = struct.pack('>I', height)
      key = key +keybody

      try:
         headers = ArmoryDB.dbheaders.Get(key)
      except:
         return None
      nheaders = struct.unpack_from('B', headers)

      pos=1
      blkkey = '\x01' + headers[pos+1:pos+33]
      val = ArmoryDB.dbheaders.Get(blkkey)
      rtBlock = PyBlockHeader()
      rtBlock.unserialize(val)
         
      return rtBlock

   ########
   def getTopBlockInHeadersDB(self):

      head = ArmoryDB.dbheaders.Get('\0')
      val = struct.unpack('III' + 'I'*9, head)
      return val[2]

   ########
   def getTopBlockInBlkDataDB(self):

      head = ArmoryDB.dbblkdata.Get('\0')
      val = struct.unpack('III' + 'I'*9, head)
      return val[2]    
      

   ###################################################################################################
   # Txn fetching functions
   ###################################################################################################
   def myOwnUnpacker(self, val):
      data = val[2:]
      outputval = data[0:8]
      scriptsize, varintsize = unpackVarInt(data[8:])
      scriptend = 8 + varintsize + scriptsize
      #print 'script length: %d, varintSize: %d, scriptEnd - dataSize: %d' % (scriptsize, varintsize, scriptend - len(data))
      #print 'val length: %d' % (len(val))

   #####
   def myOwnUnpackerTxIn(self, val):
      data = val[38:]
      scriptsize, varintsize = unpackVarInt(data)
      data = val[38+varintsize:]
      
      scriptsize, varintsize = unpackVarInt(data[36:])
      scriptend = 40 + varintsize + scriptsize
      print 'script length: %d, varintSize: %d, scriptEnd - dataSize: %d' % (scriptsize, varintsize, scriptend - len(data))
      print 'len(val): %d' % (len(val))

      dathash = val
      rtstr = ":".join("{0:x}".format(ord(c)) for c in dathash)
      print rtstr
      
   #####      
   def getTxnByKey(self, key):

      txIns = ArmoryDB.dbblkdata.Get(key)
      txoutkey = key + '\x00'
      txOuts = ArmoryDB.dbblkdata.RangeIter(key_from = txoutkey, key_to = None, include_value = True)

      txOutsVal = ""
      for (k, value) in txOuts:
         if(k[0:7]==key):
            txOutsVal = txOutsVal + value[2:]
         else:
            break

      txData = txIns[34:len(txIns)-4] + txOutsVal + txIns[len(txIns)-4:]
      RtTx = PyTx()
      RtTx.unserialize(txData)

      return RtTx

   #####
   def getTxnByHash(self, Hash):
      HashLeftOver = Hash[4:32]
      key = '\x04' + Hash[0:4]

      try:
         val = ArmoryDB.dbblkdata.Get(key)
      except:
         return None
   
      nCandidates = unpackVarInt(val)
      pos = nCandidates[1]
      for i in range(0, nCandidates[0]):
         key =  '\x03' + val[pos +i*6:pos +(i+1)*6]
         Candidate = ArmoryDB.dbblkdata.Get(key)
         CandidateHash = Candidate[6:34]

         if(CandidateHash==HashLeftOver):
            return self.getTxnByKey(key)

      return None
      
   #####
   def getAllTxnByPrefix(self, Prefix):
      key = '\x04' + Prefix
      try:
         val = ArmoryDB.dbblkdata.Get(key)
      except:
         return None
   
      nCandidates = unpackVarInt(val)
      RtTxn = []
      pos = nCandidates[1]
      for i in range(0, nCandidates[0]):
         key = '\x03' + val[pos +i*6:pos +(i+1)*6]
         rt = self.getTxnByKey(key)
         RtTxn.append(rt)

      return RtTxn

   ##################################################################################################
   # Look Up Blocks by Hash functions
   ##################################################################################################
   def headersDBHasBlockHash(self, Hash):
      key = '\x01' + Hash
      try:
         val = ArmoryDB.dbheaders.Get(key)
         return True
      except:
         return False

   #####
   def blkdataDBHasBlockHash(self, Hash):
      key = '\x01' + Hash
      val = ArmoryDB.dbblkdata.Get(key)

      if(len(val)==84):
         key = '\x03' + val[80:84]
         try:
            val = ArmoryDB.bblkdata.Get(key)
            return True
         except:
            return False


###################################################################################################
# DBStatus class, filled by ArmoryDB.GetStatus(), holds:
#   nDups
###################################################################################################
class DBstatus:
   def __init__(self):
      TopBlockInHeadersDB=0
      TopBlockInBlkDataDB=0
      
      nMissingHeight=0
      MissingHeight=[]
      
      nDupHeight=0
      DupHeight=[]

###################################################
###################################################
# end of lib
###################################################
###################################################
