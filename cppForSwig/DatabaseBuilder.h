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

class BlockDataManager_LevelDB;
class ScrAddrFilter;

typedef function<void(BDMPhase, double, unsigned, unsigned)> ProgressCallback;

#define DEBUG_THREAD_COUNT 2

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

   const unsigned threadCount_;

private:
   void findLastKnownBlockPos();
   BlockOffset loadBlockHeadersFromDB(const ProgressCallback &progress);
   
   bool addBlocksToDB(
      BlockDataLoader& bdl, uint16_t fileID, size_t startOffset,
      shared_ptr<BlockOffset> bo);
   void parseBlockFile(const uint8_t* fileMap, size_t fileSize, size_t startOffset,
      function<void(const uint8_t* data, size_t size, size_t offset)>);

   Blockchain::ReorganizationState updateBlocksInDB(
      const ProgressCallback &progress, bool verbose);
   BinaryData updateTransactionHistory(uint32_t startHeight);
   BinaryData scanHistory(uint32_t startHeight, bool reportprogress);
   void undoHistory(Blockchain::ReorganizationState& reorgState);

   unsigned getThreadCount(void)
   {
      #ifdef _DEBUG
            return DEBUG_THREAD_COUNT;
      #else
            return thread::hardware_concurrency();
      #endif
   }

   void resetHistory(void);
   void resetSSHdb(void);

   bool reparseBlkFiles(unsigned fromID);
   map<BinaryData, BlockHeader> assessBlkFile(BlockDataLoader& bdl,
      unsigned fileID);

public:
   DatabaseBuilder(BlockFiles&, BlockDataManager_LevelDB&,
      const ProgressCallback&);

   void init(void);
   uint32_t update(void);
};
