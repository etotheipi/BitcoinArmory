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

private:
   void findLastKnownBlockPos();
   BlockOffset loadBlockHeadersFromDB(const ProgressCallback &progress);
   
   bool addBlocksToDB(
      BlockDataLoader& bdl, uint16_t fileID, size_t startOffset,
      BlockOffset& bo);
   void parseBlockFile(const uint8_t* fileMap, size_t fileSize, size_t startOffset,
      function<void(const uint8_t* data, size_t size, size_t offset)>);

   Blockchain::ReorganizationState updateBlocksInDB(
      const ProgressCallback &progress);
   BinaryData updateTransactionHistory(uint32_t startHeight);
   BinaryData scanHistory(uint32_t startHeight);
   void undoHistory(Blockchain::ReorganizationState& reorgState);


public:
   DatabaseBuilder(BlockFiles&, BlockDataManager_LevelDB&,
      const ProgressCallback&);

   void init(void);
   uint32_t update(void);
};