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
class UnresolvedHashException {};

typedef function<void(BDMPhase, double, unsigned, unsigned)> ProgressCallback;

/////////////////////////////////////////////////////////////////////////////
class DatabaseBuilder
{
private:
   BlockFiles& blockFiles_;
   shared_ptr<Blockchain> blockchain_;
   LMDBBlockDatabase* db_;
   shared_ptr<ScrAddrFilter> scrAddrFilter_;

   const ProgressCallback progress_;
   const BinaryData magicBytes_;
   BlockOffset topBlockOffset_;
   const BlockDataManagerConfig bdmConfig_;

   unsigned checkedTransactions_ = 0;

private:
   void findLastKnownBlockPos();
   BlockOffset loadBlockHeadersFromDB(const ProgressCallback &progress);
   
   bool addBlocksToDB(
      BlockDataLoader& bdl, uint16_t fileID, size_t startOffset,
      shared_ptr<BlockOffset> bo, bool fullHints);
   void parseBlockFile(const uint8_t* fileMap, size_t fileSize, size_t startOffset,
      function<bool(const uint8_t* data, size_t size, size_t offset)>);

   Blockchain::ReorganizationState updateBlocksInDB(
      const ProgressCallback &progress, bool verbose, bool fullHints);
   BinaryData updateTransactionHistory(int32_t startHeight);
   BinaryData scanHistory(int32_t startHeight, bool reportprogress);
   void undoHistory(Blockchain::ReorganizationState& reorgState);

   void resetHistory(void);
   void resetSSHdb(void);

   bool reparseBlkFiles(unsigned fromID);
   map<BinaryData, shared_ptr<BlockHeader>> assessBlkFile(BlockDataLoader& bdl,
      unsigned fileID);

   void verifyTransactions(void);
   void commitAllTxHints(
      const map<uint32_t, BlockData>&, const set<unsigned>&);
   void commitAllStxos(shared_ptr<BlockDataFileMap>, 
      const map<uint32_t, BlockData>&, const set<unsigned>&);

   void repairTxFilters(const set<unsigned>&);
   void reprocessTxFilter(shared_ptr<BlockDataFileMap>, unsigned);

   void cycleDatabases(void);

public:
   DatabaseBuilder(BlockFiles&, BlockDataManager&,
      const ProgressCallback&);

   void init(void);
   Blockchain::ReorganizationState update(void);

   void verifyChain(void);
   unsigned getCheckedTxCount(void) const { return checkedTransactions_; }

   void verifyTxFilters(void);
};
