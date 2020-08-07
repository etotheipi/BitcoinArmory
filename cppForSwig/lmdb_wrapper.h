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

#ifndef _LMDB_WRAPPER_
#define _LMDB_WRAPPER_

#include <list>
#include <vector>
#include "log.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "DbHeader.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"

#include "lmdb/lmdbpp.h"

class Blockchain;

////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
////////////////////////////////////////////////////////////////////////////////

#define STD_READ_OPTS       leveldb::ReadOptions()
#define STD_WRITE_OPTS      leveldb::WriteOptions()

#define KVLIST vector<pair<BinaryData,BinaryData> > 

#define DEFAULT_LDB_BLOCK_SIZE 32*1024

// Use this to create iterators that are intended for bulk scanning
// It's actually that the ReadOptions::fill_cache arg needs to be false
#define BULK_SCAN false

class BlockHeader;
class Tx;
class TxIn;
class TxOut;
class TxRef;
class TxIOPair;
class GlobalDBUtilities;

class StoredHeader;
class StoredTx;
class StoredTxOut;
class StoredScriptHistory;


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// NOTE:  VERY IMPORTANT NOTE ABOUT THE DATABASE STRUCTURE
//
//    Almost everywhere you see integers serialized throughout Bitcoin, is uses
//    little-endian.  This is critical to follow because you are always handling
//    hashes of these serializations, so the byte-ordering matters.
//
// *HOWEVER*:  
//     
//    This database design relies on the natural ordering of database
//    keys which are frequently concatenations of integers.  For instance, each 
//    block is indexed by height, and we expect an iteration over all keys will
//    traverse the blocks in height-order.  BUT THIS DOESN'T WORK IF THE KEYS
//    ARE WRITTEN IN LITTLE-ENDIAN.  Therefore, all serialized integers in 
//    database KEYS are BIG-ENDIAN.  All other serializations in database VALUES
//    are LITTLE-ENDIAN (including var_ints, and all put/get_uintX_t() calls).
//
// *HOWEVER-2*:
//
//    This gets exceptionally confusing because some of the DB VALUES include 
//    references to DB KEYS, thus requiring those specific serializations to be 
//    BE, even though the rest of the data uses LE.
//
// REPEATED:
//
//    Database Keys:    BIG-ENDIAN integers
//    Database Values:  LITTLE-ENDIAN integers
//
//
// How to avoid getting yourself in a mess with this:
//
//    Always use hgtx methods:
//       hgtxToHeight( BinaryData(4) )
//       hgtxToDupID( BinaryData(4) )
//       heightAndDupToHgtx( uint32_t, uint8_t)
//
//    Always use BIGENDIAN for txIndex_ or txOutIndex_ serializations:
//       BinaryWriter.put_uint16_t(txIndex,    BIGENDIAN);
//       BinaryWriter.put_uint16_t(txOutIndex, BIGENDIAN);
//       BinaryReader.get_uint16_t(BIGENDIAN);
//       BinaryReader.get_uint16_t(BIGENDIAN);
//
//
// *OR*  
//
//    Don't mess with the internals of the DB!  The public methods that are
//    used to access the data in the DB externally do not require an 
//    understanding of how the data is actually serialized under the hood.
//
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

class LDBIter
{
public: 

   // fill_cache argument should be false for large bulk scans
   LDBIter(void) { isDirty_=true;}
   LDBIter(LMDB::Iterator&& move);
   LDBIter(LDBIter&& move);
   LDBIter(const LDBIter& cp);
   LDBIter& operator=(LMDB::Iterator&& move);
   LDBIter& operator=(LDBIter&& move);

   bool isNull(void) const { return !iter_.isValid(); }
   bool isValid(void) const { return iter_.isValid(); }
   bool isValid(DB_PREFIX dbpref);

   bool readIterData(void);
   
   bool retreat();
   bool advance(void);
   bool advance(DB_PREFIX prefix);
   bool advanceAndRead(void);
   bool advanceAndRead(DB_PREFIX prefix);

   BinaryData       getKey(void) const;
   BinaryData       getValue(void) const;
   BinaryDataRef    getKeyRef(void) const;
   BinaryDataRef    getValueRef(void) const;
   BinaryRefReader& getKeyReader(void) const;
   BinaryRefReader& getValueReader(void) const;

   // All the seekTo* methods do the exact same thing, the variant simply 
   // determines the meaning of the return true/false value.
   bool seekTo(BinaryDataRef key);
   bool seekTo(DB_PREFIX pref, BinaryDataRef key);
   bool seekToExact(BinaryDataRef key);
   bool seekToExact(DB_PREFIX pref, BinaryDataRef key);
   bool seekToStartsWith(BinaryDataRef key);
   bool seekToStartsWith(DB_PREFIX prefix);
   bool seekToStartsWith(DB_PREFIX pref, BinaryDataRef key);
   bool seekToBefore(BinaryDataRef key);
   bool seekToBefore(DB_PREFIX prefix);
   bool seekToBefore(DB_PREFIX pref, BinaryDataRef key);
   bool seekToFirst(void);

   // Return true if the iterator is currently on valid data, with key match
   bool checkKeyExact(BinaryDataRef key);
   bool checkKeyExact(DB_PREFIX prefix, BinaryDataRef key);
   bool checkKeyStartsWith(BinaryDataRef key);
   bool checkKeyStartsWith(DB_PREFIX prefix, BinaryDataRef key);

   bool verifyPrefix(DB_PREFIX prefix, bool advanceReader=true);

   void resetReaders(void){currKeyReader_.resetPosition();currValueReader_.resetPosition();}

private:

   LMDB::Iterator iter_;

   mutable BinaryDataRef    currKey_;
   mutable BinaryDataRef    currValue_;
   mutable BinaryRefReader  currKeyReader_;
   mutable BinaryRefReader  currValueReader_;
   bool isDirty_;
   
   
};

////////////////////////////////////////////////////////////////////////////////
template<typename T> class TxFilterPool
{
   //16 bytes bucket filter for transactions hash lookup
   //each bucket represents on blk file

private:
   set<TxFilter<T>> pool_;
   const uint8_t* poolPtr_ = nullptr;
   size_t len_ = SIZE_MAX;

public:
   TxFilterPool(void) 
   {}

   TxFilterPool(set<TxFilter<T>> pool) :
      pool_(move(pool)), len_(pool_.size())
   {}

   TxFilterPool(const TxFilterPool<T>& filter) :
      pool_(filter.pool_), len_(filter.len_)
   {}

   TxFilterPool(const uint8_t* ptr, size_t len) :
      poolPtr_(ptr), len_(len)
   {}

   void update(const set<TxFilter<T>>& hashSet)
   {
      pool_.insert(hashSet.begin(), hashSet.end());
      len_ = pool_.size();
   }

   bool isValid(void) const { return len_ != SIZE_MAX; }

   map<uint32_t, set<uint32_t>> compare(const BinaryData& hash) const
   {
      if (hash.getSize() != 32)
         throw runtime_error("hash is 32 bytes long");

      if (!isValid())
         throw runtime_error("invalid pool");

      //get key

      map<uint32_t, set<uint32_t>> returnMap;

      if (pool_.size())
      {
         for (auto& filter : pool_)
         {
            auto&& resultSet = filter.compare(hash);
            if (resultSet.size() > 0)
            {
               returnMap.insert(make_pair(
                  filter.getBlockKey(),
                  move(resultSet)));
            }
         }
      }
      else if (poolPtr_ != nullptr) //running against a pointer
      {
         //get count
         auto size = (uint32_t*)poolPtr_;
         uint32_t* filterSize;
         size_t pos = 4;

         for (uint32_t i = 0; i < *size; i++)
         {
            if (pos >= len_)
               throw runtime_error("overflow while reading pool ptr");

            //iterate through entries
            filterSize = (uint32_t*)(poolPtr_ + pos);

            TxFilter<T> filterPtr(poolPtr_ + pos);
            auto&& resultSet = filterPtr.compare(hash);
            if (resultSet.size() > 0)
            {
               returnMap.insert(make_pair(
                  filterPtr.getBlockKey(),
                  move(resultSet)));
            }

            pos += *filterSize;
         }
      }
      else
         throw runtime_error("invalid pool");

      return returnMap;
   }

   vector<TxFilter<T>> getFilterPoolPtr(void)
   {
      if (poolPtr_ == nullptr)
         throw runtime_error("missing pool ptr");

      vector<TxFilter<T>> filters;

      //get count
      auto size = (uint32_t*)poolPtr_;
      uint32_t* filterSize;
      size_t pos = 4;

      for (uint32_t i = 0; i < *size; i++)
      {
         if (pos >= len_)
            throw runtime_error("overflow while reading pool ptr");

         //iterate through entries
         filterSize = (uint32_t*)(poolPtr_ + pos);

         TxFilter<T> filterPtr(poolPtr_ + pos);
         filters.push_back(filterPtr);

         pos += *filterSize;
      }

      return filters;
   }

   void serialize(BinaryWriter& bw) const
   {
      bw.put_uint32_t(len_); //item count

      for (auto& filter : pool_)
      {
         filter.serialize(bw);
      }
   }

   void deserialize(uint8_t* ptr, size_t len)
   {
      //sanity check
      if (ptr == nullptr || len < 4)
         throw runtime_error("invalid pointer");

      len_ = *(uint32_t*)ptr;

      if (len_ == 0)
         throw runtime_error("empty pool ptr");

      size_t offset = 4;

      for (auto i = 0; i < len_; i++)
      {
         if (offset >= len)
            throw runtime_error("deser error");

         auto filtersize = (uint32_t*)(ptr + offset);

         TxFilter<TxFilterType> filter;
         filter.deserialize(ptr + offset);

         offset += *filtersize;

         pool_.insert(move(filter));
      }
   }

   const TxFilter<T>& getFilterById(uint32_t id)
   {
      TxFilter<T> filter(id, 0);
      auto filterIter = pool_.find(filter);

      if (filterIter == pool_.end())
         throw runtime_error("invalid filter id");

      return *filterIter;
   }
};

////////////////////////////////////////////////////////////////////////////////
class LMDBBlockDatabase
{
public:

   /////////////////////////////////////////////////////////////////////////////
   LMDBBlockDatabase(shared_ptr<Blockchain>, const string&, ARMORY_DB_TYPE);
   ~LMDBBlockDatabase(void);

   /////////////////////////////////////////////////////////////////////////////
   void openDatabases(const string &basedir,
      BinaryData const & genesisBlkHash,
      BinaryData const & genesisTxHash,
      BinaryData const & magic);

   /////////////////////////////////////////////////////////////////////////////
   void nukeHeadersDB(void);

   /////////////////////////////////////////////////////////////////////////////
   void closeDatabases();
   void swapDatabases(DB_SELECT, const string&);

   /////////////////////////////////////////////////////////////////////////////
   void beginDBTransaction(LMDBEnv::Transaction* tx,
      DB_SELECT db, LMDB::Mode mode) const
   {
      *tx = move(LMDBEnv::Transaction(dbEnv_[db].get(), mode));
   }

   ARMORY_DB_TYPE getDbType(void) const { return armoryDbType_; }

   DB_SELECT getDbSelect(DB_SELECT dbs) const
   {
      return dbs;
   }

   /////////////////////////////////////////////////////////////////////////////
   // Sometimes, we just need to nuke everything and start over
   void destroyAndResetDatabases(void);
   void resetHistoryDatabases(void);

   /////////////////////////////////////////////////////////////////////////////
   bool databasesAreOpen(void) { return dbIsOpen_; }

   /////////////////////////////////////////////////////////////////////////////
   // Get latest block info
   BinaryData getTopBlockHash(DB_SELECT db);
   uint32_t   getTopBlockHeight(DB_SELECT db);
   BinaryData getTopBlockHash() const;


   /////////////////////////////////////////////////////////////////////////////
   LDBIter getIterator(DB_SELECT db) const
   {
      return dbs_[db].begin();
   }


   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryData object.  If you have a string, you can use
   // BinaryData key(string(theStr));
   BinaryDataRef getValueNoCopy(DB_SELECT db, BinaryDataRef keyWithPrefix) const;

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryDataRef object.  The data from the get* call is 
   // actually stored in a member variable, and thus the refs are valid only 
   // until the next get* call.
   BinaryDataRef getValueRef(DB_SELECT db, BinaryDataRef keyWithPrefix) const;
   BinaryDataRef getValueRef(DB_SELECT db, DB_PREFIX prefix, BinaryDataRef key) const;

   /////////////////////////////////////////////////////////////////////////////
   // Same as the getValueRef, in that they are only valid until the next get*
   // call.  These are convenience methods which basically just save us 
   BinaryRefReader getValueReader(DB_SELECT db, BinaryDataRef keyWithPrefix) const;
   BinaryRefReader getValueReader(DB_SELECT db, DB_PREFIX prefix, BinaryDataRef key) const;

   BinaryData getDBKeyForHash(const BinaryData& txhash,
      uint8_t dupId = UINT8_MAX) const;
   BinaryData getHashForDBKey(BinaryData dbkey) const;
   BinaryData getHashForDBKey(uint32_t hgt,
      uint8_t  dup,
      uint16_t txi = UINT16_MAX,
      uint16_t txo = UINT16_MAX) const;

   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryDataRefs key and value
   void putValue(DB_SELECT db, BinaryDataRef key, BinaryDataRef value);
   void putValue(DB_SELECT db, BinaryData const & key, BinaryData const & value);
   void putValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key, BinaryDataRef value);

   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(DB_SELECT db, BinaryDataRef key);
   void deleteValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key);

   // Move the iterator in DB to the lowest entry with key >= inputKey
   bool seekTo(DB_SELECT db,
      BinaryDataRef key);
   bool seekTo(DB_SELECT db,
      DB_PREFIX pref,
      BinaryDataRef key);

   // Move the iterator to the first entry >= txHash
   bool seekToTxByHash(LDBIter & ldbIter, BinaryDataRef txHash) const;


   /////////////////////////////////////////////////////////////////////////////
   // "Skip" refers to the behavior that the previous operation may have left
   // the iterator already on the next desired block.  So our "advance" op may
   // have finished before it started.  Alternatively, we may be on this block 
   // because we checked it and decide we don't care, so we want to skip it.
   bool advanceToNextBlock(LDBIter & iter, bool skip = false) const;
   bool advanceIterAndRead(DB_SELECT, DB_PREFIX);

   bool dbIterIsValid(DB_SELECT db, DB_PREFIX prefix = DB_PREFIX_COUNT);

   /////////////////////////////////////////////////////////////////////////////
   void readAllHeaders(
      const function<void(shared_ptr<BlockHeader>, uint32_t, uint8_t)> &callback
      );

   /////////////////////////////////////////////////////////////////////////////
   bool startBlkDataIteration(LDBIter & iter, DB_PREFIX prefix);


   /////////////////////////////////////////////////////////////////////////////
   void getNextBlock(void);

   /////////////////////////////////////////////////////////////////////////////
   void getBlock(BlockHeader & bh,
      vector<Tx> & txList,
      LMDB::Iterator* iter = NULL,
      bool ignoreMerkle = true);


   /////////////////////////////////////////////////////////////////////////////
   void loadAllStoredHistory(void);

   map<HashString, BlockHeader> getHeaderMap(void);
   BinaryData getRawHeader(BinaryData const & headerHash);
   //bool addHeader(BinaryData const & headerHash, BinaryData const & headerRaw);

   map<uint32_t, uint32_t> getSSHSummary(BinaryDataRef scrAddrStr,
      uint32_t endBlock);

   uint32_t getStxoCountForTx(const BinaryData & dbKey6) const;
   void resetHistoryForAddressVector(const vector<BinaryData>&);

public:

   uint8_t getValidDupIDForHeight(uint32_t blockHgt) const;
   void setValidDupIDForHeight(uint32_t blockHgt, uint8_t dup,
      bool overwrite = true);

   /////////////////////////////////////////////////////////////////////////////
   uint8_t getValidDupIDForHeight_fromDB(uint32_t blockHgt);

   ////////////////////////////////////////////////////////////////////////////
   uint8_t getDupForBlockHash(BinaryDataRef blockHash);



   /////////////////////////////////////////////////////////////////////////////
   // Interface to translate Stored* objects to/from persistent DB storage
   /////////////////////////////////////////////////////////////////////////////
   StoredDBInfo getStoredDBInfo(DB_SELECT db, uint32_t id);
   void putStoredDBInfo(DB_SELECT db, StoredDBInfo const & sdbi, uint32_t id);

   /////////////////////////////////////////////////////////////////////////////
   // BareHeaders are those int the HEADERS DB with no blockdta associated
   uint8_t putBareHeader(StoredHeader & sbh, bool updateDupID = true,
      bool updateSDBI = true);
   bool    getBareHeader(StoredHeader & sbh, uint32_t blkHgt, uint8_t dup) const;
   bool    getBareHeader(StoredHeader & sbh, uint32_t blkHgt) const;
   bool    getBareHeader(StoredHeader & sbh, BinaryDataRef headHash) const;

   /////////////////////////////////////////////////////////////////////////////
   // still using the old name even though no block data is stored anymore
   bool getStoredHeader(StoredHeader&, uint32_t, uint8_t, bool withTx = true) const;

   /////////////////////////////////////////////////////////////////////////////
   // StoredTx Accessors
   void updateStoredTx(StoredTx & st);

   void putStoredTx(StoredTx & st, bool withTxOut = true);
   void putStoredZC(StoredTx & stx, const BinaryData& zcKey);

   bool getStoredZcTx(StoredTx & stx,
      BinaryDataRef dbKey) const;

   bool getStoredTx(StoredTx & stx,
      BinaryData& txHashOrDBKey) const;

   bool getStoredTx_byDBKey(StoredTx & stx,
      BinaryDataRef dbKey) const;

   bool getStoredTx_byHash(const BinaryData& txHash,
      StoredTx* stx = nullptr) const;

   bool getStoredTx(StoredTx & st,
      uint32_t blkHgt,
      uint16_t txIndex,
      bool withTxOut = true) const;

   bool getStoredTx(StoredTx & st,
      uint32_t blkHgt,
      uint8_t  dupID,
      uint16_t txIndex,
      bool withTxOut = true) const;


   /////////////////////////////////////////////////////////////////////////////
   // StoredTxOut Accessors
   void putStoredTxOut(StoredTxOut const & sto);
   void putStoredZcTxOut(StoredTxOut const & stxo, const BinaryData& zcKey);

   bool getStoredTxOut(StoredTxOut & stxo,
      uint32_t blockHeight,
      uint8_t  dupID,
      uint16_t txIndex,
      uint16_t txOutIndex) const;

   bool getStoredTxOut(StoredTxOut & stxo,
      uint32_t blockHeight,
      uint16_t txIndex,
      uint16_t txOutIndex) const;

   bool getStoredTxOut(StoredTxOut & stxo,
      const BinaryData& DBkey) const;

   bool getStoredTxOut(
      StoredTxOut & stxo, const BinaryData& txHash, uint16_t txoutid) const;

   void getUTXOflags(map<BinaryData, StoredSubHistory>&) const;
   void getUTXOflags(StoredSubHistory&) const;

   void putStoredScriptHistory(StoredScriptHistory & ssh);
   void putStoredScriptHistorySummary(StoredScriptHistory & ssh);
   void putStoredSubHistory(StoredSubHistory & subssh);

   bool getStoredScriptHistory(StoredScriptHistory & ssh,
      BinaryDataRef scrAddrStr,
      uint32_t startBlock = 0,
      uint32_t endBlock = UINT32_MAX) const;

   bool getStoredSubHistoryAtHgtX(StoredSubHistory& subssh,
      const BinaryData& scrAddrStr, const BinaryData& hgtX) const;
   
   bool getStoredSubHistoryAtHgtX(StoredSubHistory& subssh,
      const BinaryData& dbkey) const;

   void getStoredScriptHistorySummary(StoredScriptHistory & ssh,
      BinaryDataRef scrAddrStr) const;

   void getStoredScriptHistoryByRawScript(
      StoredScriptHistory & ssh,
      BinaryDataRef rawScript) const;

   // This method breaks from the convention I've used for getting/putting 
   // stored objects, because we never really handle Sub-ssh objects directly,
   // but we do need to harness them.  This method could be renamed to
   // "getPartialScriptHistory()" ... it reads the main 
   // sub-ssh from DB and adds it to the supplied regular-ssh.
   bool fetchStoredSubHistory(StoredScriptHistory & ssh,
      BinaryData hgtX,
      bool createIfDNE = false,
      bool forceReadAndMerge = false);

   // This could go in StoredBlockObj if it didn't need to lookup DB data
   bool     getFullUTXOMapForSSH(StoredScriptHistory & ssh,
      map<BinaryData, UnspentTxOut> & mapToFill,
      bool withMultisig = false);

   uint64_t getBalanceForScrAddr(BinaryDataRef scrAddr, bool withMulti = false);

   bool putStoredTxHints(StoredTxHints const & sths);
   bool getStoredTxHints(StoredTxHints & sths, BinaryDataRef hashPrefix) const;
   void updatePreferredTxHint(BinaryDataRef hashOrPrefix, BinaryData preferKey);

   bool putStoredHeadHgtList(StoredHeadHgtList const & hhl);
   bool getStoredHeadHgtList(StoredHeadHgtList & hhl, uint32_t height) const;

   ////////////////////////////////////////////////////////////////////////////
   // Some methods to grab data at the current iterator location.  Return
   // false if reading fails (maybe because we were expecting to find the
   // specified DB entry type, but the prefix byte indicated something else
   bool readStoredScriptHistoryAtIter(LDBIter & iter,
      StoredScriptHistory & ssh,
      uint32_t startBlock,
      uint32_t endBlock) const;

   // TxRefs are much simpler with LDB than the previous FileDataPtr construct
   TxRef getTxRef(BinaryDataRef txHash);
   TxRef getTxRef(BinaryData hgtx, uint16_t txIndex);
   TxRef getTxRef(uint32_t hgt, uint8_t dup, uint16_t txIndex);


   // Sometimes we already know where the Tx is, but we don't know its hash
   Tx    getFullTxCopy(BinaryData ldbKey6B) const;
   Tx    getFullTxCopy(uint32_t hgt, uint16_t txIndex) const;
   Tx    getFullTxCopy(uint32_t hgt, uint8_t dup, uint16_t txIndex) const;
   Tx    getFullTxCopy(uint16_t txIndex, shared_ptr<BlockHeader> bhPtr) const;
   TxOut getTxOutCopy(BinaryData ldbKey6B, uint16_t txOutIdx) const;
   TxIn  getTxInCopy(BinaryData ldbKey6B, uint16_t txInIdx) const;


   // Sometimes we already know where the Tx is, but we don't know its hash
   BinaryData getTxHashForLdbKey(BinaryDataRef ldbKey6B) const;

   BinaryData getTxHashForHeightAndIndex(uint32_t height,
      uint16_t txIndex);

   BinaryData getTxHashForHeightAndIndex(uint32_t height,
      uint8_t  dup,
      uint16_t txIndex);

   ////////////////////////////////////////////////////////////////////////////
   bool markBlockHeaderValid(BinaryDataRef headHash);
   bool markBlockHeaderValid(uint32_t height, uint8_t dup);
   bool markTxEntryValid(uint32_t height, uint8_t dupID, uint16_t txIndex);


   /////////////////////////////////////////////////////////////////////////////
   void computeUndoDataFromRawBlock(StoredHeader const & sbh,
      StoredUndoData & sud);
   void computeUndoDataFromRawBlock(BinaryDataRef    rawBlock,
      StoredUndoData & sud);
   bool computeUndoDataForBlock(uint32_t height,
      uint8_t dupID,
      StoredUndoData & sud);


   KVLIST getAllDatabaseEntries(DB_SELECT db);
   void   printAllDatabaseEntries(DB_SELECT db);
   void   pprintBlkDataDB(uint32_t indent = 3);

   BinaryData getGenesisBlockHash(void) { return genesisBlkHash_; }
   BinaryData getGenesisTxHash(void)    { return genesisTxHash_; }
   BinaryData getMagicBytes(void)       { return magicBytes_; }

   ARMORY_DB_TYPE armoryDbType(void) { return armoryDbType_; }

   const string& baseDir(void) const { return baseDir_; }
   void setBlkFolder(const string& path) { blkFolder_ = path; }

   string getDbName(DB_SELECT) const;
   string getDbPath(DB_SELECT) const;
   string getDbPath(const string&) const;

   void closeDB(DB_SELECT db);
   StoredDBInfo openDB(DB_SELECT);
   void resetSSHdb(void);

   const shared_ptr<Blockchain> blockchain(void) const { return blockchainPtr_; }

   /////////////////////////////////////////////////////////////////////////////
   template <typename T> TxFilterPool<T> getFilterPoolForFileNum(
      uint32_t fileNum) const
   {
      auto&& key = DBUtils::getFilterPoolKey(fileNum);

      auto db = TXFILTERS;
      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, db, LMDB::ReadOnly);

      auto val = getValueNoCopy(TXFILTERS, key);

      TxFilterPool<T> pool;
      try
      {
         pool.deserialize((uint8_t*)val.getPtr(), val.getSize());
      }
      catch (exception&)
      { }

      return pool;
   }

   /////////////////////////////////////////////////////////////////////////////
   template <typename T> TxFilterPool<T> getFilterPoolRefForFileNum(
      uint32_t fileNum) const
   {
      auto&& key = DBUtils::getFilterPoolKey(fileNum);

      auto db = TXFILTERS;
      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, db, LMDB::ReadOnly);

      auto val = getValueNoCopy(TXFILTERS, key);
      if (val.getSize() == 0)
         throw runtime_error("invalid txfilter key");

      return TxFilterPool<T>(val.getPtr(), val.getSize());
   }


   /////////////////////////////////////////////////////////////////////////////
   template <typename T> void putFilterPoolForFileNum(
      uint32_t fileNum, const TxFilterPool<T>& pool)
   {
      if (!pool.isValid())
         throw runtime_error("invalid filterpool");

      //update on disk
      auto db = TXFILTERS;
      LMDBEnv::Transaction tx;
      beginDBTransaction(&tx, db, LMDB::ReadWrite);

      auto&& key = DBUtils::getFilterPoolKey(fileNum);
      BinaryWriter bw;
      pool.serialize(bw);

      auto dataref = bw.getDataRef();
      dbs_[db].insert(
         CharacterArrayRef(key.getSize(), key.getPtr()),
         CharacterArrayRef(dataref.getSize(), dataref.getPtr()));
   }

   void putMissingHashes(const set<BinaryData>&, uint32_t);
   set<BinaryData> getMissingHashes(uint32_t) const;

public:

   mutable map<DB_SELECT, shared_ptr<LMDBEnv> > dbEnv_;
   mutable LMDB dbs_[COUNT];

private:

   string               baseDir_;
   BinaryData           genesisBlkHash_;
   BinaryData           genesisTxHash_;
   BinaryData           magicBytes_;

   ARMORY_DB_TYPE armoryDbType_;

   bool                 dbIsOpen_;
   uint32_t             ldbBlockSize_;

   uint32_t             lowestScannedUpTo_;

   map<uint32_t, uint8_t>      validDupByHeight_;

   // In this case, a address is any TxOut script, which is usually
   // just a 25-byte script.  But this generically captures all types
   // of addresses including pubkey-only, P2SH, 
   map<BinaryData, StoredScriptHistory>   registeredSSHs_;

   const BinaryData ZCprefix_ = BinaryData(2);

   string blkFolder_;

   const shared_ptr<Blockchain> blockchainPtr_;
};

#endif
// kate: indent-width 3; replace-tabs on;
