////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016-17, goatpig.                                           //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKCHAINSCANNER_H
#define _BLOCKCHAINSCANNER_H

#include "Blockchain.h"
#include "lmdb_wrapper.h"
#include "BDM_supportClasses.h"
#include "BlockDataMap.h"
#include "Progress.h"
#include "bdmenums.h"
#include "ThreadSafeClasses.h"

#include <future>
#include <atomic>
#include <exception>

#define BATCH_SIZE  1024 * 1024 * 512ULL

class ScanningException : public runtime_error
{
private:
   const unsigned badHeight_;

public:
   ScanningException(unsigned badHeight, const string &what = "")
      : runtime_error(what), badHeight_(badHeight)
   { }
};

////////////////////////////////////////////////////////////////////////////////
struct ParserBatch
{
public:
   map<unsigned, shared_ptr<BlockDataFileMap>> fileMaps_;

   atomic<unsigned> blockCounter_;
   mutex mergeMutex_;

   const unsigned start_;
   const unsigned end_;

   const unsigned startBlockFileID_;
   const unsigned targetBlockFileID_;

   map<unsigned, shared_ptr<BlockData>> blockMap_;
   map<BinaryData, map<unsigned, StoredTxOut>> outputMap_;
   map<BinaryData, map<BinaryData, StoredSubHistory>> sshMap_;
   vector<StoredTxOut> spentOutputs_;

   const shared_ptr<map<TxOutScriptRef, int>> scriptRefMap_;
   promise<bool> completedPromise_;
   unsigned count_;

public:
   ParserBatch(unsigned start, unsigned end, 
      unsigned startID, unsigned endID,
      shared_ptr<map<TxOutScriptRef, int>> scriptRefMap) :
      start_(start), end_(end), 
      startBlockFileID_(startID), targetBlockFileID_(endID),
      scriptRefMap_(scriptRefMap)
   {
      if (end < start)
         throw runtime_error("end > start");

      blockCounter_.store(start_, memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
class BlockchainScanner
{
private:

   struct TxFilterResults
   {
      BinaryData hash_;

      //map<blockId, set<tx offset>>
      map<uint32_t, set<uint32_t>> filterHits_;

      bool operator < (const TxFilterResults& rhs) const
      {
         return hash_ < rhs.hash_;
      }
   };

   shared_ptr<Blockchain> blockchain_;
   LMDBBlockDatabase* db_;
   ScrAddrFilter* scrAddrFilter_;
   BlockDataLoader blockDataLoader_;

   const unsigned totalThreadCount_;
   const unsigned writeQueueDepth_;
   const unsigned totalBlockFileCount_;

   BinaryData topScannedBlockHash_;

   ProgressCallback progress_ = 
      [](BDMPhase, double, unsigned, unsigned)->void{};
   bool reportProgress_ = false;

   //only for relevant utxos
   map<BinaryData, map<unsigned, StoredTxOut>> utxoMap_;

   unsigned startAt_ = 0;

   mutex resolverMutex_;

   BlockingStack<unique_ptr<ParserBatch>> outputQueue_;
   BlockingStack<unique_ptr<ParserBatch>> inputQueue_;
   BlockingStack<unique_ptr<ParserBatch>> commitQueue_;

   atomic<unsigned> completedBatches_;

private:
   void writeBlockData(void);
   void processAndCommitTxHints(ParserBatch*);
   void preloadUtxos(void);

   int32_t check_merkle(int32_t startHeight);

   void getFilterHitsThread(
      const set<BinaryData>& hashSet,
      atomic<int>& counter,
      map<uint32_t, set<TxFilterResults>>& resultMap);

   void processFilterHitsThread(
      map<uint32_t, map<uint32_t, 
      set<const TxFilterResults*>>>& filtersResultMap,
      TransactionalSet<BinaryData>& missingHashes,
      atomic<int>& counter, map<BinaryData, BinaryData>& results,
      function<void(size_t)> prog);

   shared_ptr<BlockData> getBlockData(
      ParserBatch*, unsigned);

   void processOutputs(void);
   void processOutputsThread(ParserBatch*);

   void processInputs(void);
   void processInputsThread(ParserBatch*);


public:
   BlockchainScanner(shared_ptr<Blockchain> bc, LMDBBlockDatabase* db,
      ScrAddrFilter* saf,
      BlockFiles& bf,
      unsigned threadcount, unsigned queue_depth, 
      ProgressCallback prg, bool reportProgress) :
      blockchain_(bc), db_(db), scrAddrFilter_(saf),
      totalThreadCount_(threadcount), writeQueueDepth_(queue_depth),
      blockDataLoader_(bf.folderPath()),
      progress_(prg), reportProgress_(reportProgress),
      totalBlockFileCount_(bf.fileCount())
   {}

   void scan(int32_t startHeight);
   void scan_nocheck(int32_t startHeight);

   void undo(Blockchain::ReorganizationState& reorgState);
   void updateSSH(bool);
   bool resolveTxHashes();

   const BinaryData& getTopScannedBlockHash(void) const
   {
      return topScannedBlockHash_;
   }
};

#endif