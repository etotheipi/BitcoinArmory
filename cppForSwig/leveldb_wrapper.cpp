////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
//
#include <iostream>
#include <sstream>
#include <map>
#include <list>
#include <vector>
#include <set>
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "leveldb_wrapper.h"

vector<InterfaceToLDB*> LevelDBWrapper::ifaceVect_(0);



////////////////////////////////////////////////////////////////////////////////
LDBIter::LDBIter(leveldb::DB* dbptr, bool fill_cache) 
{ 
   db_ = dbptr; 
   leveldb::ReadOptions readopts;
   readopts.fill_cache = fill_cache;
   iter_ = db_->NewIterator(readopts);
   isDirty_ = true;
}



////////////////////////////////////////////////////////////////////////////////
bool LDBIter::isValid(DB_PREFIX dbpref)
{
   if(!isValid() || iter_->key().size() == 0)
      return false;
   return iter_->key()[0] == (char)dbpref;
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advance(void)
{
   iter_->Next();
   isDirty_ = true;
   return isValid();
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advance(DB_PREFIX prefix)
{
   iter_->Next();
   isDirty_ = true;
   return isValid(prefix);
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::readIterData(void)
{
   if(!isValid())
   {
      isDirty_ = true;
      return false;
   }

   currKey_.setNewData((uint8_t*)iter_->key().data(), iter_->key().size());
   currValue_.setNewData((uint8_t*)iter_->value().data(), iter_->value().size());
   isDirty_ = false;
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advanceAndRead(void)
{
   if(!advance())
      return false; 
   return readIterData(); 
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advanceAndRead(DB_PREFIX prefix)
{
   if(!advance(prefix))
      return false; 
   return readIterData(); 
}


////////////////////////////////////////////////////////////////////////////////
BinaryData LDBIter::getKey(void) 
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty key ref";
      return BinaryData(0);
   }
   return currKey_.getRawRef().copy();
}
   
////////////////////////////////////////////////////////////////////////////////
BinaryData LDBIter::getValue(void) 
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty value ref";
      return BinaryData(0);
   }
   return currValue_.getRawRef().copy();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef LDBIter::getKeyRef(void) 
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty key ref";
      return BinaryDataRef();
   }
   return currKey_.getRawRef();
}
   
////////////////////////////////////////////////////////////////////////////////
BinaryDataRef LDBIter::getValueRef(void) 
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty value ref";
      return BinaryDataRef();
   }
   return currValue_.getRawRef();
}


////////////////////////////////////////////////////////////////////////////////
BinaryRefReader& LDBIter::getKeyReader(void) 
{ 
   if(isDirty_)
      LOGERR << "Returning dirty key reader";
   return currKey_; 
}

////////////////////////////////////////////////////////////////////////////////
BinaryRefReader& LDBIter::getValueReader(void) 
{ 
   if(isDirty_)
      LOGERR << "Returning dirty value reader";
   return currValue_; 
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekTo(BinaryDataRef key)
{
   if(isNull())
      return false;
   iter_->Seek(binaryDataRefToSlice(key));
   return readIterData();
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekTo(DB_PREFIX pref, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)pref);
   bw.put_BinaryData(key);
   bool didSucceed = seekTo(bw.getDataRef());
   if(didSucceed)
      readIterData();
   return didSucceed;
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToExact(BinaryDataRef key)
{
   if(!seekTo(key))
      return false;

   return checkKeyExact(key);
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToExact(DB_PREFIX pref, BinaryDataRef key)
{
   if(!seekTo(pref, key))
      return false;

   return checkKeyExact(pref, key);
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToStartsWith(BinaryDataRef key)
{
   if(!seekTo(key))
      return false;

   return checkKeyStartsWith(key);

}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToStartsWith(DB_PREFIX prefix)
{
   BinaryWriter bw(1);
   bw.put_uint8_t((uint8_t)prefix);
   if(!seekTo(bw.getDataRef()))
      return false;

   return checkKeyStartsWith(bw.getDataRef());

}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToStartsWith(DB_PREFIX pref, BinaryDataRef key)
{
   if(!seekTo(pref, key))
      return false;

   return checkKeyStartsWith(pref, key);
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToFirst(void)
{
   if(isNull())
      return false;
   iter_->SeekToFirst();
   readIterData();
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyExact(BinaryDataRef key)
{
   if(isDirty_ && !readIterData())
      return false;

   return (key==currKey_.getRawRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyExact(DB_PREFIX prefix, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   if(isDirty_ && !readIterData())
      return false;

   return (bw.getDataRef()==currKey_.getRawRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyStartsWith(BinaryDataRef key)
{
   if(isDirty_ && !readIterData())
      return false;

   return (currKey_.getRawRef().startsWith(key));
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::verifyPrefix(DB_PREFIX prefix, bool advanceReader)
{
   if(isDirty_ && !readIterData())
      return false;

   if(currKey_.getSizeRemaining() < 1)
      return false;

   if(advanceReader)
      return (currKey_.get_uint8_t() == (uint8_t)prefix);
   else
      return (currKey_.getRawRef()[0] == (uint8_t)prefix);
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyStartsWith(DB_PREFIX prefix, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   return checkKeyStartsWith(bw.getDataRef());
}




////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::checkStatus(leveldb::Status stat, bool warn)
{
   lastStatus_ = stat;
   if( lastStatus_.ok() )
      return true;
   
   if(warn)
      LOGWARN << "***LevelDB Error: " << lastStatus_.ToString();

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
      batches_[i] = NULL;
      dbs_[i] = NULL;
      dbPaths_[i] = string("");
      batchStarts_[i] = 0;
      //dbFilterPolicy_[i] = NULL;
   }

   maxOpenFiles_ = 0;
   ldbBlockSize_ = DEFAULT_LDB_BLOCK_SIZE; 
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
         LOGERR << "Unwritten batch in progress during shutdown";

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
   LOGINFO << "Opening databases...";

   baseDir_ = basedir;

   stringstream head;
   head << baseDir_ << "/" << "leveldb_headers";
   dbPaths_[0] = head.str();

   stringstream blk;
   blk << baseDir_ << "/" << "leveldb_blkdata";
   dbPaths_[1] = blk.str();
   
   magicBytes_ = magic;
   genesisTxHash_ = genesisTxHash;
   genesisBlkHash_ = genesisBlkHash;

   DBUtils.setArmoryDbType(dbtype);
   DBUtils.setDbPruneType(pruneType);


   if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      LOGERR << " must set magic bytes and genesis block";
      LOGERR << "           before opening databases.";
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
      opts.block_size = ldbBlockSize_;
      opts.compression = leveldb::kNoCompression;

      if(maxOpenFiles_ != 0)
      {
         opts.max_open_files = maxOpenFiles_;
         LOGINFO << "Using max_open_files = " << maxOpenFiles_;
      }

      //LOGINFO << "Using LDB block_size = " << ldbBlockSize_ << " bytes";

      //opts.block_cache = leveldb::NewLRUCache(100 * 1048576);
      //dbFilterPolicy_[db] = leveldb::NewBloomFilterPolicy(10);
      //opts.filter_policy = leveldb::NewBloomFilterPolicy(10);
      leveldb::Status stat = leveldb::DB::Open(opts, dbPaths_[db],  &dbs_[db]);
      if(!checkStatus(stat))
         LOGERR << "Failed to open database! DB: " << db;

      //LOGINFO << "LevelDB directories:";
      //LOGINFO << "LDB BLKDATA: " << dbPaths_[BLKDATA].c_str();
      //LOGINFO << "LDB HEADERS: " << dbPaths_[HEADERS].c_str();

      // Create an iterator that we'll use for ust about all DB seek ops
      batches_[db] = NULL;
      batchStarts_[db] = 0;

      StoredDBInfo sdbi;
      getStoredDBInfo(CURRDB, sdbi, false); 
      if(!sdbi.isInitialized())
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         StoredDBInfo sdbi;
         sdbi.magic_      = magicBytes_;
         sdbi.topBlkHgt_  = 0;
         sdbi.topBlkHash_ = genesisBlkHash_;
         putStoredDBInfo(CURRDB, sdbi);
      }
      else
      {
         // Check that the magic bytes are correct
         if(magicBytes_ != sdbi.magic_)
         {
            LOGERR << " Magic bytes mismatch!  Different blkchain?";
            closeDatabases();
            return false;
         }
   
         if(DBUtils.getArmoryDbType() == ARMORY_DB_WHATEVER)
         {
            DBUtils.setArmoryDbType(sdbi.armoryType_);
         }
         else if(DBUtils.getArmoryDbType() != sdbi.armoryType_)
         {
            LOGERR << "Mismatch in DB type";
            LOGERR << "DB is in  mode: " << (uint32_t)DBUtils.getArmoryDbType();
            LOGERR << "Expecting mode: " << sdbi.armoryType_;
            closeDatabases();
            return false;
         }

         if(DBUtils.getDbPruneType() == DB_PRUNE_WHATEVER)
         {
            DBUtils.setDbPruneType(sdbi.pruneType_);
         }
         else if(DBUtils.getDbPruneType() != sdbi.pruneType_)
         {
            LOGERR << "Mismatch in pruning mode";
            closeDatabases();
            return false;
         }
      }
   }

   // Reserve space in the vector to delay reallocation for 32 weeks
   validDupByHeight_.clear();
   validDupByHeight_.reserve(getTopBlockHeight(HEADERS) + 32768);
   validDupByHeight_.resize(getTopBlockHeight(HEADERS)+1);
   dbIsOpen_ = true;

   return true;
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::nukeHeadersDB(void)
{
   SCOPED_TIMER("nukeHeadersDB");
   LOGINFO << "Destroying headers DB, to be rebuilt.";
   LDBIter ldbIter = getIterator(HEADERS);
   ldbIter.seekToFirst();
   startBatch(HEADERS);

   while(ldbIter.isValid())
   {
      batches_[HEADERS]->Delete(binaryDataRefToSlice(ldbIter.getKeyRef()));
      ldbIter.advanceAndRead();
   }

   commitBatch(HEADERS);

   
   StoredDBInfo sdbi;
   sdbi.magic_      = magicBytes_;
   sdbi.topBlkHgt_  = 0;
   sdbi.topBlkHash_ = genesisBlkHash_;
   putStoredDBInfo(HEADERS, sdbi);

   validDupByHeight_.clear();
   validDupByHeight_.resize(0);
   validDupByHeight_.reserve(300000);
}


/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void InterfaceToLDB::closeDatabases(void)
{
   SCOPED_TIMER("closeDatabases");
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      if( batches_[db] != NULL )
      {
         delete batches_[db];
         batches_[db] = NULL;
      }

      if( dbs_[db] != NULL)
      {
         delete dbs_[db];
         dbs_[db] = NULL;
      }

   }
   dbIsOpen_ = false;

}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::destroyAndResetDatabases(void)
{
   SCOPED_TIMER("destroyAndResetDatabase");

   // We want to make sure the database is restarted with the same parameters
   // it was called with originally
   ARMORY_DB_TYPE atype = DBUtils.getArmoryDbType();
   DB_PRUNE_TYPE  dtype = DBUtils.getDbPruneType();

   closeDatabases();
   leveldb::Options options;
   leveldb::DestroyDB(dbPaths_[HEADERS], options);
   leveldb::DestroyDB(dbPaths_[BLKDATA], options);
   
   // Reopen the databases with the exact same parameters as before
   // The close & destroy operations shouldn't have changed any of that.
   openDatabases(baseDir_, genesisBlkHash_, genesisTxHash_, magicBytes_,
                                                               atype, dtype);
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::startBatch(DB_SELECT db)
{
   SCOPED_TIMER("startBatch");
   if(batchStarts_[db] == 0)
   {
      if(batches_[db] != NULL)
      {
         LOGERR << "Trying to startBatch but we already have one";
         delete batches_[db];
      }

      batches_[db] = new leveldb::WriteBatch;
   }

   // Increment the number of times we've called this function
   batchStarts_[db] += 1;
}



////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTopBlockHash(DB_SELECT db)
{
   StoredDBInfo sdbi;
   getStoredDBInfo(db, sdbi);
   return sdbi.topBlkHash_;
}


////////////////////////////////////////////////////////////////////////////////
uint32_t InterfaceToLDB::getTopBlockHeight(DB_SELECT db)
{
   StoredDBInfo sdbi;
   getStoredDBInfo(db, sdbi);
   return sdbi.topBlkHgt_;
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
         LOGERR << "Trying to commitBatch but we don't have one";
         return;
      }

      if(dbs_[db] != NULL)
         dbs_[db]->Write(leveldb::WriteOptions(), batches_[db]);
      else
         LOGWARN << "Attempted to commitBatch but dbs_ is NULL.  Skipping";

      // Even if the dbs_[db] is NULL, we still want to clear the batched data
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
BinaryDataRef InterfaceToLDB::getValueRef(DB_SELECT db, BinaryDataRef key)
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
// Header Key:  returns header hash
// Tx Key:      returns tx hash
// TxOut Key:   returns serialized OutPoint
BinaryData InterfaceToLDB::getHashForDBKey(BinaryData dbkey)
{
   uint32_t hgt;
   uint8_t  dup;
   uint16_t txi; 
   uint16_t txo; 

   uint32_t sz = dbkey.getSize();
   if(sz < 4 || sz > 9)
   {
      LOGERR << "Invalid DBKey size: " << sz << ", " << dbkey.toHexStr();
      return BinaryData(0);
   }
   
   BinaryRefReader brr(dbkey);
   if(dbkey.getSize() % 2 == 0)
      DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi, txo);
   else
      DBUtils.readBlkDataKey(brr, hgt, dup, txi, txo);

   return getHashForDBKey(hgt, dup, txi, txo);
}


/////////////////////////////////////////////////////////////////////////////
// Header Key:  returns header hash
// Tx Key:      returns tx hash
// TxOut Key:   returns serialized OutPoint
BinaryData InterfaceToLDB::getHashForDBKey(uint32_t hgt,
                                           uint8_t  dup,
                                           uint16_t txi,
                                           uint16_t txo)
{

   if(txi==UINT16_MAX)
   {
      StoredHeader sbh; 
      getBareHeader(sbh, hgt, dup);
      return sbh.thisHash_;
   }
   else if(txo==UINT16_MAX)
   {
      StoredTx stx;
      getStoredTx(stx, hgt, dup, txi, false);
      return stx.thisHash_;
   }
   else 
   {
      StoredTx stx;
      getStoredTx(stx, hgt, dup, txi, false);
      OutPoint op(stx.thisHash_, txo);
      return op.serialize();
   }
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
void InterfaceToLDB::putValue(DB_SELECT db, 
                              BinaryData const & key, 
                              BinaryData const & value)
{
   putValue(db, key.getRef(), value.getRef());
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
// Delete value based on BinaryData key.  If batch writing, pass in the batch
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
// Delete Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLDB::deleteValue(DB_SELECT db, 
                                 DB_PREFIX prefix,
                                 BinaryDataRef key)
{
   BinaryWriter bw;
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   deleteValue(db, bw.getDataRef());
}

/////////////////////////////////////////////////////////////////////////////
// Not sure why this is useful over getHeaderMap() ... this iterates over
// the headers in hash-ID-order, instead of height-order
//void InterfaceToLDB::startHeaderIteration()
//{
   //SCOPED_TIMER("startHeaderIteration");
   //seekTo(HEADERS, DB_PREFIX_HEADHASH, BinaryData(0));
//}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::startBlkDataIteration(LDBIter & ldbIter, DB_PREFIX prefix)
{
   return ldbIter.seekToStartsWith(prefix);
}



/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLDB::advanceToNextBlock(LDBIter & ldbIter, bool skip)
{
   char prefix = DB_PREFIX_TXDATA;
   BinaryData key;
   while(1) 
   {
      if(skip) 
         ldbIter.advanceAndRead();

      //if( !it->Valid() || it->key()[0] != (char)DB_PREFIX_TXDATA)
      if(!ldbIter.isValid(DB_PREFIX_TXDATA))
         return false;
      else if(ldbIter.getKeyRef().getSize() == 5)
         return true;

      if(!skip) 
         ldbIter.advanceAndRead();
         
   } 
   LOGERR << "we should never get here...";
   return false;
}


////////////////////////////////////////////////////////////////////////////////
// We frequently have a Tx hash and need to determine the Hgt/Dup/Index of it.
// And frequently when we do, we plan to read the tx right afterwards, so we
// should leave the itereator there.
bool InterfaceToLDB::seekToTxByHash(LDBIter & ldbIter, BinaryDataRef txHash)
{
   SCOPED_TIMER("seekToTxByHash");
   StoredTxHints sths = getHintsForTxHash(txHash);

   for(uint32_t i=0; i<sths.getNumHints(); i++)
   {
      BinaryDataRef hint = sths.getHint(i);
      ldbIter.seekTo(DB_PREFIX_TXDATA, hint);
      
      // We don't actually know for sure whether the seekTo() found a Tx or TxOut
      if(hint != ldbIter.getKeyRef().getSliceRef(1,6))
      {
         //LOGERR << "TxHint referenced a BLKDATA tx that doesn't exist";
         continue;
      }

      ldbIter.getValueReader().advance(2);  // skip flags
      if(ldbIter.getValueReader().get_BinaryDataRef(32) == txHash)
      {
         ldbIter.resetReaders();
         return true;
      }
   }

   //LOGERR << "No tx in DB with hash: " << txHash.toHexStr();
   ldbIter.resetReaders();
   return false;
}






/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::readStoredScriptHistoryAtIter(LDBIter & ldbIter,
                                                   StoredScriptHistory & ssh)
{
   SCOPED_TIMER("readStoredScriptHistoryAtIter");

   ldbIter.resetReaders();
   ldbIter.verifyPrefix(DB_PREFIX_SCRIPT, false);

   BinaryDataRef sshKey = ldbIter.getKeyRef();
   ssh.unserializeDBKey(sshKey, true);
   ssh.unserializeDBValue(ldbIter.getValueReader());

   if(!ssh.useMultipleEntries_)
      return true;

   if(ssh.totalTxioCount_ == 0)
      LOGWARN << "How did we end up with zero Txios in an SSH?";
      
   // If for some reason we hit the end of the DB without any tx, bail
   if( !ldbIter.advanceAndRead(DB_PREFIX_SCRIPT))
   {
      LOGERR << "No sub-SSH entries after the SSH";
      return false;  
   }

   // Now start iterating over the sub histories
   map<BinaryData, StoredSubHistory>::iterator iter;
   uint32_t numTxioRead = 0;
   do
   {
      uint32_t sz = ldbIter.getKeyRef().getSize();
      BinaryDataRef keyNoPrefix= ldbIter.getKeyRef().getSliceRef(1,sz-1);
      if(!keyNoPrefix.startsWith(ssh.uniqueKey_))
         break;

      pair<BinaryData, StoredSubHistory> keyValPair;
      keyValPair.first = keyNoPrefix.getSliceCopy(sz-5, 4);
      keyValPair.second.unserializeDBKey(ldbIter.getKeyRef());
      keyValPair.second.unserializeDBValue(ldbIter.getValueReader());
      iter = ssh.subHistMap_.insert(keyValPair).first;
      numTxioRead += iter->second.txioSet_.size(); 
   } while( ldbIter.advanceAndRead(DB_PREFIX_SCRIPT) );

   if(numTxioRead != ssh.totalTxioCount_)
   {
      LOGERR << "Number of TXIOs read does not match SSH entry value";
      ssh.totalTxioCount_ = numTxioRead;
   }
   return true;
} 

      

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::putStoredScriptHistory( StoredScriptHistory & ssh)
{
   SCOPED_TIMER("putStoredScriptHistory");
   if(!ssh.isInitialized())
   {
      LOGERR << "Trying to put uninitialized SSH into DB";
      return;
   }

   putValue(BLKDATA, ssh.getDBKey(), ssh.serializeDBValue());

   if(!ssh.useMultipleEntries_)
      return;

   map<BinaryData, StoredSubHistory>::iterator iter;
   for(iter  = ssh.subHistMap_.begin(); 
       iter != ssh.subHistMap_.end(); 
       iter++)
   {
      StoredSubHistory & subssh = iter->second;
      if(subssh.txioSet_.size() > 0)
         putValue(BLKDATA, subssh.getDBKey(), subssh.serializeDBValue());
   }
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::getStoredScriptHistorySummary( StoredScriptHistory & ssh,
                                                    BinaryDataRef scrAddrStr)
{
   LDBIter ldbIter = getIterator(BLKDATA);
   bool seekTrue = ldbIter.seekTo(DB_PREFIX_SCRIPT, scrAddrStr);

   if(!ldbIter.seekToExact(DB_PREFIX_SCRIPT, scrAddrStr))
   {
      ssh.uniqueKey_.resize(0);
      return;
   }

   ssh.unserializeDBKey(ldbIter.getKeyRef());
   ssh.unserializeDBValue(ldbIter.getValueRef());
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::getStoredScriptHistory( StoredScriptHistory & ssh,
                                             BinaryDataRef scrAddrStr)
{
   SCOPED_TIMER("getStoredScriptHistory");
   LDBIter ldbIter = getIterator(BLKDATA);
   if(!ldbIter.seekToExact(DB_PREFIX_SCRIPT, scrAddrStr))
   {
      ssh.uniqueKey_.resize(0);
      return;
   }

   readStoredScriptHistoryAtIter(ldbIter, ssh);
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::getStoredScriptHistoryByRawScript(
                                             StoredScriptHistory & ssh,
                                             BinaryDataRef script)
{
   BinaryData uniqueKey = BtcUtils::getTxOutScrAddr(script);
   getStoredScriptHistory(ssh, uniqueKey);
}


/////////////////////////////////////////////////////////////////////////////
// This doesn't actually return a SUBhistory, it grabs it and adds it to the
// regular-SSH object.  This does not affect balance or Txio count.  It's 
// simply filling in data that the SSH may be expected to have.  
bool InterfaceToLDB::fetchStoredSubHistory( StoredScriptHistory & ssh,
                                            BinaryData hgtX,
                                            bool createIfDNE,
                                            bool forceReadDB)
{
   if(!forceReadDB && KEY_IN_MAP(hgtX, ssh.subHistMap_))
      return true;
      
   BinaryData key = ssh.uniqueKey_ + hgtX; 
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_SCRIPT, key);

   StoredSubHistory subssh;
   subssh.uniqueKey_ = ssh.uniqueKey_;
   subssh.hgtX_      = hgtX;

   if(brr.getSize() > 0)
      subssh.unserializeDBValue(brr);
   else if(!createIfDNE)
      return false;

   return ssh.mergeSubHistory(subssh);
}


////////////////////////////////////////////////////////////////////////////////
uint64_t InterfaceToLDB::getBalanceForScrAddr(BinaryDataRef scrAddr, bool withMulti)
{
   StoredScriptHistory ssh;
   if(!withMulti)
   {
      getStoredScriptHistorySummary(ssh, scrAddr); 
      return ssh.totalUnspent_;
   }
   else
   {
      getStoredScriptHistory(ssh, scrAddr);
      uint64_t total = ssh.totalUnspent_;
      map<BinaryData, UnspentTxOut> utxoList;
      map<BinaryData, UnspentTxOut>::iterator iter;
      getFullUTXOMapForSSH(ssh, utxoList, true);
      for(iter = utxoList.begin(); iter != utxoList.end(); iter++)
         if(iter->second.isMultisigRef())
            total += iter->second.getValue();
      return total;
   }
}


////////////////////////////////////////////////////////////////////////////////
// We need the block hashes and scripts, which need to be retrieved from the
// DB, which is why this method can't be part of StoredBlockObj.h/.cpp
bool InterfaceToLDB::getFullUTXOMapForSSH( 
                                StoredScriptHistory & ssh,
                                map<BinaryData, UnspentTxOut> & mapToFill,
                                bool withMultisig)
{
   if(!ssh.haveFullHistoryLoaded())
      return false;

   map<BinaryData, StoredSubHistory>::iterator iterSubSSH;
   map<BinaryData, TxIOPair>::iterator iterTxio;
   for(iterSubSSH  = ssh.subHistMap_.begin(); 
       iterSubSSH != ssh.subHistMap_.end(); 
       iterSubSSH++)
   {
      StoredSubHistory & subSSH = iterSubSSH->second;
      for(iterTxio  = subSSH.txioSet_.begin(); 
          iterTxio != subSSH.txioSet_.end(); 
          iterTxio++)
      {
         TxIOPair & txio = iterTxio->second;
         StoredTx stx;
         BinaryData txoKey = txio.getDBKeyOfOutput();
         BinaryData txKey  = txio.getTxRefOfOutput().getDBKey();
         uint16_t txoIdx = txio.getIndexOfOutput();
         getStoredTx(stx, txKey);

         StoredTxOut & stxo = stx.stxoMap_[txoIdx];
         if(stxo.isSpent())
            continue;
         
         mapToFill[txoKey] = UnspentTxOut(
                                   stx.thisHash_,
                                   txoIdx,
                                   stx.blockHeight_,
                                   txio.getValue(),
                                   stx.stxoMap_[txoIdx].getScriptRef());
      }
   }

   return true;
}




////////////////////////////////////////////////////////////////////////////////
// We must guarantee that we don't overwrite data if 
void InterfaceToLDB::addRegisteredScript(BinaryDataRef rawScript, 
                                         uint32_t      blockCreated)
{
   BinaryData uniqKey = BtcUtils::getTxOutScrAddr(rawScript);
   bool       isMulti = BtcUtils::isMultisigScript(rawScript);

   StoredScriptHistory ssh;
   getStoredScriptHistory(ssh, uniqKey);
   
   uint32_t scannedTo;
   if(!ssh.isInitialized())
   {
      // Script is not registered in the DB yet
      ssh.uniqueKey_  = uniqKey;
      ssh.version_    = ARMORY_DB_VERSION;
      ssh.alreadyScannedUpToBlk_ = blockCreated;
      //ssh.multisigDBKeys_.resize(0);
      putStoredScriptHistory(ssh);
   }
   else
   {
      if(blockCreated!=UINT32_MAX)
         scannedTo = max(ssh.alreadyScannedUpToBlk_, blockCreated);
      
      // Only overwrite if the data in the DB is incorrect
      if(scannedTo != ssh.alreadyScannedUpToBlk_)
      {
         ssh.alreadyScannedUpToBlk_ = scannedTo;
         putStoredScriptHistory(ssh);
      }
   }

   registeredSSHs_[uniqKey] = ssh;
}

/////////////////////////////////////////////////////////////////////////////
// TODO: We should also read the HeaderHgtList entries to get the blockchain
//       sorting that is saved in the DB.  But right now, I'm not sure what
//       that would get us since we are reading all the headers and doing
//       a fresh organize/sort anyway.
void InterfaceToLDB::readAllHeaders(map<HashString, BlockHeader> & headerMap,
                                    map<HashString, StoredHeader> & storedMap)
{
   LDBIter ldbIter = getIterator(HEADERS);
   if(!ldbIter.seekToStartsWith(DB_PREFIX_HEADHASH))
   {
      LOGWARN << "No headers in DB yet!";
      return;
   }
   

   StoredHeader sbh;
   BlockHeader  regHead;
   do
   {
      ldbIter.resetReaders();
      ldbIter.verifyPrefix(DB_PREFIX_HEADHASH);
   
      if(ldbIter.getKeyReader().getSizeRemaining() != 32)
      {
         LOGERR << "How did we get header hash not 32 bytes?";
         continue;
      }

      ldbIter.getKeyReader().get_BinaryData(sbh.thisHash_, 32);

      sbh.unserializeDBValue(HEADERS, ldbIter.getValueRef());
      regHead.unserialize(sbh.dataCopy_);

      headerMap[sbh.thisHash_] = regHead;
      storedMap[sbh.thisHash_] = sbh;

   } while(ldbIter.advanceAndRead(DB_PREFIX_HEADHASH));
}



////////////////////////////////////////////////////////////////////////////////
uint8_t InterfaceToLDB::getValidDupIDForHeight(uint32_t blockHgt)
{
   if(validDupByHeight_.size() < blockHgt+1)
   {
      LOGERR << "Block height exceeds DupID lookup table";
      return UINT8_MAX;
   }
   return validDupByHeight_[blockHgt];
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::setValidDupIDForHeight(uint32_t blockHgt, uint8_t dup)
{
   while(validDupByHeight_.size() < blockHgt+1)
      validDupByHeight_.push_back(UINT8_MAX);
   validDupByHeight_[blockHgt] = dup;
}

////////////////////////////////////////////////////////////////////////////////
uint8_t InterfaceToLDB::getValidDupIDForHeight_fromDB(uint32_t blockHgt)
{

   BinaryData hgt4((uint8_t*)&blockHgt, 4);
   BinaryRefReader brrHgts = getValueReader(HEADERS, DB_PREFIX_HEADHGT, hgt4);

   if(brrHgts.getSize() == 0)
   {
      LOGERR << "Requested header does not exist in DB";
      return false;
   }

   uint8_t lenEntry = 33;
   uint8_t numDup = brrHgts.getSize() / lenEntry;
   for(uint8_t i=0; i<numDup; i++)
   {
      uint8_t dup8 = brrHgts.get_uint8_t(); 
      BinaryDataRef thisHash = brrHgts.get_BinaryDataRef(lenEntry-1);
      if((dup8 & 0x80) > 0)
         return (dup8 & 0x7f);
   }

   LOGERR << "Requested a header-by-height but none were marked as main";
   return UINT8_MAX;
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::putStoredDBInfo(DB_SELECT db, StoredDBInfo const & sdbi)
{
   SCOPED_TIMER("putStoredDBInfo");
   if(!sdbi.isInitialized())
   {
      LOGERR << "Tried to put DB info into DB but it's not initialized";
      return;
   }
   putValue(db, sdbi.getDBKey(), sdbi.serializeDBValue());
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredDBInfo(DB_SELECT db, StoredDBInfo & sdbi, bool warn)
{
   SCOPED_TIMER("getStoredDBInfo");
   BinaryRefReader brr = getValueRef(db, StoredDBInfo::getDBKey());
    
   if(brr.getSize() == 0 && warn) 
   {
      LOGERR << "No DB info key in database to get";
      return false;
   }
   sdbi.unserializeDBValue(brr);
   return true;
}


////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  Will 
// adjust the dupID value in the SBH after we determine it.
// Will overwrite existing data, for simplicity, and so that this method allows
// us to easily replace/update data, even if overwriting isn't always necessary
//
// NOTE:  If you want this header to be marked valid/invalid, make sure the 
//        isMainBranch_ property of the SBH is set appropriate before calling.
uint8_t InterfaceToLDB::putStoredHeader( StoredHeader & sbh, bool withBlkData)
{
   SCOPED_TIMER("putStoredHeader");

   // Put header into HEADERS DB
   uint8_t newDup = putBareHeader(sbh);

   ///////
   // If we only wanted to update the headers DB, we're done.
   if(!withBlkData)
      return newDup;

   startBatch(BLKDATA);

   BinaryData key = DBUtils.getBlkDataKey(sbh.blockHeight_, sbh.duplicateID_);
   BinaryWriter bwBlkData;
   sbh.serializeDBValue(BLKDATA, bwBlkData);
   putValue(BLKDATA, key.getRef(), bwBlkData.getDataRef());
   

   for(uint32_t i=0; i<sbh.numTx_; i++)
   {
      map<uint16_t, StoredTx>::iterator txIter = sbh.stxMap_.find(i);
      //if(txIter != sbh.stxMap_.end())
      if(ITER_IN_MAP(txIter, sbh.stxMap_))
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

   // If this is a valid block being put in BLKDATA DB, update DBInfo
   if(sbh.isMainBranch_ && withBlkData)
   {
      StoredDBInfo sdbiB;
      getStoredDBInfo(BLKDATA, sdbiB);
      if(sbh.blockHeight_ > sdbiB.topBlkHgt_)
      {
         sdbiB.topBlkHgt_  = sbh.blockHeight_;
         sdbiB.topBlkHash_ = sbh.thisHash_;
         putStoredDBInfo(BLKDATA, sdbiB);
      }
   }

   commitBatch(BLKDATA);
   return newDup;
}


////////////////////////////////////////////////////////////////////////////////
// Puts bare header into HEADERS DB.  Use "putStoredHeader" to add to both
// (which actually calls this method as the first step)
//
// Returns the duplicateID of the header just inserted
uint8_t InterfaceToLDB::putBareHeader(StoredHeader & sbh)
{
   SCOPED_TIMER("putBareHeader");

   if(!sbh.isInitialized())
   {
      LOGERR << "Attempting to put uninitialized bare header into DB";
      return UINT8_MAX;
   }

   StoredDBInfo sdbiH;
   getStoredDBInfo(HEADERS, sdbiH);

   uint32_t height  = sbh.blockHeight_;
   uint8_t sbhDupID = UINT8_MAX;

   // Check if it's already in the height-indexed DB - determine dupID if not
   StoredHeadHgtList hhl;
   getStoredHeadHgtList(hhl, height);

   bool alreadyInHgtDB = false;
   bool needToWriteHHL = false;
   if(hhl.dupAndHashList_.size() == 0)
   {
      sbhDupID = 0;
      hhl.addDupAndHash(0, sbh.thisHash_);
      if(sbh.isMainBranch_)
         hhl.preferredDup_ = 0;
      needToWriteHHL = true;
   }
   else
   {
      int8_t maxDup = -1;
      for(uint8_t i=0; i<hhl.dupAndHashList_.size(); i++)
      {
         uint8_t dup = hhl.dupAndHashList_[i].first;
         maxDup = max(maxDup, (int8_t)dup);
         if(sbh.thisHash_ == hhl.dupAndHashList_[i].second)
         {
            alreadyInHgtDB = true;
            sbhDupID = dup;
            if(hhl.preferredDup_ != dup && sbh.isMainBranch_)
            {
               // The header was in the head-hgt list, but not preferred
               hhl.preferredDup_ = dup;
               needToWriteHHL = true;
            }
            break;
         }
      }

      if(!alreadyInHgtDB)
      {
         needToWriteHHL = true;
         sbhDupID = maxDup+1;
         hhl.addDupAndHash(sbhDupID, sbh.thisHash_);
         if(sbh.isMainBranch_)
            hhl.preferredDup_ = sbhDupID;
      }
   }

   sbh.setKeyData(height, sbhDupID);
   
   // Batch the two operations to make sure they both hit the DB, or neither 
   startBatch(HEADERS);

   if(needToWriteHHL)
      putStoredHeadHgtList(hhl);
      
   // Overwrite the existing hash-indexed entry, just in case the dupID was
   // not known when previously written.  
   putValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_, 
                                                sbh.serializeDBValue(HEADERS));

   // If this block is valid, update quick lookup table, and store it in DBInfo
   if(sbh.isMainBranch_)
   {
      setValidDupIDForHeight(sbh.blockHeight_, sbh.duplicateID_);
      if(sbh.blockHeight_ >= sdbiH.topBlkHgt_)
      {
         sdbiH.topBlkHgt_  = sbh.blockHeight_;
         sdbiH.topBlkHash_ = sbh.thisHash_;
         putStoredDBInfo(HEADERS, sdbiH);
      }
   }
   commitBatch(HEADERS);
   return sbhDupID;
}

////////////////////////////////////////////////////////////////////////////////
// "BareHeader" refers to 
bool InterfaceToLDB::getBareHeader(StoredHeader & sbh, 
                                   uint32_t blockHgt, 
                                   uint8_t dup)
{
   SCOPED_TIMER("getBareHeader");

   // Get the hash from the head-hgt list
   StoredHeadHgtList hhl;
   if(!getStoredHeadHgtList(hhl, blockHgt))
   {
      LOGERR << "No headers at height " << blockHgt;
      return false;
   }

   for(uint32_t i=0; i<hhl.dupAndHashList_.size(); i++)
      if(dup==hhl.dupAndHashList_[i].first)
         return getBareHeader(sbh, hhl.dupAndHashList_[i].second);

   return false;

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getBareHeader(StoredHeader & sbh, uint32_t blockHgt)
{
   SCOPED_TIMER("getBareHeader(duplookup)");

   uint8_t dupID = getValidDupIDForHeight(blockHgt);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHgt; 

   return getBareHeader(sbh, blockHgt, dupID);
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getBareHeader(StoredHeader & sbh, BinaryDataRef headHash)
{
   SCOPED_TIMER("getBareHeader(hashlookup)");

   BinaryRefReader brr = getValueReader(HEADERS, DB_PREFIX_HEADHASH, headHash);
   if(brr.getSize() == 0)
   {
      LOGERR << "Header found in HHL but hash does not exist in DB";
      return false;
   }
   sbh.unserializeDBValue(HEADERS, brr);
   return true;
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
      BinaryData blkKey = DBUtils.getBlkDataKey(blockHgt, blockDup);
      BinaryRefReader brr = getValueReader(BLKDATA, blkKey);
      if(brr.getSize()==0)
      {
         LOGERR << "Header height&dup is not in BLKDATA";
         return false;
      }
      sbh.blockHeight_ = blockHgt;
      sbh.duplicateID_ = blockDup;
      sbh.unserializeDBValue(BLKDATA, brr, false);
      sbh.isMainBranch_ = (blockDup == getValidDupIDForHeight(blockHgt));
      return true;
   }
   else
   {
      //////
      // Do the iterator thing because we're going to traverse the whole block
      LDBIter ldbIter = getIterator(BLKDATA);
      if(!ldbIter.seekToExact(DBUtils.getBlkDataKey(blockHgt, blockDup)))
      {
         LOGERR << "Header heigh&dup is not in BLKDATA DB";
         LOGERR << "("<<blockHgt<<", "<<blockDup<<")";
         return false;
      }

      // Now we read the whole block, not just the header
      bool success = readStoredBlockAtIter(ldbIter, sbh);
      sbh.isMainBranch_ = (blockDup == getValidDupIDForHeight(blockHgt));
      return success; 
   }

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredHeader( StoredHeader & sbh,
                                      BinaryDataRef headHash, 
                                      bool withTx)
{
   SCOPED_TIMER("getStoredHeader(hashlookup)");

   BinaryData headEntry = getValue(HEADERS, DB_PREFIX_HEADHASH, headHash); 
   if(headEntry.getSize() == 0)
   {
      LOGERR << "Requested header that is not in DB";
      return false;
   }
   
   BinaryRefReader brr(headEntry);
   sbh.unserializeDBValue(HEADERS, brr);

   return getStoredHeader(sbh, sbh.blockHeight_, sbh.duplicateID_, withTx);
}


////////////////////////////////////////////////////////////////////////////////
/*
bool InterfaceToLDB::getStoredHeader( StoredHeader & sbh,
                                      uint32_t blockHgt,
                                      bool withTx)
{
   SCOPED_TIMER("getStoredHeader(duplookup)");

   uint8_t dupID = getValidDupIDForHeight(blockHgt);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHgt; 

   return getStoredHeader(sbh, blockHgt, dupID, withTx);
}
*/



////////////////////////////////////////////////////////////////////////////////
// This assumes that this new tx is "preferred" and will update the list as such
void InterfaceToLDB::putStoredTx( StoredTx & stx, bool withTxOut)
{
   SCOPED_TIMER("putStoredTx");
   BinaryData ldbKey = DBUtils.getBlkDataKeyNoPrefix(stx.blockHeight_, 
                                                      stx.duplicateID_, 
                                                      stx.txIndex_);


   // First, check if it's already in the hash-indexed DB
   StoredTxHints sths;
   getStoredTxHints(sths, stx.thisHash_);

   // Check whether the hint already exists in the DB
   bool needToAddTxToHints = true;
   bool needToUpdateHints = false;
   for(uint32_t i=0; i<sths.dbKeyList_.size(); i++)
   {
      if(sths.dbKeyList_[i] == ldbKey)
      {
         needToAddTxToHints = false;
         needToUpdateHints = (sths.preferredDBKey_!=ldbKey);
         sths.preferredDBKey_ = ldbKey;
         break;
      }
   }

   // Add it to the hint list if needed
   if(needToAddTxToHints)
   {
      sths.dbKeyList_.push_back(ldbKey);
      sths.preferredDBKey_ = ldbKey;
   }

   // Batch update the DB
   startBatch(BLKDATA);

   if(needToAddTxToHints || needToUpdateHints)
      putStoredTxHints(sths);

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
         iter->second.duplicateID_ = stx.duplicateID_;
         iter->second.txIndex_     = stx.txIndex_;
         iter->second.txOutIndex_  = iter->first;
         putStoredTxOut(iter->second);
      }
   }

   commitBatch(BLKDATA);
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::updatePreferredTxHint( BinaryDataRef hashOrPrefix,
                                            BinaryData    preferDBKey)
{
   SCOPED_TIMER("updatePreferredTxHint");
   StoredTxHints sths;
   getStoredTxHints(sths, hashOrPrefix);

   if(sths.preferredDBKey_ == preferDBKey)
      return;

   // Check whether the hint already exists in the DB
   bool exists = false;
   for(uint32_t i=0; i<sths.dbKeyList_.size(); i++)
   {
      if(sths.dbKeyList_[i] == preferDBKey)
      {
         exists = true;
         break;
      }
   }

   if(!exists)
   {
      LOGERR << "Key not in hint list, something is wrong";
      return;
   }

   // sths.dbKeyList_.push_back(preferDBKey);

   sths.preferredDBKey_ = preferDBKey;
   putStoredTxHints(sths);

}

////////////////////////////////////////////////////////////////////////////////
// We assume we have a valid iterator left at the header entry for this block
bool InterfaceToLDB::readStoredBlockAtIter(LDBIter & ldbIter, StoredHeader & sbh)
{
   SCOPED_TIMER("readStoredBlockAtIter");

   ldbIter.resetReaders();
   BinaryData blkDataKey(ldbIter.getKeyReader().getCurrPtr(), 5);

   BLKDATA_TYPE bdtype = DBUtils.readBlkDataKey(ldbIter.getKeyReader(),
                                                sbh.blockHeight_,
                                                sbh.duplicateID_);

   
   // Grab the header first, then iterate over 
   sbh.unserializeDBValue(BLKDATA, ldbIter.getValueRef(), false);
   sbh.isMainBranch_ = (sbh.duplicateID_==getValidDupIDForHeight(sbh.blockHeight_));

   // If for some reason we hit the end of the DB without any tx, bail
   //if(!ldbIter.advanceAndRead(DB_PREFIX_TXDATA)
      //return true;  // this isn't an error, it's an block w/o any StoredTx

   // Now start iterating over the tx data
   uint32_t tempHgt;
   uint8_t  tempDup;
   uint16_t currIdx;
   ldbIter.advanceAndRead();
   while(ldbIter.checkKeyStartsWith(blkDataKey))
   {

      // We can't just read the the tx, because we have to guarantee 
      // there's a place for it in the sbh.stxMap_
      BLKDATA_TYPE bdtype = DBUtils.readBlkDataKey(ldbIter.getKeyReader(), 
                                                   tempHgt, 
                                                   tempDup,
                                                   currIdx);

      if(currIdx >= sbh.numTx_)
      {
         LOGERR << "Invalid txIndex at height " << (sbh.blockHeight_)
                    << " index " << currIdx;
         return false;
      }

      //if(sbh.stxMap_.find(currIdx) == sbh.stxMap_.end())
      if(KEY_NOT_IN_MAP(currIdx, sbh.stxMap_))
         sbh.stxMap_[currIdx] = StoredTx();

      readStoredTxAtIter(ldbIter,
                         sbh.blockHeight_, 
                         sbh.duplicateID_, 
                         sbh.stxMap_[currIdx]);
   } 
   return true;
} 


////////////////////////////////////////////////////////////////////////////////
// We assume we have a valid iterator left at the beginning of (potentially) a 
// transaction in this block.  It's okay if it starts at at TxOut entry (in 
// some instances we may not have a Tx entry, but only the TxOuts).
bool InterfaceToLDB::readStoredTxAtIter( LDBIter & ldbIter,
                                         uint32_t height,
                                         uint8_t  dupID,
                                         StoredTx & stx)
{
   SCOPED_TIMER("readStoredTxAtIter");
   BinaryData blkPrefix = DBUtils.getBlkDataKey(height, dupID);

   // Make sure that we are still within the desired block (but beyond header)
   ldbIter.resetReaders();
   BinaryDataRef key = ldbIter.getKeyRef();
   if(!key.startsWith(blkPrefix) || key.getSize() < 7)
      return false;


   // Check that we are at a tx with the correct height & dup
   uint32_t storedHgt;
   uint8_t  storedDup;
   uint16_t storedIdx;
   DBUtils.readBlkDataKey(ldbIter.getKeyReader(), storedHgt, storedDup, storedIdx);

   if(storedHgt != height || storedDup != dupID)
      return false;


   // Make sure the stx has correct height/dup/idx
   stx.blockHeight_ = storedHgt;
   stx.duplicateID_ = storedDup;
   stx.txIndex_     = storedIdx;

   // Use a temp variable instead of stx.numBytes_ directly, because the 
   // stx.unserializeDBValue() call will reset numBytes to UINT32_MAX.
   // Assign it at the end, if we're confident we have the correct value.
   uint32_t nbytes  = 0;

   BinaryData txPrefix = DBUtils.getBlkDataKey(height, dupID, stx.txIndex_);

   
   // Reset the key again, and then cycle through entries until no longer
   // on an entry with the correct prefix.  Use do-while because we've 
   // already verified the iterator is at a valid tx entry
   ldbIter.resetReaders();
   do
   {


      // Stop if key doesn't start with [PREFIX | HGT | DUP | TXIDX]
      if(!ldbIter.checkKeyStartsWith(txPrefix))
         break;


      // Read the prefix, height and dup 
      uint16_t txOutIdx;
      BLKDATA_TYPE bdtype = DBUtils.readBlkDataKey(ldbIter.getKeyReader(),
                                           stx.blockHeight_,
                                           stx.duplicateID_,
                                           stx.txIndex_,
                                           txOutIdx);

      // Now actually process the iter value
      if(bdtype == BLKDATA_TX)
      {
         // Get everything else from the iter value
         stx.unserializeDBValue(ldbIter.getValueRef());
         nbytes += stx.dataCopy_.getSize();
      }
      else if(bdtype == BLKDATA_TXOUT)
      {
         stx.stxoMap_[txOutIdx] = StoredTxOut();
         StoredTxOut & stxo = stx.stxoMap_[txOutIdx];
         readStoredTxOutAtIter(ldbIter, height, dupID, stx.txIndex_, stxo);
         stxo.parentHash_ = stx.thisHash_;
         stxo.txVersion_  = stx.version_;
         nbytes += stxo.dataCopy_.getSize();
      }
      else
      {
         LOGERR << "Unexpected BLKDATA entry while iterating";
         return false;
      }

   } while(ldbIter.advanceAndRead(DB_PREFIX_TXDATA));


   // If have the correct size, save it, otherwise ignore the computation
   stx.numBytes_ = stx.haveAllTxOut() ? nbytes : UINT32_MAX;

   return true;
} 


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::readStoredTxOutAtIter(
                                       LDBIter & ldbIter, 
                                       uint32_t height,
                                       uint8_t  dupID,
                                       uint16_t txIndex,
                                       StoredTxOut & stxo)
{
   if(ldbIter.getKeyRef().getSize() < 9)
      return false;

   ldbIter.resetReaders();

   // Check that we are at a tx with the correct height & dup & txIndex
   uint32_t keyHgt;
   uint8_t  keyDup;
   uint16_t keyTxIdx;
   uint16_t keyTxOutIdx;
   DBUtils.readBlkDataKey(ldbIter.getKeyReader(), 
                          keyHgt, keyDup, keyTxIdx, keyTxOutIdx);

   if(keyHgt != height || keyDup != dupID || keyTxIdx != txIndex)
      return false;

   stxo.blockHeight_ = height;
   stxo.duplicateID_ = dupID;
   stxo.txIndex_     = txIndex;
   stxo.txOutIndex_  = keyTxOutIdx;

   stxo.unserializeDBValue(ldbIter.getValueRef());

   return true;
}


////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( BinaryData ldbKey6B )
{
   SCOPED_TIMER("getFullTxCopy");
   if(ldbKey6B.getSize() != 6)
   {
      LOGERR << "Provided zero-length ldbKey6B";
      return Tx();
   }
    
   LDBIter ldbIter = getIterator(BLKDATA);
   if(!ldbIter.seekToStartsWith(DB_PREFIX_TXDATA, ldbKey6B))
   {
      LOGERR << "TxRef key does not exist in BLKDATA DB";
      return Tx();
   }

   BinaryData hgtx = ldbKey6B.getSliceCopy(0,4);
   StoredTx stx;
   readStoredTxAtIter( ldbIter,
                       DBUtils.hgtxToHeight(hgtx), 
                       DBUtils.hgtxToDupID(hgtx), 
                       stx);

   if(!stx.haveAllTxOut())
   {
      LOGERR << "Requested full Tx but not all TxOut available";
      return Tx();
   }

   return stx.getTxCopy();
}

////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( uint32_t hgt, uint16_t txIndex)
{
   SCOPED_TIMER("getFullTxCopy");
   uint8_t dup = getValidDupIDForHeight(hgt);
   if(dup == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << hgt;

   BinaryData ldbKey = DBUtils.getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}

////////////////////////////////////////////////////////////////////////////////
Tx InterfaceToLDB::getFullTxCopy( uint32_t hgt, uint8_t dup, uint16_t txIndex)
{
   SCOPED_TIMER("getFullTxCopy");
   BinaryData ldbKey = DBUtils.getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}


////////////////////////////////////////////////////////////////////////////////
TxOut InterfaceToLDB::getTxOutCopy( BinaryData ldbKey6B, uint16_t txOutIdx)
{
   SCOPED_TIMER("getTxOutCopy");
   BinaryWriter bw(8);
   bw.put_BinaryData(ldbKey6B);
   bw.put_uint16_t(txOutIdx, BIGENDIAN);
   BinaryDataRef ldbKey8 = bw.getDataRef();

   TxOut txoOut;
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey8);
   if(brr.getSize()==0) 
   {
      LOGERR << "TxOut key does not exist in BLKDATA DB";
      return TxOut();
   }

   TxRef parent(ldbKey6B, this);

   brr.advance(2);
   txoOut.unserialize_checked(brr.getCurrPtr(), brr.getSizeRemaining(), 0, parent, (uint32_t)txOutIdx);
   return txoOut;
}


////////////////////////////////////////////////////////////////////////////////
TxIn InterfaceToLDB::getTxInCopy( BinaryData ldbKey6B, uint16_t txInIdx)
{
   SCOPED_TIMER("getTxInCopy");
   TxIn txiOut;
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B);
   if(brr.getSize()==0) 
   {
      LOGERR << "TxOut key does not exist in BLKDATA DB";
      return TxIn();
   }

   BitUnpacker<uint16_t> bitunpack(brr); // flags
   uint16_t dbVer   = bitunpack.getBits(4);
   uint16_t txVer   = bitunpack.getBits(2);
   uint16_t txSer   = bitunpack.getBits(4);
   
   brr.advance(32);

   
   if(txSer != TX_SER_FULL && txSer != TX_SER_FRAGGED)
   {
      LOGERR << "Tx not available to retrieve TxIn";
      return TxIn();
   }
   else
   {
      bool isFragged = txSer==TX_SER_FRAGGED;
      vector<uint32_t> offsetsIn;
      BtcUtils::StoredTxCalcLength(brr.getCurrPtr(), isFragged, &offsetsIn);
      if((uint32_t)(offsetsIn.size()-1) < (uint32_t)(txInIdx+1))
      {
         LOGERR << "Requested TxIn with index greater than numTxIn";
         return TxIn();
      }
      TxRef parent(ldbKey6B, this);
      uint8_t const * txInStart = brr.exposeDataPtr() + 34 + offsetsIn[txInIdx];
      uint32_t txInLength = offsetsIn[txInIdx+1] - offsetsIn[txInIdx];
      TxIn txin;
      txin.unserialize_checked(txInStart, brr.getSize() - 34 - offsetsIn[txInIdx], txInLength, parent, txInIdx);
      return txin;
   }
}




////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTxHashForLdbKey( BinaryDataRef ldbKey6B )
{
   SCOPED_TIMER("getTxHashForLdbKey");
   BinaryRefReader stxVal = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B);
   if(stxVal.getSize()==0)
   {
      LOGERR << "TxRef key does not exist in BLKDATA DB";
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
      LOGERR << "Headers DB has no block at height: " << height;
   return getTxHashForLdbKey(DBUtils.getBlkDataKey(height, dup, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLDB::getTxHashForHeightAndIndex( uint32_t height,
                                                       uint8_t  dupID,
                                                       uint16_t txIndex)
{
   SCOPED_TIMER("getTxHashForHeightAndIndex");
   return getTxHashForLdbKey(DBUtils.getBlkDataKey(height, dupID, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
StoredTxHints InterfaceToLDB::getHintsForTxHash(BinaryDataRef txHash)
{
   SCOPED_TIMER("getAllHintsForTxHash");
   StoredTxHints sths;
   sths.txHashPrefix_ = txHash.getSliceRef(0,4);
   BinaryRefReader brr = getValueReader(BLKDATA, 
                                        DB_PREFIX_TXHINTS, 
                                        sths.txHashPrefix_);
                                                
   if(brr.getSize() == 0)
   {
      // Don't need to throw any errors, we frequently ask for tx that DNE
      //LOGERR << "No hints for prefix: " << sths.txHashPrefix_.toHexStr();
   }
   else
      sths.unserializeDBValue(brr);

   return sths;
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx( StoredTx & stx,
                                  BinaryDataRef txHashOrDBKey)
{
   uint32_t sz = txHashOrDBKey.getSize();
   if(sz == 32)
      return getStoredTx_byHash(stx, txHashOrDBKey);
   else if(sz == 6 || sz == 7)
      return getStoredTx_byDBKey(stx, txHashOrDBKey);
   else
   {
      LOGERR << "Unrecognized input string: " << txHashOrDBKey.toHexStr();
      return false;
   }
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx_byDBKey( StoredTx & stx,
                                          BinaryDataRef dbKey)
{
   uint32_t hgt;
   uint8_t  dup;
   uint16_t txi;

   BinaryRefReader brrKey(dbKey);

   if(dbKey.getSize() == 6)
      DBUtils.readBlkDataKeyNoPrefix(brrKey, hgt, dup, txi);
   else if(dbKey.getSize() == 7)
      DBUtils.readBlkDataKey(brrKey, hgt, dup, txi);
   else
   {
      LOGERR << "Unrecognized input string: " << dbKey.toHexStr();
      return false;
   }

   return getStoredTx(stx, hgt, dup, txi, true);
}

////////////////////////////////////////////////////////////////////////////////
// We assume that the first TxHint that matches is correct.  This means that 
// when we mark a transaction/block valid, we need to make sure all the hints
// lists have the correct one in front.  Luckily, the TXHINTS entries are tiny 
// and the number of modifications to make for each reorg is small.
bool InterfaceToLDB::getStoredTx_byHash( StoredTx & stx,
                                         BinaryDataRef txHash)
{
   SCOPED_TIMER("getStoredTx");
   BinaryData hash4(txHash.getSliceRef(0,4));
   BinaryData hintsDBVal = getValue(BLKDATA, DB_PREFIX_TXHINTS, hash4);
   uint32_t valSize = hintsDBVal.getSize();

   if(valSize < 2)
   {
      LOGERR << "No tx in DB with hash: " << txHash.toHexStr();
      return false;
   }

   LDBIter ldbIter = getIterator(BLKDATA);
   BinaryRefReader brrHints(hintsDBVal);
   uint32_t numHints = (uint32_t)brrHints.get_var_int();
   uint32_t height;
   uint8_t  dup;
   uint16_t txIdx;
   for(uint32_t i=0; i<numHints; i++)
   {
      BinaryDataRef hint = brrHints.get_BinaryDataRef(6);
      
      if(!ldbIter.seekToExact(DB_PREFIX_TXDATA, hint))
      {
         LOGERR << "Hinted tx does not exist in DB";
         LOGERR << "TxHash: " << hint.toHexStr().c_str();
         continue;
      }

      BLKDATA_TYPE bdtype = DBUtils.readBlkDataKey(ldbIter.getKeyReader(), 
                                                   height, dup, txIdx);
      
      // We don't actually know for sure whether the seekTo() found 
      BinaryData key6 = DBUtils.getBlkDataKeyNoPrefix(height, dup, txIdx);
      if(key6 != hint)
      {
         LOGERR << "TxHint referenced a BLKDATA tx that doesn't exist";
         LOGERR << "Key:  '" << key6.toHexStr() << "', "
                << "Hint: '" << hint.toHexStr() << "'";
         continue;
      }

      ldbIter.getValueReader().advance(2);  // skip flags
      if(ldbIter.getValueReader().get_BinaryDataRef(32) == txHash)
      {
         ldbIter.resetReaders();
         return readStoredTxAtIter(ldbIter, height, dup, stx);
      }
   }

   return false;
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx( StoredTx & stx,
                                  uint32_t blockHeight,
                                  uint16_t txIndex,
                                  bool withTxOut)
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTx(stx, blockHeight, dupID, txIndex, withTxOut);

}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTx( StoredTx & stx,
                                  uint32_t blockHeight,
                                  uint8_t  dupID,
                                  uint16_t txIndex,
                                  bool withTxOut)
{
   SCOPED_TIMER("getStoredTx");

   BinaryData blkDataKey = DBUtils.getBlkDataKey(blockHeight, dupID, txIndex);
   stx.blockHeight_ = blockHeight;
   stx.duplicateID_  = dupID;
   stx.txIndex_     = txIndex;

   if(!withTxOut)
   {
      // In some situations, withTxOut may not matter here:  the TxOuts may
      // actually be serialized with the tx entry, thus the unserialize call
      // may extract all TxOuts.
      BinaryRefReader brr = getValueReader(BLKDATA, blkDataKey);
      if(brr.getSize()==0)
      {
         LOGERR << "BLKDATA DB does not have requested tx";
         LOGERR << "("<<blockHeight<<", "<<dupID<<", "<<txIndex<<")";
         return false;
      }

      stx.unserializeDBValue(brr);
   }
   else
   {
      LDBIter ldbIter = getIterator(BLKDATA);
      if(!ldbIter.seekToExact(blkDataKey))
      {
         LOGERR << "BLKDATA DB does not have the requested tx";
         LOGERR << "("<<blockHeight<<", "<<dupID<<", "<<txIndex<<")";
         return false;
      }

      return readStoredTxAtIter(ldbIter, blockHeight, dupID, stx);

   } 

   return true;
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::putStoredTxOut( StoredTxOut const & stxo)
{
    
   SCOPED_TIMER("putStoredTx");

   BinaryData ldbKey = stxo.getDBKey(false);
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
   BinaryData blkKey = DBUtils.getBlkDataKey(blockHeight, dupID, txIndex, txOutIndex);
   BinaryRefReader brr = getValueReader(BLKDATA, blkKey);
   if(brr.getSize() == 0)
   {
      LOGERR << "BLKDATA DB does not have the requested TxOut";
      return false;
   }

   stxo.blockHeight_ = blockHeight;
   stxo.duplicateID_  = dupID;
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
      LOGERR << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTxOut(stxo, blockHeight, dupID, txIndex, txOutIndex);
}





////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::putStoredUndoData(StoredUndoData const & sud)
{
   LOGERR << "putStoredUndoData not implemented yet!!!";
   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredUndoData(StoredUndoData & sud, uint32_t height)
{
   LOGERR << "getStoredUndoData not implemented yet!!!";
   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredUndoData(StoredUndoData & sud, 
                                       uint32_t         height, 
                                       uint8_t          dup)
{
   LOGERR << "getStoredUndoData not implemented yet!!!";
   return false;

   /*
   BinaryData key = DBUtils.getBlkDataKeyNoPrefix(height, dup); 
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_UNDODATA, key);

   if(brr.getSize() == 0)
   {
      LOGERR << " 
   }

   for(uint32_t i=0; i<sud.stxOutsRemovedByBlock_.size(); i++)
   {
      sud.stxOutsRemovedByBlock_[i].blockHeight_ = height;
      sud.stxOutsRemovedByBlock_[i].duplicateID_ = dup;
   }
   */
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredUndoData(StoredUndoData & sud, 
                                       BinaryDataRef    headHash)
{
   SCOPED_TIMER("getStoredUndoData");
   LOGERR << "getStoredUndoData not implemented yet!!!";
   return false;
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::putStoredTxHints(StoredTxHints const & sths)
{
   SCOPED_TIMER("putStoredTxHints");
   if(sths.txHashPrefix_.getSize()==0)
   {
      LOGERR << "STHS does have a set prefix, so cannot be put into DB";
      return false;
   }
   putValue(BLKDATA, sths.getDBKey(), sths.serializeDBValue());
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredTxHints(StoredTxHints & sths, 
                                      BinaryDataRef hashPrefix)
{
   if(hashPrefix.getSize() < 4)
   {
      LOGERR << "Cannot get hints without at least 4-byte prefix";
      return false;
   }
   BinaryDataRef prefix4 = hashPrefix.getSliceRef(0,4);
   sths.txHashPrefix_ = prefix4.copy();

   BinaryDataRef bdr = getValueRef(BLKDATA, DB_PREFIX_TXHINTS, prefix4);
   if(bdr.getSize() > 0)
   {
      sths.unserializeDBValue(bdr);
      return true;
   }
   else
   {
      sths.dbKeyList_.resize(0);
      sths.preferredDBKey_.resize(0);
      return false;
   }
}


////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::putStoredHeadHgtList(StoredHeadHgtList const & hhl)
{
   SCOPED_TIMER("putStoredHeadHgtList");

   if(hhl.height_ == UINT32_MAX)
   {
      LOGERR << "HHL does not have a valid height to be put into DB";
      return false;
   }

   putValue(HEADERS, hhl.getDBKey(), hhl.serializeDBValue());
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::getStoredHeadHgtList(StoredHeadHgtList & hhl, uint32_t height)
{
   BinaryData ldbKey = WRITE_UINT32_BE(height);
   BinaryDataRef bdr = getValueRef(HEADERS, DB_PREFIX_HEADHGT, ldbKey);
   hhl.height_ = height;
   if(bdr.getSize() > 0)
   {
      hhl.unserializeDBValue(bdr);
      return true;
   }
   else
   {
      hhl.preferredDup_ = UINT8_MAX;
      hhl.dupAndHashList_.resize(0);
      return false;
   }
}




////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef( BinaryDataRef txHash )
{
   LDBIter ldbIter = getIterator(BLKDATA);
   if(seekToTxByHash(ldbIter, txHash))
   {
      ldbIter.getKeyReader().advance(1);
      return TxRef(ldbIter.getKeyReader().get_BinaryDataRef(6), this);
   }
   
   return TxRef();
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef(BinaryData hgtx, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(hgtx);
   bw.put_uint16_t(txIndex, BIGENDIAN);
   return TxRef(bw.getDataRef(), this);
}

////////////////////////////////////////////////////////////////////////////////
TxRef InterfaceToLDB::getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(DBUtils.heightAndDupToHgtx(hgt,dup));
   bw.put_uint16_t(txIndex, BIGENDIAN);
   return TxRef(bw.getDataRef(), this);
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::markBlockHeaderValid(BinaryDataRef headHash)
{
   SCOPED_TIMER("markBlockHeaderValid");
   BinaryRefReader brr = getValueReader(HEADERS, DB_PREFIX_HEADHASH, headHash);
   if(brr.getSize()==0)
   {
      LOGERR << "Invalid header hash: " << headHash.toHexStr();
      return false;
   }
   brr.advance(HEADER_SIZE);
   BinaryData hgtx   = brr.get_BinaryData(4);
   uint32_t   height = DBUtils.hgtxToHeight(hgtx);
   uint8_t    dup    = DBUtils.hgtxToDupID(hgtx);

   return markBlockHeaderValid(height, dup);
}




////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLDB::markBlockHeaderValid(uint32_t height, uint8_t dup)
{
   SCOPED_TIMER("markBlockHeaderValid");

   StoredHeadHgtList hhl;
   getStoredHeadHgtList(hhl, height);
   if(hhl.preferredDup_ == dup)
      return true;

   bool hasEntry = false;
   for(uint32_t i=0; i<hhl.dupAndHashList_.size(); i++)
      if(hhl.dupAndHashList_[i].first == dup)
         hasEntry = true;
   

   if(hasEntry)
   {
      hhl.setPreferredDupID(dup);
      putStoredHeadHgtList(hhl);
      setValidDupIDForHeight(height, dup);
      return true;
   }   
   else
   {
      LOGERR << "Header was not found header-height list";
      return false;
   }
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
   BinaryData blkDataKey = DBUtils.getBlkDataKeyNoPrefix(height, dupID, txIndex);
   BinaryRefReader brrTx = getValueReader(BLKDATA, DB_PREFIX_TXDATA, blkDataKey);

   brrTx.advance(2);
   BinaryData key4 = brrTx.get_BinaryData(4); // only need the first four bytes

   BinaryRefReader brrHints = getValueReader(BLKDATA, DB_PREFIX_TXHINTS, key4);
   uint32_t numHints = brrHints.getSize() / 6;
   if(numHints==0)
   {
      LOGERR << "No TXHINTS entry for specified {hgt,dup,txidx}";      
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
      LOGERR << "Tx was not found in the TXHINTS list";
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
// This is used only for debugging and testing with small database sizes.
// For intance, the reorg unit test only has a couple blocks, a couple 
// addresses and a dozen transactions.  We can easily predict and construct
// the output of this function or analyze the output by eye.
KVLIST InterfaceToLDB::getAllDatabaseEntries(DB_SELECT db)
{
   SCOPED_TIMER("getAllDatabaseEntries");
   
   if(!databasesAreOpen())
      return KVLIST();

   KVLIST outList;
   outList.reserve(100);

   LDBIter ldbIter = getIterator(db);
   ldbIter.seekToFirst();
   for(ldbIter.seekToFirst(); ldbIter.isValid(); ldbIter.advanceAndRead())
   {
      size_t last = outList.size();
      outList.push_back( pair<BinaryData, BinaryData>() );
      outList[last].first  = ldbIter.getKey();
      outList[last].second = ldbIter.getValue();
   }

   return outList;
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::printAllDatabaseEntries(DB_SELECT db)
{
   SCOPED_TIMER("printAllDatabaseEntries");

   cout << "Printing DB entries... (DB=" << db << ")" << endl;
   KVLIST dbList = getAllDatabaseEntries(db);
   if(dbList.size() == 0)
   {
      cout << "   <no entries in db>" << endl;
      return;
   }

   for(uint32_t i=0; i<dbList.size(); i++)
   {
      cout << "   \"" << dbList[i].first.toHexStr() << "\"  ";
      cout << "   \"" << dbList[i].second.toHexStr() << "\"  " << endl;
   }
}

#define PPRINTENTRY(TYPE, IND) \
    TYPE data; \
    data.unserializeDBKey(key); \
    data.unserializeDBValue(val); \
    data.pprintOneLine(indent + IND); 
   

#define PPRINTENTRYDB(TYPE, IND) \
    TYPE data; \
    data.unserializeDBKey(BLKDATA, key); \
    data.unserializeDBValue(BLKDATA, val); \
    data.pprintOneLine(indent + IND); 

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLDB::pprintBlkDataDB(uint32_t indent)
{
   SCOPED_TIMER("pprintBlkDataDB");
   DB_SELECT db = BLKDATA;

   cout << "Pretty-printing BLKDATA DB" << endl;
   KVLIST dbList = getAllDatabaseEntries(db);
   if(dbList.size() == 0)
   {
      cout << "   <no entries in db>" << endl;
      return;
   }

   BinaryData lastSSH = READHEX("00");
   for(uint32_t i=0; i<dbList.size(); i++)
   {
      BinaryData key = dbList[i].first;
      BinaryData val = dbList[i].second;
      if(key.getSize() == 0)
      {
         cout << "\"" << "\"  ";
         cout << "\"" << dbList[i].second.toHexStr() << "\"  " << endl;
      }
      else if(key[0] == DB_PREFIX_DBINFO)
      {
         PPRINTENTRY(StoredDBInfo, 0);
         cout << "-------------------------------------" << endl;
      }
      else if(key[0] == DB_PREFIX_TXDATA)
      {
         if(key.getSize() == 5)      {PPRINTENTRYDB(StoredHeader, 0);}
         else if(key.getSize() == 7) {PPRINTENTRY(StoredTx, 3); }
         else if(key.getSize() == 9) {PPRINTENTRY(StoredTxOut, 6);}
         else
            cout << "INVALID TXDATA KEY: '" << key.toHexStr() << "'" << endl;
      }
      else if(key[0] == DB_PREFIX_SCRIPT) 
      {
         StoredScriptHistory ssh;
         StoredSubHistory subssh;
      
         if(!key.startsWith(lastSSH))
         {
            // New SSH object, base entry
            ssh.unserializeDBKey(key); 
            ssh.unserializeDBValue(val); 
            ssh.pprintFullSSH(indent + 3); 
            lastSSH = key;
         }
         else
         {
            // This is a sub-history for the previous SSH
            subssh.unserializeDBKey(key); 
            subssh.unserializeDBValue(val); 
            subssh.pprintFullSubSSH(indent + 6);
         }
      }
      else
      {
         for(uint32_t j=0; j<indent; j++)
            cout << " ";

         if(key[0] == DB_PREFIX_TXHINTS)
            cout << "TXHINT: ";
         else if(key[0]==DB_PREFIX_UNDODATA)
            cout << "UNDO: ";

         cout << "\"" << dbList[i].first.toHexStr() << "\"  ";
         cout << "\"" << dbList[i].second.toHexStr() << "\"  " << endl;
      }
         
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
      LOGERR << " Attempted to update a non-existent header!";
      return false;
   }
      
   BinaryWriter bw(HEADER_SIZE + 4);
   bw.put_BinaryData(headVal.getPtr(), HEADER_SIZE);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));

   putValue(HEADERS, headHash, bw.getDataRef());
   return true;
}  
*/


