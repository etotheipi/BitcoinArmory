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
struct BlockDataLink
{
   BlockData blockdata_;
   shared_future<BlockDataLink> next_;
};

////////////////////////////////////////////////////////////////////////////////
struct BlockDataBatch
{
   const unsigned start_;
   const unsigned end_;

   shared_future<BlockDataLink> first_;

   promise<bool> scanUtxosPromise;
   shared_future<bool> doneScanningUtxos_;

   mutex parseTxinMutex_, parseTxOutMutex_;
   condition_variable readThreadCV_;

   atomic<unsigned> highestProcessedHeight_;
   
   //keep a reference to the file mmaps used by this object since we don't copy 
   //the data, just point at it.
   map<unsigned, BlockFileMapPointer> fileMaps_;

   //only for addresses and utxos we track
   map<BinaryData, map<unsigned, StoredTxOut>> utxos_;
   map<BinaryData, StoredScriptHistory> ssh_;
   vector<StoredTxOut> spentTxOuts_;


   ////
   BlockDataBatch(unsigned start, unsigned end) : 
      start_(start), end_(end)
   {
      highestProcessedHeight_.store(start, memory_order_relaxed);
      doneScanningUtxos_ = scanUtxosPromise.get_future();
   }

   void flagUtxoScanDone(void) 
   { scanUtxosPromise.set_value(true); }
};

////////////////////////////////////////////////////////////////////////////////
struct BatchLink
{
   vector<shared_ptr<BlockDataBatch>> batchVec_;
   shared_future<shared_ptr<BatchLink>> next_;

   BinaryData topScannedBlockHash_;
};

////////////////////////////////////////////////////////////////////////////////
class BlockchainScanner
{
private:
   Blockchain* blockchain_;
   LMDBBlockDatabase* db_;
   shared_ptr<ScrAddrFilter> scrAddrFilter_;
   BlockDataLoader blockDataLoader_;

   const unsigned nBlockFilesPerBatch_ = 4;
   const unsigned nBlocksLookAhead_ = 10;
   const unsigned totalThreadCount_;

   BinaryData topScannedBlockHash_;

   //only for relevant utxos
   map<BinaryData, map<unsigned, StoredTxOut>> utxoMap_;

private:
   void readBlockData(shared_ptr<BlockDataBatch>);
   void scanBlockData(shared_ptr<BlockDataBatch>);
   
   void accumulateDataBeforeBatchWrite(vector<shared_ptr<BlockDataBatch>>&);
   void writeBlockData(shared_future<shared_ptr<BatchLink>>);
   void processAndCommitTxHints(
      const vector<shared_ptr<BlockDataBatch>>& batchVec);
   void preloadUtxos(void);


public:
   BlockchainScanner(Blockchain* bc, LMDBBlockDatabase* db,
      shared_ptr<ScrAddrFilter> saf,
      BlockFiles& bf) :
      blockchain_(bc), db_(db), scrAddrFilter_(saf),
      totalThreadCount_(thread::hardware_concurrency()),
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