#include <iostream>
#include <sstream>
#include "leveldb_wrapper.h"



////////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::sliceToBinaryData(leveldb::Slice slice)
{ 
   return BinaryData((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
inline void InterfaceToLevelDB::sliceToBinaryData(leveldb::Slice slice, 
                                                  BinaryData & bd)
{ 
   bd.copyFrom((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
inline BinaryReader InterfaceToLevelDB::sliceToBinaryReader(leveldb::Slice slice)
{ 
   return BinaryReader.copyFrom((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
inline void InterfaceToLevelDB::sliceToBinaryReader(leveldb::Slice slice, 
                                                    BinaryReader & brr)
{ 
   brr.setNewData((uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
inline BinaryDataRef InterfaceToLevelDB::sliceToBinaryDataRef(leveldb::Slice slice)
{ 
   return BinaryDataRef( (uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
inline BinaryRefReader InterfaceToLevelDB::sliceToBinaryRefReader(leveldb::Slice slice)
{ 
   return BinaryRefReader( (uint8_t*)(slice.data()), slice.size()); 
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::init()
{
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
InterfaceToLevelDB::InterfaceToLevelDB() 
{
   init();
}

////////////////////////////////////////////////////////////////////////////////
// The dbType and pruneType inputs are left blank if you are just going to take 
// whatever is the current state of database.  You can choose to manually 
// specify them, if you want to throw an error if it's not what you were 
// expecting
InterfaceToLevelDB::InterfaceToLevelDB(
                   string             basedir, 
                   BinaryData const & genesisBlkHash, 
                   BinaryData const & genesisTxHash, 
                   BinaryData const & magic,
                   ARMORY_DB_TYPE     dbtype=ARMORY_DB_WHATEVER,
                   DB_PRUNE_TYPE      pruneType=DB_PRUNE_WHATEVER)
{
   init();
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

   // Open databases and check that everything is correct
   // Or create the databases and start it up
   openDatabases();
}


/////////////////////////////////////////////////////////////////////////////
InterfaceToLevelDB::~InterfaceToLevelDB(void)
{
   for(uint32_t db=0; db<(uint32_t)DB_COUNT; db++)
      if(batchStarts_[db] > 0)
         Log::ERR() << "Unwritten batch in progress during shutdown";

   closeDatabases();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txOutScriptToLDBKey(BinaryData const & script,
                                                   bool withPrefix)
{
   BinaryWriter bw(22);  // reserve 22 bytes which is almost always perfect
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_SCRIPT);
   bw.put_BinaryData(getTxOutScriptUniqueKey(script.getRef());
   return bw.getData();
}




/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::openDatabases(void)
{
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
      leveldb::Options opts;
      opts.create_if_missing = true;
      //opts2.compression        = leveldb::kNoCompression;
      //opts2.filter_policy      = leveldb::NewBloomFilter(10);
      checkStatus(leveldb::DB::Open(opts2, dbPaths_[db],  &dbs_[db]));

      // Create an iterator that we'll use for ust about all DB seek ops
      iters_[db] = dbs_[db]->NewIterator(leveldb::ReadOptions());
      batches_[db] = NULL;
      batchStarts_[db] = 0;
         
      BinaryData dbInfo = getValue(dbs_[db], getDBInfoKey());
      if(dbInfo.getSize() == 0)
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         BitWriter<uint32_t> bitwrite;
         uint32_t flagBytes = 0;
         bitwrite.putBits((uint32_t)ARMORY_DB_VERSION, 4);
         bitwrite.putBits((uint32_t)armoryDbType_,     4);
         bitwrite.putBits((uint32_t)dbPruneType_,      4);

         BinaryWriter bw(48);
         bw.put_uint32_t(ARMORY_DB_VERSION)
         bw.put_BinaryData(magicBytes_);
         bw.put_uint32_t(bitwrite.getValue());
         bw.put_uint32_t(0);
         bw.put_BinaryData(genesisBlkHash_);
   
         putValue(dbs_[db], getDBInfoKey(), bw.getData());
      }
      else
      {
         // Else we read the DB info and make sure everything matches up
         if(dbinfo.getSize() < 40)
         {
            Log::ERR() << "Invalid DatabaseInfo data";
            closeDatabases();
            return false;
         }
         BinaryReader br(dbinfo);
         uint32_t version = br.get_uint32_t();
         BinaryData magic = br.get_BinaryData(4);
         uint32_t flags   = br.get_uint32_t();
         topBlockHeight_  = br.get_uint32_t();
         topBlockHash_    = br.get_BinaryData(32);
      
         // Check that the magic bytes are correct
         if(magicBytes_ != magic)
         {
            Log::ERR() << " Magic bytes mismatch!  Different blkchain?";
            closeDatabases();
            return false;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValue(dbs_[db], topBlockHash_).getSize() == 0 )
         {
            Log::ERR() << " Top block doesn't exist!";
            closeDatabases();
            return false;
         }

         BitReader<uint32_t> bitread(flags);
         uint32_t dbVer      = bitread.getBits(4);
         uint32_t dbType     = bitread.getBits(4);
         uint32_t pruneType  = bitread.getBits(4);

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

         // Reserve space in the vector to delay reallocation for 32 weeks
         validDupByHeight_.clear();
         validDupByHeight_.reserve(topBlockHeight_ + 32768);
         validDupByHeight_.resize(topBlockHeight_+1);
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readAllStoredScriptHistory(
                          map<BinaryData, StoredScriptHistory> & regScriptMap)
{
   // Now read all the StoredAddressObjects objects to make it easy to query
   // inclusion directly from RAM.
   seekTo(BLKDATA, DB_PREFIX_SCRIPT, BinaryData(0))
   lowestScannedUpTo_ = UINT32_MAX;
   while(iter->Valid())
   {
      if(!checkPrefixByte(currReadKey_, DB_PREFIX_SCRIPT)
         break;

      StoredScriptHistory ssh;
      readStoredScriptHistoryAtIter(ssh);
      registeredAddrSet_[ssh.uniqueKey] = ssh;
      lowestScannedUpTo_ = min(lowestScannedUpTo_, ssh.alreadyScannedUpToBlk_);
      iter->Next();
   }
}


/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void InterfaceToLevelDB::closeDatabases(void)
{
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      if( dbs_[db] != NULL)
         delete dbs_[db];
      
      if( batches_[db] != NULL )
         delete batches_[db];
   }
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::startBatch(DB_SELECT db)
{
   if(batchStarts_[db] == 0)
   {
      if(batches_[db] != NULL)
      {
         Log::ERR() << "Trying to startBatch but we already have one";
         delete batches_[db];
      }

      batches_[db] = new WriteBatch;
   }

   // Increment the number of times we've called this function
   batchStarts_[db] += 1;
}



////////////////////////////////////////////////////////////////////////////////
// Commit all the batched operations
void InterfaceToLevelDB::commitBatch(DB_SELECT db)
{
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
      delete batches_[db];
      batches_[db] = NULL;
      iterIsDirty_[db] = true;
   }
}

////////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
void InterfaceToLevelDB::commitBatch(DB_SELECT db, doSync=false)
{
   if(batches_[db] == NULL)
   {
      Log::ERR() << " Can't commit NULL WriteBatch";
      return;
   }
   leveldb::WriteOptions writeopt;
   writeopt.sync = doSync;
   leveldb::Status stat = dbs_[db]->Write(writeopt, batches_[db]);
   checkStatus(stat);

   batches_[db]->Clear();
   delete batches_[db];
   batches_[db] = NULL;
}

/////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
inline BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, leveldb::Slice ldbKey)
{
   leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbKey, &lastGetValue_);
   if(stat==Status::IsNotFound())
      return BinaryData(0);

   checkStatus(stat);
   return BinaryData(lastGetValue_);
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
inline BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, BinaryDataRef key)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   return getValue(db, ldbKey);
}


/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
inline BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, 
                                               DB_PREFIX prefix,
                                               BinaryDataRef key)
{
   BinaryData keyFull(key.size()+1);
   keyFull[0] = (uint8_t)prefix;
   key.copyTo(keyFull.getPtr()+1, key.getSize());
   leveldb::Slice ldbKey((char*)keyFull.getPtr(), keyFull.getSize());
   return getValue(db, ldbKey)
}


/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
inline BinaryDataRef InterfaceToLevelDB::getValueRef(DB_SELECT db, 
                                                     BinaryDataRef key)
{
   //leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   //return getValue(db, ldbKey)

   leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbKey, &lastGetValue_);
   if(stat==Status::IsNotFound())
      lastGetValue_ = string("");

   return BinaryDataRef(lastGetValue_.data(), lastGetValue_.size());
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
inline BinaryDataRef InterfaceToLevelDB::getValueRef(DB_SELECT db, 
                                                     DB_PREFIX prefix, 
                                                     BinaryDataRef key)
{
   BinaryData ldbkey(key.getSize()+1)
   ldbkey[0] = (uint8_t)prefix;
   key.copyTo(ldbkey.getPtr()+1, key.getSize());
   return getValueRef(db, ldbkey);
}


/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
inline BinaryDataRef InterfaceToLevelDB::getValueReader(
                                             DB_SELECT db, 
                                             BinaryDataRef keyWithPrefix)
{
   return BinaryRefReader(getValueRef(db, keyWithPrefix));
}


/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
inline BinaryDataRef InterfaceToLevelDB::getValueReader(
                                             DB_SELECT db, 
                                             DB_PREFIX_TYPE prefix, 
                                             BinaryDataRef key)
{
   return BinaryRefReader(getValueRef(db, prefix, key));
}






/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLevelDB::putValue(DB_SELECT db, 
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   leveldb::Slice ldbVal((char*)value.getPtr(), value.getSize());
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, &value);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(leveldb::WriteOptions(), ldbkey, &value);
      checkStatus(stat);
      iterIsDirty_[db] = true;
   }
   
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLevelDB::putValue(DB_SELECT db, 
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
void InterfaceToLevelDB::deleteValue(DB_SELECT db, 
                                     BinaryData const & key)
                 
{
   string value;
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, &value);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(leveldb::ReadOptions(), ldbkey, &value);
      checkStatus(stat);
      iterIsDirty_[db] = true;
   }
}


/////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         bool withPrefix)
{
   BinaryWriter bw(5);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         uint16_t txIdx, 
                         bool withPrefix)
{
   BinaryWriter bw(7);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(txIdx);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         uint16_t txIdx,
                         uint16_t txOutIdx,
                         bool withPrefix)
{
   BinaryWriter bw(9);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(txIdx);
   bw.put_uint16_t(txOutIdx);
   return bw.getData();
}


/////////////////////////////////////////////////////////////////////////////
// Not sure why this is useful over getHeaderMap() ... this iterates over
// the headers in hash-ID-order, instead of height-order
void InterfaceToLevelDB::startHeaderIteration()
{
   seekTo(HEADERS, DB_PREFIX_HEADHASH, BinaryData(0));
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::startBlkDataIteration(DB_PREFIX prefix)
{
   seekTo(BLKDATA, prefix, BinaryData(0));
   leveldb::Slice start(&prefix, 1);
   iters_[BLKDATA]->Seek(start);
   iteratorToRefReaders(iters_[BLKDATA], currReadKey_, currReadValue_);
}


/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLevelDB::advanceToNextBlock(bool skip)
{
   char prefix = DB_PREFIX_BLKDATA;

   leveldb::Iterator* it = iters_[BLKDATA];
   BinaryData key;
   while(1) 
   {
      if(skip) it->Next();

      if( !it->Valid() || it->key()[0] != (char)DB_PREFIX_BLKDATA)
         return false;
      else if( it->key().size() == 5)
      {
         iteratorToRefReaders(it, currReadKey_, currReadValue_);
         return true;
      }

      if(!skip) it->Next()
   } 
   Log::ERR() << "we should never get here...";
   return false;
}



/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLevelDB::seekTo(DB_SELECT db,
                                BinaryDataRef key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   it.Seek(binaryDataToSlice(key));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   bool isMatch = (currReadKey_.getRawRef()==key);
   return isMatch;
}

/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLevelDB::seekTo(DB_SELECT db,
                                DB_PREFIX prefix, 
                                BinaryDataRef key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   BinaryData ldbkey;
   if(db==HEADERS)
      return seekTo(db, key, it);
   else
   {
      uint8_t prefInt = (uint8_t)prefix;
      ldbkey = BinaryData(&prefInt, 1) + key;
      return seekTo(db, ldbkey, it);
   }
}


////////////////////////////////////////////////////////////////////////////////
// We frequently have a Tx hash and need to determine the Hgt/Dup/Index of it.
// And frequently when we do, we plan to read the tx right afterwards, so we
// should leave the itereator there.
bool seekToTxByHash(BinaryDataRef txHash)
{
   BinaryData hash4(txHash.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);

   if(existingHints.getSize() == 0)
   {
      Log::ERR() << "No tx in DB with hash: " << txHash.toHexStr();
      return false;
   }

   // Now go through all the hints looking for the first one with a matching hash
   uint32_t numHints = existingHints.getSize() / 6;
   uint32_t hgtx, height;
   uint8_t  dup;
   for(uint32_t i=0; i<numHints; i++)
   {
      BinaryDataRef hint = existingHints.getSliceRef(i*6, 6);
      seekTo(BLKDATA, DB_PREFIX_BLKDATA, hint);

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
void InterfaceToLevelDB::seekFirstScript( levelbd::Iterator* it=NULL)
{
   if(it==NULL)
      it = iters_[BLKDATA];

   char prefix = DB_PREFIX_SCRIPT;
   leveldb::Slice start(&prefix, 1);
   it.Seek(start);
}


/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::seekToRegAddr(BinaryData const & addr,
                                       leveldb::Iterator* it=NULL)
{
   if(it==NULL)
      it = iters_[BLKDATA];

   uint8_t prefix = DB_PREFIX_SCRIPT;
   BianryData ldbkey = BinaryData(&prefix, 1) + addr;

   it.Seek(binaryDataToSlice(ldbkey));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   uint8_t itPrefix = currReadKey_.get_uint8_t();
   uint32_t sz = currReadKey_.getSize();
   if(itPrefix != prefix ||
      currReadKey_.get_BinaryDataRef(sz-1) != addr)
   {
      currReadKey_.resetPosition();
      return false;
   }

   currReadKey_.resetPosition();
   return true;
}


/////////////////////////////////////////////////////////////////////////////
// Makes copies of the key and value
void InterfaceToLevelDB::iteratorToReaders( leveldb::Iterator* it, 
                                            BinaryReader & brKey,
                                            BinaryReader & brValue)
{
   brKey.setNewData(it->key().data(), it->key().size());      
   brValue;.setNewData(it->value().data(), it->value().size());      
}



/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::deleteIterator(DB_SELECT db)
{
   delete iters_[db];
   iters_[db] = NULL;
   iterIsDirty_[db] = false;
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::resetIterator(DB_SELECT db)
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
void InterfaceToLevelDB::iteratorToRefReaders( leveldb::Iterator* it, 
                                               BinaryRefReader & brrKey,
                                               BinaryRefReader & brrValue)
{
   brrKey.setNewData(it->key().data(), it->key().size());      
   brrValue;.setNewData(it->value().data(), it->value().size());      
}

}


////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE InterfaceToLevelDB::readBlkDataKey5B(
                                 BinaryRefReader & brr,
                                 uint32_t & height,
                                 uint8_t  & dupID)
{
   uint8_t  prefix = brr.get_uint8_t()
   if(prefix != DB_PREFIX_BLKDATA)
   {
      height = 0xffffffff;
      dupID  =       0xff;
      return NOT_BLKDATA;
   }
   
   uint32_t hgtX   = brr.get_uint32_t()
   height = hgtxToHeight(hgtX);
   dupID  = hgtxToDupID(hgtX);

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



////////////////////////////////////////////////////////////////////////////////
//void InterfaceToLevelDB::readBlkDataTxKey( BinaryRefReader & brr, StoredTx & tx)
//{
   //BLKDATA_TYPE bdtype = readBlkDataKey5B(brr, tx.storedHeight_, tx.storedDupID_);
   //if(bdtype != DB_PREFIX_BLKDATA)
   //{
      //Log::ERR() << "Attempted to read Tx key, but not a StoredTx entry";
      //tx = StoredTx();
      //return;
   //}

   //tx.txIndex_ = brr.get_uint16_t()
//}

////////////////////////////////////////////////////////////////////////////////
//void InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr, 
                                              //StoredTxOut & txout)
//{
   //BLKDATA_TYPE bdt = readBlkDataKey5B(brr, txOut.blockHeight_, tx.blockDupID_);
   //if(bdt != DB_PREFIX_BLKDATA)
   //{
      //Log::ERR() << "Attempted to read Tx key, but not a StoredTx entry";
      //tx = StoredTx();
      //return;
   //}
   
   //txout.txIndex_    = brr.get_uint16_t();
   //txout.txOutIndex_ = brr.get_uint16_t();
//}

////////////////////////////////////////////////////////////////////////////////
//StoredTxOut InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr)
//{
   //StoredTxOut txo;
   //BLKDATA_TYPE bdt = readBlkDataKey5B(brr, txo.blockHeight_, txo.blockDupID_);
   //if(bdt != DB_PREFIX_BLKDATA)
      //return

   //txo.txIndex_    = brr.get_uint16_t();
   //txo.txOutIndex_ = brr.get_uint16_t();
//}


////////////////////////////////////////////////////////////////////////////////
string InterfaceToLevelDB::getPrefixName(DB_PREFIX_TYPE pref)
{
   switch(pref)
   {
      case DB_PREFIX_DBINFO:    return string("DBINFO"); 
      case DB_PREFIX_BLKDATA:   return string("BLKDATA"); 
      case DB_PREFIX_SCRIPT:    return string("SCRIPT"); 
      case DB_PREFIX_TXHINTS:   return string("TXHINTS"); 
      case DB_PREFIX_TRIENODES: return string("TRIENODES"); 
      case DB_PREFIX_HEADHASH:  return string("HEADHASH"); 
      case DB_PREFIX_HEADHGT:   return string("HEADHGT"); 
      case DB_PREFIX_UNDODATA:  return string("UNDODATA"); 
      case default:             return string("<unknown>"); 
   }
}

/////////////////////////////////////////////////////////////////////////////
inline bool InterfaceToLevelDB::checkPrefixByte(BinaryRefReader brr, 
                                                DB_PREFIX_TYPE prefix,
                                                bool rewindWhenDone);
{
   uint8_t oneByte = brr.get_uint8_t()
   bool out;
   if(oneByte == (uint8_t)prefix)
      out = true;
   else
   {
      Log::ERR() << "Unexpected prefix byte: "
                 << "Expected: " << getPrefixName(prefix)
                 << "Received: " << getPrefixName(oneByte)
      out = false;
   }

   if(rewindWhenDone)
      brr.rewind(1);
}

/////////////////////////////////////////////////////////////////////////////
inline bool InterfaceToLevelDB::checkPrefixByte(DB_PREFIX_TYPE prefix);
{
   return checkPrefixByte(currReadKey_, prefix); 
}

/////////////////////////////////////////////////////////////////////////////
bool readStoredScriptHistoryAtIter( StoredScriptHistory & ssh)
                               
{
   resetIterReaders();

   checkPrefixByte(currReadKey_, DB_PREFIX_SCRIPT);
      
   uint32_t nBytes = currReadKey_.getSizeRemaining();
   ssh.addrType_ = currReadKey_.get_uint8_t()
   currReadKey_.get_BinaryData(ssh.uniqueKey_, nBytes-1);

   unserializeStoredScriptHistory(currReadValue_, ssh, accumTxIO);
}


////////////////////////////////////////////////////////////////////////////////
// The list of spent/unspent txOuts is exactly what is needed to construct 
// a full vector<TxIOPair> for each address.  Keep in mind that this list
// only contains TxOuts and spentness of those TxOuts that are:
//    (1) Already in the blockchain
//    (2) On the longest chain at the time is was written
// It contains no zero-confirmation tx data, and it may not be accurate 
// if there was a reorg since it was written.  Part of the challenge of 
// implementing this DB stuff correctly is making sure both conditions 
// above are adhered to, despite TxIOPair objects being used in RAM to store
// zero-confirmation data as well as in-blockchain data.
//
void InterfaceToLevelDB::unserializeStoredScriptHistory(
                                    BinaryRefReader      & brr, 
                                    StoredScriptHistory  & ssh)
{
   // Now read the stored data fro this registered address
   BitReader<uint16_t> bitread(brr);
   ssh.version_                 =                    bitread.getBits(4);
   DB_PRUNE_TYPE pruneType      = (DB_PRUNE_TYPE)    bitread.getBits(2);
   SCRIPT_UTXO_TYPE txoListType = (SCRIPT_UTXO_TYPE) bitread.getBits(2);
   ssh.hasMultisigEntries_      =                    bitread.getBit();

   ssh.alreadyScannedUpToBlk_ = brr.get_uint32_t();

   if(txoListType == SCRIPT_UTXO_TREE)
   {
      // This is where we might implement the Reiner-Tree concept, by
      // having only a reference to one TxOut here, but it's actually 
      // the root of some kind of authenticated tree structure.
      Log::ERR() << "TXO-trees are not implemented, yet!";
      return;
   }
   else if(txoListType == SCRIPT_UTXO_VECTOR)
   {
      // Get the TxOut list if a pointer was supplied
      // This list is unspent-TxOuts only if pruning enabled.  You will
      // have to dereference each one to check spentness if not pruning
      uint32_t numTxo = (uint32_t)(brr.get_var_int());
      ssh.txioVect_.reserve(numTxo);
      for(uint32_t i=0; i<numTxo; i++)
      {
         BitReader<uint8_t> bitread(brr);
         bool isFromSelf  = bitread.getBit();
         bool isCoinbase  = bitread.getBit();
         bool isSpent     = bitread.getBit();

         // We always include the value, here
         uint64_t txoValue  = brr.get_uint64_t();

         TxIOPair txio;
         if(!isSpent)
         {
            BinaryDataRef  txokey = brr.get_BinaryDataRef(6);
            uint16_t       txoidx = brr.get_uint16_t();

            txio = TxIOPair(TxRef(txokey,this), txoidx);
         }
         else
         {
            BinaryDataRef  txokey = brr.get_BinaryDataRef(6);
            uint16_t       txoidx = brr.get_uint16_t();
            BinaryDataRef  txikey = brr.get_BinaryDataRef(6);
            uint16_t       txiidx = brr.get_uint16_t();

            txio = TxIOPair(TxRef(txokey,this), txoidx, 
                            TxRef(txikey,this), txiidx);

         }
         txio.setValue(txoValue);
         txio.setTxOutFromSelf(isFromSelf);
         txio.setFromCoinbase(isCoinbase);
         ssh.txioVect_.push_back(txio);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::serializeStoredAddress(
                                          StoredScriptHistory & ssh,
                                          BinaryWriter        & bw)
{
      

   // Write out all the flags
   BitWriter<uint16_t> bitwrite;
   bitwrite.putBits((uint16_t)ARMORY_DB_VERSION,   4);
   bitwrite.putBits((uint16_t)dbPruneType_,        2);
   bitwrite.putBits((uint16_t)SCRIPT_UTXO_VECTOR, 2);
   bitwrite.putBit(ssh.hasMultisigEntries_);
   bw.put_uint16_t(bitwrite.getValue());

   // 
   bw.put_uint32_t(ra.alreadyScannedUpToBlk_); 

   if(txoListType == SCRIPT_UTXO_TREE)
   {
      // This is where we might implement the Reiner-Tree concept, by
      // having only a reference to one TxOut here, but it's actually 
      // the root of some kind of authenticated tree structure.
      Log::ERR() << "TXO-trees are not implemented, yet!";
      return;
   }
   else if(txoListType == SCRIPT_UTXO_VECTOR)
   {
      // Get the TxOut list if a pointer was supplied
      // This list is unspent-TxOuts only if pruning enabled.  You will
      // have to dereference each one to check spentness if not pruning
      uint32_t numTxo = (uint32_t)ssh.getTxIOList().size();
      for(uint32_t i=0; i<numTxo; i++)
      {
         TxIOPair* txio = ssh.getTxIOList()[i];
         bool isSpent = txio->hasTxInInMain();

         // If spent and only maintaining a pruned DB, skip it
         if(isSpent && dbPruneType_==DB_PRUNE_ALL)
            continue;

         BitWriter<uint8_t> bitwrite;
         bitwrite.putBit(txio->isTxOutFromSelf());
         bitwrite.pubBit(txio->isFromCoinbase());
         bitwrite.pubBit(txio->hasTxInInMain());
         bw.put_uint8_t(bitwrite.getValue());

         // Always write the value and 8-byte TxOut
         bw.put_uint64_t(txio->getValue());
         bw.put_BinaryData(txio->getTxRefOfOutput().getLevelDBKeyRef());
         bw.put_uint16_t(txio->getIndexOfOutput());

         // If not supposed to write the TxIn, we would've bailed earlier
         if(isSpent)
         {
            if(!txio->getTxRefOfInput().isInitialized())
               bw.put_uint64_t(0);
            else
            {
               bw.put_BinaryData(txio->getTxRefOfInput().getLevelDBKeyRef());
               bw.put_uint16_t(txio->getIndexOfInput());
            }
         }
      }
   }
}


void InterfaceToLevelDB::getStoredScriptHistoryByScript(BinaryDataRef txOutScript,
                                                      StoredScriptHistory & sad)
{
   BinaryData uniqueKey = txOutScriptToLDBKey(txOutScript);
   getStoredScriptHistory(uniqueKey, sad);
}

void InterfaceToLevelDB::getStoredScriptHistory(BinaryDataRef uniqueKey,
                                              StoredScriptHistory & sad)
{
   BinaryRefReader brr = getValueRef(BLKDATA, DB_PREFIX_SCRIPT, uniqueKey);
   
}

/*
/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readStoredScriptHistory(StoredScriptHistory & regAddr,
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
bool InterfaceToLevelDB::getUnspentTxOut( BinaryData & const ldbKey8B,
                                          UnspentTxOut & utxo)
{
   BinaryRefReader txrr(txoData[i]);
   uint32_t hgtX   = txrr.get_uint32_t();
   uint16_t txIdx  = txrr.get_uint16_t();
   uint16_t outIdx = txrr.get_uint16_t();


   BinaryDataRef txRef(txoData[i].getPtr(), 6);
   bool isFound = seekTo(BLKDATA, DB_PREFIX_BLKDATA, txRef);
   if(!isFound)
   {
      Log::ERR() << " could not find transaction in DB";
      return false;
   }

   // Need to get the height and hash of the parent transaction
   Tx tx;
   readBlkDataTxValue(currReadValue_, tx)

   // Now get the TxOut directly
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_BLKDATA, txoData[i]);
   if(brr.getSize()==0)
   {
      Log::ERR() << " could not find TxOut in DB";
      return false;
   }

   TxOut txout;
   readBlkDataTxOutValue(brr, txout);

   utxo.txHash_     = tx.thisHash_;
   utxo.txOutIndex_ = outIdx;
   utxo.txHeight_   = hgtxToHeight(hgtX);
   utxo.value_      = txout.getValue();
   utxo.script_     = txout.getScript();

   return txout.storedIsSpent_;
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getUtxoListForAddr( BinaryData & const scriptWithType,
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



bool InterfaceToLevelDB::readFullTx(Tx & tx, leveldb::Iterator* iter=NULL)
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
bool InterfaceToLevelDB::advanceIterAndRead(leveldb::Iterator* iter)
{
   iter->Next();
   if(!iter->Valid())
      return false;

   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
   return true;
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::advanceIterAndRead(DB_SELECT db, DB_PREFIX prefix)
{
   if(iterIsDirty_[db])
      Log::ERR() << "DB has been changed since this iterator was created";

   if(advanceIterAndRead(iters_[db]))
      return checkPrefixByte(currReadKey_, prefix, true);
   else 
      return false;
}



/////////////////////////////////////////////////////////////////////////////
map<HashString, BlockHeader> InterfaceToLevelDB::getHeaderMap(void)
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
      uint32_t hgtX    = brr.get_uint32_t();
      uint32_t txCount = brr.get_uint32_t();
      uint32_t nBytes  = brr.get_uint32_t();

      // The "height" is actually a 3-byte height, and a "duplicate ID"
      // Reorgs lead to multiple headers having the same height.  Since 
      // the blockdata
      header.storedHeight_(hgtxToHeight(hgtX));
      header.duplicateID_(hgtxToDupID(hgtX));

      outMap[headerHash] = header;
   }

   return outMap;
}


////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getRawHeader(BinaryData const & headerHash)
{
   // I used the seek method originally to try to return
   // a slice that didn't need to be copied.  But in the 
   // end, I'm doing a copy anyway.  So I switched to 
   // regular DB.Get and commented out the seek method 
   // so it's still here for reference
   static BinaryData headerOut(HEADER_SIZE);
   headerOut = getValue(HEADERS, DB_PREFIX_HEADHASH, headerHash);
   return headerOut;
}



////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getDBInfoKey(void)
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

StoredTx InterfaceToLevelDB::getFullTxFromKey6B(BinaryDataRef key6B)
{

}

StoredTx InterfaceToLevelDB::getFullTxFromHash(BinaryDataRef txHash)
{

}


////////////////////////////////////////////////////////////////////////////////
/*  I think the BDM will do this, not the DB interface
bool InterfaceToLevelDB::addBlockToDB(BinaryDataRef newBlock,
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
uint8_t InterfaceToLevelDB::getValidDupIDForHeight(uint32_t blockHgt)
{
   if(validDupByHeight_.size() < blockHgt+1)
   {
      Log::ERR() << "Block height exceeds DupID lookup table";
      return UINT8_MAX;
   }

   return validDupByHeight_[blockHgt];
}

////////////////////////////////////////////////////////////////////////////////
uint8_t InterfaceToLevelDB::getValidDupIDForHeight_fromDB(uint32_t blockHgt)
{
   SCOPED_TIMER("getValidDupIDForHeight");

   BinaryData hgt4((uint8_t*)&blockHgt, 4);
   BinaryRefReader brrHgts = getValueReader(HEADERS, DB_PREFIX_HEADHGT, hgt4);

   if(brrHgts.getSize() == 0)
   {
      Log::ERR() << "Requested header does not exist in DB";
      return false
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
////////////////////////////////////////////////////////////////////////////////
// Interface methods between Stored* objects and the DB (how they are serialized
// and unserialized)

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::unserializeStoredBlockHeaderValue( 
                                          DB_SELECT db,
                                          BinaryRefReader & brr,
                                          StoredBlockHeader & sbh,
                                          bool ignoreMerkle)
{

   if(db==HEADERS)
   {
      brr.get_BinaryData(sbh.dataCopy_, HEADER_SIZE);
      uint32_t hgtx = brr.get_uint32_t();
      sbh.blockHeight_ = hgtxToHeight(hgtx);
      sbh.duplicateID_ = hgtxToDupID(hgtx);
   }
   else if(db==BLKDATA)
   {
      // Unserialize the raw header into the SBH object
      brr.get_BinaryData(sbh.dataCopy_, HEADER_SIZE);
   
      // Read the flags byte
      BitReader<uint32_t> bitread(brr);
      uint32_t        dbVersion  =                  bitread.getBits(4);
      uint32_t        blkVersion =                  bitread.getBits(4);
      ARMORY_DB_TYPE  dbtype     = (ARMORY_DB_TYPE) bitread.getBits(4);
      DB_PRUNE_TYPE   pruneType  = (DB_PRUNE_TYPE)  bitread.getBits(2);
      MERKLE_SER_TYPE merkType   = (MERKLE_SER_TYPE)bitread.getBits(2);
   
      sbh.storedNumTx_    = brr.get_uint32_t();
      sbh.storedNumBytes_ = brr.get_uint32_t();
   
      if(dbVersion != (uint8_t)ARMORY_DB_VERSION)
      {
         Log::ERR() << "Version mismatch in IFTLDB::getBlock()";
         advanceToNextBlock();
         return
      }

      if( !ignoreMerkle )
      {
         uint32_t currPos = brr.getPosition();
         uint32_t totalSz = brr.getSize();
         if(merkleCode == MERKLE_SER_NONE)
            sbh.merkle_.resize(0);
         else
         {
            sbh.merkleIsPartial_ = (merkleCode == MERKLE_SER_PARTIAL);
            brr.get_BinaryData(sbh.merkle_, totalSz - currPos);
         }
      }
   }
}


////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  
void InterfaceToLevelDB::serializeStoredBlockHeaderValue(
                                          DB_SELECT db,
                                          StoredBlockHeader const & sbh,
                                          BinaryWriter & bw)
{
   if(!sbh.isInitialized_)
   {
      Log::ERROR() << "Attempted to serialize uninitialized block header";
      return;
   }

   if(db==HEADERS)
   {
      uint32_t hgtx = heightAndDupToHgtx(sbh.blockheight, sbh.duplicateID_);
      bw.put_BinaryData(sbh.dataCopy_);
      bw.put_uint32_t(hgtx);
   }
   else if(db==BLKDATA)
   {
      uint32_t version = *(uint32_t*)sbh.dataCopy_.getPtr();

      MERKLE_SER_TYPE mtype;
      switch(armoryDbType_)
      {
         // If we store all the tx anyway, don't need any/partial merkle trees
         case ARMORY_DB_LITE:    mtype = MERKLE_SER_PARTIAL; break;
         case ARMORY_DB_PARTIAL: mtype = MERKLE_SER_FULL;    break;
         case ARMORY_DB_FULL:    mtype = MERKLE_SER_NONE;    break;
         case ARMORY_DB_SUPER:   mtype = MERKLE_SER_NONE;    break;
         default: 
            Log::ERR() << "Invalid DB mode in serializeStoredBlockHeaderValue";
      }
      
      if(sbh.merkle_.getSize() > 0)
         mtype = (sbh.merkleIsPartial_ ? MERKLE_SER_PARTIAL : MERKLE_SER_FULL);
   
      // Create the flags byte
      BitWriter<uint32_t> bitwrite;
      bitwrite.putBits((uint32_t)ARMORY_DB_VERSION,  4);
      bitwrite.putBits((uint32_t)version,            4);
      bitwrite.putBits((uint32_t)armoryDbType_,      4);
      bitwrite.putBits((uint32_t)dbPruneType_,       2);
      bitwrite.putBits((uint32_t)mtype,              2);
      uint32_t flags = bitwrite.getValue();

      bw.put_uint32_t(flags);
      bw.put_BinaryData(sbh.dataCopy_);
      bw.put_uint32_t(sbh.numTx_);
      bw.put_uint32_t(sbh.numBytes_);

      if( mtype != MERKLE_SER_NONE )
         bw.put_BinaryData(sbh.merkle_);
   }
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::unserializeStoredTxValue( 
                                    BinaryRefReader & brr, 
                                    StoredTx & tx)
{
   // flags
   //    DBVersion      4 bits
   //    TxVersion      2 bits
   //    HowTxSer       4 bits   (FullTxOut, TxNoTxOuts, numTxOutOnly)
   BitReader<uint16_t> bitread(brr); // flags
   uint16_t dbVer   = bitread.getBits(4);
   uint16_t txVer   = bitread.getBits(2);
   uint16_t txSer   = bitread.getBits(4);
   
   brr.get_BinaryData(tx.thisHash_, 32);

   if(txSer == TX_SER_FULL || txSer == TX_SER_FRAGGED)
      tx.unserialize(brr, txSer==TX_SER_FRAGGED);
   else
      tx.numTxOut_ = brr.get_var_int();

}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::serializeStoredTxValue(
                                          StoredTx const & stx,
                                          BinaryWriter & bw)
{
   uint16_t version = *(uint16_t*)stx.dataCopy_.getPtr();
   TX_SERIALIZE_TYPE serType;
   
   switch(armoryDbType_)
   {
      // If we store all the tx anyway, don't need any/partial merkle trees
      case ARMORY_DB_LITE:    serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_PARTIAL: serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_FULL:    serType = TX_SER_FULL;    break;
      case ARMORY_DB_SUPER:   serType = TX_SER_FULL;    break;
      default: 
         Log::ERR() << "Invalid DB mode in serializeStoredTxValue";
   }

   BitWriter<uint16_t> bitwrite;
   bitwrite.putBits((uint16_t)ARMORY_DB_VERSION,  4);
   bitwrite.putBits((uint16_t)version,            2);
   bitwrite.putBits((uint16_t)serType,            2);

   
   bw.put_uint16_t(bitwrite.getValue());
   bw.put_BinaryData(stx.thisHash_);

   if(serType == TX_SER_FULL    || 
      serType == TX_SER_FRAGGED )
      bw.put_BinaryData(stx.dataCopy_);
   else:
      bw.put_var_int(stx.numTxOut_);
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::unserializeStoredTxOutValue(
                                             BinaryRefReader & brr, 
                                             StoredTxOut & stxo)
{
   // Similar to TxValue flags
   //    DBVersion   4 bits
   //    TxVersion   2 bits
   //    Spentness   2 bits
   BitReader<uint16_t> bitread(brr);
   uint16_t dbVer   =  bitread.getBits(4);
   uint16_t txVer   =  bitread.getBits(2);
   uint16_t isSpent =  bitread.getBits(2);
   uint16_t isCBase =  bitread.getBits(1);

   stxo.unserialize(brr);
   stxo.storedIsSpent_  = isSpent;
   stxo.isFromCoinbase_ = isCBase;

   if((TXOUT_SPENTNESS)isSpent == TXOUT_SPENT && brr.getSizeRemaining()>=8)
   {
      stxo.spentByHgtX_      = brr.get_uint32_t(); 
      stxo.spentByTxIndex_   = brr.get_uint16_t(); 
      stxo.spentByTxInIndex_ = brr.get_uint16_t(); 
   }
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::unserializeStoredTxOutValue(
                                             BinaryRefReader & brr, 
                                             Tx & tx, 
                                             uint32_t txOutIndex)
{
   if(tx.storedTxOuts_.find(txOutIndex) == tx.storedTxOuts_.end())
   {
      Log::WARN() << "Tx does not have txOutIndex: " << txOutIndex;
   }
   readBlkDataTxOutValue(brr, tx.storedTxOuts_[txOutIndex]);
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::serializeStoredTxOutValue(
                                          StoredTxOut const & stxo,
                                          BinaryWriter & bw,
                                          bool forceSaveSpentness)
{
   TXOUT_SPENTNESS spentness = (stxo.isSpent_ ? TXOUT_SPENT : TXOUT_UNSPENT);
   
   if(!forceSaveSpentness)
   { 
      switch(dbPruneType_)
      {
         //// If the DB is in lite or partial modes, we don't bother recording
         //   spentness (in fact, if it's spent, this entry probably won't even
         //   be written to the DB).
         case ARMORY_DB_LITE:    spentness = TXOUT_SPENTUNK; break;
         case ARMORY_DB_PARTIAL: spentness = TXOUT_SPENTUNK; break;
         case ARMORY_DB_FULL:                                break;
         case ARMORY_DB_SUPER:                               break;
         default: 
            Log::ERR() << "Invalid DB mode in serializeStoredTxOutValue";
      }
   }

   uint16_t isCbase = (stxo.isFromCoinbase_ ? 1 : 0);

   BitWriter<uint16_t> bitwrite;
   bitwrite.putBits((uint16_t)ARMORY_DB_VERSION,  4);
   bitwrite.putBits((uint16_t)stxo.txVersion_,    4);
   bitwrite.putBits((uint16_t)spentness,          2);
   bitwrite.putBits((uint16_t)isCbase,            1);

   bw.put_uint16_t(bitwrite.getValue());
   bw.put_BinaryData(stxo.dataCopy_);  // 8-byte value, var_int sz, pkscript
   
   if(spentness == TXOUT_SPENT)
   {
      bw.put_uint32_t(spentByHgtX_);
      bw.put_uint16_t(spentByTxIndex_);
      bw.put_uint16_t(spentByTxInIndex_);
   }
}



////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  Will 
// adjust the dupID value  in the input SBH
// Will overwrite existing data, for simplicity, and so that this method allows
// us to easily replace/update data, even if overwriting isn't always necessary
void InterfaceToLevelDB::putStoredBlockHeader(
                          StoredBlockHeader & sbh,
                          bool withTx)
{
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
      bw.put_BinaryData(sbh.thisHash_)
      bw.put_BinaryData(hgtList);
      putValue(HEADERS, DB_PREFIX_HEADHGT, hgt4, bw.getDataRef());
   }
      
   // Overwrite the existing hash-indexed entry, just in case the dupID was
   // not known when previously written.  
   BinaryWriter bwHeaders;
   serializeStoredBlockHeader(HEADERS, sbh, bwHeaders);
   putValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_, bwHeaders.getDataRef());

   commitBatch(HEADERS);


   startBatch(BLKDATA);

   // Now put the data into the blkdata DB
   BinaryData key = getBlkDataKey(sbh.blockHeight_, sbh.duplicateID_);
   BinaryWriter bwBlkData;
   serializeStoredBlockHeader(BLKDATA, sbh, bwBlkData);
   putValue(BLKDATA, DB_PREFIX_BLKDATA, key.getRef(), bwBlkData.getDataRef());
   
   // If we only wanted to update the BlockHeader record, we're done.
   if(!withTx)
   {
      commitBatch(BLKDATA);
      return;
   }

   for(uint32_t i=0; i<numTx_; i++)
   {
      map<uint32_t, StoredTx>::iterator txIter = txMap_.find(i);
      if(txIter != txMap_.end())
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
void InterfaceToLevelDB::getStoredBlockHeader(
                                    StoredBlockHeader & sbh,
                                    uint32_t blockHgt,
                                    uint8_t blockDup,
                                    bool withTx)
{

   if(!withTx)
   {
      //////
      // Don't need to mess with seeking if we don't need the transactions.
      BinaryData blkKey = getBlkDataKey(blockHgt, blockDup);
      BinaryRefReader brr = getValueReader(BLKDATA, blkKey);
      if(brr.getSize()==0)
      {
         Log::ERR() << "Header height&dup is not in BLKDATA";
         return false;
      }
      unserializeStoredBlockHeaderValue(BLKDATA, brr, sbh, false);
      return true;
   }
   else
   {
      //////
      // Do the iterator thing because we're going to traverse the whole block
      bool isInDB = seekTo(BLKDATA, getBlkDataKey(blockHgt, blockDup));
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
bool InterfaceToLevelDB::getStoredBlockHeader(
                          StoredBlockHeader & sbh,
                          BinaryDataRef headHash, 
                          bool withTx)
{

   BinaryData headEntry = getValue(HEADERS, DB_PREFIX_HEADHASH, headHash); 
   if(headEntry.getSize() == 0)
   {
      Log::ERR() << "Requested header that is not in DB";
      return false;
   }
   
   BinaryRefReader brr(headEntry);
   unserializeStoredBlockHeaderValue(HEADERS, brr, sbh);

   return getStoredBlockHeader(sbh, sbh.blockHeight_, sbh.duplicateID_, withTx);
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getStoredBlockHeader(
                              StoredBlockHeader & sbh,
                              uint32_t blockHgt,
                              bool withTx)
{
   uint8_t dupID = getValidDupIDForHeight(blockHgt);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHgt; 

   return getStoredBlockHeader(sbh, blockHgt, dupID, withTx);
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::putStoredTx( StoredTx const & stx, bool withTxOut)
{
   BinaryData ldbKey = getBlkDataKey(stx.blockHeight_, 
                                     stx.blockDupID_, 
                                     stx.txIndex_,
                                     false);

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
   serializeStoredTxValue(stx, bw);
   putValue(BLKDATA, DB_PREFIX_BLKDATA, ldbKey, bw.getDataRef());


   // Add the individual TxOut entries if requested
   if(withTxOut)
   {
      map<uint32_t, StoredTxOut>::iterator iter;
      for(iter  = txOutMap_.begin();
          iter != txOutMap_.end();
          iter++)
      {
         // Make sure all the parameters of the TxOut are set right 
         iter->second.txVersion_   = *(uint32_t*)stx.dataCopy_.getPtr();
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
bool InterfaceToLevelDB::readStoredBlockAtIter(StoredBlockHeader & sbh)
{
   currReadKey_.resetPosition();
   BinaryData blkDataKey(currReadKey_.getCurrPtr(), 5);
   BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                          sbh.blockHeight_,
                                          sbh.duplicateID_);

   
   // Grab the header first, then iterate over 
   unserializeStoredBlockHeaderValue(BLKDATA, currReadValue_, sbh, false);

   // If for some reason we hit the end of the DB without any tx, bail
   bool iterValid = advanceIterAndRead(BLKDATA, DB_PREFIX_BLKDATA);
   if(!iterValid)
      return true;  // this isn't an error, it's an block w/o any StoredTx

   // Now start iterating over the tx data
   uint32_t tempHgt;
   uint8_t  tempDup;
   while(currReadKey_.getRawRef().startsWith(blkDataKey))
   {
      // We can't just read the the tx, because we have to guarantee 
      // there's a place for it in the sbh.txMap_
      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, tempHgt, tempDup);

      currTxIdx = currReadKey_.get_uint16_t(); 
      if(currTxIdx >= sbh.numTx_)
      {
         Log::ERR() << "Invalid txIndex at height " << (sbh.blockHeight_)
                    << " index " << index << endl;
         return false;
      }

      if(sbh.txMap_.find(currTxIdx) == sbh.txMap_.end())
         sbh.txMap_[currTxIdx] = StoredTx();

      readStoredTxAtIter(sbh.blockHeight_, 
                         sbh.duplicateID_, 
                         sbh.txMap_[currTxIdx]);
   } 
} 


////////////////////////////////////////////////////////////////////////////////
// We assume we have a valid iterator left at the beginning of (potentially) a 
// transaction in this block.  It's okay if it starts at at TxOut entry (in 
// some instances we may not have a Tx entry, but only the TxOuts).
bool InterfaceToLevelDB::readStoredTxAtIter(       
                                       uint32_t height,
                                       uint8_t  dupID,
                                       StoredTx & stx)
{
   BinaryData blkPrefix = getBlkDataKey(height, dupID);

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

   BinaryData txPrefix = getBlkDataKey(height, dupID, stx.txIndex_);

   
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
                                             sbh.blockHeight_,
                                             sbh.duplicateID_);


      // Now actually process the iter value
      if(bdtype == BLKDATA_TX)
      {
         // Get everything else from the iter value
         unserializeStoredTxValue(currReadValue_, stx);
      }
      else if(bdtype == BLKDATA_TXOUT)
      {
         currReadKey_.advance(2);
         uint16_t txOutIdx = currReadKey_.get_uint16_t();
         txOutMap_[txOutIdx] = StoredTxOut();
         readStoredTxOutAtIter(height, dupID, stx.txIndex_, txOutMap_[txOutIdx]);
      }
      else
      {
         Log::ERR() << "Unexpected BLKDATA entry while iterating";
         return false;
      }
   } while(advanceIterAndRead(BLKDATA, DB_PREFIX_BLKDATA))

   return true;
} 


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::readStoredTxOutAtIter(       
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

   unserializeStoredTxOutValue(currReadValue_, stxo);

}


////////////////////////////////////////////////////////////////////////////////
// Although this method technically makes a DB access, it's likely to be very
// fast because the DB is so small and probably entirely cached.
//
// This seems redundant w.r.t. to getValidDupIDForHeight
//bool isBlockHeightAndDupValid(uint32_t hgt, uint8_t dup)
//{
   //SCOPED_TIMER("isBlockHeightAndDupValid");

   //static uint32_t const lenEntry = 33;

   //uint32_t hgtX = heightAndDupToHgtx(hgt,dup);
   //BinaryDataRef hgtxRef((uint8_t*)&hgtX, 4);
   //BinaryDataRef dupList = getValueRef(HEADERS, DB_PREFIX_HEADHGT, hgtxRef);
   
   //uint8_t numDup = dupList.getSize() / lenEntry;
   //BinaryRefReader brr(dupList);
   //for(uint32_t dup=0; dup<numDup; dup++)
   //{
      //uint8_t dup8 = brr.get_uint8_t(); 
      //if(dup8 & 0x7f == dup)
         //return ((dup8 & 0x80) > 0);
   
      //brr.advance(32);
   //}
   
   //Log::ERR() << "Height & Dup requested was not found in HEADERS DB";
   //return false;
//}


////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> getAllTxHints(BinaryDataRef txHash)
{
   BinaryDataRef allHints = getValueRef(BLKDATA, 
                                        DB_PREFIX_TXHINTS, 
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
bool InterfaceToLevelDB::getStoredTx(         
                          StoredTx & stx,
                          BinaryDataRef txHash,
                          bool returnValidOnly)
{
   BinaryData hash4(txHash.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);

   if(existingHints.getSize() == 0)
   {
      Log::ERR() << "No tx in DB with hash: " << txHash.toHexStr();
      return false;
   }

   // Now go through all the hints looking for the first one with a matching hash
   uint32_t numHints = existingHints.getSize() / 6;
   uint32_t hgtx, height;
   uint8_t  dup;
   for(uint32_t i=0; i<numHints; i++)
   {
      BinaryDataRef hint = existingHints.getSliceRef(i*6, 6);
      seekTo(BLKDATA, DB_PREFIX_BLKDATA, hint);

      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, height, dup);
      uint16_t txIdx = currReadKey_.get_uint16_t();
      
      // We don't actually know for sure whether the seekTo() found 
      BinaryData key6 = getBlkDataKey(height, dup, txIdx, false);
      if(key6 != hint)
      {
         Log::ERR() << "TxHint referenced a BLKDATA tx that doesn't exist";
         continue;
      }

      currReadValue_.advance(2);  // skip flags
      if(currReadValue_.get_BinaryDataRef(32) == txHash)
      {
         resetIterReaders();
         return readStoredTxAtIter(hgtxToHeight(hgtX), hgtxToDupID(hgtX), stx);
      }
   }

   if(returnValidOnly)
      Log::ERR() << "Could not find valid Tx with hash: " << txHash.toHexStr();
   else
      Log::ERR() << "Could not find any Tx with hash: " << txHash.toHexStr();

   return false;
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getStoredTx(         
                          StoredTx & stx,
                          uint32_t blockHeight,
                          uint32_t txIndex,
                          bool withTxOut)
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTx(stx, blockHeight, dupID, txIndex, withTxOut);

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getStoredTx(         
                          StoredTx & stx,
                          uint32_t blockHeight,
                          uint32_t dupID,
                          uint32_t txIndex,
                          bool withTxOut)
{
   BinaryData blkDataKey = getBlkDataKey(blockHeight, dupID, txIndex);

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

      stx.blockHeight_ = blockHeight;
      stx.blockDupID_  = dupID;
      stx.txIndex_     = txIndex;

      unserializeStoredTxValue(brr, stx);
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

      // Grab the header first, then iterate over 
      unserializeStoredTxValue(BLKDATA, currReadValue_, sbh, false);

      while(advanceIterAndRead(BLKDATA))
      {
         // If the iter key doesn't start with [PREFIX | HGT | DUP], we're done
         if(!currReadKey_.getRawRef().startsWith(blkDataKey))
            break;

         
         BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                                sbh.blockHeight_,
                                                sbh.duplicateID_);
   
         currTxIdx = currReadKey_.get_uint16_t(); 
         if(index > txList().size())
         {
            Log::ERR() << "Invalid index for tx at height " << (hgtX>>8)
                     << " index " << index << endl;
            return;
         }
   
         // If this tx doesn't exist, we need to make it.  I think it's 
         // technically possible to not have a BLKDATA_TX entry, and only 
         // BLKDATA_TXOUT entries, thus we need to create the StoredTx 
         // even if this is a BLKDATA_TXOUT.
         if(sbh.txMap_.find(currTxIdx) == sbh.txMap_.end())
         {
            sbh.txMap_[currTxIdx] = StoredTx();
            StoredTx & stx = sbh.txMap_[currTxIdx];

            // Set the StoredTx parameters that it needs from the iter key
            stx.blockHeight_ = sbh.blockHeight_;
            stx.blockDupID_  = sbh.duplicateID_;
            stx.txIndex_     = currTxIdx;
         }

         if(bdtype == BLKDATA_TX)
         {
            // Get everything else from the iter value
            unserializeStoredTxValue(currReadValue_, stx);
         }
         else if(bdtype == BLKDATA_TXOUT)
         {
            currTxOutIdx = currReadKey_.get_uint16_t(); 

            sbh.txMap_[currTxIdx].txOutMap_[currTxOutIdx] = StoredTxOut();
            StoredTxOut & stxo = sbh.txMap_[currTxIdx].txOutMap_[currTxOutIdx];

            unserializeStoredTxOutValue(currReadValue_, stxo, currTxOutIdx);
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
void InterfaceToLevelDB::putStoredTxOut( StoredTxOut const & stxo)
{
    
   BinaryData ldbKey = getBlkDataKey(stxo.blockHeight_, 
                                     stxo.blockDupID_, 
                                     stxo.txIndex_,
                                     stxo.txOutIndex_,
                                     false);

   BinaryWriter bw;
   serializeStoredTxOutValue(stxo, bw);
   putValue(BLKDATA, DB_PREFIX_BLKDATA, ldbKey, bw.getDataRef());
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint32_t dupID,
                              uint32_t txIndex,
                              uint32_t txOutIndex)
{
   BinaryData blkKey = getBlkDataKey( blockHeight, dupID, txIndex, txOutIndex);
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

   unserializeStoredTxOutValue(brr, stxo);

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint32_t txIndex,
                              uint32_t txOutIndex)
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      Log::ERR() << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTxOut(stxo, blockHeight, dupID, txIndex, txOutIndex);
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::markBlockHeaderValid(BinaryDataRef headHash)
{
   BinaryRefReader brr = getValueReader(HEADERS, DB_PREFIX_HEADHASH, headHash);
   if(brr.getSize()==0)
   {
      Log::ERR() << "Invalid header hash: " << headHash.toHexStr();
      return false;
   }
   brr.advance(HEADER_SIZE);
   uint32_t hgtX = *(uint32_t*)brr.getCurrPtr();
   uint32_t height = hgtxToHeight(hgtX);
   uint8_t  dup    = hgtxToDupID(hgtX);

   return markBlockHeaderValid(height, dup);
}



////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLevelDB::getTxRef( BinaryDataRef txHash )
{
   if(seekToTxByHash(txHash))
   {
      currReadKey_.advance(1);
      return TxRef(currReadKey_.get_BinaryDataRef(6), this);
   }
   
   return TxRef();
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLevelDB::getTxRef( uint32_t hgtx, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_uint32_t(hgtx);
   bw.put_uint16_t(txIndex);
   return TxRef(bw.getDataRef(), this);
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLevelDB::getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_uint32_t(heightAndDupToHgtx(hgt,dup));
   bw.put_uint16_t(txIndex);
   return TxRef(bw.getDataRef(), this);
}



////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::markBlockHeaderValid(uint32_t height, uint8_t dup)
{
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
         bwOut.put_uint8_t(brr.get_uint8_t() | 0x80)
      else                 
         bwOut.put_uint8_t(brr.get_uint8_t() & 0x7f)
      
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
bool InterfaceToLevelDB::markTxEntryValid(uint32_t height,
                                          uint8_t  dupID,
                                          uint16_t txIndex)
{
   BinaryData blkDataKey = getBlkDataKey(height, dupID, txIndex, false);
   BinaryRefReader brrTx = getValueReader(BLKDATA, DB_PREFIX_BLKDATA, blkDataKey);

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

      if(thisHint != blkDataKey);
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


/*
////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getUndoDataForTx( Tx const & tx,
                                           list<TxOut> &    txOutsRemoved,
                                           list<OutPoint> & outpointsAdded)
{
   // For ARMORY_DB_FULL we don't need undo data yet.
}

////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getUndoDataForBlock( list<TxOut> &    txOutsRemoved,
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
bool InterfaceToLevelDB::purgeOldUndoData(uint32_t earlierThanHeight)
{
   // For ARMORY_DB_FULL we don't need undo data yet.
}
*/

   
////////////////////////////////////////////////////////////////////////////////
//  Not sure that this is possible...
/*
bool InterfaceToLevelDB::updateHeaderHeight(BinaryDataRef headHash, 
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
   bw.put_uint32_t(heightAndDupToHgtx(height, dup));

   putValue(HEADERS, headHash, bw.getDataRef());
   return true;
}  
*/

