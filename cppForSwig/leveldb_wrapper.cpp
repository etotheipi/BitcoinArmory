#include <iostream>
#include <sstream>
#include <map>
#include <list>
#include <vector>
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "leveldb_wrapper.h"

vector<InterfaceToLDB*> LevelDBWrapper::ifaceVect_(0);

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::checkStatus(leveldb::Status stat, bool warn)
{
   if( stat.ok() )
      return true;
   
   if(warn)
      Log::ERR() << "***LevelDB Error: " << stat.ToString();

   return false;
}


////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::sliceToBinaryData(leveldb::Slice slice)
{ 
   return BinaryData((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::sliceToBinaryData(leveldb::Slice slice, 
                                                  BinaryData & bd)
{ 
   bd.copyFrom((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
BinaryReader InterfaceToLDB::sliceToBinaryReader(leveldb::Slice slice)
{ 
   return BinaryReader((uint8_t*)(slice.data()), slice.size());
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::sliceToBinaryReader(leveldb::Slice slice, 
                                                    BinaryReader & br)
{ 
   br.setNewData((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef InterfaceToLDB::sliceToBinaryDataRef(leveldb::Slice slice)
{ 
   return BinaryDataRef( (uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
BinaryRefReader InterfaceToLDB::sliceToBinaryRefReader(leveldb::Slice slice)
{ 
   return BinaryRefReader( (uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::init()
{
   SCOPED_TIMER("InterfaceToLDB::init");
   dbIsOpen_ = false;
   for(uint8_t i=0; i<DB_COUNT; i++)
   {
      iters_[i] = NULL;
      batches_[i] = NULL;
      dbs_[i] = NULL;
      dbPaths_[i] = string("");
      batchStarts_[i] = 0;
   }
}

////////////////////////////////////////////////////////////////////////////////
InterfaceToLDB::InterfaceToLDB() 
{
   init();
}


/////////////////////////////////////////////////////////////////////////////
InterfaceToLDB::~InterfaceToLDB(void)
{
   for(uint32_t db=0; db<(uint32_t)DB_COUNT; db++)
      if(batchStarts_[db] > 0)
         Log::ERR() << "Unwritten batch in progress during shutdown";

   closeDatabases();
}





/////////////////////////////////////////////////////////////////////////////
// The dbType and pruneType inputs are left blank if you are just going to 
// take whatever is the current state of database.  You can choose to 
// manually specify them, if you want to throw an error if it's not what you 
// were expecting
bool InterfaceToLDB::openDatabases(string basedir, 
                                   BinaryData const & genesisBlkHash,
                                   BinaryData const & genesisTxHash,
                                   BinaryData const & magic,
                                   ARMORY_DB_TYPE     dbtype,
                                   DB_PRUNE_TYPE      pruneType)
{
   SCOPED_TIMER("openDatabases");

   baseDir_ = basedir;
   char dbname[1024];

   stringstream head;
   head << baseDir_ << "/" << "leveldb_headers";
   dbPaths_[0] = head.str();

   stringstream blk;
   blk << baseDir_ << "/" << "leveldb_blkdata";
   dbPaths_[1] = blk.str();
   
   magicBytes_ = magic;
   genesisTxHash_ = genesisTxHash;
   genesisBlkHash_ = genesisBlkHash;

   armoryDbType_ = dbtype;
   dbPruneType_  = pruneType;


   if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      Log::ERR() << " must set magic bytes and genesis block";
      Log::ERR() << "           before opening databases.";
      return false;
   }

   // Just in case this isn't the first time we tried to open it.
   closeDatabases();


   vector<leveldb::DB*> dbs[2];
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      DB_SELECT CURRDB = (DB_SELECT)db;
      
      leveldb::Options opts;
      opts.create_if_missing = true;
      leveldb::Status stat = leveldb::DB::Open(opts, dbPaths_[db],  &dbs_[db]);
      if(!checkStatus(stat))
         Log::ERR() << "Failed to open database! DB: " << db;

      // Create an iterator that we'll use for ust about all DB seek ops
      iters_[db] = dbs_[db]->NewIterator(leveldb::ReadOptions());
      batches_[db] = NULL;
      batchStarts_[db] = 0;

      BinaryDataRef dbInfo = getValueRef(CURRDB, getDBInfoKey());
      if(dbInfo.getSize() == 0)
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         BitPacker<uint32_t> bitpack;
         uint32_t flagBytes = 0;
         bitpack.putBits((uint32_t)ARMORY_DB_VERSION, 4);
         bitpack.putBits((uint32_t)armoryDbType_,     4);
         bitpack.putBits((uint32_t)dbPruneType_,      4);

         BinaryWriter bw(48);
         bw.put_BinaryData(magicBytes_);
         bw.put_BitPacker(bitpack);
         bw.put_uint32_t(0);
         bw.put_BinaryData(genesisBlkHash_);
   
         putValue(CURRDB, getDBInfoKey(), bw.getData());
      }
      else
      {
         // Else we read the DB info and make sure everything matches up
         if(dbInfo.getSize() < 40)
         {
            Log::ERR() << "Invalid DatabaseInfo data";
            closeDatabases();
            return false;
         }

         BinaryRefReader brr(dbInfo);
         uint32_t version = brr.get_uint32_t();
         BinaryData magic = brr.get_BinaryData(4);
         uint32_t flags   = brr.get_uint32_t();
         topBlockHeight_  = brr.get_uint32_t();
         topBlockHash_    = brr.get_BinaryData(32);
      
         // Check that the magic bytes are correct
         if(magicBytes_ != magic)
         {
            Log::ERR() << " Magic bytes mismatch!  Different blkchain?";
            closeDatabases();
            return false;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValueRef(CURRDB, DB_PREFIX_HEADHASH, topBlockHash_).getSize() == 0 )
         {
            Log::ERR() << " Top block doesn't exist!";
            closeDatabases();
            return false;
         }

         BitUnpacker<uint32_t> bitunpack(flags);
         uint32_t dbVer      = bitunpack.getBits(4);
         uint32_t dbType     = bitunpack.getBits(4);
         uint32_t pruneType  = bitunpack.getBits(4);

         if(armoryDbType_ == ARMORY_DB_WHATEVER)
            armoryDbType_ = (ARMORY_DB_TYPE)dbType;
         else if(armoryDbType_ != dbType)
         {
            Log::ERR() << "Mismatch in DB type";
            closeDatabases();
            return false;
         }

         if(dbPruneType_ == DB_PRUNE_WHATEVER)
            dbPruneType_ = (DB_PRUNE_TYPE)pruneType;
         else if(dbPruneType_ != pruneType)
         {
            Log::ERR() << "Mismatch in DB type";
            closeDatabases();
            return false;
         }
      }
   }

   // Reserve space in the vector to delay reallocation for 32 weeks
   validDupByHeight_.clear();
   validDupByHeight_.reserve(topBlockHeight_ + 32768);
   validDupByHeight_.resize(topBlockHeight_+1);

   return true;
}


/////////////////////////////////////////////////////////////////////////////
uint32_t InterfaceToLDB::readAllStoredScriptHistory(
                          map<BinaryData, StoredScriptHistory> & regScriptMap)
{
   SCOPED_TIMER("readAllStoredScriptHistory");
   // Now read all the StoredAddressObjects objects to make it easy to query
   // inclusion directly from RAM.
   seekTo(BLKDATA, DB_PREFIX_SCRIPT, BinaryData(0));
   startBlkDataIteration(DB_PREFIX_SCRIPT);
   uint32_t lowestSync = UINT32_MAX;
   while(advanceIterAndRead(BLKDATA, DB_PREFIX_SCRIPT))
   {
      if(!checkPrefixByte(DB_PREFIX_SCRIPT))
         break;

      StoredScriptHistory ssh;
      readStoredScriptHistoryAtIter(ssh);
      regScriptMap[ssh.uniqueKey_] = ssh;
      lowestSync = min(lowestScannedUpTo_, ssh.alreadyScannedUpToBlk_);
   }

   return lowestSync;
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::loadAllStoredHistory(void)
{
   SCOPED_TIMER("loadAllStoredHistory");
   lowestScannedUpTo_ = readAllStoredScriptHistory(registeredSSHs_);
}


/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void InterfaceToLDB::closeDatabases(void)
{
   SCOPED_TIMER("closeDatabases");
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      if( dbs_[db] != NULL)
         delete dbs_[db];
      
      if( batches_[db] != NULL )
         delete batches_[db];
   }
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::startBatch(DB_SELECT db)
{
   SCOPED_TIMER("startBatch");
   if(batchStarts_[db] == 0)
   {
      if(batches_[db] != NULL)
      {
         Log::ERR() << "Trying to startBatch but we already have one";
         delete batches_[db];
      }

      batches_[db] = new leveldb::WriteBatch;
   }

   // Increment the number of times we've called this function
   batchStarts_[db] += 1;
}



////////////////////////////////////////////////////////////////////////////////
// Commit all the batched operations
void InterfaceToLDB::commitBatch(DB_SELECT db)
{
   SCOPED_TIMER("commitBatch");

   // Decrement the numbers of starts and only write if it's at zero
   batchStarts_[db] -= 1;

   if(batchStarts_[db] == 0)
   {
      if(batches_[db] == NULL)
      {
         Log::ERR() << "Trying to commitBatch but we don't have one";
         return;
      }

      dbs_[db]->Write(leveldb::WriteOptions(), batches_[db]);
      batches_[db]->Clear();
      delete batches_[db];
      batches_[db] = NULL;
      iterIsDirty_[db] = true;
   }
}


/////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
BinaryData InterfaceToLDB::getValue(DB_SELECT db, leveldb::Slice ldbKey)
{
   leveldb::Status stat = dbs_[db]->Get(STD_READ_OPTS, ldbKey, &lastGetValue_);
   if(!checkStatus(stat, false))
      return BinaryData(0);

   return BinaryData(lastGetValue_);
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLDB::getValue(DB_SELECT db, BinaryDataRef key)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   return getValue(db, ldbKey);
}


/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLDB::getValue(DB_SELECT db, 
                                               DB_PREFIX prefix,
                                               BinaryDataRef key)
{
   BinaryData keyFull(key.getSize()+1);
   keyFull[0] = (uint8_t)prefix;
   key.copyTo(keyFull.getPtr()+1, key.getSize());
   leveldb::Slice ldbKey((char*)keyFull.getPtr(), keyFull.getSize());
   return getValue(db, ldbKey);
}


/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
BinaryDataRef InterfaceToLDB::getValueRef(DB_SELECT db, 
                                                     BinaryDataRef key)
{
   leveldb::Slice ldbKey = binaryDataRefToSlice(key);
   leveldb::Status stat = dbs_[db]->Get(STD_READ_OPTS, ldbKey, &lastGetValue_);
   if(!checkStatus(stat, false))
      lastGetValue_ = string("");

   return BinaryDataRef((uint8_t*)lastGetValue_.data(), lastGetValue_.size());
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
BinaryDataRef InterfaceToLDB::getValueRef(DB_SELECT db, 
                                                     DB_PREFIX prefix, 
                                                     BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   return getValueRef(db, bw.getDataRef());
}


/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
BinaryRefReader InterfaceToLDB::getValueReader(
                                             DB_SELECT db, 
                                             BinaryDataRef keyWithPrefix)
{
   return BinaryRefReader(getValueRef(db, keyWithPrefix));
}


/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
BinaryRefReader InterfaceToLDB::getValueReader(
                                             DB_SELECT db, 
                                             DB_PREFIX prefix, 
                                             BinaryDataRef key)
{
   return BinaryRefReader(getValueRef(db, prefix, key));
}






/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLDB::putValue(DB_SELECT db, 
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   leveldb::Slice ldbkey = binaryDataRefToSlice(key);
   leveldb::Slice ldbval = binaryDataRefToSlice(value);
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, ldbval);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(STD_WRITE_OPTS, ldbkey, ldbval);
      checkStatus(stat);
      iterIsDirty_[db] = true;
   }
   
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLDB::putValue(DB_SELECT db, 
                                  DB_PREFIX prefix,
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   BinaryWriter bw;
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   putValue(db, bw.getDataRef(), value);
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLDB::deleteValue(DB_SELECT db, 
                                     BinaryDataRef key)
                 
{
   string value;
   leveldb::Slice ldbKey = binaryDataRefToSlice(key);
   
   if(batches_[db]!=NULL)
      batches_[db]->Delete(ldbKey);
   else
   {
      leveldb::Status stat = dbs_[db]->Delete(STD_WRITE_OPTS, ldbKey);
      checkStatus(stat);
      iterIsDirty_[db] = true;
   }
}



/////////////////////////////////////////////////////////////////////////////
// Not sure why this is useful over getHeaderMap() ... this iterates over
// the headers in hash-ID-order, instead of height-order
void InterfaceToLDB::startHeaderIteration()
{
   SCOPED_TIMER("startHeaderIteration");
   seekTo(HEADERS, DB_PREFIX_HEADHASH, BinaryData(0));
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::startBlkDataIteration(DB_PREFIX prefix)
{
   SCOPED_TIMER("startBlkDataIteration");
   seekTo(BLKDATA, prefix, BinaryData(0));
   leveldb::Slice start((char*)(&prefix), 1);
   iters_[BLKDATA]->Seek(start);
   iteratorToRefReaders(iters_[BLKDATA], currReadKey_, currReadValue_);
}



/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLDB::advanceToNextBlock(bool skip)
{
   char prefix = DB_PREFIX_TXDATA;

   leveldb::Iterator* it = iters_[BLKDATA];
   BinaryData key;
   while(1) 
   {
      if(skip) 
         it->Next();

      if( !it->Valid() || it->key()[0] != (char)DB_PREFIX_TXDATA)
         return false;
      else if( it->key().size() == 5)
      {
         iteratorToRefReaders(it, currReadKey_, currReadValue_);
         return true;
      }

      if(!skip) 
         it->Next();
   } 
   Log::ERR() << "we should never get here...";
   return false;
}



/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLDB::seekTo(DB_SELECT db,
                                BinaryDataRef key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   it->Seek(binaryDataRefToSlice(key));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   bool isMatch = (currReadKey_.getRawRef()==key);
   return isMatch;
}

/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLDB::seekTo(DB_SELECT db,
                                DB_PREFIX prefix, 
                                BinaryDataRef key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   BinaryData ldbKey;
   if(db==HEADERS)
      return seekTo(db, key, it);
   else
   {
      uint8_t prefInt = (uint8_t)prefix;
      ldbKey = BinaryData(&prefInt, 1) + key;
      return seekTo(db, ldbKey, it);
   }
}


////////////////////////////////////////////////////////////////////////////////
// We frequently have a Tx hash and need to determine the Hgt/Dup/Index of it.
// And frequently when we do, we plan to read the tx right afterwards, so we
// should leave the itereator there.
bool InterfaceToLDB::seekToTxByHash(BinaryDataRef txHash)
{
   SCOPED_TIMER("seekToTxByHash");
   BinaryData hash4(txHash.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);

   if(existingHints.getSize() == 0)
   {
      Log::ERR() << "No tx in DB with hash: " << txHash.toHexStr();
      return false;
   }

   // Now go through all the hints looking for the first one with a matching hash
   uint32_t numHints = existingHints.getSize() / 6;
   uint32_t height;
   uint8_t  dup;
   for(uint32_t i=0; i<numHints; i++)
   {
      BinaryDataRef hint = existingHints.getSliceRef(i*6, 6);
      seekTo(BLKDATA, DB_PREFIX_TXDATA, hint);

      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, height, dup);
      uint16_t txIdx = currReadKey_.get_uint16_t();
      
      // We don't actually know for sure whether the seekTo() found a Tx or TxOut
      if(hint != currReadKey_.getRawRef().getSliceRef(1,6))
      {
         Log::ERR() << "TxHint referenced a BLKDATA tx that doesn't exist";
         continue;
      }

      currReadValue_.advance(2);  // skip flags
      if(currReadValue_.get_BinaryDataRef(32) == txHash)
      {
         resetIterReaders();
         return true;
      }
   }

   Log::ERR() << "No tx in DB with hash: " << txHash.toHexStr();
   resetIterReaders();
   return false;
}



/////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::deleteIterator(DB_SELECT db)
{
   delete iters_[db];
   iters_[db] = NULL;
   iterIsDirty_[db] = false;
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::resetIterator(DB_SELECT db)
{
   // This may be very slow, so you should only do it when you're sure it's
   // necessary.  You might just 
   BinaryData key = currReadKey_.getRawRef().copy();
   if(iters_[db] != NULL)
      delete iters_[db];

   iters_[db] = dbs_[db]->NewIterator(leveldb::ReadOptions());
   seekTo(db, key);
   iterIsDirty_[db] = false;
}

/////////////////////////////////////////////////////////////////////////////
// Returns refs to key and value that become invalid when iterator is moved
void InterfaceToLDB::iteratorToRefReaders( leveldb::Iterator* it, 
                                               BinaryRefReader & brrKey,
                                               BinaryRefReader & brrValue)
{
   brrKey.setNewData((uint8_t*)(it->key().data()), it->key().size());      
   brrValue.setNewData((uint8_t*)(it->value().data()), it->value().size());      
}


////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE InterfaceToLDB::readBlkDataKey5B(
                                       BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID)
{
   uint8_t prefix = brr.get_uint8_t();
   if(prefix != (uint8_t)DB_PREFIX_TXDATA)
   {
      height = 0xffffffff;
      dupID  =       0xff;
      return NOT_BLKDATA;
   }
   
   BinaryData hgtx = brr.get_BinaryData(4);
   height = ARMDB.hgtxToHeight(hgtx);
   dupID  = ARMDB.hgtxToDupID(hgtx);

   if(brr.getSizeRemaining() == 0)
      return BLKDATA_HEADER;
   else if(brr.getSizeRemaining() == 2)
      return BLKDATA_TX;
   else if(brr.getSizeRemaining() == 4)
      return BLKDATA_TXOUT;
   else
   {
      Log::ERR() << "Unexpected bytes remaining: " << brr.getSizeRemaining();
      return NOT_BLKDATA;
   }
}



/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::readStoredScriptHistoryAtIter( StoredScriptHistory & ssh)
                               
{
   resetIterReaders();

   checkPrefixByte(DB_PREFIX_SCRIPT);
      
   uint32_t nBytes = currReadKey_.getSizeRemaining();
   ssh.scriptType_ = (SCRIPT_PREFIX)currReadKey_.get_uint8_t();
   currReadKey_.get_BinaryData(ssh.uniqueKey_, nBytes-1);

   ssh.unserializeDBValue(currReadValue_);
}




////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::getStoredScriptHistory(BinaryDataRef uniqueKey,
                                                StoredScriptHistory & ssh)
{
   BinaryRefReader brr = getValueRef(BLKDATA, DB_PREFIX_SCRIPT, uniqueKey);
   ssh.unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::getStoredScriptHistoryByRawScript(
                                             BinaryDataRef script,
                                             StoredScriptHistory & ssh)
{
   BinaryData uniqueKey = BtcUtils::getTxOutScriptUniqueKey(script);
   getStoredScriptHistory(uniqueKey, ssh);
}
/*
/////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::readStoredScriptHistory(StoredScriptHistory & regAddr,
                                            vector<BinaryData>* txoVect=NULL)
{
   if(iter==NULL)
      iter = iters_[BLKDATA];

   if(!iter->Valid())
   { 
      Log::ERR() << "Tried to access invalid iterator!";
      return;
   }

   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
    
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getUnspentTxOut( BinaryData & const ldbKey8B,
                                          UnspentTxOut & utxo)
{
   BinaryRefReader txrr(txoData[i]);
   BinaryData hgtx   = txrr.get_BinaryData(4);
   uint16_t   txIdx  = txrr.get_uint16_t();
   uint16_t   outIdx = txrr.get_uint16_t();


   BinaryDataRef txRef(txoData[i].getPtr(), 6);
   bool isFound = seekTo(BLKDATA, DB_PREFIX_TXDATA, txRef);
   if(!isFound)
   {
      Log::ERR() << " could not find transaction in DB";
      return false;
   }

   // Need to get the height and hash of the parent transaction
   Tx tx;
   readBlkDataTxValue(currReadValue_, tx)

   // Now get the TxOut directly
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, txoData[i]);
   if(brr.getSize()==0)
   {
      Log::ERR() << " could not find TxOut in DB";
      return false;
   }

   TxOut txout;
   readBlkDataTxOutValue(brr, txout);

   utxo.txHash_     = tx.thisHash_;
   utxo.txOutIndex_ = outIdx;
   utxo.txHeight_   = ARMDB.hgtxToHeight(hgtx);
   utxo.value_      = txout.getValue();
   utxo.script_     = txout.getScript();

   return txout.storedIsSpent_;
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getUtxoListForAddr( BinaryData & const scriptWithType,
                                             vector<UnspentTxOut> & utxoVect)
{
   BinaryWriter bw(22);
   bw.put_uint8_t(DB_PREFIX_SCRIPT);
   bw.put_BinaryData(scriptWithType);

   seekTo(BLKDATA, DB_PREFIX_SCRIPT, bw.getData());

   StoredScriptHistory ra;
   vector<BinaryData> txoData;

   readRegisteredAddr(ra, &txoData);
   utxoVect.clear();
   utxoVect.reserve(txoData.size());

   for(uint32_t i=0; i<txoData.size(); i++)
   {
      UnspentTxOut utxo;
      bool isSpent = getUnspentTxOut(txoData[i], utxo);
      if(!isSpent)
         utxoVect.push_back(utxo);
   }
   
   return true;

}



bool InterfaceToLDB::readFullTx(Tx & tx, leveldb::Iterator* iter=NULL)
{
   if(iter==NULL)
      iter = iters_[BLKDATA];

   readBlkDataTxKey(currReadKey_, tx);
   if(!tx.isInitialized())
   {
      Log::ERR() << "iterator is not pointing to a Tx";
      return false;
   }

   readBlkDataTxValue(currReadValue_, tx);

   if(!tx.isPartial_)
      return;
   
   while(1)
   {
      advanceIterAndRead(iter);
      if(readBlkDataKey5B(currReadKey_) != BLKDATA_TXOUT)
      {
         currReadKey_.resetPosition();
         break;
      }

      TxOut txout;
      readBlkDataTxOutKey(currReadKey_, txout);
      readBlkDataTxOutValue(currReadValue_, txout);

      
   }
}
*/



/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::advanceIterAndRead(leveldb::Iterator* iter)
{
   iter->Next();
   if(!iter->Valid())
      return false;

   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::advanceIterAndRead(DB_SELECT db, DB_PREFIX prefix)
{
   if(iterIsDirty_[db])
      Log::ERR() << "DB has been changed since this iterator was created";

   if(advanceIterAndRead(iters_[db]))
      return checkPrefixByte(prefix, true);
   else 
      return false;
}



/////////////////////////////////////////////////////////////////////////////
/*
map<HashString, BlockHeader> InterfaceToLDB::getHeaderMap(void)
{
   map<HashString, BlockHeader> outMap;

   iters_[HEADERS]->SeekToFirst();
   if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey() )
      Log::WARN() << "How do we not have a DB info key?" ;
   else
      it->Next()

   BinaryData headerHash;
   BinaryData headerEntry;
   BlockHeader header;
   for (; it->Valid(); it->Next())
   {
      sliceToBinaryData(it->key(),   headerHash);
      sliceToBinaryData(it->value(), headerEntry);

      BinaryRefReader brr(headerEntry);
      header.unserialize(brr);
      BinaryData hgtx    = brr.get_BinaryData();
      uint32_t   txCount = brr.get_uint32_t();
      uint32_t   nBytes  = brr.get_uint32_t();

      // The "height" is actually a 3-byte height, and a "duplicate ID"
      // Reorgs lead to multiple headers having the same height.  Since 
      // the blockdata
      header.storedHeight_(ARMDB.hgtxToHeight(hgtx));
      header.duplicateID_(ARMDB.hgtxToDupID(hgtx));

      outMap[headerHash] = header;
   }

   return outMap;
}
*/


////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getRawHeader(BinaryData const & headerHash)
{
   // I used the seek method originally to try to return
   // a slice that didn't need to be copied.  But in the 
   // end, I'm doing a copy anyway.  So I switched to 
   // regular DB.Get and commented out the seek method 
   // so it's still here for reference
   static BinaryData headerOut(HEADER_SIZE);
   headerOut = getValue(HEADERS, DB_PREFIX_HEADHASH, headerHash);
   return headerOut.getSliceCopy(0, HEADER_SIZE);
}



////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getDBInfoKey(void)
{
   // Return a key that is guaranteed to be before all other non-empty
   // DB keys
   static BinaryData dbinfokey(0);
   if(dbinfokey.getSize() == 0)
   {
      BinaryWriter bw(1);
      bw.put_uint8_t((uint8_t)DB_PREFIX_DBINFO); 
      dbinfokey = bw.getData();
   }
   return dbinfokey;
}

//StoredTx InterfaceToLDB::getFullTxFromKey6B(BinaryDataRef key6B)
//{

//}

//StoredTx InterfaceToLDB::getFullTxFromHash(BinaryDataRef txHash)
//{

//}


////////////////////////////////////////////////////////////////////////////////
/*  I think the BDM will do this, not the DB interface
bool InterfaceToLDB::addBlockToDB(BinaryDataRef newBlock,
                                      bool withLead8B, 
                                      UPDATE_DB_TYPE updType=UPDATE_DB_NORMAL)
{
   
   BinaryRefReader brr(newBlock);

   if(withLead8B)
   {
      BinaryDataRef first4 = brr.get_BinaryDataRef(4);
      if(first4 != magicBytes_)
      {
         Log::ERR() << "Magic bytes don't match! " << first4.toHexStr().c_str();
         return false;
      }
      
      // The next 4 bytes is the block size, but we will end up computing this
      // anyway, as we dissect the block.
      brr.advance(4);
   }

   BlockHeader bh(brr);
   
   uint32_t nTx = brr.get_var_int();
   vector<Tx> allTxInBlock(nTx);
   for(uint32_t itx=0; itx<nTx; itx++)
      allTxInBlock[itx].unserialize(brr);
   
   
   // Check whether the DB has it already.
   bool chkAlready = (getValue(HEADERS, bh.getThisHash()).getSize() == 0);

   bool doValid;
   bool skipEntirely = false;
   if(updType==UPDATE_DB_NORMAL)
   {
   }
   
}
*/

////////////////////////////////////////////////////////////////////////////////
uint8_t InterfaceToLDB::getValidDupIDForHeight(uint32_t blockHgt)
{
   if(validDupByHeight_.size() < blockHgt+1)
   {
      Log::ERR() << "Block height exceeds DupID lookup table";
      return UINT8_MAX;
   }

   return validDupByHeight_[blockHgt];
}

////////////////////////////////////////////////////////////////////////////////
uint8_t InterfaceToLDB::getValidDupIDForHeight_fromDB(uint32_t blockHgt)
{
   SCOPED_TIMER("getValidDupIDForHeight");

   BinaryData hgt4((uint8_t*)&blockHgt, 4);
   BinaryRefReader brrHgts = getValueReader(HEADERS, DB_PREFIX_HEADHGT, hgt4);

   if(brrHgts.getSize() == 0)
   {
      Log::ERR() << "Requested header does not exist in DB";
      return false;
   }

   uint8_t lenEntry = 33;
   uint8_t numDup = brrHgts.getSize() / lenEntry;
   for(uint8_t i=0; i<numDup; i++)
   {
      uint8_t dup8 = brrHgts.get_uint8_t(); 
      BinaryDataRef thisHash = brrHgts.get_BinaryDataRef(lenEntry-1);
      if(dup8 & 0x80 > 0)
         return (dup8 & 0x7f);
   }

   Log::ERR() << "Requested a header-by-height but none were marked as main";
   return UINT8_MAX;
}



////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  Will 
// adjust the dupID value  in the input SBH
// Will overwrite existing data, for simplicity, and so that this method allows
// us to easily replace/update data, even if overwriting isn't always necessary
void InterfaceToLDB::putStoredHeader( StoredHeader & sbh, bool withTx)
{
   SCOPED_TIMER("putStoredHeader");
   uint32_t height  = sbh.blockHeight_;
   bool     isValid = sbh.isMainBranch_;

   // First, check if it's already in the hash-indexed DB
   BinaryData existingHead = getValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_);
   if(existingHead.getSize() > 0)
   {
      // Felt like there was something else to do here besides Log::WARN...
      Log::WARN() << "Header already exists in DB.  Overwriting";
   }

   // Check if it's already in the height-indexed DB - determine dupID if not
   bool alreadyInHgtDB = false;
   BinaryData hgt4((uint8_t*)&height, 4);
   BinaryData hgtList = getValue(HEADERS, DB_PREFIX_HEADHGT, hgt4);
   if(hgtList.getSize() == 0)
      sbh.setParamsTrickle(height, 0, isValid);
   else
   {
      // If we already have 1+ headers at this height, figure out the dupID
      int const lenEntry = 33;
      if(hgtList.getSize() % lenEntry > 0)
         Log::ERR() << "Invalid entry in headers-by-hgt db";

      int8_t maxDup = -1;
      for(uint8_t i=0; i<hgtList.getSize() / lenEntry; i++)
      {
         uint8_t dupID =  *(hgtList.getPtr() + i*lenEntry) & 0x7f;
         bool    valid = (*(hgtList.getPtr() + i*lenEntry) & 0x80) > 0;
         maxDup = max(maxDup, (int8_t)dupID);
         BinaryDataRef hash = hgtList.getSliceRef(lenEntry*i+1, lenEntry-1);
         if(sbh.thisHash_.startsWith(hash))
         {
            alreadyInHgtDB = true;
            sbh.setParamsTrickle(height, i, isValid);
         }
      }

      if(!alreadyInHgtDB)
         sbh.setParamsTrickle(height, maxDup+1, isValid);
   }
   
   // Batch the two operations to make sure they both hit the DB, or neither 
   startBatch(HEADERS);

   if(!alreadyInHgtDB)
   {
      // Top bit is "isMainBranch_", lower 7 is the dupID
      uint8_t dup8 = sbh.duplicateID_ | (sbh.isMainBranch_ ? 0x80 : 0x00);

      // Make sure it exists in height index.  Put the new ones first so 
      // we can do less searching (since the last one stored is almost 
      // always the one we think is valid
      BinaryWriter bw(1+32+hgtList.getSize());  // reserve just enough size
      bw.put_uint8_t(dup8);
      bw.put_BinaryData(sbh.thisHash_);
      bw.put_BinaryData(hgtList);
      putValue(HEADERS, DB_PREFIX_HEADHGT, hgt4, bw.getDataRef());
   }
      
   // Overwrite the existing hash-indexed entry, just in case the dupID was
   // not known when previously written.  
   BinaryWriter bwHeaders;
   sbh.serializeDBValue(HEADERS, bwHeaders);
   putValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_, bwHeaders.getDataRef());

   commitBatch(HEADERS);

   startBatch(BLKDATA);

   // Now put the data into the blkdata DB
   BinaryData key = ARMDB.getBlkDataKey(sbh.blockHeight_, sbh.duplicateID_);
   BinaryWriter bwBlkData;
   sbh.serializeDBValue(BLKDATA, bwBlkData);
   putValue(BLKDATA, DB_PREFIX_TXDATA, key.getRef(), bwBlkData.getDataRef());
   
   // If we only wanted to update the BlockHeader record, we're done.
   if(!withTx)
   {
      commitBatch(BLKDATA);
      return;
   }

   for(uint32_t i=0; i<sbh.numTx_; i++)
   {
      map<uint16_t, StoredTx>::iterator txIter = sbh.stxMap_.find(i);
      if(txIter != sbh.stxMap_.end())
      {
         // Make sure the txIndex value is correct, then dump it to DB.
         txIter->second.txIndex_ = i;

         // When writing out the tx, we always write out the TxOuts.  
         // (that's what the second "true" argument is specifying)
         // There's no situation where we indicate *at the block-header 
         // level*, that we want to put the Txs but not the TxOuts.  
         // In other contexts, it may be desired to put/update a Tx 
         // without updating the TxOuts.
         putStoredTx(txIter->second, true);
      }
   }

   commitBatch(BLKDATA);
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredHeader( StoredHeader & sbh,
                                      uint32_t blockHgt,
                                      uint8_t blockDup,
                                      bool withTx)
{
   SCOPED_TIMER("getStoredHeader");

   if(!withTx)
   {
      //////
      // Don't need to mess with seeking if we don't need the transactions.
      BinaryData blkKey = ARMDB.getBlkDataKey(blockHgt, blockDup);
      BinaryRefReader brr = getValueReader(BLKDATA, blkKey);
      if(brr.getSize()==0)
      {
         Log::ERR() << "Header height&dup is not in BLKDATA";
         return false;
      }
      sbh.unserializeDBValue(BLKDATA, brr, false);
      return true;
   }
   else
   {
      //////
      // Do the iterator thing because we're going to traverse the whole block
      bool isInDB = seekTo(BLKDATA, ARMDB.getBlkDataKey(blockHgt, blockDup));
      if(!isInDB)
      {
         Log::ERR() << "Header heigh&dup is not in BLKDATA DB";
         Log::ERR() << "("<<blockHgt<<", "<<blockDup<<")";
         return false;
      }

      // Now we read the whole block, not just the header
      return readStoredBlockAtIter(sbh);
   }

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredHeader( StoredHeader & sbh,
                                      BinaryDataRef headHash, 
                                      bool withTx)
{
   SCOPED_TIMER("getStoredHeader");

   BinaryData headEntry = getValue(HEADERS, DB_PREFIX_HEADHASH, headHash); 
   if(headEntry.getSize() == 0)
   {
      Log::ERR() << "Requested header that is not in DB";
      return false;
   }
   
   BinaryRefReader brr(headEntry);
   sbh.unserializeDBValue(HEADERS, brr);

   return getStoredHeader(sbh, sbh.blockHeight_, sbh.duplicateID_, withTx);
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredHeader( StoredHeader & sbh,
                                      uint32_t blockHgt,
                                      bool withTx)
{
   uint8_t dupID = getValidDupIDForHeight(blockHgt);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHgt; 

   return getStoredHeader(sbh, blockHgt, dupID, withTx);
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::putStoredTx( StoredTx & stx, bool withTxOut)
{
   SCOPED_TIMER("putStoredTx");
   BinaryData ldbKey = ARMDB.getBlkDataKeyNoPrefix(stx.blockHeight_, 
                                                   stx.blockDupID_, 
                                                   stx.txIndex_);

   startBatch(BLKDATA);

   // First, check if it's already in the hash-indexed DB
   BinaryData hash4(stx.thisHash_.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);

   // Check for an existing Tx hint and add it if not there.  
   if(existingHints.getSize() > 0)
   {
      uint32_t numHints = existingHints.getSize() / 6;
      bool alreadyHasHint = false;
      for(uint32_t i=0; i<numHints; i++)
      {
         if(existingHints.getSliceRef(i*6, 6) == ldbKey)
         {
            alreadyHasHint = true;
            break;
         }
      }
      
      if(!alreadyHasHint)
      {
         BinaryWriter bw;
         bw.put_BinaryData(ldbKey);
         bw.put_BinaryData(existingHints);
         putValue(BLKDATA, DB_PREFIX_TXHINTS, hash4, bw.getDataRef());
      }
         
   }


   // Now add the base Tx entry in the BLKDATA DB.
   BinaryWriter bw;
   stx.serializeDBValue(bw);
   putValue(BLKDATA, DB_PREFIX_TXDATA, ldbKey, bw.getDataRef());


   // Add the individual TxOut entries if requested
   if(withTxOut)
   {
      map<uint16_t, StoredTxOut>::iterator iter;
      for(iter  = stx.stxoMap_.begin();
          iter != stx.stxoMap_.end();
          iter++)
      {
         // Make sure all the parameters of the TxOut are set right 
         iter->second.txVersion_   = READ_UINT32_LE(stx.dataCopy_.getPtr());
         iter->second.blockHeight_ = stx.blockHeight_;
         iter->second.blockDupID_  = stx.blockDupID_;
         iter->second.txIndex_     = stx.txIndex_;
         iter->second.txOutIndex_  = iter->first;
         putStoredTxOut(iter->second);
      }
   }

   commitBatch(BLKDATA);
}

////////////////////////////////////////////////////////////////////////////////
// We assume we have a valid iterator left at the header entry for this block
bool InterfaceToLDB::readStoredBlockAtIter(StoredHeader & sbh)
{
   currReadKey_.resetPosition();
   BinaryData blkDataKey(currReadKey_.getCurrPtr(), 5);
   BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                          sbh.blockHeight_,
                                          sbh.duplicateID_);

   
   // Grab the header first, then iterate over 
   sbh.unserializeDBValue(BLKDATA, currReadValue_, false);

   // If for some reason we hit the end of the DB without any tx, bail
   bool iterValid = advanceIterAndRead(BLKDATA, DB_PREFIX_TXDATA);
   if(!iterValid)
      return true;  // this isn't an error, it's an block w/o any StoredTx

   // Now start iterating over the tx data
   uint32_t tempHgt;
   uint8_t  tempDup;
   while(currReadKey_.getRawRef().startsWith(blkDataKey))
   {
      // We can't just read the the tx, because we have to guarantee 
      // there's a place for it in the sbh.stxMap_
      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, tempHgt, tempDup);

      uint16_t currTxIdx = currReadKey_.get_uint16_t(); 
      if(currTxIdx >= sbh.numTx_)
      {
         Log::ERR() << "Invalid txIndex at height " << (sbh.blockHeight_)
                    << " index " << currTxIdx;
         return false;
      }

      if(sbh.stxMap_.find(currTxIdx) == sbh.stxMap_.end())
         sbh.stxMap_[currTxIdx] = StoredTx();

      readStoredTxAtIter(sbh.blockHeight_, 
                         sbh.duplicateID_, 
                         sbh.stxMap_[currTxIdx]);
   } 
} 


////////////////////////////////////////////////////////////////////////////////
// We assume we have a valid iterator left at the beginning of (potentially) a 
// transaction in this block.  It's okay if it starts at at TxOut entry (in 
// some instances we may not have a Tx entry, but only the TxOuts).
bool InterfaceToLDB::readStoredTxAtIter(       
                                       uint32_t height,
                                       uint8_t  dupID,
                                       StoredTx & stx)
{
   BinaryData blkPrefix = ARMDB.getBlkDataKey(height, dupID);

   // Make sure that we are still within the desired block (but beyond header)
   currReadKey_.resetPosition();
   BinaryDataRef key = currReadKey_.getRawRef();
   if(!key.startsWith(blkPrefix) || key.getSize() < 7)
      return false;

   // Check that we are at a tx with the correct height & dup
   uint32_t storedHgt;
   uint8_t  storedDup;
   readBlkDataKey5B(currReadKey_, storedHgt, storedDup);
   if(storedHgt != height || storedDup != dupID)
      return false;

   // Make sure the stx has correct height/dup/idx
   stx.blockHeight_ = height;
   stx.blockDupID_  = dupID;
   stx.txIndex_     = currReadKey_.get_uint16_t();

   BinaryData txPrefix = ARMDB.getBlkDataKey(height, dupID, stx.txIndex_);

   
   // Reset the key again, and then cycle through entries until no longer
   // on an entry with the correct prefix.  Use do-while because we've 
   // already verified the iterator is at a valid tx entry
   currReadKey_.resetPosition();
   do
   {
      // Stop if key doesn't start with [PREFIX | HGT | DUP | TXIDX]
      if(!currReadKey_.getRawRef().startsWith(txPrefix))
         break;

      // Read the prefix, height and dup 
      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                             stx.blockHeight_,
                                             stx.blockDupID_);


      // Now actually process the iter value
      if(bdtype == BLKDATA_TX)
      {
         // Get everything else from the iter value
         stx.unserializeDBValue(currReadValue_);
      }
      else if(bdtype == BLKDATA_TXOUT)
      {
         currReadKey_.advance(2);
         uint16_t txOutIdx = currReadKey_.get_uint16_t();
         stx.stxoMap_[txOutIdx] = StoredTxOut();
         readStoredTxOutAtIter(height, dupID, stx.txIndex_, 
                                             stx.stxoMap_[txOutIdx]);
      }
      else
      {
         Log::ERR() << "Unexpected BLKDATA entry while iterating";
         return false;
      }
   } while(advanceIterAndRead(BLKDATA, DB_PREFIX_TXDATA));

   return true;
} 


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::readStoredTxOutAtIter(       
                                       uint32_t height,
                                       uint8_t  dupID,
                                       uint16_t txIndex,
                                       StoredTxOut & stxo)
{
   if(currReadKey_.getSize() < 9)
      return false;

   currReadKey_.resetPosition();

   // Check that we are at a tx with the correct height & dup & txIndex
   uint32_t storedHgt;
   uint8_t  storedDup;
   readBlkDataKey5B(currReadKey_, storedHgt, storedDup);
   uint16_t storedTxIdx    = currReadKey_.get_uint16_t();
   uint16_t storedTxOutIdx = currReadKey_.get_uint16_t();

   if(storedHgt != height || storedDup != dupID || storedTxIdx != txIndex)
      return false;

   stxo.blockHeight_ = height;
   stxo.blockDupID_  = dupID;
   stxo.txIndex_     = txIndex;
   stxo.txOutIndex_  = storedTxOutIdx;

   stxo.unserializeDBValue(currReadValue_);

}


////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( BinaryDataRef ldbKey6B )
{
   SCOPED_TIMER("getFullTxCopy");
   if(ldbKey6B.getSize() != 6)
   {
      Log::ERR() << "Provided zero-length ldbKey6B";
      return BinaryData(0);
   }
    
   if(seekTo(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B))
   {
      Log::ERR() << "TxRef key does not exist in BLKDATA DB";
      return BinaryData(0);
   }

   BinaryData hgtx = ldbKey6B.getSliceCopy(0,4);
   StoredTx stx;
   readStoredTxAtIter( ARMDB.hgtxToHeight(hgtx), ARMDB.hgtxToDupID(hgtx), stx);

   if(!stx.haveAllTxOut())
   {
      Log::ERR() << "Requested full Tx but not all TxOut available";
      return BinaryData(0);
   }

   return stx.getTxCopy();
}

////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( uint32_t hgt, uint16_t txIndex)
{
   SCOPED_TIMER("getFullTxCopy");
   uint8_t dup = getValidDupIDForHeight(hgt);
   if(dup == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << hgt;

   BinaryData ldbKey = ARMDB.getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}

////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( uint32_t hgt, uint8_t dup, uint16_t txIndex)
{
   SCOPED_TIMER("getFullTxCopy");
   BinaryData ldbKey = ARMDB.getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}


////////////////////////////////////////////////////////////////////////////////
TxOut InterfaceToLDB::getTxOutCopy( BinaryDataRef ldbKey6B, uint16_t txOutIdx)
{
   SCOPED_TIMER("getTxOutCopy");
   BinaryWriter bw(8);
   bw.put_BinaryData(ldbKey6B);
   bw.put_uint16_t(txOutIdx);
   BinaryDataRef ldbKey8 = bw.getDataRef();

   TxOut txoOut;
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey8);
   if(brr.getSize()==0) 
   {
      Log::ERR() << "TxOut key does not exist in BLKDATA DB";
      return TxOut();
   }

   TxRef parent(ldbKey6B, this);

   brr.advance(2);
   txoOut.unserialize(brr.getCurrPtr(), 0, parent, (uint32_t)txOutIdx);
}


////////////////////////////////////////////////////////////////////////////////
TxIn InterfaceToLDB::getTxInCopy( BinaryDataRef ldbKey6B, uint16_t txInIdx)
{
   SCOPED_TIMER("getTxInCopy");
   TxIn txiOut;
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B);
   if(brr.getSize()==0) 
   {
      Log::ERR() << "TxOut key does not exist in BLKDATA DB";
      return TxIn();
   }

   BitUnpacker<uint16_t> bitunpack(brr); // flags
   uint16_t dbVer   = bitunpack.getBits(4);
   uint16_t txVer   = bitunpack.getBits(2);
   uint16_t txSer   = bitunpack.getBits(4);
   
   brr.advance(32);

   
   if(txSer != TX_SER_FULL && txSer != TX_SER_FRAGGED)
   {
      Log::ERR() << "Tx not available to retrieve TxIn";
      return TxIn();
   }
   else
   {
      bool isFragged = txSer==TX_SER_FRAGGED;
      vector<uint32_t> offsetsIn;
      BtcUtils::StoredTxCalcLength(brr.getCurrPtr(), isFragged, &offsetsIn);
      if(offsetsIn.size()-1 < txInIdx+1) // offsets.size() is numTxIn+1
      {
         Log::ERR() << "Requested TxIn with index greater than numTxIn";
         return TxIn();
      }
      TxRef parent(ldbKey6B, this);
      uint8_t const * txInStart = brr.exposeDataPtr() + 34 + offsetsIn[txInIdx];
      uint32_t txInLength = offsetsIn[txInIdx+1] - offsetsIn[txInIdx];
      return TxIn(txInStart, txInLength, parent, txInIdx);
   }
}




////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTxHashForLdbKey( BinaryDataRef ldbKey6B )
{
   SCOPED_TIMER("getTxHashForLdbKey");
   BinaryRefReader stxVal = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B);
   if(stxVal.getSize()==0)
   {
      Log::ERR() << "TxRef key does not exist in BLKDATA DB";
      return BinaryData(0);
   }

   // We can't get here unless we found the precise Tx entry we were looking for
   stxVal.advance(2);
   return stxVal.get_BinaryData(32);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTxHashForHeightAndIndex( uint32_t height,
                                                       uint16_t txIndex)
{
   SCOPED_TIMER("getTxHashForHeightAndIndex");
   uint8_t dup = getValidDupIDForHeight(height);
   if(dup == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << height;
   return getTxHashForLdbKey(ARMDB.getBlkDataKey(height, dup, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTxHashForHeightAndIndex( uint32_t height,
                                                       uint8_t  dupID,
                                                       uint16_t txIndex)
{
   SCOPED_TIMER("getTxHashForHeightAndIndex");
   return getTxHashForLdbKey(ARMDB.getBlkDataKey(height, dupID, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> InterfaceToLDB::getAllHintsForTxHash(BinaryDataRef txHash)
{
   SCOPED_TIMER("getAllHintsForTxHash");
   BinaryDataRef allHints = getValueRef(BLKDATA, DB_PREFIX_TXHINTS, 
                                                txHash.getSliceRef(0,4));

   vector<BinaryData> hintsOut(allHints.getSize() / 6);
   for(uint32_t i=0; i<allHints.getSize()/6; i++)
      hintsOut[i] = allHints.getSliceCopy(i*6, 6);

   return hintsOut;
}


////////////////////////////////////////////////////////////////////////////////
// We assume that the first TxHint that matches is correct.  This means that 
// when we mark a transaction/block valid, we need to make sure all the hints
// lists have the correct one in front.  Luckily, the TXHINTS entries are tiny 
// and the number of modifications to make for each reorg is small.
bool InterfaceToLDB::getStoredTx( StoredTx & stx,
                                      BinaryDataRef txHash)
{
   SCOPED_TIMER("getStoredTx");
   BinaryData hash4(txHash.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);

   if(existingHints.getSize() == 0)
   {
      Log::ERR() << "No tx in DB with hash: " << txHash.toHexStr();
      return false;
   }

   // Now go through all the hints looking for the first one with a matching hash
   uint32_t numHints = existingHints.getSize() / 6;
   uint32_t height;
   uint8_t  dup;
   for(uint32_t i=0; i<numHints; i++)
   {
      BinaryDataRef hint = existingHints.getSliceRef(i*6, 6);
      seekTo(BLKDATA, DB_PREFIX_TXDATA, hint);

      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, height, dup);
      uint16_t txIdx = currReadKey_.get_uint16_t();
      
      // We don't actually know for sure whether the seekTo() found 
      BinaryData key6 = ARMDB.getBlkDataKeyNoPrefix(height, dup, txIdx);
      if(key6 != hint)
      {
         Log::ERR() << "TxHint referenced a BLKDATA tx that doesn't exist";
         continue;
      }

      currReadValue_.advance(2);  // skip flags
      if(currReadValue_.get_BinaryDataRef(32) == txHash)
      {
         resetIterReaders();
         return readStoredTxAtIter(height, dup, stx);
      }
   }

   return false;
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx(  StoredTx & stx,
                                       uint32_t blockHeight,
                                       uint16_t txIndex,
                                       bool withTxOut)
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTx(stx, blockHeight, dupID, txIndex, withTxOut);

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx(  StoredTx & stx,
                                       uint32_t blockHeight,
                                       uint8_t  dupID,
                                       uint16_t txIndex,
                                       bool withTxOut)
{
   SCOPED_TIMER("getStoredTx");
   BinaryData blkDataKey = ARMDB.getBlkDataKey(blockHeight, dupID, txIndex);
   stx.blockHeight_ = blockHeight;
   stx.blockDupID_  = dupID;
   stx.txIndex_     = txIndex;

   if(!withTxOut)
   {
      // In some situations, withTxOut may not matter here:  the TxOuts may
      // actually be serialized with the tx entry, thus the unserialize call
      // may extract all TxOuts.
      BinaryRefReader brr = getValueReader(BLKDATA, blkDataKey);
      if(brr.getSize()==0)
      {
         Log::ERR() << "BLKDATA DB does not have requested tx";
         Log::ERR() << "("<<blockHeight<<", "<<dupID<<", "<<txIndex<<")";
         return false;
      }

      stx.unserializeDBValue(brr);
   }
   else
   {
      
      bool isInDB = seekTo(BLKDATA, blkDataKey);
      if(!isInDB)
      {
         Log::ERR() << "BLKDATA DB does not have the requested tx";
         Log::ERR() << "("<<blockHeight<<", "<<dupID<<", "<<txIndex<<")";
         return false;
      }

      while(advanceIterAndRead(BLKDATA, DB_PREFIX_TXDATA))
      {
         // If the iter key doesn't start with [PREFIX | HGT | DUP], we're done
         if(!currReadKey_.getRawRef().startsWith(blkDataKey))
            break;

         
         BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                                stx.blockHeight_,
                                                stx.blockDupID_);
   
         uint16_t currTxIdx = currReadKey_.get_uint16_t(); 

         if(bdtype == BLKDATA_TX)
         {
            stx.unserializeDBValue(currReadValue_);
         }
         else if(bdtype == BLKDATA_TXOUT)
         {
            uint16_t currTxOutIdx = currReadKey_.get_uint16_t(); 

            stx.stxoMap_[currTxOutIdx] = StoredTxOut();
            StoredTxOut & stxo = stx.stxoMap_[currTxOutIdx];

            stxo.blockHeight_ = blockHeight;
            stxo.blockDupID_  = dupID;
            stxo.txIndex_     = txIndex;
            stxo.txOutIndex_  = currTxOutIdx;
            stxo.unserializeDBValue(currReadValue_);
         }
         else
         {
            Log::ERR() << "Unexpected BLKDATA entry while iterating";
            return false;
         }
      } // while(advanceIter)
   } // fetch header & txs

   return true;
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::putStoredTxOut( StoredTxOut const & stxo)
{
    
   SCOPED_TIMER("putStoredTx");
   BinaryData ldbKey = ARMDB.getBlkDataKeyNoPrefix(stxo.blockHeight_, 
                                                   stxo.blockDupID_, 
                                                   stxo.txIndex_,
                                                   stxo.txOutIndex_);

   BinaryWriter bw;
   stxo.serializeDBValue(bw);
   putValue(BLKDATA, DB_PREFIX_TXDATA, ldbKey, bw.getDataRef());
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint8_t  dupID,
                              uint16_t txIndex,
                              uint16_t txOutIndex)
{
   SCOPED_TIMER("getStoredTxOut");
   BinaryData blkKey = ARMDB.getBlkDataKey(blockHeight, dupID, txIndex, txOutIndex);
   BinaryRefReader brr = getValueReader(BLKDATA, blkKey);
   if(brr.getSize() == 0)
   {
      Log::ERR() << "BLKDATA DB does not have the requested TxOut";
      return false;
   }

   stxo.blockHeight_ = blockHeight;
   stxo.blockDupID_  = dupID;
   stxo.txIndex_     = txIndex;
   stxo.txOutIndex_  = txOutIndex;

   stxo.unserializeDBValue(brr);

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint16_t txIndex,
                              uint16_t txOutIndex)
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTxOut(stxo, blockHeight, dupID, txIndex, txOutIndex);
}



////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef( BinaryDataRef txHash )
{
   if(seekToTxByHash(txHash))
   {
      currReadKey_.advance(1);
      return TxRef(currReadKey_.get_BinaryDataRef(6), this);
   }
   
   return TxRef();
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef(BinaryData hgtx, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(hgtx);
   bw.put_uint16_t(txIndex);
   return TxRef(bw.getDataRef(), this);
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(ARMDB.heightAndDupToHgtx(hgt,dup));
   bw.put_uint16_t(txIndex);
   return TxRef(bw.getDataRef(), this);
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::markBlockHeaderValid(BinaryDataRef headHash)
{
   SCOPED_TIMER("markBlockHeaderValid");
   BinaryRefReader brr = getValueReader(HEADERS, DB_PREFIX_HEADHASH, headHash);
   if(brr.getSize()==0)
   {
      Log::ERR() << "Invalid header hash: " << headHash.toHexStr();
      return false;
   }
   brr.advance(HEADER_SIZE);
   BinaryData hgtx   = brr.get_BinaryData(4);
   uint32_t   height = ARMDB.hgtxToHeight(hgtx);
   uint8_t    dup    = ARMDB.hgtxToDupID(hgtx);

   return markBlockHeaderValid(height, dup);
}




////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::markBlockHeaderValid(uint32_t height, uint8_t dup)
{
   SCOPED_TIMER("markBlockHeaderValid");
   BinaryData keyHgt((uint8_t*)&height, 4);

   BinaryRefReader brrHgts = getValueReader(HEADERS, DB_PREFIX_HEADHGT, keyHgt);
   uint32_t numDup = brrHgts.getSize() / 33;

   if(numDup==0)
   {
      Log::ERR() << "Height and dup do not exist in HEADERS DB";
      return false;
   }

   // First create a list with the correct header in front
   list<BinaryDataRef> collectList;
   bool hasEntry = false;
   for(uint8_t i=0; i<numDup; i++)
   {
      uint8_t dup8 = *(brrHgts.getCurrPtr()); // just peek at the next byte

      if(dup8 & 0x7f != dup)
         collectList.push_back( brrHgts.get_BinaryDataRef(33) );
      else
      {
         collectList.push_front( brrHgts.get_BinaryDataRef(33) );
         hasEntry = true;
      }
   }
   
   // If there was no entry with this hash, then all existing values will be 
   // written with not-valid.
   BinaryWriter bwOut(33*numDup);
   list<BinaryDataRef>::iterator iter = collectList.begin();
   for(uint8_t i=0; i<numDup; i++, iter++)
   {
      BinaryRefReader brr(*iter);
      if(i==0 && hasEntry) 
         bwOut.put_uint8_t(brr.get_uint8_t() | 0x80);
      else                 
         bwOut.put_uint8_t(brr.get_uint8_t() & 0x7f);
      
      bwOut.put_BinaryData(brr.get_BinaryDataRef(32));
   }
   
   // Rewrite the HEADHGT entries
   putValue(HEADERS, DB_PREFIX_HEADHGT, keyHgt, bwOut.getDataRef());

   // Make sure we have a quick-lookup available.
   validDupByHeight_[height] = dup;

   if(!hasEntry)
      Log::ERR() << "Header was not found header-height list";

   return hasEntry;
}

////////////////////////////////////////////////////////////////////////////////
// This is an inelegant consequence of this DB design -- if a tx 
// appears in two branches, it will be in the DB twice and appear twice
// in the TXHINTS list.  We have chosen to NOT store a "isValid" flag
// with each tx and txout, to avoid duplication of data that might 
// possibly de-synchronize and cause all sorts of problems (just go verify
// the HEADHGT entry).  But to avoid unnecessary lookups, we must make 
// sure that the correct {hgt,dup,txidx} is in the front of the TXHINTS 
// list.  
bool InterfaceToLDB::markTxEntryValid(uint32_t height,
                                          uint8_t  dupID,
                                          uint16_t txIndex)
{
   SCOPED_TIMER("markTxEntryValid");
   BinaryData blkDataKey = ARMDB.getBlkDataKeyNoPrefix(height, dupID, txIndex);
   BinaryRefReader brrTx = getValueReader(BLKDATA, DB_PREFIX_TXDATA, blkDataKey);

   brrTx.advance(2);
   BinaryData key4 = brrTx.get_BinaryData(4); // only need the first four bytes

   BinaryRefReader brrHints = getValueReader(BLKDATA, DB_PREFIX_TXHINTS, key4);
   uint32_t numHints = brrHints.getSize() / 6;
   if(numHints==0)
   {
      Log::ERR() << "No TXHINTS entry for specified {hgt,dup,txidx}";      
      return false;
   }
   
   // Create a list of refs with the correct tx in front
   list<BinaryDataRef> collectList;
   bool hasEntry = false;
   for(uint8_t i=0; i<numHints; i++)
   {
      BinaryDataRef thisHint = brrHints.get_BinaryDataRef(6);

      if(thisHint != blkDataKey)
         collectList.push_back(thisHint);
      else
      {
         collectList.push_front(thisHint);
         hasEntry = true;
      }
   }
   
   // If this hint didn't exist, we don't need to change anything (besides 
   // triggering an error/warning it didn't exist.
   if(!hasEntry)
   {
      Log::ERR() << "Tx was not found in the TXHINTS list";
      return false;
   }


   // If there was no entry with this hash, then all existing values will be 
   // written with not-valid.
   BinaryWriter bwOut(6*numHints);
   list<BinaryDataRef>::iterator iter;
   for(iter = collectList.begin(); iter != collectList.end(); iter++)
      bwOut.put_BinaryData(*iter);
   
   putValue(HEADERS, DB_PREFIX_HEADHGT, key4, bwOut.getDataRef());
   return true;
}

////////////////////////////////////////////////////////////////////////////////
list< pair<BinaryData, BinaryData> > InterfaceToLDB::getAllDatabaseEntries(DB_SELECT db)
{
   SCOPED_TIMER("getAllDatabaseEntries");
   KVLIST outList;
   KVITER outIter;

   iters_[db] = dbs_[db]->NewIterator(leveldb::ReadOptions());
   iters_[db]->SeekToFirst();
   for (; iters_[db]->Valid(); iters_[db]->Next())
   {
      outList.push_back( pair<BinaryData, BinaryData>() );
      outIter = outList.end();
      outIter--;
      sliceToBinaryData(iters_[db]->key(),   outIter->first);
      sliceToBinaryData(iters_[db]->value(), outIter->second);
   }
   return outList;
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::printAllDatabaseEntries(DB_SELECT db)
{
   SCOPED_TIMER("printAllDatabaseEntries");
   cout << "Printing DB entries... (DB=" << db << ")" << endl;
   KVLIST dbList = getAllDatabaseEntries(db);
   KVITER dbIter;
   for(dbIter = dbList.begin();  dbIter != dbList.end(); dbIter++)
   {
      cout << "   \"" << dbIter->first.toHexStr() << "\"  ";
      cout << "   \"" << dbIter->second.toHexStr() << "\"  " << endl;
   }
}


/*
////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getUndoDataForTx( Tx const & tx,
                                           list<TxOut> &    txOutsRemoved,
                                           list<OutPoint> & outpointsAdded)
{
   // For ARMORY_DB_FULL we don't need undo data yet.
}

////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getUndoDataForBlock( list<TxOut> &    txOutsRemoved,
                                              list<OutPoint> & outpointsAdded)
{
   // Maybe don't clear them, so that we can accumulate multi-block data, if 
   // we have some reason to do that.  Let the caller clear the lists
   //txOutsRemoved.clear();
   //outpointsAdded.clear();

   // For ARMORY_DB_FULL we don't need undo data yet.
   for(uint32_t i=0; i<numTx_; i++)
      getUndoDataForTx(block.txList[i], txOutsRemoved, outpointsAdded);
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::purgeOldUndoData(uint32_t earlierThanHeight)
{
   // For ARMORY_DB_FULL we don't need undo data yet.
}
*/

   
////////////////////////////////////////////////////////////////////////////////
//  Not sure that this is possible...
/*
bool InterfaceToLDB::updateHeaderHeight(BinaryDataRef headHash, 
                                            uint32_t height, uint8_t dup)
{
   BinaryDataRef headVal = getValueRef(HEADERS, headHash);
   if(headVal.isNull())
   {
      Log::ERR() << " Attempted to update a non-existent header!";
      return false;
   }
      
   BinaryWriter bw(HEADER_SIZE + 4);
   bw.put_BinaryData(headVal.getPtr(), HEADER_SIZE);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));

   putValue(HEADERS, headHash, bw.getDataRef());
   return true;
}  
*/


