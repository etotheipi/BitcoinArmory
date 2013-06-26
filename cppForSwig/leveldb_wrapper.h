#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <sstream>
#include <stack>
#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "BtcUtils.h"

#include "leveldb/db.h"
#include "leveldb/write_batch.h"
#include "log.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
////////////////////////////////////////////////////////////////////////////////

#define ARMORY_DB_VERSION   0x00

typedef enum
{
  NOT_BLKDATA,
  BLKDATA_HEADER,
  BLKDATA_TX,
  BLKDATA_TXOUT
} BLKDATA_TYPE

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

#define ARMORY_DB_DEFAULT ARMORY_DB_FULL

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
} TXOUT_SPENTNESS

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





class InterfaceToLevelDB
{
public:
   InterfaceToLevelDB(string basedir, 
                      BinaryData const & genesisBlkHash,
                      BinaryData const & genesisTxHash,
                      BinaryData const & magic,
                      ARMORY_DB_TYPE     dbtype=ARMORY_DB_DEFAULT,
                      DB_PRUNE_TYPE      pruneType=DB_PRUNE_NONE);

   ~InterfaceToLevelDB(void);

private:
   BinaryData txOutScriptToLDBKey(BinaryData const & script);
   BinaryData txHashToLDBKey(BinaryData const & txHash);
   //BinaryData headerHashToLDBKey(BinaryData const & headHash);

   /////////////////////////////////////////////////////////////////////////////
   void openDatabases(void);
   
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
   BinaryDataRef getValueRef(DB_SELECT db, DB_PREFIX_TYPE prefix, BinaryDataRef key);

   /////////////////////////////////////////////////////////////////////////////
   // Same as the getValueRef, in that they are only valid until the next get*
   // call.  These are convenience methods which basically just save us 
   BinaryDataRef getValueReader(DB_SELECT db, BinaryDataRef keyWithPrefix);
   BinaryDataRef getValueReader(DB_SELECT db, DB_PREFIX_TYPE prefix, BinaryDataRef key);



   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryDataRefs key and value
   void putValue(DB_SELECT db, BinaryDataRef key, BinaryDataRef value);
   void putValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key, BinaryDataRef value);
   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(DB_SELECT db, BinaryData const & key);
   void deleteValue(DB_SELECT db, DB_PREFIX pref, BinaryData const & key);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData sliceToBinaryData(leveldb::Slice slice);
   void       sliceToBinaryData(leveldb::Slice slice, BinaryData & bd);

   /////////////////////////////////////////////////////////////////////////////
   leveldb::Slice binaryDataToSlice(BinaryData const & bd) 
         {return leveldb::Slice(bd.getPtr(), bd.getSize());}
   leveldb::Slice binaryDataRefToSlice(BinaryDataRef const & bdr)
         {return leveldb::Slice(bdr.getPtr(), bdr.getSize());}

   /////////////////////////////////////////////////////////////////////////////
   // "Skip" refers to the behavior that the previous operation may have left
   // the iterator already on the next desired block.  So our "advance" op may
   // have finished before it started.  Alternatively, we may be on this block 
   // because we checked it and decide we don't care, so we want to skip it.
   bool advanceToNextHeader(bool skip=false);
   bool advanceToNextBlock(bool skip=false);
   void advanceIterAndRead(leveldb::Iterator* iter);

   bool seekTo(DB_SELECT db, 
               BinaryDataRef key, 
               leveldb::Iterator* it=NULL);
   bool seekTo(DB_SELECT db, 
               DB_PREFIX pref, 
               BinaryDataRef key, 
               leveldb::Iterator* it=NULL);


   /////////////////////////////////////////////////////////////////////////////
   string getPrefixName(DB_PREFIX_TYPE pref);
   bool checkPrefixByte(BinaryRefReader brr, DB_PREFIX_TYPE prefix);

   /////////////////////////////////////////////////////////////////////////////
   // NOTE:  These ref readers become invalid as soon as the iterator is moved!
   void iteratorToRefReaders( leveldb::Iterator* it, 
                              BinaryRefReader & brrKey,
                              BinaryRefReader & brrValue);


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
   uint32_t hgtxToHeight(uint32_t hgtx)  {return (hgtX & 0xffffff00)>>8;}
   uint8_t  hgtxToDupID(uint32_t hgtx)   {return (hgtX & 0x000000ff);}
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
                 ignoreMerkle = true);

   void readBlkDataTxValue(BinaryRefReader & brr, Tx* tx);

   map<HashString, BlockHeader> getHeaderMap(void);
   BinaryData getRawHeader(BinaryData const & headerHash);
   bool addHeader(BinaryData const & headerHash, BinaryData const & headerRaw);

   /////////////////////////////////////////////////////////////////////////////
   // All put/del ops will be batched/queued, and only executed when called
   // commitBatch().  We track the number calls to startBatch and commitBatch
   // and only write if we've called commit as many times as we called start.
   // In this way, we can have multiple levels starting and ending batches 
   // without caring whether a batched operation is already in process or if 
   // it's the first
   void startBatch(DB_SELECT db);
   void commitBatch(DB_SELECT db);
   void batchIsOn(DB_SELECT db)   { return (batches_[db] != NULL); }


   // Interface to translate Stored* objects to persistent DB storage
   void putStoredBlockHeader(StoredBlockHeader const & sbh,
                             bool withTx=false);

   void getStoredBlockHeader(StoredBlockHeader & sbh,
                             BinaryDataRef headHash, 
                             bool withTx=false);

   void getStoredBlockHeader(StoredBlockHeader & sbh,
                             uint32_t blockHgt,
                             uint8_t blockDup=UINT8_MAX,
                             bool withTx=false);

   void getStoredBlockHeader(StoredBlockHeader & sbh,
                             uint32_t hgtX,
                             bool withTx=false);


   void putStoredTx(         StoredTx const & st,
                             bool withTxOut=false);

   void getStoredTx(         StoredTx & st,
                             BinaryDataRef txHash, 
                             uint32_t txIndex,
                             bool withTxOut=false);

   void getStoredTx(         StoredTx & st,
                             uint32_t hgtX,
                             uint32_t txIndex,
                             bool withTxOut=false);


   void putStoredTxOut(      StoredTxOut const & sto)

   void getStoredTxOut(      StoredTxOut & sto,
                             BinaryDataRef txHash, 
                             uint32_t txIndex,
                             uint32_t txOutIndex,
                             BinaryDataRef txHash)

   void getStoredTxOut(      StoredTxOut & sto,
                             uint32_t hgtX,
                             uint32_t txIndex,
                             uint32_t txOutIndex,
                             BinaryDataRef txHash)


   // TxRefs are much simpler with LDB than the previous FileDataPtr construct
   TxRef getTxRef( BinaryDataRef txHash);
   TxRef getTxRef( uint32_t hgtx, uint16_t txIndex);
   TxRef getTxRef( uint32_t hgt, uint8_t  dup, uint16_t txIndex);


   bool checkStatus(leveldb::Status stat)
   {
      if( stat.ok() )
         return true;
      Log::ERR() << "***LevelDB Error: " << stat.ToString();
      return false;
   }



private:
   string baseDir_;

   BinaryData genesisBlkHash_;
   BinaryData genesisTxHash_;
   BinaryData magicBytes_;

   HashString topBlockHash_;
   uint32_t   topBlockHeight_;

   ARMORY_DB_TYPE  armoryDbType_;
   DB_PRUNE_TYPE   dbPruneType_;

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

   BinaryRefReader currReadKey_;
   BinaryRefReader currReadValue_;;
   
   string lastGetValue_;
   bool   dbIsOpen_;

   // In this case, a address is any TxOut script, which is usually
   // just a 25-byte script.  But this generically captures all types
   // of addresses including pubkey-only, P2SH, 
   set<RegisteredAddress>   registeredAddrSet_;
   uint32_t                 lowestScannedUpTo_;
};


#endif
