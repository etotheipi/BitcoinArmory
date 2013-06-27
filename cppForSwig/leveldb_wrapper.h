#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <list>
#include <vector>
#include "log.h"
#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "BtcUtils.h"

#include "leveldb/db.h"
#include "leveldb/write_batch.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
////////////////////////////////////////////////////////////////////////////////

#define ARMORY_DB_VERSION   0x00

#define STD_READ_OPTS       leveldb::ReadOptions()
#define STD_WRITE_OPTS      leveldb::WriteOptions()

#define ARMORY_DB_DEFAULT   ARMORY_DB_FULL
#define UTXO_STORAGE        SCRIPT_UTXO_VECTOR


typedef enum
{
  NOT_BLKDATA,
  BLKDATA_HEADER,
  BLKDATA_TX,
  BLKDATA_TXOUT
} BLKDATA_TYPE;

typedef enum
{
  DB_PREFIX_DBINFO,
  DB_PREFIX_HEADHASH,
  DB_PREFIX_HEADHGT,
  DB_PREFIX_BLKDATA,
  DB_PREFIX_TXHINTS,
  DB_PREFIX_SCRIPT,
  DB_PREFIX_MULTISIG,
  DB_PREFIX_UNDODATA,
  DB_PREFIX_TRIENODES,
  DB_PREFIX_COUNT
} DB_PREFIX;


typedef enum
{
  ARMORY_DB_LITE,
  ARMORY_DB_PARTIAL,
  ARMORY_DB_FULL,
  ARMORY_DB_SUPER,
  ARMORY_DB_WHATEVER
} ARMORY_DB_TYPE;

typedef enum
{
  DB_PRUNE_ALL,
  DB_PRUNE_NONE,
  DB_PRUNE_WHATEVER
} DB_PRUNE_TYPE;


typedef enum
{
  LDB_TX_EXISTS,
  LDB_TX_GETBLOCK,
  LDB_TX_UNKNOWN
} LDB_TX_AVAIL;

typedef enum
{
  HEADERS,
  BLKDATA,
  DB_COUNT
} DB_SELECT;


typedef enum
{
  TX_SER_FULL,
  TX_SER_FRAGGED,
  TX_SER_COUNTOUT
} TX_SERIALIZE_TYPE;

typedef enum
{
  TXOUT_UNSPENT,
  TXOUT_SPENT,
  TXOUT_SPENTUNK,
} TXOUT_SPENTNESS;

typedef enum
{
  MERKLE_SER_NONE,
  MERKLE_SER_PARTIAL,
  MERKLE_SER_FULL
} MERKLE_SER_TYPE;

typedef enum
{
  SCRIPT_UTXO_VECTOR,
  SCRIPT_UTXO_TREE
} SCRIPT_UTXO_TYPE;




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// InterfaceToLevelDB
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
//         methods return/modify static member of InterfaceToLevelDB:
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
//         Similarly, when using the seek/start/advance iterator methods, 
//         keep in mind that various submethods you call may move the 
//         iterator out from under you.  To be safe from this issue, it is
//         best to copy the data behind currReadKey_ and currReadValue_ 
//         after you move the iterator.
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


class InterfaceToLevelDB
{
public:
   InterfaceToLevelDB(void);

   InterfaceToLevelDB(string basedir, 
                      BinaryData const & genesisBlkHash,
                      BinaryData const & genesisTxHash,
                      BinaryData const & magic,
                      ARMORY_DB_TYPE     dbtype=ARMORY_DB_DEFAULT,
                      DB_PRUNE_TYPE      pruneType=DB_PRUNE_NONE);

   void init(void);

   ~InterfaceToLevelDB(void);

private:

   /////////////////////////////////////////////////////////////////////////////
   bool openDatabases(void);
   
   /////////////////////////////////////////////////////////////////////////////
   void closeDatabases(void);

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



   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryDataRefs key and value
   void putValue(DB_SELECT db, BinaryDataRef key, BinaryDataRef value);
   void putValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key, BinaryDataRef value);
   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(DB_SELECT db, BinaryDataRef key);
   void deleteValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key);


   /////////////////////////////////////////////////////////////////////////////
   leveldb::Slice binaryDataToSlice(BinaryData const & bd) 
         {return leveldb::Slice((char*)bd.getPtr(), bd.getSize());}
   leveldb::Slice binaryDataRefToSlice(BinaryDataRef const & bdr)
         {return leveldb::Slice((char*)bdr.getPtr(), bdr.getSize());}

   /////////////////////////////////////////////////////////////////////////////
   // "Skip" refers to the behavior that the previous operation may have left
   // the iterator already on the next desired block.  So our "advance" op may
   // have finished before it started.  Alternatively, we may be on this block 
   // because we checked it and decide we don't care, so we want to skip it.
   bool advanceToNextHeader(bool skip=false);
   bool advanceToNextBlock(bool skip=false);
   bool advanceIterAndRead(leveldb::Iterator* iter);
   bool advanceIterAndRead(DB_SELECT, DB_PREFIX);

   bool seekTo(DB_SELECT db, 
               BinaryDataRef key, 
               leveldb::Iterator* it=NULL);
   bool seekTo(DB_SELECT db, 
               DB_PREFIX pref, 
               BinaryDataRef key, 
               leveldb::Iterator* it=NULL);

   bool seekToTxByHash(BinaryDataRef txHash);

   /////////////////////////////////////////////////////////////////////////////
   string getPrefixName(uint8_t prefixInt);
   string getPrefixName(DB_PREFIX pref);

   bool checkPrefixByte(DB_PREFIX prefix,
                        bool rewindWhenDone=false);

   bool checkPrefixByte(BinaryRefReader brr, 
                        DB_PREFIX prefix,
                        bool rewindWhenDone=false);


   /////////////////////////////////////////////////////////////////////////////
   // NOTE:  These ref readers become invalid as soon as the iterator is moved!
   void iteratorToRefReaders( leveldb::Iterator* it, 
                              BinaryRefReader & brrKey,
                              BinaryRefReader & brrValue);


   
   BLKDATA_TYPE readBlkDataKey5B( BinaryRefReader & brr,
                                  uint32_t & height,
                                  uint8_t  & dupID);

   /////////////////////////////////////////////////////////////////////////////
   void deleteIterator(DB_SELECT db);
   void resetIterator(DB_SELECT db);


   /////////////////////////////////////////////////////////////////////////////
   // Not sure why this is useful over getHeaderMap() ... this iterates over
   // the headers in hash-ID-order, instead of height-order
   void startHeaderIteration(void);

   /////////////////////////////////////////////////////////////////////////////
   void startBlkDataIteration(DB_PREFIX prefix);

   /////////////////////////////////////////////////////////////////////////////
   uint32_t hgtxToHeight(uint32_t hgtX)  {return (hgtX & 0xffffff00)>>8;}
   uint8_t  hgtxToDupID(uint32_t hgtX)   {return (hgtX & 0x000000ff);}
   uint32_t heightAndDupToHgtx(uint32_t hgt, uint8_t dup) {return hgt<<8|dup;}

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            bool     withPrefix=true);

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx, 
                            bool     withPrefix=true);

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx,
                            uint16_t txOutIdx,
                            bool     withPrefix=true);

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


   /////////////////////////////////////////////////////////////////////////////
   void resetIterReaders(void) 
               { currReadKey_.resetPosition(); currReadValue_.resetPosition(); }

   /////////////////////////////////////////////////////////////////////////////
   void getNextBlock(void);

   /////////////////////////////////////////////////////////////////////////////
   void getBlock(BlockHeader & bh, 
                 vector<Tx> & txList, 
                 leveldb::Iterator* iter=NULL,
                 bool ignoreMerkle = true);

   void readBlkDataTxValue(BinaryRefReader & brr, Tx* tx);




   void loadAllStoredHistory(void); 

   map<HashString, BlockHeader> getHeaderMap(void);
   BinaryData getRawHeader(BinaryData const & headerHash);
   bool addHeader(BinaryData const & headerHash, BinaryData const & headerRaw);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData getDBInfoKey(void);

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

   ////////////////////////////////////////////////////////////////////////////
   // SERIALIZE / UNSERIALIZE STORED* METHODS
   // These methods define exactly how Stored* objects are read and written
   // to the values of the database entries.  They don't do anything with the
   // keys of those entries.
   ////////////////////////////////////////////////////////////////////////////
   // UNSERIALIZE METHODS
   void unserializeStoredHeaderValue(   DB_SELECT            db,
                                        BinaryRefReader &    brr,
                                        StoredHeader &       sbh,
                                        bool ignoreMerkle = false);

   void unserializeStoredTxValue(       BinaryRefReader &    brr, 
                                        StoredTx &           stx);

   void unserializeStoredTxOutValue(    BinaryRefReader &    brr, 
                                        StoredTxOut &        stxo);

   bool unserializeStoredTxOutValue(    BinaryRefReader &    brr, 
                                        StoredTx &           stx, 
                                        uint32_t             txOutIndex);

   void unserializeStoredScriptHistory( BinaryRefReader &    brr, 
                                        StoredScriptHistory &ssh);


   ////////////////////////////////////////////////////////////////////////////
   // SERIALIZE METHODS
   void serializeStoredHeaderValue(     DB_SELECT db,
                                        StoredHeader const &        sbh,
                                        BinaryWriter &              bw);

   void serializeStoredTxValue(         StoredTx const &            stx,
                                        BinaryWriter &              bw);

   void serializeStoredTxOutValue(      StoredTxOut const &         stxo,
                                        BinaryWriter &              bw,
                                        bool forceSaveSpentness=false);

   void serializeStoredScriptHistory(   StoredScriptHistory &       ssh,
                                        BinaryWriter &              bw);

   /////////////////////////////////////////////////////////////////////////////
   // Interface to translate Stored* objects to/from persistent DB storage
   void putStoredHeader(StoredHeader & sbh,
                        bool withTx=false);

   bool getStoredHeader(StoredHeader & sbh,
                        BinaryDataRef headHash, 
                        bool withTx=false);

   bool getStoredHeader(StoredHeader & sbh,
                        uint32_t blockHgt,
                        uint8_t blockDup=UINT8_MAX,
                        bool withTx=false);

   bool getStoredHeader(StoredHeader & sbh,
                        uint32_t hgtX,
                        bool withTx=false);


   /////////////////////////////////////////////////////////////////////////////
   void putStoredTx(         StoredTx & st,
                             bool withTxOut=false);

   bool getStoredTx(         StoredTx & st,
                             BinaryDataRef txHash, 
                             uint32_t txIndex,
                             bool withTxOut=false);

   bool getStoredTx(         StoredTx & st,
                             uint32_t hgtX,
                             uint32_t txIndex,
                             bool withTxOut=false);


   /////////////////////////////////////////////////////////////////////////////
   void putStoredTxOut(      StoredTxOut const & sto);

   bool getStoredTxOut(      StoredTxOut & stxo,
                             uint32_t blockHeight,
                             uint32_t dupID,
                             uint32_t txIndex,
                             uint32_t txOutIndex);

   bool getStoredTxOut(      StoredTxOut & stxo,
                             uint32_t blockHeight,
                             uint32_t txIndex,
                             uint32_t txOutIndex);


   void putStoredScriptHistory( StoredScriptHistory & ssh);

   void getStoredScriptHistory( BinaryDataRef uniqueKey,
                                StoredScriptHistory & ssh);

   void getStoredScriptHistoryByRawScript(
                                BinaryDataRef rawScript,
                                StoredScriptHistory & ssh);

   ////////////////////////////////////////////////////////////////////////////
   // Some methods to grab data at the current iterator location.  Return
   // false if reading fails (maybe because we were expecting to find the
   // specified DB entry type, but the prefix byte indicated something else
   bool readStoredBlockAtIter(StoredHeader & sbh);

   bool readStoredTxAtIter(uint32_t height, uint8_t dupID, StoredTx & stx);

   bool readStoredTxOutAtIter(uint32_t height, uint8_t  dupID, uint16_t txIndex,
                                                            StoredTxOut & stxo);

   bool readStoredScriptHistoryAtIter( StoredScriptHistory & ssh);

   uint32_t readAllStoredScriptHistory(
                       map<BinaryData, StoredScriptHistory> & storedScrMap);


   // TxRefs are much simpler with LDB than the previous FileDataPtr construct
   TxRef getTxRef( BinaryDataRef txHash);
   TxRef getTxRef( uint32_t hgtx, uint16_t txIndex);
   TxRef getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex);


   bool checkStatus(leveldb::Status stat, bool warn=true);



private:
   string               baseDir_;

   BinaryData           genesisBlkHash_;
   BinaryData           genesisTxHash_;
   BinaryData           magicBytes_;

   HashString           topBlockHash_;
   uint32_t             topBlockHeight_;

   ARMORY_DB_TYPE       armoryDbType_;
   DB_PRUNE_TYPE        dbPruneType_;

   leveldb::Iterator*   iters_[2];
   leveldb::WriteBatch* batches_[2];
   leveldb::DB*         dbs_[2];  
   string               dbPaths_[2];
   bool                 iterIsDirty_[2];

   // This will be incremented every time startBatch is called, decremented
   // every time commitBatch is called.  We will only *actually* start a new
   // batch when the value starts at zero, or commit when it ends at zero.
   uint32_t             batchStarts_[2];
   

   vector<uint8_t>      validDupByHeight_;

   BinaryRefReader      currReadKey_;
   BinaryRefReader      currReadValue_;;
   
   string               lastGetValue_;
   bool                 dbIsOpen_;

   uint32_t             lowestScannedUpTo_;

   // In this case, a address is any TxOut script, which is usually
   // just a 25-byte script.  But this generically captures all types
   // of addresses including pubkey-only, P2SH, 
   map<BinaryData, StoredScriptHistory>   registeredSSH_;
};


#endif
