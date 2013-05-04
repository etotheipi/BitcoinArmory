#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <sstream>
#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"
#include "BtcUtils.h"

#include "leveldb/db.h"
#include "leveldb/write_batch.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
//
////////////////////////////////////////////////////////////////////////////////

#define ARMORY_DB_VERSION   0x00

typedef enum
{
  BLK_PREFIX_DBINFO,
  BLK_PREFIX_BLKDATA,
  BLK_PREFIX_REGADDR,
  BLK_PREFIX_TXHINTS,
  BLK_PREFIX_TRIENODES,
  BLK_PREFIX_COUNT,
} BLK_PREFIX_TYPE;


typedef enum
{
  ARMORY_DB_LITE,
  ARMORY_DB_PARTIAL,
  ARMORY_DB_FULL,
  ARMORY_DB_SUPER
} ARMORY_DB_TYPE;

#define ARMORY_DB_DEFAULT ARMORY_DB_PARTIAL

typedef enum
{
  DB_PRUNE_ALL,
  DB_PRUNE_NONE
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
  TX_SER_NOTXOUT,
  TX_SER_COUNTOUT
} TX_SERIALIZE_TYPE;

typedef enum
{
  MERKLE_SER_NONE,
  MERKLE_SER_PARTIAL,
  MERKLE_SER_FULL
} MERKLE_SERIALIZE_TYPE;

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
   BinaryData txOutScriptToLevelDBKey(BinaryData const & script);
   BinaryData headerHashToLevelDBKey(BinaryData const & headHash);
   BinaryData txHashToLevelDBKey(BinaryData const & txHash);

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
   BinaryData getValue(DB_SELECT db, BinaryData const & key);


   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void putValue(DB_SELECT db, 
                 BinaryData const & key, 
                 BinaryData const & value);


   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(DB_SELECT db, 
                    BinaryData const & key);
                    

   /////////////////////////////////////////////////////////////////////////////
   BinaryData sliceToBinaryData(leveldb::Slice slice);
   void       sliceToBinaryData(leveldb::Slice slice, BinaryData & bd);

   /////////////////////////////////////////////////////////////////////////////
   // "Skip" refers to the behavior that the previous operation may have left
   // the iterator already on the next desired block.  So our "advance" op may
   // have finished before it started.  Alternatively, we may be on this block 
   // because we checked it and decide we don't care, so we want to skip it.
   bool advanceToNextBlock(bool skip=false);
   void advanceIterAndRead(leveldb::Iterator* iter);


   /////////////////////////////////////////////////////////////////////////////
   // Not sure why this is useful over getHeaderMap() ... this iterates over
   // the headers in hash-ID-order, instead of height-order
   void startHeaderIteration(void);

   /////////////////////////////////////////////////////////////////////////////
   void startBlockIteration(void);

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

   // The reamining sliceTo* methods are reference-based, which become
   // invalid after the iterator moves on.  Since they are just pointers,
   // there's no reason not to just copy them out.
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

   map<HashString, BlockHeader> getHeaderMap(void);
   BinaryData getRawHeader(BinaryData const & headerHash);
   bool addHeader(BinaryData const & headerHash, BinaryData const & headerRaw);

   BinaryData getDBInfoKey(void);

   bool checkStatus(leveldb::Status stat)
   {
      if( stat.ok() )
         return true;
      cout << "***LevelDB Error: " << stat.ToString() << endl;
      return false;
   }



private:
   string baseDir_;

   BinaryData genesisBlkHash_;
   BinaryData genesisTxHash_;
   BinaryData magicBytes_;

   HashString topBlockHash_;
   uint32_t   topBlockHeight_;

   ARMORY_DB_TYPE  dbTypeMin_;
   DB_PRUNE_TYPE   pruneTypeMin_;

   leveldb::Iterator*   iters_[2];
   leveldb::WriteBatch* batches_[2];
   leveldb::DB*         dbs_[2];  
   string               dbPaths_[2];


   BinaryRefReader currReadKey_;
   BinaryRefReader currReadValue_;;
   
   // In this case, a address is any TxOut script, which is usually
   // just a 25-byte script.  But this generically captures all types
   // of addresses including pubkey-only, P2SH, 
   set<registeredAddrSet_>      registeredAddrSet_;
   

};


#endif
