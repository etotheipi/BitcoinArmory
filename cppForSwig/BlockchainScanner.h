////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Blockchain.h"
#include "lmdb_wrapper.h"
#include "BDM_supportClasses.h"
#include "BlockDataMap.h"

#include <future>
#include <atomic>
#include <condition_variable>

#ifndef _BLOCKCHAINSCANNER_H
#define _BLOCKCHAINSCANNER_H

////////////////////////////////////////////////////////////////////////////////
struct BlockDataBatch
{
   const unsigned start_;
   const unsigned end_;

   promise<bool> scanUtxosPromise;
   shared_future<bool> doneScanningUtxos_;

   mutex parseTxinMutex_;

   unsigned highestProcessedHeight_;
   
   //keep a reference to the file mmaps used by this object since we don't copy 
   //the data, just point at it.
   map<unsigned, BlockFileMapPointer> fileMaps_;

   //only for addresses and utxos we track
   map<BinaryData, map<unsigned, StoredTxOut>> utxos_;
   map<BinaryData, StoredScriptHistory> ssh_;
   vector<StoredTxOut> spentTxOuts_;

   map<unsigned, BlockData> blocks_;

   ////
   BlockDataBatch(unsigned start, unsigned end) : 
      start_(start), end_(end)
   {
      highestProcessedHeight_ = start;
      doneScanningUtxos_ = scanUtxosPromise.get_future();
   }

   void flagUtxoScanDone(void) 
   { scanUtxosPromise.set_value(true); }
};

////////////////////////////////////////////////////////////////////////////////
struct BatchLink
{
   vector<shared_ptr<BlockDataBatch>> batchVec_;
   shared_ptr<BatchLink> next_;

   mutex readyToWrite_;
   BinaryData topScannedBlockHash_;
};

////////////////////////////////////////////////////////////////////////////////
class BlockchainScanner
{
private:
   Blockchain* blockchain_;
   LMDBBlockDatabase* db_;
   ScrAddrFilter* scrAddrFilter_;
   BlockDataLoader blockDataLoader_;

   const unsigned nBlockFilesPerBatch_ = 4;
   const unsigned nBlocksLookAhead_ = 10;
   const unsigned totalThreadCount_;

   BinaryData topScannedBlockHash_;

   //only for relevant utxos
   map<BinaryData, map<unsigned, StoredTxOut>> utxoMap_;

private:
   void scanBlockData(shared_ptr<BlockDataBatch>);
   
   void accumulateDataBeforeBatchWrite(vector<shared_ptr<BlockDataBatch>>&);
   void writeBlockData(shared_ptr<BatchLink>);
   void processAndCommitTxHints(
      const vector<shared_ptr<BlockDataBatch>>& batchVec);
   void preloadUtxos(void);


public:
   BlockchainScanner(Blockchain* bc, LMDBBlockDatabase* db,
      ScrAddrFilter* saf,
      BlockFiles& bf,
      unsigned threadcount) :
      blockchain_(bc), db_(db), scrAddrFilter_(saf),
      totalThreadCount_(threadcount),
      blockDataLoader_(bf.folderPath(), true, true, true)
   {
   }

   void scan(uint32_t startHeight);
   void undo(Blockchain::ReorganizationState& reorgState);
   void updateSSH(void);
   
   const BinaryData& getTopScannedBlockHash(void) const
   {
      return topScannedBlockHash_;
   }
};

#endif