////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "BlockUtils.h"
#include "log.h"
#include "txio.h"
#include "SSHheaders.h"

#include <thread>
#include <condition_variable>
#include <chrono>

class StoredUndoData;
class StoredScriptHistory;
struct BlockDataManagerConfig;
class ProgressFilter;

#define MODIFIED_SSH_THRESHOLD 500

struct PulledTx : public DBTx
{
   map<uint16_t, shared_ptr<StoredTxOut>> stxoMap_;
   map<uint16_t, TxIOPair> preprocessedUTXO_;
   vector<size_t> txInIndexes_;

   //trying to avoid as many copies as possible, for speed and RAM
   BinaryDataRef dataCopy_;
   BinaryData bdDataCopy_;

   //32bytes for the hash and another 2 for the txout id
   vector<BinaryData> txHash34_;

   bool isCoinbase_ = false;
   ////
   virtual StoredTxOut& initAndGetStxoByIndex(uint16_t index)
   {
      auto& thisStxo = stxoMap_[index];
      thisStxo.reset(new StoredTxOut());
      thisStxo->txVersion_ = version_;
      return *thisStxo;
   }

   virtual bool haveAllTxOut(void) const
   {
      if (!isInitialized())
         return false;

      if (!isFragged_)
         return true;

      return stxoMap_.size() == numTxOut_;
   }

   virtual void unserialize(BinaryRefReader & brr, bool isFragged = false)
   {
      vector<size_t> offsetsOut;
      uint32_t nbytes = BtcUtils::StoredTxCalcLength(brr.getCurrPtr(),
         isFragged,
         &txInIndexes_,
         &offsetsOut);
      if (brr.getSizeRemaining() < nbytes)
      {
         LOGERR << "Not enough bytes in BRR to unserialize StoredTx";
         return;
      }

      brr.get_BinaryData(bdDataCopy_, nbytes);
      dataCopy_.setRef(bdDataCopy_);
      
      for (uint32_t i = 0; i < txInIndexes_.size() - 1; i++)
      {
         BinaryData opTxHashAndId = 
            dataCopy_.getSliceCopy(txInIndexes_[i], 32);

         const uint32_t opTxoIdx =
            READ_UINT32_LE(dataCopy_.getPtr() + txInIndexes_[i] + 32);
         opTxHashAndId.append(WRITE_UINT16_BE(opTxoIdx));

         txHash34_.push_back(move(opTxHashAndId));
      }

      isFragged_ = isFragged;
      numTxOut_ = (uint16_t)offsetsOut.size() - 1;
      version_ = READ_UINT32_LE(bdDataCopy_.getPtr());
      lockTime_ = READ_UINT32_LE(bdDataCopy_.getPtr() + nbytes - 4);

      if (isFragged_)
      {
         fragBytes_ = nbytes;
         numBytes_ = UINT32_MAX;
      }
      else
      {
         numBytes_ = nbytes;
         uint32_t span = offsetsOut[numTxOut_] - offsetsOut[0];
         fragBytes_ = numBytes_ - span;
         BtcUtils::getHash256(bdDataCopy_, thisHash_);
      }
   }
   
   virtual const BinaryDataRef getDataCopyRef(void) const
   {
      return dataCopy_;
   }

   virtual BinaryData& getDataCopy(void)
   {
      throw runtime_error("non const getDataCopy not implemented for PulledTx");
   }
   
   ////
   void computeTxInIndexes()
   {
      if (txInIndexes_.size() == 0)
      BtcUtils::TxInCalcLength(dataCopy_.getPtr(), dataCopy_.getSize(),
         &txInIndexes_);
   }
};

struct PulledBlock : public DBBlock
{
   map<uint16_t, PulledTx> stxMap_;
   shared_ptr<PulledBlock> nextBlock_ = nullptr;
   FileMapContainer fmp_;

   ////
   PulledBlock(void) : DBBlock() {}

   PulledBlock(const PulledBlock&) = default;
   PulledBlock& operator=(const PulledBlock&) = default;
	
   PulledBlock(PulledBlock&& pb)
   {
      dataCopy_ = move(pb.dataCopy_);
      thisHash_ = move(pb.thisHash_);
      merkle_ = move(pb.merkle_);
      stxMap_ = move(pb.stxMap_);

      fmp_ = pb.fmp_;

      numTx_ = pb.numTx_;
      numBytes_ = pb.numBytes_;
      blockHeight_ = pb.blockHeight_;
      duplicateID_ = pb.duplicateID_;
      merkleIsPartial_ = pb.merkleIsPartial_;
      isMainBranch_ = pb.isMainBranch_;
      blockAppliedToDB_ = pb.blockAppliedToDB_;
      isPartial_ = pb.isPartial_;
      unserBlkVer_ = pb.unserBlkVer_;
      unserDbType_ = pb.unserDbType_;
      unserPrType_ = pb.unserPrType_;
      unserMkType_ = pb.unserMkType_;
      hasBlockHeader_ = pb.hasBlockHeader_;
   }

   virtual DBTx& getTxByIndex(uint16_t index)
   {
      return stxMap_[index];
   }

   void preprocessTx(ARMORY_DB_TYPE dbType)
   {
      for (auto& stx : stxMap_)
      {
         stx.second.computeTxInIndexes();
         for (auto& stxo : stx.second.stxoMap_)
         {
            stxo.second->getScrAddress();
            stxo.second->getHgtX();

            stxo.second->hashAndId_ = stx.second.thisHash_;
            stxo.second->hashAndId_.append(
               WRITE_UINT16_BE(stxo.second->txOutIndex_));
            
            if (dbType == ARMORY_DB_SUPER)
            {
               auto& txio = stx.second.preprocessedUTXO_[stxo.first];
               txio.setTxOut(stxo.second->getDBKey(false));
               txio.setValue(stxo.second->getValue());
               txio.setFromCoinbase(stxo.second->isCoinbase_);
               txio.setMultisig(false);
               txio.setUTXO(true);
            }
         }
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   virtual void unserializeFullBlock(BinaryRefReader brr,
      bool doFrag,
      bool withPrefix)
   {
      if (withPrefix)
      {
         BinaryData magic = brr.get_BinaryData(4);
         uint32_t   nBytes = brr.get_uint32_t();

         if (brr.getSizeRemaining() < nBytes)
         {
            LOGERR << "Not enough bytes remaining in BRR to read block";
            return;
         }
      }

      BlockHeader bh(brr);
      uint32_t nTx = (uint32_t)brr.get_var_int();
      uint32_t hgt = blockHeight_;
      uint8_t dupid = duplicateID_;

      createFromBlockHeader(bh);
      numTx_ = nTx;
      blockHeight_ = hgt;
      duplicateID_ = dupid;

      numBytes_ = HEADER_SIZE + BtcUtils::calcVarIntSize(numTx_);
      if (dataCopy_.getSize() != HEADER_SIZE)
      {
         LOGERR << "Unserializing header did not produce 80-byte object!";
         return;
      }

      if (numBytes_ > brr.getSize())
      {
         LOGERR << "Anticipated size of block header is more than what we have";
         throw BlockDeserializingException();
      }

      thisHash_ = bh.getThisHash();

      for (uint32_t tx = 0; tx < nTx; tx++)
      {
         PulledTx & stx = stxMap_[tx];

         // We're going to have to come back to the beginning of the tx, later
         uint32_t txStart = brr.getPosition();

         // Read a regular tx and then convert it
         const uint8_t* ptr = brr.getCurrPtr();
         vector<size_t> txOutIndexes;
         size_t txSize = BtcUtils::TxCalcLength(ptr, brr.getSizeRemaining(),
            &stx.txInIndexes_, &txOutIndexes);
         numBytes_ += txSize;
         BtcUtils::getHash256(ptr, txSize, stx.thisHash_);


         //if fileMapPtr_ is poiting to something, we go this block from a
         //FileMap object, let's avoid copies and just point the data through a
         //bdref. If it's NULL, we got this the block data through the regular
         //DB accessor and it will die when pullBlockAtIter scopes out. In this 
         //case, we can't avoid the copy it.
         if (fmp_.current_ != nullptr)
            stx.dataCopy_ = BinaryDataRef(ptr, txSize);
         else
         {
            stx.bdDataCopy_ = BinaryData(ptr, txSize);
            stx.dataCopy_.setRef(stx.bdDataCopy_);
         }

         stx.numTxOut_ = txOutIndexes.size() - 1;

         stx.blockHeight_ = blockHeight_;
         stx.duplicateID_ = duplicateID_;

         stx.isFragged_ = doFrag;
         stx.version_ = READ_UINT32_LE(ptr);
         stx.txIndex_ = tx;

         for (uint32_t i = 0; i < stx.txInIndexes_.size() - 1; i++)
         {
            BinaryData opTxHashAndId =
               stx.dataCopy_.getSliceCopy(stx.txInIndexes_[i], 32);

            const uint32_t opTxoIdx =
               READ_UINT32_LE(stx.dataCopy_.getPtr() + stx.txInIndexes_[i] + 32);
            opTxHashAndId.append(WRITE_UINT16_BE(opTxoIdx));

            stx.txHash34_.push_back(move(opTxHashAndId));
         }

         if (stx.txHash34_.size() == 0)
            throw range_error("Block deserialization error: no txin found in tx");

         if (stx.txHash34_[0].startsWith(BtcUtils::EmptyHash_))
            stx.isCoinbase_ = true;

         //get the stxo map
         brr.resetPosition();
         brr.advance(txStart + txOutIndexes[0]);

         for (uint32_t txo = 0; txo < stx.numTxOut_; txo++)
         {
            StoredTxOut & stxo = stx.initAndGetStxoByIndex(txo);

            size_t numBytes = txOutIndexes[txo + 1] - txOutIndexes[txo];
            stxo.dataCopy_ = BinaryData(brr.getCurrPtr(), numBytes);

            stxo.txVersion_ = stx.version_;
            stxo.blockHeight_ = blockHeight_;
            stxo.duplicateID_ = duplicateID_;
            stxo.txIndex_ = tx;
            stxo.txOutIndex_ = txo;
            stxo.isCoinbase_ = stx.isCoinbase_;

            brr.advance(numBytes);
         }

         // Sitting at the nLockTime, 4 bytes before the end
         brr.advance(4);
      }

      /*
      This is actually not a valid marker of bad block data, some blocks are 
      shorter than the advertized length in raw data (after the magic word 
      and before the actual block). Only calculating the merkle root can
      guarantee the block data is sound.

      if (brr.getSizeRemaining() > 0)
      {
         throw runtime_error("Block deserialization error: "
            "deser size did not match block size in header");
      }*/
   }
};

class BlockWriteBatcher;
class BlockBatchProcessor;
class BatchThreadContainer;
class BlockDataBatchLoader;
struct PullBlockThread;

class BlockDataBatch
{
   /***
   Batch of PulledBlock objects, split in nThreads BlockPacket structs. Each 
   processor thread gets its own BlockPacket struct, so the amount of processing
   threads per batch is effectively defined by each current BlockDataBatch 
   nThreads_.
   ***/

   friend class BlockDataBatchLoader;
   friend class BatchThreadContainer;

   struct BlockPacket
   {
      vector<shared_ptr<PulledBlock>> blocks_;
      size_t byteSize_ = 0;
   };

public:
   BlockDataBatch(uint32_t nReaders, uint32_t nWorkers, uint32_t nWriters) :
      nReaders_(nReaders), nWorkers_(nWorkers), nWriters_(nWriters)
   {
      blockPackets_.resize(nWorkers);
   }

   ~BlockDataBatch(void)
   {

   }

private:
   void chargeBatch(BlockDataBatchLoader& blockData);


public:
   const uint32_t nReaders_;
   const uint32_t nWorkers_;
   const uint32_t nWriters_;

   clock_t chargeSleep_ = 0;
   clock_t readTime_ = 0;
   
   vector<BlockPacket> blockPackets_;

   BinaryData topBlockHash_;
   uint32_t topBlockHeight_;
   uint32_t bottomBlockHeight_;
   uint32_t totalSizeInBytes_;

   /***Reference to all stxos within each batch of block data. Each thread only
   knows of the blocks within its own BlockPacket, yet each thread needs to be 
   aware of all existing stxos.
   ***/
   shared_ptr<map<BinaryData, shared_ptr<StoredTxOut>>> batchStxos_;

   //Set to false to indicate grab threads ran out of raw data
   bool hasData_ = false;
};

class BlockDataBatchLoader
{
   /***
   Maintains threads that load up BlockDataBatch objects.
   ***/
   friend struct PullBlockThread;
   friend class BlockDataBatch;

private:

   uint32_t startBlock_ = 0;
   uint32_t endBlock_ = 0;
   int32_t currentHeight_ = 0;

   const uint32_t nThreads_;

   const ScrAddrFilter& scrAddrFilter_;

   BlockFileAccessor BFA_;
   vector<PullBlockThread> pullThreads_;

   atomic<bool> terminate_;

   BlockWriteBatcher* const bwbPtr_;

public:
   mutex pullLock_;
   condition_variable pullCV_;

   shared_ptr<PulledBlock> interruptBlock_ = nullptr;
   
   static shared_ptr<BlockDataBatch> interruptBatch_;

public:
   static int32_t getOffsetHeight(BlockDataBatchLoader&, uint32_t);
   static bool isHeightValid(BlockDataBatchLoader&, int32_t);
   static void nextHeight(BlockDataBatchLoader&, int32_t&);
   static uint32_t getTopHeight(BlockDataBatchLoader& lbd, PulledBlock&);
   static BinaryData getTopHash(BlockDataBatchLoader& lbd, PulledBlock&);

   uint32_t startBlock(void) const { return startBlock_; }

private:
   BlockDataBatchLoader(const BlockDataBatchLoader&) = delete;
   
   BFA_PREFETCH getPrefetchMode(void)
   {
      if (startBlock_ < endBlock_ && endBlock_ - startBlock_ > 100)
         return PREFETCH_FORWARD;
      
      return PREFETCH_NONE;
   }

public:
   BlockDataBatchLoader(BlockWriteBatcher *bwbPtr,
      uint32_t nthreads, shared_ptr<BlockDataBatchLoader> prevLoader);

   ~BlockDataBatchLoader(void);

   shared_ptr<PulledBlock> getNextBlock(unique_lock<mutex>* mu);
   void startPullThreads(shared_ptr<BlockDataBatchLoader>& lbd);
   void wakePullThreadsIfNecessary();

   shared_ptr<BlockDataBatch> chargeNextBatch(
      uint32_t nReaders, uint32_t nWorkers, uint32_t nWriters);

   void terminate(void);
};

struct PullBlockThread
{
   PullBlockThread(void)
   { 
      bufferLoad_ = 0; 
      block_.reset(new PulledBlock());
   }

   PullBlockThread(const PullBlockThread&) = delete;

   PullBlockThread(PullBlockThread&& gtd)
   {
      bufferLoad_ = 0;
      block_ = gtd.block_;
   }

   ~PullBlockThread(void)
   {
   /*   if (tID_.joinable())
         tID_.join();*/
   }

   //////
   static void pullThread(shared_ptr<BlockDataBatchLoader>, uint32_t threadId);

   static bool pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
      LMDBBlockDatabase* db, BlockFileAccessor& bfa);

   //////
   shared_ptr<PulledBlock> block_ = nullptr;
   volatile atomic<uint32_t> bufferLoad_;

   thread tID_;
   mutex assignLock_, grabLock_;
   condition_variable grabCV_;
};

struct keyHasher
{
   size_t operator()(const BinaryData& k) const
   {
      size_t* keyHash = (size_t*)k.getPtr();

      return *keyHash;
   }
};

struct STXOS;

struct ProcessedBatchSerializer
{
   struct SerializedSubSSH
   {
      BinaryData sshKey_;
      map<BinaryData, BinaryWriter> subSshMap_;
   };

   map<uint32_t, map<uint32_t, vector<SerializedSubSSH*>>>  keyedSubSshToApply_;
   map<uint32_t, map<uint32_t, set<BinaryData>>>            subSshKeysToDelete_;
   vector<map<uint32_t, set<BinaryData>>>                   sshKeysToDelete_;
   vector<map<BinaryData, SerializedSubSSH>>                subSshToApply_;
   vector<map<uint32_t, map<BinaryData, BinaryWriter>>>     serializedSshToModify_;
   
   map<BinaryData, BinaryWriter>          serializedStxOutToModify_;
   map<BinaryData, BinaryWriter>          serializedSpentness_;
   
   set<BinaryData>                        spentnessToDelete_;
   map<BinaryData, set<BinaryData>>       intermediarrySubSshKeysToDelete_;

   //Fullnode only
   map<BinaryData, BinaryWriter> serializedTxCountAndHash_;
   map<BinaryData, BinaryWriter> serializedTxHints_;

   uint32_t mostRecentBlockApplied_;
   BinaryData topBlockHash_;

   bool isSerialized_ = false;

   ////
   ProcessedBatchSerializer(void) 
   {
   }

   ~ProcessedBatchSerializer()
   {
      auto subsshcleanup = [this](uint32_t tID)->void
      {
         subSshToApply_[tID].clear();
      };

      auto sshcleanup = [this](uint32_t tID)->void
      {
         serializedSshToModify_[tID].clear();
      };

      vector<thread> cleanupThreads;
      for (uint32_t i = 0; i < subSshToApply_.size(); i++)
         cleanupThreads.push_back(thread(subsshcleanup, i));

      for (uint32_t i = 0; i < serializedSshToModify_.size(); i++)
         cleanupThreads.push_back(thread(sshcleanup, i));

      for (auto& thr : cleanupThreads)
      {
         if (thr.joinable())
            thr.join();
      }
   }

   ProcessedBatchSerializer(ProcessedBatchSerializer&&);

   ////
   void serializeBatch(shared_ptr<BatchThreadContainer>,
      unique_lock<mutex>* serializeLock);
   void updateSSH(shared_ptr<BatchThreadContainer>);
   void updateSSHThread(
      shared_ptr<BatchThreadContainer> btc, uint32_t tID);
   void serializeStxo(STXOS& stxos);
   void serializeSubSSH(shared_ptr<BatchThreadContainer>);
   void serializeSubSSHThread(
      shared_ptr<BatchThreadContainer> btc, uint32_t tID);
   void finalizeSerialization(
      shared_ptr<BatchThreadContainer> btc);
   void serializeSSH(
      shared_ptr<BatchThreadContainer> btc);


   void putSSH(uint32_t nWriters);
   void putSubSSH(uint32_t keyLength, uint32_t threadCount);
   void putSTX();
   void deleteEmptyKeys();
   void updateSDBI();

   uint32_t getProcessSSHnThreads(void) const;

   //During reorgs, alreadyScannedUpToBlock is not an accurate indicator of the 
   //last blocks this ssh has seen anymore. This value should be used instead.
   uint32_t forceUpdateSshAtHeight_ = UINT32_MAX;
};

struct STXOS
{
#if defined(_DEBUG) || defined(DEBUG )
   //use a tiny update thresholds to trigger multiple commit threads for 
   //unit tests in debug builds
   static const uint32_t UTXO_THRESHOLD = 2;
#else
   static const uint32_t UTXO_THRESHOLD = 300000;
#endif

   ///data containers
   map<BinaryData, shared_ptr<StoredTxOut>> utxoMap_;
   shared_ptr<map<BinaryData, shared_ptr<StoredTxOut>>> utxoMapBackup_;
   vector<shared_ptr<StoredTxOut>>          stxoToUpdate_;
   vector<BinaryData>                       keysToDelete_;

   ///write members
   ProcessedBatchSerializer processedBatchSerializer_;

   STXOS* parent_ = nullptr;
   shared_ptr<map<BinaryData, shared_ptr<StoredTxOut>>> feedStxos_;
   mutex writeMutex_;
   thread committhread_;

   const BlockWriteBatcher* bwbPtr_;

   ///
   STXOS(const BlockWriteBatcher* bwbPtr) : 
      bwbPtr_(bwbPtr)
   { 
      utxoMapBackup_.reset(new map<BinaryData, shared_ptr<StoredTxOut>>());
   }

   STXOS(STXOS& parent) :
      bwbPtr_(parent.bwbPtr_)
   {
      parent_ = &parent;
      utxoMapBackup_ = parent.utxoMapBackup_;
   }

   ///
   StoredTxOut* getStoredTxOut(const BinaryData& txHash, uint16_t utxoid);
   StoredTxOut* lookForUTXOInMap(const BinaryData& txHashAndId34, 
      bool forceFetch=false);

   void moveStxoToUTXOMap(const shared_ptr<StoredTxOut>& thisTxOut);

   void commit(shared_ptr<BatchThreadContainer> bdp);
   thread commitStxo(shared_ptr<BatchThreadContainer> bdp);
   static void writeStxoToDB(shared_ptr<STXOS>);
};

class BlockDataThread
{
   friend class BatchThreadContainer;
   friend class BlockBatchProcessor;
   friend class SSHheaders;
   friend struct ProcessedBatchSerializer;
   friend struct STXOS;

public:

   BlockDataThread(BatchThreadContainer& parent);

   void processBlockFeed(void);

private:
   
   void applyBlockToDB(shared_ptr<PulledBlock> pb);
   void applyTxToBatchWriteData(
      PulledTx& thisSTX,
      StoredUndoData * sud);

   bool parseTxIns(PulledTx& thisSTX, StoredUndoData * sud);
   bool parseTxOuts(PulledTx& thisSTX, StoredUndoData * sud);

   void prepareUndoData(StoredUndoData& sud,
      shared_ptr<PulledBlock> block);
   void processUndoData(StoredUndoData &sud, shared_ptr<PulledBlock>);
   void undoBlockFromDB(shared_ptr<PulledBlock> block);

   StoredSubHistory& makeSureSubSSHInMap(
      const BinaryData& uniqKey,
      const BinaryData& hgtX);
   StoredSubHistory& makeSureSubSSHInMap_IgnoreDB(
      const BinaryData& uniqKey,
      const BinaryData& hgtX);
   StoredScriptHistory& makeSureSSHInMap(
      const BinaryData& uniqKey);

   bool hasScrAddress(const BinaryData& scrAddr) const;

private:

   BlockDataThread(BlockDataThread& bdp) = delete;

   struct CountAndHint
   {
      uint32_t count_ = 0;
      BinaryData hash_;
   };


   thread tID_;
   BatchThreadContainer* container_;

   vector<shared_ptr<PulledBlock>> blocks_;

   map<BinaryData, map<BinaryData, StoredSubHistory> > subSshMap_;
   STXOS stxos_;

   function<void(shared_ptr<PulledBlock>)> processMethod_;

   const bool undo_;

   //Fullnode only
   map<BinaryData, CountAndHint> txCountAndHint_;
};

class BatchThreadContainer
{
   friend class BlockBatchProcessor;
   friend class BlockDataThread;
   friend class SSHheaders;
   friend struct ProcessedBatchSerializer;

private:
   shared_ptr<ProcessedBatchSerializer> processedBatchSerializer_;

   BlockBatchProcessor *processor_;
   bool updateSDBI_ = true;
   bool forceUpdateSsh_ = false;

   shared_ptr<SSHheaders> sshHeaders_;

   const uint32_t commitId_;
   shared_ptr<BlockDataBatch> dataBatch_;

   clock_t workTime_;
   clock_t writeTime_;

public:
   STXOS commitStxos_;
   
   uint32_t highestBlockProcessed_ = 0;
   uint32_t lowestBlockProcessed_ = 0;
   BinaryData topScannedBlockHash_ = BtcUtils::EmptyHash_;
   
   vector<shared_ptr<BlockDataThread>> threads_;

   const bool undo_;

   mutex serializeMutex_;
   condition_variable serializeCV_;

public:
   BatchThreadContainer(BlockBatchProcessor* bdpPtr, 
      shared_ptr<BlockDataBatch> bdb);

   void startThreads(void)
   {
      auto processThread = [this](uint32_t i)->void
      { threads_[i]->processBlockFeed(); };

      for (uint32_t i = 0; i < dataBatch_->nWorkers_; i++)
         threads_[i]->tID_ = thread(processThread, i);
   }
};

class BlockBatchProcessor
{
   friend class BatchThreadContainer;
private:

   const bool undo_;
   uint32_t commitId_ = 0;
   atomic<uint32_t> commitedId_;

   public:
   shared_ptr<SSHheaders> sshHeaders_;

   shared_ptr<BatchThreadContainer> worker_;
   shared_ptr<SSHheaders> currentSSHheaders_;
   
   mutex writeMutex_;
   condition_variable writeCV_;

   map<uint32_t, shared_ptr<BatchThreadContainer>> writeMap_;

   bool forceUpdateSSH_ = false;
   uint32_t forceUpdateSshAtHeight_ = UINT32_MAX;
   BinaryData lastScannedBlockHash_;

   BlockWriteBatcher* const bwbPtr_;

   clock_t cumulatedReadTime_ = 0;
   clock_t cumulatedWorkTime_ = 0;
   clock_t cumulatedWriteTime_ = 0;
   clock_t cumulatedBatchSleep_ = 0;
   uint32_t cumulatedCount_ = 0;

public:
   BlockBatchProcessor(BlockWriteBatcher* const, bool undo);

   ~BlockBatchProcessor()
   {
   }

   thread startThreads();
   void processBlockData();
   void commit();
   uint32_t getCommitedId(void) const
   { 
      return commitedId_.load(memory_order_acquire); 
   }

   map<BinaryData, map<BinaryData, StoredSubHistory>> getSubSSHMap(void) const
   {
      if (worker_->threads_.size() != 1)
         throw runtime_error(
            "do not call this method with several processing threads");

      return worker_->threads_[0]->subSshMap_;
   }

   void adjustThreadCount(shared_ptr<BatchThreadContainer> bdc);

   STXOS stxos_;

private:
   void serializeData(shared_ptr<BatchThreadContainer>);
   void writeThread();
};

class BlockWriteBatcher
{
   friend class BlockDataBatchLoader;
   friend struct ProcessedBatchSerializer;

public:
   BlockWriteBatcher(const BlockDataManagerConfig &config, 
      LMDBBlockDatabase* iface, const ScrAddrFilter&, bool undo=false);
   
   BinaryData scanBlocks(ProgressFilter &prog, 
      uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca,
      bool forceUpdateFromHeight=false);
   
   void setThreadCounts(
      uint32_t nReaders, uint32_t nWorkers, uint32_t nWriters) const;
   
   shared_ptr<BlockDataBatch> popBatch();

   bool hasScrAddress(const BinaryData& scrAddr) const
   { return scrAddrFilter_->hasScrAddress(scrAddr); }

   void rescanSSH();

private:
   void prepareSshHeaders(BlockBatchProcessor&, const ScrAddrFilter&);

   BinaryData applyBlocksToDB(ProgressFilter &progress, ScrAddrFilter& scf);
   void updateSSH(const BinaryData& topBlockHash, bool forceReset, bool versbose);
   
   bool pullBlockFromDB(PulledBlock& pb,
      uint32_t height, uint8_t dup,
      BlockFileAccessor& bfa);

   void insertSpentTxio(
      const TxIOPair& txio,
            StoredSubHistory& inHgtSubSsh,
      const BinaryData& txOutKey,
      const BinaryData& txInKey);

   //blocks if until the queue has room
   void pushBatch(shared_ptr<BlockDataBatch>);

public:
   static ARMORY_DB_TYPE armoryDbType_;
   static LMDBBlockDatabase* iface_;

   /***
   controls the amount of threads per task:

   Readers pull raw block data from DB/blockchain and serialize them into
   PulledBlock objects. Readers control thread load PullBlock objects into
   BlockDataBatch objects.

   Workers process take BlockDataBatch Objects and process the content into
   ssh, subssh and txios

   Writers commit to DB. Serializing runs on as many threads as writers.
   ***/

   uint32_t nThreads_ = 0;
   uint32_t totalThreadCount_;
   mutable atomic<uint32_t> nReaders_;
   mutable atomic<uint32_t> nWorkers_;
   mutable atomic<uint32_t> nWriters_;
   
   const bool undo_;

private:

   const ScrAddrFilter* scrAddrFilter_;
   
   uint32_t startBlock_;
   uint32_t endBlock_;
   bool forceUpdateSSH_;

   /***
   Supernode only:
   Keep track of all modified SSH if less than 500 blocks are scanned to speed up 
   updateSSH processing.
   ***/
   map<uint32_t, map<uint32_t, set<BinaryData>>> modifiedSSH_;
   bool trackSSH_ = false;

   /***
   The batches the readers thread load are put in this vector for the process
   thread to grab. The vector is MAX_BATCH_BUFFER large and behaves
   like a FIFO queue.
   ***/
   vector<shared_ptr<BlockDataBatch>> batchVector_;
   mutex grabLock_, batchLock_;
   condition_variable batchCV_;

   uint32_t currentBatch_ = 0;
   uint32_t topBatch_ = 0;
};

#endif
// kate: indent-width 3; replace-tabs on;
