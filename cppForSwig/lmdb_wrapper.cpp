////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

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
#include "lmdb_wrapper.h"
#include "txio.h"
#include "BlockDataMap.h"

#include "Blockchain.h"

////////////////////////////////////////////////////////////////////////////////
LDBIter::LDBIter(LMDB::Iterator&& mv)
   : iter_(std::move(mv))
{ 
   isDirty_ = true;
}

////////////////////////////////////////////////////////////////////////////////
LDBIter::LDBIter(LDBIter&& mv)
: iter_(std::move(mv.iter_))
{
   isDirty_ = true;
}

LDBIter::LDBIter(const LDBIter& cp)
: iter_(cp.iter_)
{
   isDirty_ = true;
}

////////////////////////////////////////////////////////////////////////////////
LDBIter& LDBIter::operator=(LMDB::Iterator&& mv)
{ 
   iter_ = std::move(mv);
   return *this;
}

////////////////////////////////////////////////////////////////////////////////
LDBIter& LDBIter::operator=(LDBIter&& mv)
{ 
   iter_ = std::move(mv.iter_);
   return *this;
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::isValid(DB_PREFIX dbpref)
{
   if(!isValid() || iter_.key().mv_size == 0)
      return false;
   return (*(uint8_t*)iter_.key().mv_data) == (uint8_t)dbpref;
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advance(void)
{
   ++iter_;
   isDirty_ = true;
   return isValid();
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::retreat(void)
{
   --iter_;
   isDirty_ = true;
   return isValid();
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::advance(DB_PREFIX prefix)
{
   ++iter_;
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

   currKey_ = BinaryDataRef(
      (uint8_t*)iter_.key().mv_data, 
      iter_.key().mv_size);
   currValue_ = BinaryDataRef(
      (uint8_t*)iter_.value().mv_data, 
      iter_.value().mv_size);

   currKeyReader_.setNewData( currKey_ );
   currValueReader_.setNewData( currValue_ );
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
BinaryData LDBIter::getKey(void) const
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty key ref";
      return BinaryData(0);
   }
   return currKey_;
}
   
////////////////////////////////////////////////////////////////////////////////
BinaryData LDBIter::getValue(void) const
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty value ref";
      return BinaryData(0);
   }
   return currValue_;
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef LDBIter::getKeyRef(void) const
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty key ref";
      return BinaryDataRef();
   }
   return currKeyReader_.getRawRef();
}
   
////////////////////////////////////////////////////////////////////////////////
BinaryDataRef LDBIter::getValueRef(void) const
{ 
   if(isDirty_)
   {
      LOGERR << "Returning dirty value ref";
      return BinaryDataRef();
   }
   return currValueReader_.getRawRef();
}


////////////////////////////////////////////////////////////////////////////////
BinaryRefReader& LDBIter::getKeyReader(void) const
{ 
   if(isDirty_)
      LOGERR << "Returning dirty key reader";
   return currKeyReader_; 
}

////////////////////////////////////////////////////////////////////////////////
BinaryRefReader& LDBIter::getValueReader(void) const
{ 
   if(isDirty_)
      LOGERR << "Returning dirty value reader";
   return currValueReader_; 
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekTo(BinaryDataRef key)
{
   iter_.seek(CharacterArrayRef(key.getSize(), key.getPtr()), LMDB::Iterator::Seek_GE);
   return readIterData();
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekTo(DB_PREFIX pref, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)pref);
   bw.put_BinaryData(key);
   return seekTo(bw.getDataRef());
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


bool LDBIter::seekToBefore(BinaryDataRef key)
{
   iter_.seek(CharacterArrayRef(key.getSize(), key.getPtr()), LMDB::Iterator::Seek_LE);
   return readIterData();
}

bool LDBIter::seekToBefore(DB_PREFIX prefix)
{
   BinaryWriter bw(1);
   bw.put_uint8_t((uint8_t)prefix);
   return seekToBefore(bw.getDataRef());
}

bool LDBIter::seekToBefore(DB_PREFIX pref, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)pref);
   bw.put_BinaryData(key);
   return seekToBefore(bw.getDataRef());
}


////////////////////////////////////////////////////////////////////////////////
bool LDBIter::seekToFirst(void)
{
   iter_.toFirst();
   readIterData();
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyExact(BinaryDataRef key)
{
   if(isDirty_ && !readIterData())
      return false;

   return (key==currKeyReader_.getRawRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyExact(DB_PREFIX prefix, BinaryDataRef key)
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   if(isDirty_ && !readIterData())
      return false;

   return (bw.getDataRef()==currKeyReader_.getRawRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::checkKeyStartsWith(BinaryDataRef key)
{
   if(isDirty_ && !readIterData())
      return false;

   return (currKeyReader_.getRawRef().startsWith(key));
}

////////////////////////////////////////////////////////////////////////////////
bool LDBIter::verifyPrefix(DB_PREFIX prefix, bool advanceReader)
{
   if(isDirty_ && !readIterData())
      return false;

   if(currKeyReader_.getSizeRemaining() < 1)
      return false;

   if(advanceReader)
      return (currKeyReader_.get_uint8_t() == (uint8_t)prefix);
   else
      return (currKeyReader_.getRawRef()[0] == (uint8_t)prefix);
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
LMDBBlockDatabase::LMDBBlockDatabase(
   shared_ptr<Blockchain> bcPtr, const string& blkFolder,
   ARMORY_DB_TYPE dbtype) :
   blockchainPtr_(bcPtr), blkFolder_(blkFolder), armoryDbType_(dbtype)
{
   //for some reason the WRITE_UINT16 macros create 4 byte long BinaryData 
   //instead of 2, so I'm doing this the hard way instead
   uint8_t* ptr = const_cast<uint8_t*>(ZCprefix_.getPtr());
   memset(ptr, 0xFF, 2);
}


/////////////////////////////////////////////////////////////////////////////
LMDBBlockDatabase::~LMDBBlockDatabase(void)
{
   closeDatabases();
}





/////////////////////////////////////////////////////////////////////////////
// The dbType and pruneType inputs are left blank if you are just going to 
// take whatever is the current state of database.  You can choose to 
// manually specify them, if you want to throw an error if it's not what you 
// were expecting
void LMDBBlockDatabase::openDatabases(
   const string& basedir,
   BinaryData const & genesisBlkHash,
   BinaryData const & genesisTxHash,
   BinaryData const & magic)
{
   baseDir_ = basedir;

   SCOPED_TIMER("openDatabases");
   LOGINFO << "Opening databases...";

   magicBytes_ = magic;
   genesisTxHash_ = genesisTxHash;
   genesisBlkHash_ = genesisBlkHash;

   if (genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      LOGERR << " must set magic bytes and genesis block";
      LOGERR << "           before opening databases.";
      throw runtime_error("magic bytes not set");
   }

   // Just in case this isn't the first time we tried to open it.
   closeDatabases();


   for (int i = 0; i < COUNT; i++)
   {
      DB_SELECT CURRDB = DB_SELECT(i);
      StoredDBInfo sdbi = openDB(CURRDB);

      // Check that the magic bytes are correct
      if (magicBytes_ != sdbi.magic_)
      {
         throw DbErrorMsg("Magic bytes mismatch!  Different blokchain?");
      }

      if (CURRDB == HEADERS)
      {
         if (armoryDbType_ != sdbi.armoryType_)
            armoryDbType_ = sdbi.armoryType_;
      }
   }
 
   {
      //sanity check: try to open older SDBI version
      LMDBEnv::Transaction tx(dbEnv_[HEADERS].get(), LMDB::ReadOnly);
      BinaryData key;
      key.append(DB_PREFIX_DBINFO);
      auto valueRef = getValueNoCopy(HEADERS, key.getRef());

      if (valueRef.getSize() != 0)
      {
         //old style db, fail
         LOGERR << "DB version mismatch. Use another dbdir!";
         throw DbErrorMsg("DB version mismatch. Use another dbdir!");
      }
   }

   dbIsOpen_ = true;
}

/////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::nukeHeadersDB(void)
{
   SCOPED_TIMER("nukeHeadersDB");
   LOGINFO << "Destroying headers DB, to be rebuilt.";
   
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, HEADERS, LMDB::ReadWrite);
   
   LMDB::Iterator begin = dbs_[HEADERS].begin();
   LMDB::Iterator end = dbs_[HEADERS].end();
   
   while(begin != end)
   {
      CharacterArrayRef keydata(
         begin.key().mv_size, 
         (const char*)begin.key().mv_data);
      ++begin;
      
      dbs_[HEADERS].erase(keydata);
   }

   StoredDBInfo sdbi;
   sdbi.magic_      = magicBytes_;
   sdbi.topBlkHgt_  = 0;
   sdbi.armoryType_ = armoryDbType_;
   sdbi.armoryVer_ = ARMORY_DB_VERSION;
   
   putStoredDBInfo(HEADERS, sdbi, 0);
}


/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void LMDBBlockDatabase::closeDatabases(void)
{
   for(uint32_t db=0; db<COUNT; db++)
      closeDB(DB_SELECT(db));

   dbIsOpen_ = false;
}

/////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::swapDatabases(DB_SELECT db, const string& swap_path)
{
   /*replace a db underlying file with file [swap_path]*/

   auto&& full_swap_path = getDbPath(swap_path);

   //close db
   closeDB(db);

   //delete underlying files
   auto&& db_name = getDbPath(db);
   auto lock_name = db_name;
   lock_name.append("-lock");

   remove(db_name.c_str());
   remove(lock_name.c_str());

   //rename swap_path to db name
   rename(full_swap_path.c_str(), db_name.c_str());

   //rename lock file
   auto swap_lock = full_swap_path;
   swap_lock.append("-lock");

   rename(swap_lock.c_str(), lock_name.c_str());

   //open db
   openDB(db);
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::resetHistoryDatabases(void)
{
   if (armoryDbType_ != ARMORY_DB_SUPER)
   {
      resetSSHdb();

      closeDatabases();
      remove(getDbPath(SUBSSH).c_str());
      remove(getDbPath(TXHINTS).c_str());
      remove(getDbPath(STXO).c_str());

   }
   else
   {
      closeDatabases();
      remove(getDbPath(SUBSSH).c_str());
      remove(getDbPath(SSH).c_str());
      remove(getDbPath(SPENTNESS).c_str());
   }
   
   openDatabases(baseDir_, genesisBlkHash_, genesisTxHash_,
         magicBytes_);
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::destroyAndResetDatabases(void)
{
   //TODO: update to support the new DB_SELECTs
   SCOPED_TIMER("destroyAndResetDatabase");

   // We want to make sure the database is restarted with the same parameters
   // it was called with originally
   {
      closeDatabases();
      for (unsigned db = HEADERS; db != COUNT; db++)
         remove(getDbPath(static_cast<DB_SELECT>(db)).c_str());
   }
   
   // Reopen the databases with the exact same parameters as before
   // The close & destroy operations shouldn't have changed any of that.
   openDatabases(baseDir_, genesisBlkHash_, genesisTxHash_, 
      magicBytes_);
}


////////////////////////////////////////////////////////////////////////////////
BinaryData LMDBBlockDatabase::getTopBlockHash(DB_SELECT db)
{
   if (armoryDbType_ != ARMORY_DB_SUPER && db == BLKDATA)
      throw runtime_error("No SDBI in BLKDATA in Fullnode");

   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, db, LMDB::ReadOnly);
   auto&& sdbi = getStoredDBInfo(db, 0);
   return sdbi.topScannedBlkHash_;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData LMDBBlockDatabase::getTopBlockHash() const
{
   return blockchainPtr_->top()->getThisHash();
}

////////////////////////////////////////////////////////////////////////////////
uint32_t LMDBBlockDatabase::getTopBlockHeight(DB_SELECT db)
{
   auto&& sdbi = getStoredDBInfo(db, 0);
   return sdbi.topBlkHgt_;
}

/////////////////////////////////////////////////////////////////////////////
// Get value without resorting to a DB iterator
BinaryDataRef LMDBBlockDatabase::getValueNoCopy(DB_SELECT db, 
   BinaryDataRef key) const
{
   CharacterArrayRef data = dbs_[db].get_NoCopy(CharacterArrayRef(
      key.getSize(), (char*)key.getPtr()));
   if (data.data)
      return BinaryDataRef((uint8_t*)data.data, data.len);
   else
      return BinaryDataRef();
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
BinaryDataRef LMDBBlockDatabase::getValueRef(DB_SELECT db, BinaryDataRef key) const
{
   return getValueNoCopy(db, key);
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  The data from the get* call is 
// actually copied to a member variable, and thus the refs are valid only 
// until the next get* call.
BinaryDataRef LMDBBlockDatabase::getValueRef(DB_SELECT db, 
                                             DB_PREFIX prefix, 
                                             BinaryDataRef key) const
{
   BinaryWriter bw(key.getSize() + 1);
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   return getValueRef(db, bw.getDataRef());
}

/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
BinaryRefReader LMDBBlockDatabase::getValueReader(
                                             DB_SELECT db, 
                                             BinaryDataRef keyWithPrefix) const
{
   return BinaryRefReader(getValueRef(db, keyWithPrefix));
}

/////////////////////////////////////////////////////////////////////////////
// Same as the getValueRef, in that they are only valid until the next get*
// call.  These are convenience methods which basically just save us 
BinaryRefReader LMDBBlockDatabase::getValueReader(
                                             DB_SELECT db, 
                                             DB_PREFIX prefix, 
                                             BinaryDataRef key) const
{

   return BinaryRefReader(getValueRef(db, prefix, key));
}

/////////////////////////////////////////////////////////////////////////////
// Header Key:  returns header hash
// Tx Key:      returns tx hash
// TxOut Key:   returns serialized OutPoint
BinaryData LMDBBlockDatabase::getHashForDBKey(BinaryData dbkey) const
{
   uint32_t hgt;
   uint8_t  dup;
   uint16_t txi; 
   uint16_t txo; 

   size_t sz = dbkey.getSize();
   if(sz < 4 || sz > 9)
   {
      LOGERR << "Invalid DBKey size: " << sz << ", " << dbkey.toHexStr();
      return BinaryData(0);
   }
   
   BinaryRefReader brr(dbkey);
   if(dbkey.getSize() % 2 == 0)
      DBUtils::readBlkDataKeyNoPrefix(brr, hgt, dup, txi, txo);
   else
      DBUtils::readBlkDataKey(brr, hgt, dup, txi, txo);

   return getHashForDBKey(hgt, dup, txi, txo);
}


/////////////////////////////////////////////////////////////////////////////
// Header Key:  returns header hash
// Tx Key:      returns tx hash
// TxOut Key:   returns serialized OutPoint
BinaryData LMDBBlockDatabase::getHashForDBKey(uint32_t hgt,
                                           uint8_t  dup,
                                           uint16_t txi,
                                           uint16_t txo) const
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
BinaryData LMDBBlockDatabase::getDBKeyForHash(const BinaryData& txhash,
   uint8_t expectedDupId) const
{
   if (txhash.getSize() < 4)
   {
      LOGWARN << "txhash is less than 4 bytes long";
      return BinaryData();
   }

   BinaryData hash4(txhash.getSliceRef(0, 4));

   LMDBEnv::Transaction txHints(dbEnv_[TXHINTS].get(), LMDB::ReadOnly);
   BinaryRefReader brrHints = getValueRef(TXHINTS, DB_PREFIX_TXHINTS, hash4);

   uint32_t valSize = brrHints.getSize();
   if (valSize < 6)
      return BinaryData();
   uint32_t numHints = (uint32_t)brrHints.get_var_int();

   if (armoryDbType_ != ARMORY_DB_SUPER)
   {
      uint32_t height;
      uint8_t  dup;
      uint16_t txIdx;
      for (uint32_t i = 0; i < numHints; i++)
      {
         BinaryDataRef hint = brrHints.get_BinaryDataRef(6);
         BinaryRefReader brrHint(hint);
         BLKDATA_TYPE bdtype = DBUtils::readBlkDataKeyNoPrefix(
            brrHint, height, dup, txIdx);

         if (dup != expectedDupId)
         {
            if (dup != getValidDupIDForHeight(height) && numHints > 1)
               continue;
         }

         auto&& txKey = DBUtils::getBlkDataKey(height, dup, txIdx);
         auto dbVal = getValueNoCopy(TXHINTS, txKey.getRef());
         if (dbVal.getSize() < 36)
            continue;

         auto txHashRef = dbVal.getSliceRef(4, 32);

         if (txHashRef != txhash)
            continue;

         return txKey.getSliceCopy(1, 6);
      }
   }
   else
   {
      if (numHints == 1)
         return brrHints.get_BinaryData(6);

      for (uint32_t i = 0; i < numHints; i++)
      {
         BinaryDataRef hint = brrHints.get_BinaryDataRef(6);
         //grab tx by key, hash and check

         TxRef ref(hint);
         if (txhash == getTxHashForLdbKey(hint))
            return hint;
      }
   }

   return BinaryData();
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void LMDBBlockDatabase::putValue(DB_SELECT db, 
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   dbs_[db].insert(
      CharacterArrayRef(key.getSize(), key.getPtr()),
      CharacterArrayRef(value.getSize(), value.getPtr())
   );
}

/////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putValue(DB_SELECT db, 
                              BinaryData const & key, 
                              BinaryData const & value)
{
   putValue(db, key.getRef(), value.getRef());
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void LMDBBlockDatabase::putValue(DB_SELECT db, 
                                  DB_PREFIX prefix,
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   BinaryWriter bw;
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key.getPtr(), key.getSize());
   putValue(db, bw.getDataRef(), value);
}

/////////////////////////////////////////////////////////////////////////////
// Delete value based on BinaryData key.  If batch writing, pass in the batch
void LMDBBlockDatabase::deleteValue(DB_SELECT db, 
                                 BinaryDataRef key)
                 
{
   dbs_[db].erase( CharacterArrayRef(key.getSize(), key.getPtr() ) );
}


/////////////////////////////////////////////////////////////////////////////
// Delete Put value based on BinaryData key.  If batch writing, pass in the batch
void LMDBBlockDatabase::deleteValue(DB_SELECT db, 
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
//void LMDBBlockDatabase::startHeaderIteration()
//{
   //SCOPED_TIMER("startHeaderIteration");
   //seekTo(HEADERS, DB_PREFIX_HEADHASH, BinaryData(0));
//}

/////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::startBlkDataIteration(LDBIter & ldbIter, DB_PREFIX prefix)
{
   return ldbIter.seekToStartsWith(prefix);
}



/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool LMDBBlockDatabase::advanceToNextBlock(LDBIter & ldbIter, bool skip) const
{
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
bool LMDBBlockDatabase::seekToTxByHash(LDBIter & ldbIter, BinaryDataRef txHash) const
{
   SCOPED_TIMER("seekToTxByHash");
   StoredTxHints sths;
   if (!getStoredTxHints(sths, txHash))
      return false;

   for(uint32_t i=0; i<sths.getNumHints(); i++)
   {
      BinaryDataRef hint = sths.getHint(i);
      ldbIter.seekTo(DB_PREFIX_TXDATA, hint);
      {
         BinaryWriter bw(hint.getSize() + 1);
         bw.put_uint8_t((uint8_t)DB_PREFIX_TXDATA);
         bw.put_BinaryData(hint);
      }
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
bool LMDBBlockDatabase::readStoredScriptHistoryAtIter(LDBIter & ldbIter,
                                                   StoredScriptHistory & ssh,
                                                   uint32_t startBlock,
                                                   uint32_t endBlock) const
{
   SCOPED_TIMER("readStoredScriptHistoryAtIter");

   ldbIter.resetReaders();
   ldbIter.verifyPrefix(DB_PREFIX_SCRIPT, false);

   BinaryDataRef sshKey = ldbIter.getKeyRef();
   ssh.unserializeDBKey(sshKey, true);
   ssh.unserializeDBValue(ldbIter.getValueReader());
      
   size_t sz = sshKey.getSize();
   BinaryData scrAddr(sshKey.getSliceRef(1, sz - 1));

   LMDBEnv::Transaction subsshtx;
   beginDBTransaction(&subsshtx, SUBSSH, LMDB::ReadOnly);
   auto subsshIter = getIterator(SUBSSH);

   BinaryData dbkey_withHgtX(sshKey);

   if (startBlock != 0)
   {
      dbkey_withHgtX.append(DBUtils::heightAndDupToHgtx(startBlock, 0));
   }
    
   if (!subsshIter.seekTo(dbkey_withHgtX))
      return false;
   
   // Now start iterating over the sub histories
   map<BinaryData, StoredSubHistory>::iterator iter;
   size_t numTxioRead = 0;
   do
   {
      size_t _sz = subsshIter.getKeyRef().getSize();
      BinaryDataRef keyNoPrefix= subsshIter.getKeyRef().getSliceRef(1,_sz-1);
      if(!keyNoPrefix.startsWith(ssh.uniqueKey_))
         break;

      pair<BinaryData, StoredSubHistory> keyValPair;
      keyValPair.first = keyNoPrefix.getSliceCopy(_sz-5, 4);
      keyValPair.second.unserializeDBKey(subsshIter.getKeyRef());

      //iter is at the right ssh, make sure hgtX <= endBlock
      if (keyValPair.second.height_ > endBlock)
         break;

      //skip invalid dupIDs
      if (keyValPair.second.dupID_ !=
         getValidDupIDForHeight(keyValPair.second.height_))
         continue;

      keyValPair.second.unserializeDBValue(subsshIter.getValueReader());
      iter = ssh.subHistMap_.insert(keyValPair).first;
      numTxioRead += iter->second.txioMap_.size(); 
   } while(subsshIter.advanceAndRead(DB_PREFIX_SCRIPT) );

   return true;
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredScriptHistory( StoredScriptHistory & ssh)
{
   SCOPED_TIMER("putStoredScriptHistory");
   if(!ssh.isInitialized())
   {
      LOGERR << "Trying to put uninitialized ssh into DB";
      return;
   }

   auto db = SSH;
      
   putValue(db, ssh.getDBKey(), serializeDBValue(ssh, armoryDbType_));

   //onyl supporting these for unit tests, phase out eventually
   {
      map<BinaryData, StoredSubHistory>::iterator iter;
      for (iter = ssh.subHistMap_.begin();
         iter != ssh.subHistMap_.end();
         iter++)
      {
         StoredSubHistory & subssh = iter->second;
         if (subssh.txioMap_.size() > 0)
            putValue(SUBSSH, subssh.getDBKey(),
            serializeDBValue(subssh, this, armoryDbType_)
            );
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredScriptHistorySummary(StoredScriptHistory & ssh)
{
   SCOPED_TIMER("putStoredScriptHistory");
   if (!ssh.isInitialized())
   {
      LOGERR << "Trying to put uninitialized ssh into DB";
      return;
   }

   putValue(SSH, ssh.getDBKey(), serializeDBValue(ssh, armoryDbType_));
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredSubHistory(StoredSubHistory & subssh)

{
   DB_SELECT db = SUBSSH;

   if (subssh.txioMap_.size() > 0)
      putValue(db, subssh.getDBKey(),
         serializeDBValue(subssh, this, armoryDbType_));
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::getStoredScriptHistorySummary( StoredScriptHistory & ssh,
   BinaryDataRef scrAddrStr) const
{
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, SSH, LMDB::ReadOnly);

   DB_SELECT db = SSH;

   LDBIter ldbIter = getIterator(db);
   ldbIter.seekTo(DB_PREFIX_SCRIPT, scrAddrStr);

   if(!ldbIter.seekToExact(DB_PREFIX_SCRIPT, scrAddrStr))
   {
      ssh.clear();
      return;
   }

   ssh.unserializeDBKey(ldbIter.getKeyRef());
   ssh.unserializeDBValue(ldbIter.getValueRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredScriptHistory( StoredScriptHistory & ssh,
                                               BinaryDataRef scrAddrStr,
                                               uint32_t startBlock,
                                               uint32_t endBlock) const
{
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, SSH, LMDB::ReadOnly);
   LDBIter ldbIter = getIterator(getDbSelect(SSH));

   if (!ldbIter.seekToExact(DB_PREFIX_SCRIPT, scrAddrStr))
   {
      ssh.uniqueKey_.resize(0);
      return false;
   }

   bool status = 
      readStoredScriptHistoryAtIter(ldbIter, ssh, startBlock, endBlock);

   if (!status)
      return false;

   //grab UTXO flags
   getUTXOflags(ssh.subHistMap_);

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredSubHistoryAtHgtX(StoredSubHistory& subssh,
   const BinaryData& scrAddrStr, const BinaryData& hgtX) const
{
   BinaryWriter bw(scrAddrStr.getSize() + hgtX.getSize());
   bw.put_BinaryData(scrAddrStr);
   bw.put_BinaryData(hgtX);

   return getStoredSubHistoryAtHgtX(subssh, bw.getDataRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredSubHistoryAtHgtX(StoredSubHistory& subssh,
   const BinaryData& dbkey) const
{
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, SUBSSH, LMDB::ReadOnly);
   LDBIter ldbIter = getIterator(getDbSelect(SUBSSH));

   if (!ldbIter.seekToExact(DB_PREFIX_SCRIPT, dbkey))
      return false;

   subssh.hgtX_ = dbkey.getSliceRef(-4, 4);
   subssh.unserializeDBValue(ldbIter.getValueReader());
   return true;
}


////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::getStoredScriptHistoryByRawScript(
                                             StoredScriptHistory & ssh,
                                             BinaryDataRef script) const
{
   BinaryData uniqueKey = BtcUtils::getTxOutScrAddr(script);
   getStoredScriptHistory(ssh, uniqueKey);
}


/////////////////////////////////////////////////////////////////////////////
// This doesn't actually return a SUBhistory, it grabs it and adds it to the
// regular-ssh object.  This does not affect balance or Txio count.  It's 
// simply filling in data that the ssh may be expected to have.  
bool LMDBBlockDatabase::fetchStoredSubHistory( StoredScriptHistory & ssh,
                                            BinaryData hgtX,
                                            bool createIfDNE,
                                            bool forceReadDB)
{
   auto subIter = ssh.subHistMap_.find(hgtX);
   if (!forceReadDB && ITER_IN_MAP(subIter, ssh.subHistMap_))
   {
      return true;
   }

   BinaryData key = ssh.uniqueKey_ + hgtX; 
   BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_SCRIPT, key);

   StoredSubHistory subssh;
   subssh.uniqueKey_ = ssh.uniqueKey_;
   subssh.hgtX_      = hgtX;

   if(brr.getSize() > 0)
      subssh.unserializeDBValue(brr);
   else if(!createIfDNE)
      return false;

   ssh.mergeSubHistory(subssh);
   
   return true;
}


////////////////////////////////////////////////////////////////////////////////
uint64_t LMDBBlockDatabase::getBalanceForScrAddr(BinaryDataRef scrAddr, bool withMulti)
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
bool LMDBBlockDatabase::getFullUTXOMapForSSH( 
                                StoredScriptHistory & ssh,
                                map<BinaryData, UnspentTxOut> & mapToFill,
                                bool withMultisig)
{
   //TODO: deprecate. replace with paged version once new coin control is
   //implemented

   if(!ssh.haveFullHistoryLoaded())
      return false;

   LMDBEnv::Transaction stxotx, hinttx;
   beginDBTransaction(&stxotx, STXO, LMDB::ReadOnly);
   beginDBTransaction(&hinttx, TXHINTS, LMDB::ReadOnly);

   {
      for (const auto& ssPair : ssh.subHistMap_)
      {
         const StoredSubHistory & subSSH = ssPair.second;
         for (const auto& txioPair : subSSH.txioMap_)
         {
            const TxIOPair & txio = txioPair.second;
            if (txio.isUTXO())
            {
               BinaryData txoKey = txio.getDBKeyOfOutput();
               BinaryData txKey = txio.getTxRefOfOutput().getDBKey();
               uint16_t txoIdx = txio.getIndexOfOutput();


               StoredTxOut stxo;
               getStoredTxOut(stxo, txoKey);
               BinaryData txHash = getTxHashForLdbKey(txKey);

               mapToFill[txoKey] = UnspentTxOut(
                  txHash,
                  txoIdx,
                  stxo.blockHeight_,
                  txio.getValue(),
                  stxo.getScriptRef());
            }
         }
      }
   }

   return true;
}

/////////////////////////////////////////////////////////////////////////////
// TODO: We should also read the HeaderHgtList entries to get the blockchain
//       sorting that is saved in the DB.  But right now, I'm not sure what
//       that would get us since we are reading all the headers and doing
//       a fresh organize/sort anyway.
void LMDBBlockDatabase::readAllHeaders(
   const function<void(shared_ptr<BlockHeader>, uint32_t, uint8_t)> &callback
)
{
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, HEADERS, LMDB::ReadOnly);

   LDBIter ldbIter = getIterator(HEADERS);

   if(!ldbIter.seekToStartsWith(DB_PREFIX_HEADHASH))
   {
      LOGWARN << "No headers in DB yet!";
      return;
   }
   
   do
   {
      ldbIter.resetReaders();
      ldbIter.verifyPrefix(DB_PREFIX_HEADHASH);
   
      if(ldbIter.getKeyReader().getSizeRemaining() != 32)
      {
         LOGERR << "How did we get header hash not 32 bytes?";
         continue;
      }

      StoredHeader sbh;
      ldbIter.getKeyReader().get_BinaryData(sbh.thisHash_, 32);

      sbh.unserializeDBValue(HEADERS, ldbIter.getValueRef());

      auto regHead = make_shared<BlockHeader>();

      regHead->unserialize(sbh.dataCopy_);
      regHead->setBlockSize(sbh.numBytes_);
      regHead->setNumTx(sbh.numTx_);

      regHead->setBlockFileNum(sbh.fileID_);
      regHead->setBlockFileOffset(sbh.offset_);
      regHead->setUniqueID(sbh.uniqueID_);

      if (sbh.thisHash_ != regHead->getThisHash())
      {
         LOGWARN << "Corruption detected: block header hash " <<
            sbh.thisHash_.copySwapEndian().toHexStr() << " does not match "
            << regHead->getThisHash().copySwapEndian().toHexStr();
      }
      callback(regHead, sbh.blockHeight_, sbh.duplicateID_);

   } while(ldbIter.advanceAndRead(DB_PREFIX_HEADHASH));
}

////////////////////////////////////////////////////////////////////////////////
uint8_t LMDBBlockDatabase::getValidDupIDForHeight(uint32_t blockHgt) const
{
   auto iter = validDupByHeight_.find(blockHgt);

   if(iter == validDupByHeight_.end())
   {
      LOGERR << "Block height exceeds DupID lookup table";
      return UINT8_MAX;
   }

   return iter->second;
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::setValidDupIDForHeight(uint32_t blockHgt, uint8_t dup,
                                               bool overwrite)
{
   auto iter = validDupByHeight_.find(blockHgt);
   if (iter == validDupByHeight_.end())
      validDupByHeight_[blockHgt] = UINT8_MAX;

   uint8_t& dupid = validDupByHeight_[blockHgt];
   if (!overwrite && dupid != UINT8_MAX)
      return;

   dupid = dup;
}

////////////////////////////////////////////////////////////////////////////////
uint8_t LMDBBlockDatabase::getValidDupIDForHeight_fromDB(uint32_t blockHgt)
{

   BinaryData hgt4((uint8_t*)&blockHgt, 4);
   BinaryRefReader brrHgts = getValueReader(HEADERS, DB_PREFIX_HEADHGT, hgt4);

   if(brrHgts.getSize() == 0)
   {
      LOGERR << "Requested header does not exist in DB";
      return false;
   }

   uint8_t lenEntry = 33;
   uint8_t numDup = (uint8_t)(brrHgts.getSize() / lenEntry);
   for(uint8_t i=0; i<numDup; i++)
   {
      uint8_t dup8 = brrHgts.get_uint8_t(); 
      // BinaryDataRef thisHash = brrHgts.get_BinaryDataRef(lenEntry-1);
      if((dup8 & 0x80) > 0)
         return (dup8 & 0x7f);
   }

   LOGERR << "Requested a header-by-height but none were marked as main";
   return UINT8_MAX;
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredDBInfo(
   DB_SELECT db, StoredDBInfo const & sdbi, uint32_t id)
{
   SCOPED_TIMER("putStoredDBInfo");
   if (!sdbi.isInitialized())
      throw runtime_error("tried to write uninitiliazed sdbi");

   putValue(db, StoredDBInfo::getDBKey(id), serializeDBValue(sdbi));
}

////////////////////////////////////////////////////////////////////////////////
StoredDBInfo LMDBBlockDatabase::getStoredDBInfo(DB_SELECT db, uint32_t id)
{
   SCOPED_TIMER("getStoredDBInfo");
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, db, LMDB::ReadOnly);

   auto&& key = StoredDBInfo::getDBKey(id);
   BinaryRefReader brr = getValueRef(db, key.getRef());

   if (brr.getSize() == 0)
      throw runtime_error("no sdbi at this key");

   StoredDBInfo sdbi;
   sdbi.unserializeDBValue(brr);
   return sdbi;
}

////////////////////////////////////////////////////////////////////////////////
// Puts bare header into HEADERS DB.  Use "putStoredHeader" to add to both
// (which actually calls this method as the first step)
//
// Returns the duplicateID of the header just inserted
uint8_t LMDBBlockDatabase::putBareHeader(StoredHeader & sbh, bool updateDupID,
   bool updateSDBI)
{
   SCOPED_TIMER("putBareHeader");

   if(!sbh.isInitialized())
   {
      LOGERR << "Attempting to put uninitialized bare header into DB";
      return UINT8_MAX;
   }
   
   if (sbh.blockHeight_ == UINT32_MAX)
   {
      throw runtime_error("Attempted to put a header with no height");
   }

   // Batch the two operations to make sure they both hit the DB, or neither 
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, HEADERS, LMDB::ReadWrite);

   auto&& sdbiH = getStoredDBInfo(HEADERS, 0);


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
            if(hhl.preferredDup_ != dup && sbh.isMainBranch_ && updateDupID)
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
         if(sbh.isMainBranch_ && updateDupID)
            hhl.preferredDup_ = sbhDupID;
      }
   }

   sbh.setKeyData(height, sbhDupID);
   

   if(needToWriteHHL)
      putStoredHeadHgtList(hhl);
      
   // Overwrite the existing hash-indexed entry, just in case the dupID was
   // not known when previously written.  
   putValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_,
      serializeDBValue(sbh, HEADERS, armoryDbType_));

   // If this block is valid, update quick lookup table, and store it in DBInfo
   if(sbh.isMainBranch_)
   {
      setValidDupIDForHeight(sbh.blockHeight_, sbh.duplicateID_, updateDupID);
      if (updateSDBI)
      {
         sdbiH = move(getStoredDBInfo(HEADERS, 0));
         if (sbh.blockHeight_ >= sdbiH.topBlkHgt_)
         {
            sdbiH.topBlkHgt_ = sbh.blockHeight_;
            putStoredDBInfo(HEADERS, sdbiH, 0);
         }
      }
   }
   return sbhDupID;
}

////////////////////////////////////////////////////////////////////////////////
// "BareHeader" refers to 
bool LMDBBlockDatabase::getBareHeader(StoredHeader & sbh, 
                                   uint32_t blockHgt, 
                                   uint8_t dup) const
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
bool LMDBBlockDatabase::getBareHeader(
   StoredHeader & sbh, uint32_t blockHgt) const
{
   SCOPED_TIMER("getBareHeader(duplookup)");

   uint8_t dupID = getValidDupIDForHeight(blockHgt);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHgt; 

   return getBareHeader(sbh, blockHgt, dupID);
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getBareHeader(
   StoredHeader & sbh, BinaryDataRef headHash) const
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
void LMDBBlockDatabase::updateStoredTx(StoredTx & stx)
{
   // Add the individual TxOut entries if requested

   uint32_t version = READ_UINT32_LE(stx.dataCopy_.getPtr());

   for (auto& stxo : stx.stxoMap_)
   {      // Make sure all the parameters of the TxOut are set right 
      stxo.second.txVersion_ = version;
      stxo.second.blockHeight_ = stx.blockHeight_;
      stxo.second.duplicateID_ = stx.duplicateID_;
      stxo.second.txIndex_ = stx.txIndex_;
      stxo.second.txOutIndex_ = stxo.first;
      putStoredTxOut(stxo.second);
   }
}


////////////////////////////////////////////////////////////////////////////////
// This assumes that this new tx is "preferred" and will update the list as such
void LMDBBlockDatabase::putStoredTx( StoredTx & stx, bool withTxOut)
{
   if (armoryDbType_ != ARMORY_DB_SUPER)
   {
      LOGERR << "putStoredTx is only meant for Supernode";
      throw runtime_error("mismatch dbType with putStoredTx");
   }

   SCOPED_TIMER("putStoredTx");
   BinaryData ldbKey = DBUtils::getBlkDataKeyNoPrefix(stx.blockHeight_, 
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

   if(needToAddTxToHints || needToUpdateHints)
      putStoredTxHints(sths);

   // Now add the base Tx entry in the BLKDATA DB.
   BinaryWriter bw;
   stx.serializeDBValue(bw, armoryDbType_);
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
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredZC(StoredTx & stx, const BinaryData& zcKey)
{
   SCOPED_TIMER("putStoredTx");

   DB_SELECT dbs = ZERO_CONF;

   // Now add the base Tx entry in the BLKDATA DB.
   BinaryWriter bw;
   stx.serializeDBValue(bw, armoryDbType_);
   bw.put_uint32_t(stx.unixTime_);
   putValue(dbs, DB_PREFIX_ZCDATA, zcKey, bw.getDataRef());


   // Add the individual TxOut entries
   {
      map<uint16_t, StoredTxOut>::iterator iter;
      for (iter = stx.stxoMap_.begin();
         iter != stx.stxoMap_.end();
         iter++)
      {
         // Make sure all the parameters of the TxOut are set right 
         iter->second.txVersion_ = READ_UINT32_LE(stx.dataCopy_.getPtr());
         //iter->second.blockHeight_ = stx.blockHeight_;
         //iter->second.duplicateID_ = stx.duplicateID_;
         iter->second.txIndex_ = stx.txIndex_;
         iter->second.txOutIndex_ = iter->first;
         BinaryData zcStxoKey(zcKey);
         zcStxoKey.append(WRITE_UINT16_BE(iter->second.txOutIndex_));
         putStoredZcTxOut(iter->second, zcStxoKey);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::updatePreferredTxHint( BinaryDataRef hashOrPrefix,
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
Tx LMDBBlockDatabase::getFullTxCopy(BinaryData ldbKey6B) const
{
   unsigned height;
   uint8_t dup;
   uint16_t txid;

   if (ldbKey6B.getSize() == 6)
   {
      BinaryRefReader brr(ldbKey6B);
      DBUtils::readBlkDataKeyNoPrefix(brr, height, dup, txid);
   }
   else if (ldbKey6B.getSize() == 7)
   {
      BinaryRefReader brr(ldbKey6B);
      DBUtils::readBlkDataKey(brr, height, dup, txid);
   }
   else
   {
      LOGERR << "invalid key length";
      throw runtime_error("invalid key length");
   }
   
   shared_ptr<BlockHeader> header;
   if (armoryDbType_ != ARMORY_DB_SUPER)
      header = blockchainPtr_->getHeaderByHeight(height);
   else
      header = blockchainPtr_->getHeaderById(height);

   return getFullTxCopy(txid, header);
}

////////////////////////////////////////////////////////////////////////////////
Tx LMDBBlockDatabase::getFullTxCopy( uint32_t hgt, uint16_t txIndex) const
{
   SCOPED_TIMER("getFullTxCopy");
   uint8_t dup = getValidDupIDForHeight(hgt);
   if(dup == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << hgt;

   BinaryData ldbKey = DBUtils::getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}

////////////////////////////////////////////////////////////////////////////////
Tx LMDBBlockDatabase::getFullTxCopy( 
   uint32_t hgt, uint8_t dup, uint16_t txIndex) const
{
   SCOPED_TIMER("getFullTxCopy");
   BinaryData ldbKey = DBUtils::getBlkDataKey(hgt, dup, txIndex);
   return getFullTxCopy(ldbKey);
}

////////////////////////////////////////////////////////////////////////////////
Tx LMDBBlockDatabase::getFullTxCopy(
   uint16_t txIndex, shared_ptr<BlockHeader> bhPtr) const
{
   if (bhPtr == nullptr)
      throw runtime_error("null bhPtr");

   if (txIndex >= bhPtr->getNumTx())
      throw range_error("txid > numTx");

   if (blkFolder_.size() == 0)
      throw runtime_error("invalid blkFolder");

   //open block file
   BlockDataLoader bdl(blkFolder_);

   auto fileMapPtr = bdl.get(bhPtr->getBlockFileNum());
   auto dataPtr = fileMapPtr->getPtr();

   auto getID = [bhPtr]
      (const BinaryData&)->uint32_t {return bhPtr->getThisID(); };

   BlockData block;
   block.deserialize(dataPtr + bhPtr->getOffset(),
      bhPtr->getBlockSize(), bhPtr, getID, false, false);

   auto bctx = block.getTxns()[txIndex];

   BinaryRefReader brr(bctx->data_, bctx->size_);

   return Tx(brr);
}


////////////////////////////////////////////////////////////////////////////////
TxOut LMDBBlockDatabase::getTxOutCopy( 
   BinaryData ldbKey6B, uint16_t txOutIdx) const
{
   SCOPED_TIMER("getTxOutCopy");
   BinaryWriter bw(8);
   bw.put_BinaryData(ldbKey6B);
   bw.put_uint16_t(txOutIdx, BE);
   BinaryDataRef ldbKey8 = bw.getDataRef();

   TxOut txoOut;

   BinaryRefReader brr;
   if (!ldbKey6B.startsWith(ZCprefix_))
   {
      if (armoryDbType_ == ARMORY_DB_SUPER)
      {
         BinaryRefReader brr_key(ldbKey6B);
         unsigned block;
         uint8_t dup;
         uint16_t txid;
         DBUtils::readBlkDataKeyNoPrefix(brr_key, block, dup, txid);

         auto header = blockchainPtr_->getHeaderByHeight(block);
         auto&& key_super = DBUtils::getBlkDataKeyNoPrefix(
            header->getThisID(), 0xFF, txid, txOutIdx);
         brr = getValueReader(STXO, key_super);

         if (brr.getSize() == 0)
         {
            LOGERR << "TxOut key does not exist in BLKDATA DB";
            return TxOut();
         }

         StoredTxOut stxo;
         stxo.unserializeDBValue(brr.getRawRef());
         auto&& txout_raw = stxo.getSerializedTxOut();
         TxRef txref(ldbKey6B);
         txoOut.unserialize(txout_raw, txout_raw.getSize(), txref, txOutIdx);
         return txoOut;
      }
      else
      {
         brr = getValueReader(STXO, DB_PREFIX_TXDATA, ldbKey8);
      }
   }
   else
   {
      LMDBEnv::Transaction zctx;
      beginDBTransaction(&zctx, ZERO_CONF, LMDB::ReadOnly);
      brr = getValueReader(ZERO_CONF, DB_PREFIX_ZCDATA, ldbKey8);
   }

   if(brr.getSize()==0) 
   {
      LOGERR << "TxOut key does not exist in BLKDATA DB";
      return TxOut();
   }

   TxRef parent(ldbKey6B);

   brr.advance(2);
   txoOut.unserialize_checked(
      brr.getCurrPtr(), brr.getSizeRemaining(), 0, parent, (uint32_t)txOutIdx);
   return txoOut;
}


////////////////////////////////////////////////////////////////////////////////
TxIn LMDBBlockDatabase::getTxInCopy( 
   BinaryData ldbKey6B, uint16_t txInIdx) const
{
   SCOPED_TIMER("getTxInCopy");

   if (armoryDbType_ == ARMORY_DB_SUPER)
   {
      TxIn txiOut;
      BinaryRefReader brr = getValueReader(BLKDATA, DB_PREFIX_TXDATA, ldbKey6B);
      if (brr.getSize() == 0)
      {
         LOGERR << "TxOut key does not exist in BLKDATA DB";
         return TxIn();
      }

      BitUnpacker<uint16_t> bitunpack(brr); // flags
      uint16_t dbVer = bitunpack.getBits(4);
      (void)dbVer;
      uint16_t txVer = bitunpack.getBits(2);
      (void)txVer;
      uint16_t txSer = bitunpack.getBits(4);

      brr.advance(32);


      if (txSer != TX_SER_FULL && txSer != TX_SER_FRAGGED)
      {
         LOGERR << "Tx not available to retrieve TxIn";
         return TxIn();
      }
      else
      {
         bool isFragged = txSer == TX_SER_FRAGGED;
         vector<size_t> offsetsIn;
         BtcUtils::StoredTxCalcLength(brr.getCurrPtr(), 
            brr.getSize(), isFragged, &offsetsIn, nullptr, nullptr);
         if ((uint32_t)(offsetsIn.size() - 1) < (uint32_t)(txInIdx + 1))
         {
            LOGERR << "Requested TxIn with index greater than numTxIn";
            return TxIn();
         }
         TxRef parent(ldbKey6B);
         uint8_t const * txInStart = brr.exposeDataPtr() + 34 + offsetsIn[txInIdx];
         uint32_t txInLength = offsetsIn[txInIdx + 1] - offsetsIn[txInIdx];
         TxIn txin;
         txin.unserialize_checked(txInStart, brr.getSize() - 34 - offsetsIn[txInIdx], txInLength, parent, txInIdx);
         return txin;
      }
   }
   else
   {
      Tx thisTx = getFullTxCopy(ldbKey6B);
      return thisTx.getTxInCopy(txInIdx);
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData LMDBBlockDatabase::getTxHashForLdbKey(BinaryDataRef ldbKey6B) const
{
   if (!ldbKey6B.startsWith(ZCprefix_))
   {
      if (armoryDbType_ != ARMORY_DB_SUPER)
      {
         LMDBEnv::Transaction tx(dbEnv_[TXHINTS].get(), LMDB::ReadOnly);
         BinaryData keyFull(ldbKey6B.getSize() + 1);
         keyFull[0] = (uint8_t)DB_PREFIX_TXDATA;
         ldbKey6B.copyTo(keyFull.getPtr() + 1, ldbKey6B.getSize());

         BinaryDataRef txData = getValueNoCopy(TXHINTS, keyFull);

         if (txData.getSize() >= 36)
         {
            return txData.getSliceRef(4, 32);
         }
      }
      else
      {
         //convert height to id
         unsigned height;
         uint8_t dup;
         uint16_t txid;
         BinaryRefReader brr(ldbKey6B);

         DBUtils::readBlkDataKeyNoPrefix(brr, height, dup, txid);
         
         unsigned block_id = height;
         if (dup != 0x7F)
         {
            try
            {
               auto header = blockchainPtr_->getHeaderByHeight(height);
               block_id = header->getThisID();
            }
            catch (exception&)
            {
               LOGWARN << "failed to grab header while resolving txhash";
               return BinaryData();
            }
         }

         auto&& id_key = DBUtils::getBlkDataKeyNoPrefix(
            block_id, 0xFF, txid, 0);

         //get stxo at this key
         LMDBEnv::Transaction tx(dbEnv_[STXO].get(), LMDB::ReadOnly);
         auto data = getValueNoCopy(STXO, id_key);
         if (data.getSize() == 0)
            return BinaryData();

         StoredTxOut stxo;
         stxo.unserializeDBValue(data);
         return stxo.parentHash_;
      }
   }
   else
   {
      LMDBEnv::Transaction tx(dbEnv_[ZERO_CONF].get(), LMDB::ReadOnly);
      BinaryRefReader stxVal =
         getValueReader(ZERO_CONF, DB_PREFIX_ZCDATA, ldbKey6B);

      if (stxVal.getSize() == 0)
      {
         LOGERR << "TxRef key does not exist in BLKDATA DB";
         return BinaryData(0);
      }

      // We can't get here unless we found the precise Tx entry we were looking for
      stxVal.advance(4);
      return stxVal.get_BinaryData(32);
   }

   return BinaryData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData LMDBBlockDatabase::getTxHashForHeightAndIndex( uint32_t height,
                                                       uint16_t txIndex)
{
   SCOPED_TIMER("getTxHashForHeightAndIndex");
   uint8_t dup = getValidDupIDForHeight(height);
   if(dup == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << height;
   return getTxHashForLdbKey(DBUtils::getBlkDataKeyNoPrefix(height, dup, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
BinaryData LMDBBlockDatabase::getTxHashForHeightAndIndex( uint32_t height,
                                                       uint8_t  dupID,
                                                       uint16_t txIndex)
{
   SCOPED_TIMER("getTxHashForHeightAndIndex");
   return getTxHashForLdbKey(DBUtils::getBlkDataKeyNoPrefix(height, dupID, txIndex));
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredHeader(
   StoredHeader& sbh, uint32_t height, uint8_t dupId, bool withTx) const
{
   try
   {
      if (blkFolder_.size() == 0)
         throw runtime_error("invalid blkFolder");

      auto bh = blockchainPtr_->getHeaderByHeight(height);
      if (bh->getDuplicateID() != dupId)
         throw runtime_error("invalid dupId");

      //open block file
      BlockDataLoader bdl(blkFolder_);

      auto fileMapPtr = bdl.get(bh->getBlockFileNum());
      auto dataPtr = fileMapPtr->getPtr();
      BinaryRefReader brr(dataPtr + bh->getOffset(), bh->getBlockSize());

      if (withTx)
         sbh.unserializeFullBlock(brr, false, false);
      else
         sbh.unserializeSimple(brr);
   }
   catch (...)
   {
      return false;
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTx( StoredTx & stx,
                                  BinaryData& txHashOrDBKey) const
{
   uint32_t sz = txHashOrDBKey.getSize();
   if(sz == 32)
      return getStoredTx_byHash(txHashOrDBKey, &stx);
   else if(sz == 6 || sz == 7)
      return getStoredTx_byDBKey(stx, txHashOrDBKey);
   else
   {
      LOGERR << "Unrecognized input string: " << txHashOrDBKey.toHexStr();
      return false;
   }
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTx_byDBKey( StoredTx & stx,
                                          BinaryDataRef dbKey) const
{
   uint32_t hgt;
   uint8_t  dup;
   uint16_t txi;

   BinaryRefReader brrKey(dbKey);

   if(dbKey.getSize() == 6)
      DBUtils::readBlkDataKeyNoPrefix(brrKey, hgt, dup, txi);
   else if(dbKey.getSize() == 7)
      DBUtils::readBlkDataKey(brrKey, hgt, dup, txi);
   else
   {
      LOGERR << "Unrecognized input string: " << dbKey.toHexStr();
      return false;
   }

   return getStoredTx(stx, hgt, dup, txi, true);
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredZcTx(StoredTx & stx,
   BinaryDataRef zcKey) const
{
   auto dbs = ZERO_CONF;
   
   //only by zcKey
   BinaryData zcDbKey;

   if (zcKey.getSize() == 6)
   {
      zcDbKey = BinaryData(7);
      uint8_t* ptr = zcDbKey.getPtr();
      ptr[0] = DB_PREFIX_ZCDATA;
      memcpy(ptr + 1, zcKey.getPtr(), 6);
   }
   else
      zcDbKey = zcKey;

   LDBIter ldbIter = getIterator(dbs);
   if (!ldbIter.seekToExact(zcDbKey))
   {
      LOGERR << "BLKDATA DB does not have the requested ZC tx";
      LOGERR << "(" << zcKey.toHexStr() << ")";
      return false;
   }

   size_t nbytes = 0;
   do
   {
      // Stop if key doesn't start with [PREFIX | ZCkey | TXIDX]
      if(!ldbIter.checkKeyStartsWith(zcDbKey))
         break;


      // Read the prefix, height and dup 
      uint16_t txOutIdx;
      BinaryRefReader txKey = ldbIter.getKeyReader();

      // Now actually process the iter value
      if(txKey.getSize()==7)
      {
         // Get everything else from the iter value
         stx.unserializeDBValue(ldbIter.getValueRef());
         nbytes += stx.dataCopy_.getSize();
      }
      else if(txKey.getSize() == 9)
      {
         txOutIdx = READ_UINT16_BE(ldbIter.getKeyRef().getSliceRef(7, 2));
         StoredTxOut & stxo = stx.stxoMap_[txOutIdx];
         stxo.unserializeDBValue(ldbIter.getValueRef());
         stxo.parentHash_ = stx.thisHash_;
         stxo.txVersion_  = stx.version_;
         stxo.txOutIndex_ = txOutIdx;
         nbytes += stxo.dataCopy_.getSize();
      }
      else
      {
         LOGERR << "Unexpected BLKDATA entry while iterating";
         return false;
      }

   } while(ldbIter.advanceAndRead(DB_PREFIX_ZCDATA));


   stx.numBytes_ = stx.haveAllTxOut() ? nbytes : UINT32_MAX;

   return true;
}

////////////////////////////////////////////////////////////////////////////////
// We assume that the first TxHint that matches is correct.  This means that 
// when we mark a transaction/block valid, we need to make sure all the hints
// lists have the correct one in front.  Luckily, the TXHINTS entries are tiny 
// and the number of modifications to make for each reorg is small.
bool LMDBBlockDatabase::getStoredTx_byHash(const BinaryData& txHash,
                                           StoredTx* stx) const
{
   if (stx == nullptr)
      return false;

   auto&& dbKey = getDBKeyForHash(txHash);
   if (dbKey.getSize() == 0)
      return false;

   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, STXO, LMDB::ReadOnly);
   return getStoredTx_byDBKey(*stx, dbKey);
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTx( StoredTx & stx,
                                  uint32_t blockHeight,
                                  uint16_t txIndex,
                                  bool withTxOut) const
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTx(stx, blockHeight, dupID, txIndex, withTxOut);

}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTx( StoredTx & stx,
                                  uint32_t blockHeight,
                                  uint8_t  dupID,
                                  uint16_t txIndex,
                                  bool withTxOut) const
{
   SCOPED_TIMER("getStoredTx");

   BinaryData blkDataKey = DBUtils::getBlkDataKey(blockHeight, dupID, txIndex);
   stx.blockHeight_ = blockHeight;
   stx.duplicateID_  = dupID;
   stx.txIndex_     = txIndex;

   auto&& theTx = getFullTxCopy(blkDataKey);
   stx.createFromTx(theTx, false, withTxOut);

   return true;
}



////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putStoredTxOut( StoredTxOut const & stxo)
{
    
   SCOPED_TIMER("putStoredTx");

   BinaryData ldbKey = stxo.getDBKey(false);
   BinaryData bw = serializeDBValue(stxo, armoryDbType_);
   putValue(STXO, DB_PREFIX_TXDATA, ldbKey, bw);
}

void LMDBBlockDatabase::putStoredZcTxOut(StoredTxOut const & stxo, 
   const BinaryData& zcKey)
{
   SCOPED_TIMER("putStoredTx");

   BinaryData bw = serializeDBValue(stxo, armoryDbType_);
   putValue(ZERO_CONF, DB_PREFIX_ZCDATA, zcKey, bw);
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTxOut(
   StoredTxOut & stxo, const BinaryData& txHash, uint16_t txoutid) const
{
   if (armoryDbType_ != ARMORY_DB_SUPER)
      throw runtime_error("supernode only call");

   //grab hints
   StoredTxHints txhints;
   if (!getStoredTxHints(txhints, txHash.getRef()))
      return false;

   for (auto hint : txhints.dbKeyList_)
   {
      BinaryRefReader brrHint(hint);
      unsigned id;
      uint8_t dup;
      uint16_t txIdx;
      BLKDATA_TYPE bdtype = DBUtils::readBlkDataKeyNoPrefix(
         brrHint, id, dup, txIdx);

      //grab header
      auto header = blockchainPtr_->getHeaderById(id);

      //grab tx
      auto&& theTx = getFullTxCopy(txIdx, header);
      if (theTx.getThisHash() != txHash)
         continue;

      //grab txout
      auto txOutOffset = theTx.getTxOutOffset(txoutid);

      //grab dataref
      BinaryDataRef tx_bdr(theTx.getPtr(), theTx.getSize());
      BinaryRefReader brr(tx_bdr);
      brr.advance(txOutOffset);

      //convert to stxo
      stxo.unserialize(brr);
      stxo.parentHash_ = theTx.getThisHash();
      stxo.blockHeight_ = header->getBlockHeight();
      stxo.duplicateID_ = header->getDuplicateID();
      stxo.txIndex_ = txIdx;
      stxo.txOutIndex_ = txoutid;
      stxo.isCoinbase_ = (txIdx == 0);

      return true;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTxOut(
   StoredTxOut & stxo, const BinaryData& DBkey) const
{
   if (DBkey.getSize() != 8)
   {
      LOGERR << "Tried to get StoredTxOut, but the provided key is not of the "
         "proper size. Expect size is 8, this key is: " << DBkey.getSize();
      return false;
   }

   //Let's look in the db first. Stxos are fetched mostly to spend coins,
   //so there is a high chance we wont need to pull the stxo from the raw
   //block, since fullnode keeps track of all relevant stxos

   if (armoryDbType_ != ARMORY_DB_SUPER)
   {
      LMDBEnv::Transaction tx(dbEnv_[STXO].get(), LMDB::ReadOnly);
      BinaryRefReader brr = getValueReader(STXO, DB_PREFIX_TXDATA, DBkey);

      if (brr.getSize() > 0)
      {
         stxo.blockHeight_ = DBUtils::hgtxToHeight(DBkey.getSliceRef(0, 4));
         stxo.duplicateID_ = DBUtils::hgtxToDupID(DBkey.getSliceRef(0, 4));
         stxo.txIndex_ = READ_UINT16_BE(DBkey.getSliceRef(4, 2));
         stxo.txOutIndex_ = READ_UINT16_BE(DBkey.getSliceRef(6, 2));

         stxo.unserializeDBValue(brr);
         return true;
      }
   }
   else
   {
      unsigned id;
      uint8_t dup;
      uint16_t txIdx, txoutid;

      BinaryRefReader txout_key(DBkey);
      DBUtils::readBlkDataKeyNoPrefix(txout_key, id, dup, txIdx, txoutid);

      if (dup != 0x7F)
      {
         LOGINFO << "need id in block key, got height";
         throw runtime_error("unexpected block key format");
      }

      //grab header
      auto header = blockchainPtr_->getHeaderById(id);

      //grab tx
      auto&& theTx = getFullTxCopy(txIdx, header);

      //grab txout
      auto txOutOffset = theTx.getTxOutOffset(txoutid);

      //grab dataref
      BinaryDataRef tx_bdr(theTx.getPtr(), theTx.getSize());
      BinaryRefReader brr(tx_bdr);
      brr.advance(txOutOffset);

      //convert to stxo
      stxo.unserialize(brr);
      stxo.parentHash_ = theTx.getThisHash();
      stxo.blockHeight_ = header->getBlockHeight();
      stxo.duplicateID_ = header->getDuplicateID();
      stxo.txIndex_ = txIdx;
      stxo.txOutIndex_ = txoutid;
      stxo.isCoinbase_ = (txIdx == 0);

      return true;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint8_t  dupID,
                              uint16_t txIndex,
                              uint16_t txOutIndex) const
{
   SCOPED_TIMER("getStoredTxOut");
   BinaryData blkKey = DBUtils::getBlkDataKeyNoPrefix(
      blockHeight, dupID, txIndex, txOutIndex);
   return getStoredTxOut(stxo, blkKey);
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTxOut(      
                              StoredTxOut & stxo,
                              uint32_t blockHeight,
                              uint16_t txIndex,
                              uint16_t txOutIndex) const
{
   uint8_t dupID = getValidDupIDForHeight(blockHeight);
   if(dupID == UINT8_MAX)
      LOGERR << "Headers DB has no block at height: " << blockHeight; 

   return getStoredTxOut(stxo, blockHeight, dupID, txIndex, txOutIndex);
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::getUTXOflags(map<BinaryData, StoredSubHistory>&
   subSshMap) const
{
   LMDBEnv::Transaction tx;
   if (armoryDbType_ != ARMORY_DB_SUPER)
      beginDBTransaction(&tx, STXO, LMDB::ReadOnly);
   else
      beginDBTransaction(&tx, SPENTNESS, LMDB::ReadOnly);

   for (auto& subssh : subSshMap)
      getUTXOflags(subssh.second);
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::getUTXOflags(StoredSubHistory& subssh) const
{
   for (auto& txioPair : subssh.txioMap_)
   {
      auto& txio = txioPair.second;

      txio.setUTXO(false);
      if (txio.hasTxIn())
         continue;

      auto&& stxoKey = txio.getDBKeyOfOutput();
      
      if (armoryDbType_ != ARMORY_DB_SUPER)
      {
         StoredTxOut stxo;
         if (!getStoredTxOut(stxo, stxoKey))
            continue;

         if (stxo.spentness_ == TXOUT_UNSPENT)
            txio.setUTXO(true);
      }
      else
      {
         auto value = getValueNoCopy(SPENTNESS, stxoKey);
         if (value.getSize() == 0)
            txio.setUTXO(true);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::putStoredTxHints(StoredTxHints const & sths)
{
   SCOPED_TIMER("putStoredTxHints");
   if(sths.txHashPrefix_.getSize()==0)
   {
      LOGERR << "STHS does have a set prefix, so cannot be put into DB";
      return false;
   }

   putValue(getDbSelect(TXHINTS), sths.getDBKey(), sths.serializeDBValue());

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredTxHints(StoredTxHints & sths, 
                                      BinaryDataRef hashPrefix) const
{
   if(hashPrefix.getSize() < 4)
   {
      LOGERR << "Cannot get hints without at least 4-byte prefix";
      return false;
   }
   BinaryDataRef prefix4 = hashPrefix.getSliceRef(0,4);
   sths.txHashPrefix_ = prefix4.copy();

   BinaryDataRef bdr;
   bdr = getValueRef(getDbSelect(TXHINTS), DB_PREFIX_TXHINTS, prefix4);

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
bool LMDBBlockDatabase::putStoredHeadHgtList(StoredHeadHgtList const & hhl)
{
   SCOPED_TIMER("putStoredHeadHgtList");

   if(hhl.height_ == UINT32_MAX)
   {
      LOGERR << "HHL does not have a valid height to be put into DB";
      return false;
   }

   putValue(getDbSelect(HEADERS), hhl.getDBKey(), hhl.serializeDBValue());
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::getStoredHeadHgtList(
   StoredHeadHgtList & hhl, uint32_t height) const
{
   BinaryData ldbKey = WRITE_UINT32_BE(height);
   BinaryDataRef bdr = getValueRef(getDbSelect(HEADERS), DB_PREFIX_HEADHGT, ldbKey);

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
TxRef LMDBBlockDatabase::getTxRef(BinaryDataRef txHash)
{
   auto&& key = getDBKeyForHash(txHash);
   if (key.getSize() == 6)
      return TxRef(key);

   return TxRef();
}

////////////////////////////////////////////////////////////////////////////////
TxRef LMDBBlockDatabase::getTxRef(BinaryData hgtx, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(hgtx);
   bw.put_uint16_t(txIndex, BE);
   return TxRef(bw.getDataRef());
}

////////////////////////////////////////////////////////////////////////////////
TxRef LMDBBlockDatabase::getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex)
{
   BinaryWriter bw;
   bw.put_BinaryData(DBUtils::heightAndDupToHgtx(hgt,dup));
   bw.put_uint16_t(txIndex, BE);
   return TxRef(bw.getDataRef());
}

////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::markBlockHeaderValid(BinaryDataRef headHash)
{
   SCOPED_TIMER("markBlockHeaderValid");
   BinaryRefReader brr = getValueReader(HEADERS, DB_PREFIX_HEADHASH, headHash);
   if(brr.getSize()==0)
   {
      LOGERR << "Invalid header hash: " << headHash.copy().copySwapEndian().toHexStr();
      return false;
   }
   brr.advance(HEADER_SIZE);
   BinaryData hgtx   = brr.get_BinaryData(4);
   uint32_t   height = DBUtils::hgtxToHeight(hgtx);
   uint8_t    dup    = DBUtils::hgtxToDupID(hgtx);

   return markBlockHeaderValid(height, dup);
}




////////////////////////////////////////////////////////////////////////////////
bool LMDBBlockDatabase::markBlockHeaderValid(uint32_t height, uint8_t dup)
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

//Dropped this behavior starting 0.93
bool LMDBBlockDatabase::markTxEntryValid(uint32_t height,
                                      uint8_t  dupID,
                                      uint16_t txIndex)
{
   SCOPED_TIMER("markTxEntryValid");
   BinaryData blkDataKey = DBUtils::getBlkDataKeyNoPrefix(height, dupID, txIndex);
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
KVLIST LMDBBlockDatabase::getAllDatabaseEntries(DB_SELECT db)
{
   SCOPED_TIMER("getAllDatabaseEntries");
   
   if(!databasesAreOpen())
      return KVLIST();

   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, db, LMDB::ReadOnly);

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
void LMDBBlockDatabase::printAllDatabaseEntries(DB_SELECT db)
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
void LMDBBlockDatabase::pprintBlkDataDB(uint32_t indent)
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
            // New ssh object, base entry
            ssh.unserializeDBKey(key); 
            ssh.unserializeDBValue(val); 
            ssh.pprintFullSSH(indent + 3); 
            lastSSH = key;
         }
         else
         {
            // This is a sub-history for the previous ssh
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

////////////////////////////////////////////////////////////////////////////////
map<uint32_t, uint32_t> LMDBBlockDatabase::getSSHSummary(BinaryDataRef scrAddrStr,
   uint32_t endBlock)
{
   SCOPED_TIMER("getSSHSummary");

   map<uint32_t, uint32_t> SSHsummary;

   LDBIter ldbIter = getIterator(SSH);

   if (!ldbIter.seekToExact(DB_PREFIX_SCRIPT, scrAddrStr))
      return SSHsummary;

   StoredScriptHistory ssh;
   BinaryDataRef sshKey = ldbIter.getKeyRef();
   ssh.unserializeDBKey(sshKey, true);
   ssh.unserializeDBValue(ldbIter.getValueReader());

   return ssh.subsshSummary_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t LMDBBlockDatabase::getStxoCountForTx(const BinaryData & dbKey6) const
{
   if (dbKey6.getSize() != 6)
   {
      LOGERR << "wrong key size";
      return UINT32_MAX;
   }

   if (!dbKey6.startsWith(ZCprefix_))
   {
      if (armoryDbType_ != ARMORY_DB_SUPER)
      {
         LMDBEnv::Transaction tx;
         beginDBTransaction(&tx, TXHINTS, LMDB::ReadOnly);

         BinaryRefReader brr = getValueRef(TXHINTS, DB_PREFIX_TXDATA, dbKey6);
         if (brr.getSize() == 0)
         {
            LOGERR << "no Tx data at key";
            return UINT32_MAX;
         }

         return brr.get_uint32_t();
      }
      else
      {
         LMDBEnv::Transaction tx;
         beginDBTransaction(&tx, STXO, LMDB::ReadOnly);

         //convert height to id
         unsigned height;
         uint8_t dup;
         uint16_t txid;

         BinaryRefReader brr(dbKey6.getRef());
         DBUtils::readBlkDataKeyNoPrefix(brr, height, dup, txid);

         auto header = blockchainPtr_->getHeaderByHeight(height);
         auto id = header->getThisID();

         auto&& id_key = DBUtils::getBlkDataKeyNoPrefix(id, 0xFF, txid);
         auto data = getValueNoCopy(STXO, id_key);

         BinaryRefReader data_brr(data);
         return data_brr.get_var_int();
      }
   }
   else
   {
      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, ZERO_CONF, LMDB::ReadOnly);

      StoredTx stx;
      if (!getStoredZcTx(stx, dbKey6))
      {
         LOGERR << "no Tx data at key";
         return UINT32_MAX;
      }

      return stx.stxoMap_.size();
   }

   return UINT32_MAX;
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::resetHistoryForAddressVector(
   const vector<BinaryData>& addrVec)
{
   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, SSH, LMDB::ReadWrite);

   for (auto& addr : addrVec)
   {
      if (addr.getSize() == 0)
         continue;

      BinaryData addrWithPrefix;
      if (addr.getPtr()[0] == DB_PREFIX_SCRIPT)
      {
         addrWithPrefix = addr;
      }
      else
      {
         addrWithPrefix = WRITE_UINT8_LE(DB_PREFIX_SCRIPT);
         addrWithPrefix.append(addr);
      }

      deleteValue(SSH, addrWithPrefix.getRef());
   }
}

////////////////////////////////////////////////////////////////////////////////
StoredDBInfo LMDBBlockDatabase::openDB(DB_SELECT db)
{
   dbEnv_[db] = make_shared<LMDBEnv>();
   dbEnv_[db]->open(getDbPath(db));

   LMDBEnv::Transaction tx(dbEnv_[db].get(), LMDB::ReadWrite);
   dbs_[db].open(dbEnv_[db].get(), getDbName(db));

   StoredDBInfo sdbi;
   try
   {
      sdbi = move(getStoredDBInfo(db, 0));
   }
   catch (runtime_error&)
   {
      // If DB didn't exist yet (dbinfo key is empty), seed it
      sdbi.magic_ = magicBytes_;
      sdbi.metaHash_ = BtcUtils::EmptyHash_;
      sdbi.topBlkHgt_ = 0;
      sdbi.armoryType_ = armoryDbType_;
      putStoredDBInfo(db, sdbi, 0);
   }

   return sdbi;
}

////////////////////////////////////////////////////////////////////////////////
string LMDBBlockDatabase::getDbPath(DB_SELECT db) const
{
   return getDbPath(getDbName(db));
}

////////////////////////////////////////////////////////////////////////////////
string LMDBBlockDatabase::getDbPath(const string& dbName) const
{
   stringstream ss;
   ss << baseDir_ << "/" << dbName;
   return ss.str();
}

////////////////////////////////////////////////////////////////////////////////
string LMDBBlockDatabase::getDbName(DB_SELECT db) const
{
   switch(db)
   {
      case HEADERS:
         return "headers";

      case BLKDATA:
         return "blkdata";

      case HISTORY:
         return "history";

      case TXHINTS:
         return "txhints";

      case SSH:
         return "ssh";

      case SUBSSH:
         return "subssh";

      case STXO:
         return "stxo";

      case ZERO_CONF:
         return "zeroconf";

      case TXFILTERS:
         return "txfilters";

      case SPENTNESS:
         return "spentness";

      default: 
         throw runtime_error("unknown db");
   }

   return "";
}

////////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::closeDB(DB_SELECT db)
{
   dbs_[db].close();
   if (dbEnv_[db] != nullptr)
   {
      dbEnv_[db]->close();
      dbEnv_[db].reset();
   }
}

/////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::resetSSHdb()
{
   map<BinaryData, int> sshKeys;

   {
      //gather keys
      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, SSH, LMDB::ReadOnly);

      auto dbIter = getIterator(SSH);

      while (dbIter.advanceAndRead(DB_PREFIX_SCRIPT))
      {
         StoredScriptHistory ssh;
         ssh.unserializeDBValue(dbIter.getValueRef());

         sshKeys[dbIter.getKeyRef()] = ssh.scanHeight_;
      }
   }

   {
      //reset them

      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, SSH, LMDB::ReadWrite);


      for (auto& sshkey : sshKeys)
      {
         StoredScriptHistory ssh;
         BinaryWriter bw;
         
         ssh.scanHeight_ = sshkey.second;
         ssh.serializeDBValue(bw, ARMORY_DB_FULL);

         putValue(SSH, sshkey.first.getRef(), bw.getDataRef());
      }

      auto&& sdbi = getStoredDBInfo(SSH, 0);
      sdbi.topBlkHgt_ = 0;
      sdbi.topScannedBlkHash_ = BtcUtils::EmptyHash_;
      putStoredDBInfo(SSH, sdbi, 0);
   }
}

/////////////////////////////////////////////////////////////////////////////
void LMDBBlockDatabase::putMissingHashes(
   const set<BinaryData>& hashSet, uint32_t id)
{
   auto&& missingHashesKey = DBUtils::getMissingHashesKey(id);

   BinaryWriter bw;
   bw.put_uint32_t(hashSet.size());
   for (auto& hash : hashSet)
      bw.put_BinaryData(hash);

   putValue(TXFILTERS, missingHashesKey.getRef(), bw.getDataRef());
}

/////////////////////////////////////////////////////////////////////////////
set<BinaryData> LMDBBlockDatabase::getMissingHashes(uint32_t id) const
{
   auto&& missingHashesKey = DBUtils::getMissingHashesKey(id);

   LMDBEnv::Transaction tx;
   beginDBTransaction(&tx, TXFILTERS, LMDB::ReadOnly);

   auto&& rawMissingHashes = getValueNoCopy(TXFILTERS, missingHashesKey);

   BinaryRefReader brr(rawMissingHashes);
   if (brr.getSizeRemaining() < 4)
      throw runtime_error("invalid missing hashes entry");

   set<BinaryData> missingHashesSet;

   auto&& len = brr.get_uint32_t();
   if (rawMissingHashes.getSize() != len * 32 + 4)
      throw runtime_error("missing hashes entry size mismatch");

   for (uint32_t i = 0; i < len; i++)
      missingHashesSet.insert(move(brr.get_BinaryData(32)));

   return missingHashesSet;
}