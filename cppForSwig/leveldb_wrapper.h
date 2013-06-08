#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <sstream>
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
  DB_PREFIX_BLKDATA,
  DB_PREFIX_REGADDR,
  DB_PREFIX_TXHINTS,
  DB_PREFIX_TRIENODES,
  DB_PREFIX_COUNT,
  DB_PREFIX_HEADHASH,
  DB_PREFIX_HEADHGT,
  DB_PREFIX_NONE,  // for seeking into DBs that don't use a prefix
} DB_PREFIX;


typedef enum
{
  ARMORY_DB_LITE,
  ARMORY_DB_PARTIAL,
  ARMORY_DB_FULL,
  ARMORY_DB_SUPER,
  ARMORY_DB_WHATEVER
} ARMORY_DB_TYPE;

#define ARMORY_DB_DEFAULT ARMORY_DB_PARTIAL

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
  TXOUT_SPENTSAV,
  TXOUT_SPENTFGT,
} TXOUT_SPENTNESS

typedef enum
{
  MERKLE_SER_NONE,
  MERKLE_SER_PARTIAL,
  MERKLE_SER_FULL
} MERKLE_SER_TYPE;

typedef enum
{
  REGADDR_UTXO_VECTOR,
  REGADDR_UTXO_TREE
} REGADDR_UTXO_TYPE;

typedef enum
{
  UPDATE_DB_NORMAL,
  UPDATE_DB_FORCE_VALID,
  UPDATE_DB_FORCE_INVALID,
} UPDATE_DB_TYPE




class InterfaceToLevelDB
{
public:
   InterfaceToLevelDB(string basedir, 
                      BinaryData const & genesisBlkHash,
                      BinaryData const & genesisTxHash,
                      BinaryData const & magic,
                      ARMORY_DB_TYPE     dbtype=ARMORY_DB_DEFAULT,
                      DB_PRUNE_TYPE      pruneType=DB_PRUNE_NONE);

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
   BinaryData getValue(DB_SELECT db, BinaryDataRef key);

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryDataRef object.  Remember, references are only valid
   // for as long as the iterator stays in one place.  If you want to collect 
   // lots of values from the database, you must make copies of them using reg
   // getValue() calls.
   BinaryDataRef getValueRef(DB_SELECT db, BinaryDataRef keyWithPrefix);

   /////////////////////////////////////////////////////////////////////////////
   // Get value using BinaryDataRef object.  Remember, references are only valid
   // for as long as the iterator stays in one place.  If you want to collect 
   // lots of values from the database, you must make copies of them using reg
   // getValue() calls.
   BinaryDataRef getValueRef(DB_SELECT db, DB_PREFIX_TYPE prefix, BinaryDataRef key);

   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryDataRefs key and value
   void putValue(DB_SELECT db, BinaryDataRef key, BinaryDataRef value);
   void putValue(DB_SELECT db, DB_PREFIX pref, BinaryDataRef key, BinaryDataRef value);

   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(DB_SELECT db, 
                    BinaryData const & key);
                    

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
               BinaryData const & key, 
               leveldb::Iterator* it=NULL);
   bool seekTo(DB_SELECT db, 
               DB_PREFIX pref, 
               BinaryData const & key, 
               leveldb::Iterator* it=NULL);



   /////////////////////////////////////////////////////////////////////////////
   // NOTE:  These ref readers become invalid as soon as the iterator is moved!
   void iteratorToRefReaders( leveldb::Iterator* it, 
                              BinaryRefReader & brrKey,
                              BinaryRefReader & brrValue);

   /////////////////////////////////////////////////////////////////////////////
   // Not sure why this is useful over getHeaderMap() ... this iterates over
   // the headers in hash-ID-order, instead of height-order
   void startHeaderIteration(void);

   /////////////////////////////////////////////////////////////////////////////
   void startBlockIteration(void);

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
   BinaryData sliceToBinaryData(leveldb::Slice slice)
      { return BinaryData((uint8_t*)(slice.data()), slice.size()); }
   void sliceToBinaryData(leveldb::Slice slice, BinaryData & bd)
      { bd.copyFrom((uint8_t*)(slice.data()), slice.size()); }
   BinaryReader sliceToBinaryReader(leveldb::Slice slice)
      { return BinaryReader.copyFrom((uint8_t*)(slice.data()), slice.size()); }
   void sliceToBinaryReader(leveldb::Slice slice, BinaryReader & brr)
      { brr.setNewData((uint8_t*)(slice.data()), slice.size()); }

   /////////////////////////////////////////////////////////////////////////////
   // The reamining sliceTo* methods are reference-based, which become
   // invalid after the iterator moves on.  
   BinaryDataRef sliceToBinaryDataRef(leveldb::Slice slice)
      { return BinaryDataRef( (uint8_t*)(slice.data()), slice.size()); }
   BinaryRefReader sliceToBinaryRefReader(leveldb::Slice slice)
      { return BinaryRefReader( (uint8_t*)(slice.data()), slice.size()); }

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


   BinaryData key
   
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

   void putStoredTx(         StoredTx const & st,
                             bool withTxOut=false);
   void getStoredTx(         StoredTx & st,
                             BinaryDataRef txHash, 
                             bool withTxOut=false);

   void putStoredTxOut(      StoredTxOut const & sto)
   void getStoredTxOut(      StoredTxOut & sto,
                             BinaryDataRef txHash)


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
