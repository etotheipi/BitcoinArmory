////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataMap.h"
#include "Blockchain.h"
#include "bdmenums.h"
#include "Progress.h"

class BlockDataManager;
class ScrAddrFilter;

typedef function<void(BDMPhase, double, unsigned, unsigned)> ProgressCallback;

/////////////////////////////////////////////////////////////////////////////
class DatabaseBuilder
{
private:
   BlockFiles& blockFiles_;
   Blockchain& blockchain_;
   LMDBBlockDatabase* db_;
   shared_ptr<ScrAddrFilter> scrAddrFilter_;

   const ProgressCallback progress_;
   const BinaryData magicBytes_;
   BlockOffset topBlockOffset_;
   const ARMORY_DB_TYPE dbType_;

   const BlockDataManagerConfig bdmConfig_;

private:
   void findLastKnownBlockPos();
   BlockOffset loadBlockHeadersFromDB(const ProgressCallback &progress);
   
   bool addBlocksToDB(
      BlockDataLoader& bdl, uint16_t fileID, size_t startOffset,
      shared_ptr<BlockOffset> bo);
   void parseBlockFile(const uint8_t* fileMap, size_t fileSize, size_t startOffset,
      function<bool(const uint8_t* data, size_t size, size_t offset)>);

   Blockchain::ReorganizationState updateBlocksInDB(
      const ProgressCallback &progress, bool verbose, bool initialLoad);
   BinaryData updateTransactionHistory(uint32_t startHeight);
   BinaryData scanHistory(uint32_t startHeight, bool reportprogress);
   void undoHistory(Blockchain::ReorganizationState& reorgState);

   void resetHistory(void);
   void resetSSHdb(void);

   bool reparseBlkFiles(unsigned fromID);
   map<BinaryData, BlockHeader> assessBlkFile(BlockDataLoader& bdl,
      unsigned fileID);

   ARMORY_DB_TYPE getDbType(void) const;

public:
   DatabaseBuilder(BlockFiles&, BlockDataManager&,
      const ProgressCallback&);

   void init(void);
   Blockchain::ReorganizationState update(void);
};
