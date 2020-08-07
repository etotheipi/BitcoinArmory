////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKCHAINSCANNER_SUPER_H
#define _BLOCKCHAINSCANNER_SUPER_H

#include "Blockchain.h"
#include "lmdb_wrapper.h"
#include "BlockDataMap.h"
#include "Progress.h"
#include "bdmenums.h"
#include "ThreadSafeClasses.h"

#include <future>
#include <atomic>
#include <exception>

#define COMMIT_SSH_SIZE 1024 * 1024 * 256ULL
#define BATCH_SIZE_SUPER 1024 * 1024 * 128ULL

////////////////////////////////////////////////////////////////////////////////
struct ParserBatch_Super
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
   map<BinaryData, map<BinaryData, StoredSubHistory>> sshMap_;
   map<BinaryData, BinaryData> spentness_;

   map<BinaryData, BinaryData> hashToDbKey_;

   vector<pair<BinaryWriter, BinaryWriter>> serializedSubSsh_;

   promise<bool> completedPromise_;
   unsigned count_;

public:
   ParserBatch_Super(unsigned start, unsigned end,
      unsigned startID, unsigned endID) :
      start_(start), end_(end),
      startBlockFileID_(startID), targetBlockFileID_(endID)
   {
      if (end < start)
         throw runtime_error("end > start");

      blockCounter_.store(start_, memory_order_relaxed);
   }
};

////////////////////////////////////////////////////////////////////////////////
class SshIterator
{
private:
   LDBIter iter_;
   const pair<BinaryData, BinaryData>& bounds_;

public:
   SshIterator(LMDBBlockDatabase* db,
      pair<BinaryData, BinaryData>& bounds) :
      bounds_(move(bounds))
   {
      iter_ = db->getIterator(SUBSSH);
      iter_.seekTo(bounds.first);
   }

   bool isValid(void) const
   {
      if (!iter_.isValid())
         return false;

      return withinUpperBound();
   }

   bool withinUpperBound(void) const
   {
      return !(iter_.getKeyRef().getSliceRef(0, bounds_.second.getSize()) >
         bounds_.second);
   }

   bool advanceAndRead(void)
   {
      return iter_.advanceAndRead(DB_PREFIX_SCRIPT);
   }

   BinaryDataRef getKeyRef(void) const
   {
      return iter_.getKeyRef();
   }

   BinaryDataRef getValueRef(void) const
   {
      return iter_.getValueRef();
   }

   bool seekTo(const BinaryData& key)
   {
      return iter_.seekTo(key);
   }
};

////////////////////////////////////////////////////////////////////////////////
struct SshContainer
{
   StoredScriptHistory obj_;
   bool changed_ = false;

   void clear(void)
   {
      changed_ = false;
      obj_.clear();
   }
};

////////////////////////////////////////////////////////////////////////////////
class BlockchainScanner_Super
{
private:
   int startAt_ = 0;
   bool withUpdateSshHints_ = false;

   shared_ptr<Blockchain> blockchain_;
   LMDBBlockDatabase* db_;
   BlockDataLoader blockDataLoader_;

   BlockingStack<unique_ptr<ParserBatch_Super>> outputQueue_;
   BlockingStack<unique_ptr<ParserBatch_Super>> inputQueue_;
   BlockingStack<unique_ptr<ParserBatch_Super>> commitQueue_;
   
   BlockingStack<pair<BinaryData, BinaryData>>  sshBoundsQueue_;
   BlockingStack<unique_ptr<map<BinaryData, BinaryWriter>>> serializedSshQueue_;

   set<BinaryData> updateSshHints_;

   const unsigned totalThreadCount_;
   const unsigned writeQueueDepth_;
   const unsigned totalBlockFileCount_;
   map<unsigned, HeightAndDup> heightAndDupMap_;

   BinaryData topScannedBlockHash_;

   ProgressCallback progress_ =
      [](BDMPhase, double, unsigned, unsigned)->void{};
   bool reportProgress_ = false;

   atomic<unsigned> completedBatches_;
  
private:
   shared_ptr<BlockData> getBlockData(
      ParserBatch_Super*, unsigned);
   
   void writeBlockData(void);

   void processOutputs(void);
   void processOutputsThread(ParserBatch_Super*);

   void processInputs(void);
   void processInputsThread(ParserBatch_Super*);

   void updateSSHThread(int);
   void putSSH(const string& dbname);
   void putSpentness(ParserBatch_Super*);

   StoredTxOut getStxoByHash(
      BinaryDataRef&, uint16_t,
      ParserBatch_Super*,
      map<unsigned, shared_ptr<BlockDataFileMap>>&);

public:
   BlockchainScanner_Super(
      shared_ptr<Blockchain> bc, LMDBBlockDatabase* db,
      BlockFiles& bf,
      unsigned threadcount, unsigned queue_depth,
      ProgressCallback prg, bool reportProgress) :
      blockchain_(bc), db_(db),
      totalThreadCount_(threadcount), writeQueueDepth_(queue_depth),
      blockDataLoader_(bf.folderPath()),
      progress_(prg), reportProgress_(reportProgress),
      totalBlockFileCount_(bf.fileCount())
   {}

   void scan(void);
   void updateSSH(bool);
   void undo(Blockchain::ReorganizationState&);

   const BinaryData& getTopScannedBlockHash(void) const
   {
      return topScannedBlockHash_;
   }
};

#endif
