////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
//
#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <list>
#include <vector>
#include "log.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"

#include "leveldb/db.h"
#include "leveldb/write_batch.h"
#include "leveldb/cache.h"
//#include "leveldb/filter_policy.h"


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


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// InterfaceToLDB
//
// This is intended to be the only part of the project that communicates 
// directly with LevelDB objects.  All the public methods only interact with 
// BinaryData, BinaryDataRef, and BinaryRefReader objects.  
//
// As of this writing (the first implementation of this interface), the 
// interface and underlying DB structure is designed and tested for 
// ARMORY_DB_FULL and DB_PRUNE_NONE, which is essentially the same mode that 
// Armory used before the persistent blockchain upgrades.  However, much of
// the design decisions about how to store and access data was done to best
// accommodate future implementation of pruned/lite modes, as well as a 
// supernode mode (which tracks all addresses and can be used to respond to
// balance/UTXO queries from other nodes).  There is still implementation 
// work to be done to enable these other modes, but it shouldn't require
// changing the DB structure dramatically.  The biggest modification will 
// adding and tracking undo-data to deal with reorgs in a pruned blockchain.
//
// NOTE 1: This class was designed with certain optimizations that may cause 
//         unexpected behavior if you are not aware of it.  The following 
//         methods return/modify static member of InterfaceToLDB:
//
//            getValue*
//            seekTo*
//            start*Iteration
//            advance*
//
//         This is especially dangerous with getValueRef() which returns a
//         reference to lastGetValue_ which changes under you as soon as you
//         execute any other getValue* calls.  This eliminates unnecessary 
//         copying of DB data but can cause all sorts of problems if you are 
//         doing sequences of find-and-modify operations.  
//
//         It is best to avoid getValueRef() unless you are sure that you 
//         understand how to use it safely.  Only use getValue() unless there
//         is reason to believe that the optimization is needed.
//
//
//
// NOTE 2: Batch writing operations are smoothed so that multiple, nested
//         startBatch-commitBatch calls do not actually do anything except
//         at the outer-most level.  But this means that you MUST make sure
//         that there is a commit for every start, at every level.  If you
//         return a value from a method sidestepping a required commitBatch 
//         call, the code will stop writing to the DB at all!  
//          


////////////////////////////////////////////////////////////////////////////////
class LDBIter
{
public: 

   // fill_cache argument should be false for large bulk scans
   LDBIter(void) { db_=NULL; iter_=NULL; isDirty_=true;}
   LDBIter(leveldb::DB* dbptr, bool fill_cache=true);
   ~LDBIter(void) { destroy(); }
   void destroy(void) {if(iter_!=NULL) delete iter_; iter_ = NULL; db_ = NULL;}

   bool isNull(void) { return iter_==NULL; }
   bool isValid(void) { return (!isNull() && iter_->Valid()); }
   bool isValid(DB_PREFIX dbpref);

   bool readIterData(void);

   bool advance(void);
   bool advance(DB_PREFIX prefix);
   bool advanceAndRead(void);
   bool advanceAndRead(DB_PREFIX prefix);

   BinaryData       getKey(void) ;
   BinaryData       getValue(void) ;
   BinaryDataRef    getKeyRef(void) ;
   BinaryDataRef    getValueRef(void) ;
   BinaryRefReader& getKeyReader(void) ;
   BinaryRefReader& getValueReader(void) ;

   // All the seekTo* methods do the exact same thing, the variant simply 
   // determines the meaning of the return true/false value.
   bool seekTo(BinaryDataRef key);
   bool seekTo(DB_PREFIX pref, BinaryDataRef key);
   bool seekToExact(BinaryDataRef key);
   bool seekToExact(DB_PREFIX pref, BinaryDataRef key);
   bool seekToStartsWith(BinaryDataRef key);
   bool seekToStartsWith(DB_PREFIX prefix);
   bool seekToStartsWith(DB_PREFIX pref, BinaryDataRef key);
   bool seekToFirst(void);

   // Return true if the iterator is currently on valid data, with key match
   bool checkKeyExact(BinaryDataRef key);
   bool checkKeyExact(DB_PREFIX prefix, BinaryDataRef key);
   bool checkKeyStartsWith(BinaryDataRef key);
   bool checkKeyStartsWith(DB_PREFIX prefix, BinaryDataRef key);

   bool verifyPrefix(DB_PREFIX prefix, bool advanceReader=true);

   void resetReaders(void){currKey_.resetPosition();currValue_.resetPosition();}

   leveldb::Slice binaryDataToSlice(BinaryData const & bd) 
         {return leveldb::Slice((char*)bd.getPtr(), bd.getSize());}
   leveldb::Slice binaryDataRefToSlice(BinaryDataRef const & bdr)
         {return leveldb::Slice((char*)bdr.getPtr(), bdr.getSize());}

private:


   leveldb::DB* db_;
   leveldb::Iterator* iter_;

   BinaryRefReader  currKey_;
   BinaryRefReader  currValue_;
   bool isDirty_;
   
   
};



////////////////////////////////////////////////////////////////////////////////
class InterfaceToLDB
{
private:

   /////////////////////////////////////////////////////////////////////////////
   leveldb::Slice binaryDataToSlice(BinaryData const & bd) 
         {return leveldb::Slice((char*)bd.getPtr(), bd.getSize());}
   leveldb::Slice binaryDataRefToSlice(BinaryDataRef const & bdr)
         {return leveldb::Slice((char*)bdr.getPtr(), bdr.getSize());}



   /////////////////////////////////////////////////////////////////////////////
   // These four sliceTo* methods make copies, and thus safe to use even after
   // we have advanced the iterator to new data
   /////////////////////////////////////////////////////////////////////////////
   BinaryData   sliceToBinaryData(   leveldb::Slice slice);
   void         sliceToBinaryData(   leveldb::Slice slice, BinaryData & bd);
   BinaryReader sliceToBinaryReader( leveldb::Slice slice);
   void         sliceToBinaryReader( leveldb::Slice slice, BinaryReader & brr);

   /////////////////////////////////////////////////////////////////////////////
   // The reamining sliceTo* methods are reference-based, which become
   // invalid after the iterator moves on.
   BinaryDataRef   sliceToBinaryDataRef(  leveldb::Slice slice);
   BinaryRefReader sliceToBinaryRefReader(leveldb::Slice slice);


public:

   /////////////////////////////////////////////////////////////////////////////
   InterfaceToLDB(void);
   ~InterfaceToLDB(void);



   /////////////////////////////////////////////////////////////////////////////
   void init(void);

   /////////////////////////////////////////////////////////////////////////////
   bool openDatabases(string basedir, 
                      BinaryData const & genesisBlkHash,
                      BinaryData const & genesisTxHash,
                      BinaryData const & magic,
                      ARMORY_DB_TYPE     dbtype=ARMORY_DB_WHATEVER,
                      DB_PRUNE_TYPE      pruneType=DB_PRUNE_WHATEVER);

   /////////////////////////////////////////////////////////////////////////////
   void nukeHeadersDB(void);
   
   /////////////////////////////////////////////////////////////////////////////
   void closeDatabases(void);

   /////////////////////////////////////////////////////////////////////////////
   // Sometimes, we just need to nuke everything and start over
   void destroyAndResetDatabases(void);

   /////////////////////////////////////////////////////////////////////////////
   bool databasesAreOpen(void) { return dbIsOpen_; }

   /////////////////////////////////////////////////////////////////////////////
   // Get latest block info
   BinaryData getTopBlockHash(DB_SELECT db);
   uint32_t   getTopBlockHeight(DB_SELECT db);
   
   /////////////////////////////////////////////////////////////////////////////
   LDBIter getIterator(DB_SELECT db, bool fill_cache=true) 
                                    { return LDBIter(dbs_[db], fill_cache); }
   

   /////////////////////////////////////////////////////////////////////////////
   // Get value using pre-created slice
   BinaryData getValue(DB_SELECT db, leveldb::Slice ldbKey);

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryData object.  If you have a string, you can use
   // BinaryData key(string(theStr));
   BinaryData getValue(DB_SELECT db, BinaryDataRef keyWithPrefix);

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryData object.  If you have a string, you can use
   // BinaryData key(string(theStr));
   BinaryData getValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key);

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryDataRef object.  The data from the get* call is 
   // actually stored in a member variable, and thus the refs are valid only 
   // until the next get* call.
   BinaryDataRef getValueRef(DB_SELECT db, BinaryDataRef keyWithPrefix);
   BinaryDataRef getValueRef(DB_SELECT db, DB_PREFIX prefix, BinaryDataRef key);

   /////////////////////////////////////////////////////////////////////////////
   // Same as the getValueRef, in that they are only valid until the next get*
   // call.  These are convenience methods which basically just save us 
   BinaryRefReader getValueReader(DB_SELECT db, BinaryDataRef keyWithPrefix);
   BinaryRefReader getValueReader(DB_SELECT db, DB_PREFIX prefix, BinaryDataRef key);


   BinaryData getHashForDBKey(BinaryData dbkey);
   BinaryData getHashForDBKey(uint32_t hgt,
                              uint8_t  dup,
                              uint16_t txi=UINT16_MAX,
                              uint16_t txo=UINT16_MAX);

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
   bool seekToTxByHash(LDBIter & ldbIter, BinaryDataRef txHash);


   /////////////////////////////////////////////////////////////////////////////
   // "Skip" refers to the behavior that the previous operation may have left
   // the iterator already on the next desired block.  So our "advance" op may
   // have finished before it started.  Alternatively, we may be on this block 
   // because we checked it and decide we don't care, so we want to skip it.
   bool advanceToNextBlock(LDBIter & iter, bool skip=false);
   bool advanceIterAndRead(DB_SELECT, DB_PREFIX);

   bool dbIterIsValid(DB_SELECT db, DB_PREFIX prefix=DB_PREFIX_COUNT);

   /////////////////////////////////////////////////////////////////////////////
   void readAllHeaders(map<HashString, BlockHeader>  & headerMap,
                       map<HashString, StoredHeader> & storedMap);

   /////////////////////////////////////////////////////////////////////////////
   // When we're not in supernode mode, we're going to need to track only 
   // specific addresses.  We will keep a list of those addresses here.
   // UINT32_MAX for the "scannedUpToBlk" arg means that this address is totally
   // new and does not require a rescan.  If you don't know when the scraddress
   // was created, use 0.  Or if you know something, you can supply it.  Though
   // in many cases, we will just do a full rescan if it's not totally new.
   void addRegisteredScript(BinaryDataRef rawScript,
                            uint32_t      scannedUpToBlk=UINT32_MAX);
   
   

   /////////////////////////////////////////////////////////////////////////////
   bool startBlkDataIteration(LDBIter & iter, DB_PREFIX prefix);


   /////////////////////////////////////////////////////////////////////////////
   void getNextBlock(void);

   /////////////////////////////////////////////////////////////////////////////
   void getBlock(BlockHeader & bh, 
                 vector<Tx> & txList, 
                 leveldb::Iterator* iter=NULL,
                 bool ignoreMerkle = true);


   /////////////////////////////////////////////////////////////////////////////
   void loadAllStoredHistory(void); 

   map<HashString, BlockHeader> getHeaderMap(void);
   BinaryData getRawHeader(BinaryData const & headerHash);
   //bool addHeader(BinaryData const & headerHash, BinaryData const & headerRaw);


   /////////////////////////////////////////////////////////////////////////////
   // All put/del ops will be batched/queued, and only executed when called
   // commitBatch().  We track the number calls to startBatch and commitBatch
   // and only write if we've called commit as many times as we called start.
   // In this way, we can have multiple levels starting and ending batches 
   // without caring whether a batched operation is already in process or if 
   // it's the first
   void startBatch(DB_SELECT db);
   void commitBatch(DB_SELECT db);
   bool isBatchOn(DB_SELECT db)   { return batchStarts_[db] > 0; }


   /////////////////////////////////////////////////////////////////////////////
   uint8_t getValidDupIDForHeight_fromDB(uint32_t blockHgt);
   uint8_t getValidDupIDForHeight(uint32_t blockHgt);
   void    setValidDupIDForHeight(uint32_t blockHgt, uint8_t dup);

   ////////////////////////////////////////////////////////////////////////////
   uint8_t getDupForBlockHash(BinaryDataRef blockHash);



   /////////////////////////////////////////////////////////////////////////////
   // Interface to translate Stored* objects to/from persistent DB storage
   /////////////////////////////////////////////////////////////////////////////
   void putStoredDBInfo(DB_SELECT db, StoredDBInfo const & sdbi);
   bool getStoredDBInfo(DB_SELECT db, StoredDBInfo & sdbi, bool warn=true);
   
   /////////////////////////////////////////////////////////////////////////////
   // BareHeaders are those int the HEADERS DB with no blockdta associated
   uint8_t putBareHeader(StoredHeader & sbh); 
   bool    getBareHeader(StoredHeader & sbh, uint32_t blkHgt, uint8_t dup); 
   bool    getBareHeader(StoredHeader & sbh, uint32_t blkHgt); 
   bool    getBareHeader(StoredHeader & sbh, BinaryDataRef headHash);

   /////////////////////////////////////////////////////////////////////////////
   // StoredHeader accessors
   uint8_t putStoredHeader(StoredHeader & sbh,
                        bool withBlkData=true);

   bool getStoredHeader(StoredHeader & sbh,
                        uint32_t blockHgt,
                        uint8_t blockDup=UINT8_MAX,
                        bool withTx=true);

   bool getStoredHeader(StoredHeader & sbh,
                        BinaryDataRef headHash, 
                        bool withTx=true);

   // This seemed unnecessary and was also causing conflicts with optional args
   //bool getStoredHeader(StoredHeader & sbh,
                        //uint32_t blockHgt,
                        //bool withTx=true);


   /////////////////////////////////////////////////////////////////////////////
   // StoredTx Accessors
   void putStoredTx(         StoredTx & st,
                             bool withTxOut=true);

   bool getStoredTx(         StoredTx & stx,
                             BinaryDataRef txHashOrDBKey);

   bool getStoredTx_byDBKey( StoredTx & stx,
                             BinaryDataRef dbKey);

   bool getStoredTx_byHash(  StoredTx & stx,
                             BinaryDataRef txHash);

   bool getStoredTx(         StoredTx & st,
                             uint32_t blkHgt,
                             uint16_t txIndex,
                             bool withTxOut=true);

   bool getStoredTx(         StoredTx & st,
                             uint32_t blkHgt,
                             uint8_t  dupID,
                             uint16_t txIndex,
                             bool withTxOut=true);


   /////////////////////////////////////////////////////////////////////////////
   // StoredTxOut Accessors
   void putStoredTxOut(      StoredTxOut const & sto);

   bool getStoredTxOut(      StoredTxOut & stxo,
                             uint32_t blockHeight,
                             uint8_t  dupID,
                             uint16_t txIndex,
                             uint16_t txOutIndex);

   bool getStoredTxOut(      StoredTxOut & stxo,
                             uint32_t blockHeight,
                             uint16_t txIndex,
                             uint16_t txOutIndex);


   void putStoredScriptHistory( StoredScriptHistory & ssh);

   void getStoredScriptHistory( StoredScriptHistory & ssh,
                                BinaryDataRef scrAddrStr);

   void getStoredScriptHistorySummary( StoredScriptHistory & ssh,
                                       BinaryDataRef scrAddrStr);

   void getStoredScriptHistoryByRawScript(
                                StoredScriptHistory & ssh,
                                BinaryDataRef rawScript);

   // This method breaks from the convention I've used for getting/putting 
   // stored objects, because we never really handle Sub-SSH objects directly,
   // but we do need to harness them.  This method could be renamed to
   // "getPartialScriptHistory()" ... it reads the main 
   // sub-SSH from DB and adds it to the supplied regular-SSH.
   bool fetchStoredSubHistory( StoredScriptHistory & ssh, 
                               BinaryData hgtX,
                               bool createIfDNE=false,
                               bool forceReadAndMerge=false);

   // This could go in StoredBlockObj if it didn't need to lookup DB data
   bool     getFullUTXOMapForSSH(StoredScriptHistory & ssh,
                                 map<BinaryData, UnspentTxOut> & mapToFill,
                                 bool withMultisig=false);

   uint64_t getBalanceForScrAddr(BinaryDataRef scrAddr, bool withMulti=false);
   
   // TODO: We should probably implement some kind of method for accessing or 
   //       running calculations on an SSH without ever loading the entire
   //       thing into RAM.  

   // None of the SUD methods are implemented because we don't actually need
   // to read/write SUD to the database -- our only mode is ARMORY_DB_SUPER
   // which doesn't require storing undo data
   bool putStoredUndoData(StoredUndoData const & sud);
   bool getStoredUndoData(StoredUndoData & sud, uint32_t height);
   bool getStoredUndoData(StoredUndoData & sud, uint32_t height, uint8_t dup);
   bool getStoredUndoData(StoredUndoData & sud, BinaryDataRef headHash);

   bool putStoredTxHints(StoredTxHints const & sths);
   bool getStoredTxHints(StoredTxHints & sths, BinaryDataRef hashPrefix);
   void updatePreferredTxHint(BinaryDataRef hashOrPrefix, BinaryData preferKey);

   bool putStoredHeadHgtList(StoredHeadHgtList const & hhl);
   bool getStoredHeadHgtList(StoredHeadHgtList & hhl, uint32_t height);

   ////////////////////////////////////////////////////////////////////////////
   // Some methods to grab data at the current iterator location.  Return
   // false if reading fails (maybe because we were expecting to find the
   // specified DB entry type, but the prefix byte indicated something else
   bool readStoredBlockAtIter(LDBIter & iter, 
                              StoredHeader & sbh);

   bool readStoredTxAtIter(LDBIter & iter, 
                           uint32_t height, 
                           uint8_t dupID, 
                           StoredTx & stx);

   bool readStoredTxOutAtIter(LDBIter & iter, 
                              uint32_t height, 
                              uint8_t  dupID, 
                              uint16_t txIndex,
                              StoredTxOut & stxo);

   bool readStoredScriptHistoryAtIter(LDBIter & iter, 
                                      StoredScriptHistory & ssh);


   // TxRefs are much simpler with LDB than the previous FileDataPtr construct
   TxRef getTxRef( BinaryDataRef txHash);
   TxRef getTxRef( BinaryData hgtx, uint16_t txIndex);
   TxRef getTxRef( uint32_t hgt, uint8_t dup, uint16_t txIndex);


   // Sometimes we already know where the Tx is, but we don't know its hash
   Tx    getFullTxCopy( BinaryData ldbKey6B );
   Tx    getFullTxCopy( uint32_t hgt, uint16_t txIndex);
   Tx    getFullTxCopy( uint32_t hgt, uint8_t dup, uint16_t txIndex);
   TxOut getTxOutCopy(  BinaryData ldbKey6B, uint16_t txOutIdx);
   TxIn  getTxInCopy(   BinaryData ldbKey6B, uint16_t txInIdx );


   // Sometimes we already know where the Tx is, but we don't know its hash
   BinaryData getTxHashForLdbKey( BinaryDataRef ldbKey6B );

   BinaryData getTxHashForHeightAndIndex( uint32_t height, 
                                          uint16_t txIndex);

   BinaryData getTxHashForHeightAndIndex( uint32_t height, 
                                          uint8_t  dup, 
                                          uint16_t txIndex);

   StoredTxHints getHintsForTxHash(BinaryDataRef txHash);


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



   /////////////////////////////////////////////////////////////////////////////
   bool checkStatus(leveldb::Status stat, bool warn=true);

   void     setMaxOpenFiles(uint32_t n) {  maxOpenFiles_ = n;   }
   uint32_t getMaxOpenFiles(void)       { return maxOpenFiles_; }
   void     setLdbBlockSize(uint32_t sz){ ldbBlockSize_ = sz;   }
   uint32_t getLdbBlockSize(void)       { return ldbBlockSize_; }


   KVLIST getAllDatabaseEntries(DB_SELECT db);
   void   printAllDatabaseEntries(DB_SELECT db);
   void   pprintBlkDataDB(uint32_t indent=3);

   BinaryData getGenesisBlockHash(void) { return genesisBlkHash_; }
   BinaryData getGenesisTxHash(void)    { return genesisTxHash_; }
   BinaryData getMagicBytes(void)       { return magicBytes_; }



private:
   string               baseDir_;

   BinaryData           genesisBlkHash_;
   BinaryData           genesisTxHash_;
   BinaryData           magicBytes_;

   ARMORY_DB_TYPE       armoryDbType_;
   DB_PRUNE_TYPE        dbPruneType_;

   //leveldb::Iterator*     iters_[2];
   leveldb::WriteBatch*   batches_[2];
   leveldb::DB*           dbs_[2];  
   string                 dbPaths_[2];
   bool                   iterIsDirty_[2];
   //leveldb::FilterPolicy* dbFilterPolicy_[2];

   // This will be incremented every time startBatch is called, decremented
   // every time commitBatch is called.  We will only *actually* start a new
   // batch when the value starts at zero, or commit when it ends at zero.
   uint32_t             batchStarts_[2];
   

   vector<uint8_t>      validDupByHeight_;

   //BinaryRefReader      currReadKey_;
   //BinaryRefReader      currReadValue_;;
   string               lastGetValue_;
   
   bool                 dbIsOpen_;
   uint32_t             ldbBlockSize_;

   uint32_t             lowestScannedUpTo_;

   leveldb::Status      lastStatus_;

   uint32_t             maxOpenFiles_;

   // In this case, a address is any TxOut script, which is usually
   // just a 25-byte script.  But this generically captures all types
   // of addresses including pubkey-only, P2SH, 
   map<BinaryData, StoredScriptHistory>   registeredSSHs_;
};


////////////////////////////////////////////////////////////////////////////////
// A semi-singleton class: this basically allows you 
class LevelDBWrapper
{
public:

   /////////////////////////////////////////////////////////////////////////////
   static InterfaceToLDB & GetInterface(uint32_t i=0)
   {
      if(ifaceVect_.size() < i+1)
      {
         ifaceVect_.resize(i+1); 
         ifaceVect_[i] = new InterfaceToLDB;
         ifaceVect_[i]->init();
      }

      return *(ifaceVect_[i]);
   }

   /////////////////////////////////////////////////////////////////////////////
   static InterfaceToLDB* GetInterfacePtr(uint32_t i=0)
   {
      if(ifaceVect_.size() < i+1)
      {
         ifaceVect_.resize(i+1); 
         ifaceVect_[i] = new InterfaceToLDB;
         ifaceVect_[i]->init();
      }

      return ifaceVect_[i];
   }

private:

   static vector<InterfaceToLDB*> ifaceVect_;
};


#endif
