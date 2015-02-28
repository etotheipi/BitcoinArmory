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

#include <thread>
#include <condition_variable>
#include <chrono>

class StoredUndoData;
class StoredScriptHistory;
struct BlockDataManagerConfig;
class ProgressFilter;

/*
 This class accumulates changes to write to the database,
 and will do so when it gets to a certain threshold
*/

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

      for (uint32_t tx = 0; tx<nTx; tx++)
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

         stx.numTxOut_ = txOutIndexes.size() -1;

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
   }
};

class BlockWriteBatcher;

struct keyHasher
{
   size_t operator()(const BinaryData& k) const
   {
      size_t* keyHash = (size_t*)k.getPtr();

      return *keyHash;
   }
};

struct STXOS;

struct DataToCommit
{
   map<uint32_t, map<BinaryData, BinaryWriter>> serializedSubSshToApply_;
   map<BinaryData, map<BinaryData, BinaryWriter>> intermidiarrySubSshToApply_;
   map<BinaryData, set<BinaryData>> intermediarrySubSshKeysToDelete_;

   map<BinaryData, BinaryWriter>    serializedSshToModify_;
   map<BinaryData, BinaryWriter>    serializedStxOutToModify_;
   map<BinaryData, BinaryWriter>    serializedSpentness_;
   set<BinaryData>                  sshKeysToDelete_;
   map<uint32_t, set<BinaryData>>   subSshKeysToDelete_;
   set<BinaryData>                  spentnessToDelete_;
   map<BinaryData, BinaryData>      sshPrefixes_;
   
   //Fullnode only
   map<BinaryData, BinaryWriter> serializedTxCountAndHash_;
   map<BinaryData, BinaryWriter> serializedTxHints_;

   uint32_t mostRecentBlockApplied_;
   BinaryData topBlockHash_;

   bool isSerialized_ = false;

   const ARMORY_DB_TYPE dbType_;

   mutex lock_;

   ////
   DataToCommit(ARMORY_DB_TYPE dbType) :
      dbType_(dbType)
   {}

   DataToCommit(DataToCommit&&);

   ////
   void serializeData(BlockWriteBatcher& bwb,
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);
   void serializeSSH(BlockWriteBatcher& bwb,
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);
   void serializeStxo(STXOS& stxos);
   void serializeDataToCommit(BlockWriteBatcher& bwb,
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);

   void putSSH(LMDBBlockDatabase* db);
   void putSTX(LMDBBlockDatabase* db);
   void putSBH(LMDBBlockDatabase* db);
   void deleteEmptyKeys(LMDBBlockDatabase* db);
   void updateSDBI(LMDBBlockDatabase* db);

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
   static const uint32_t STXO_THRESHOLD = 2;
#else
   static const uint32_t UTXO_THRESHOLD = 200000;
   static const uint32_t STXO_THRESHOLD = 300000;
#endif

   ///data containers
   map<BinaryData, shared_ptr<StoredTxOut>> utxoMap_;
   map<BinaryData, shared_ptr<StoredTxOut>> utxoMapBackup_;
   vector<shared_ptr<StoredTxOut>>          stxoToUpdate_;

   ///
   const ARMORY_DB_TYPE dbType_;
   LMDBBlockDatabase* iface_ = nullptr;

   ///write members
   DataToCommit dataToCommit_;
   shared_ptr<mutex> writeMutex_;

   ///transaction syncing and recycling members
   mutex signalMutex_;
   condition_variable signalCV_;

   shared_ptr<STXOS> nextStxo_;
   atomic<bool> resetTxn_;
   atomic<bool> cleanup_;

   bool waitOnCleanup_ = false;

   LMDBEnv::Transaction dbTxn_;

   ///
   STXOS(LMDBBlockDatabase* db)
      : iface_(db), dbType_(db->getDbType()),
      dataToCommit_(dbType_)
   {
      writeMutex_.reset(new mutex());
   }

   STXOS(const STXOS& parent) :
      iface_(parent.iface_), dbType_(parent.dbType_),
      dataToCommit_(dbType_)
   {
      writeMutex_ = parent.writeMutex_;
      
      resetTxn_.store(false);
      cleanup_.store(false);
   }

   ~STXOS(void)
   {
      if (waitOnCleanup_)
         return;

      dbTxn_.commit();

      //signal all left over write threads to cleanup
      shared_ptr<STXOS> next = nextStxo_;
      while (next != nullptr)
      {
         next->cleanup_.store(true, memory_order_release);
         next->signalCV_.notify_all();

         next = next->nextStxo_;         
      }
   }
   
   ///
   StoredTxOut* lookForUTXOInMap(const BinaryData& txHash);
   StoredTxOut* makeSureSTXOInMap(LMDBBlockDatabase* iface, BinaryDataRef txHash,
      uint16_t txoId);
   
   void moveStxoToUTXOMap(const shared_ptr<StoredTxOut>& thisTxOut);

   void commit(void);
   thread commitStxo(bool waitOnCleanup);
   static void writeStxoToDB(shared_ptr<STXOS>);

   ///
   void resetTransactions(void);
   void recycleTxn(void);
};

class BlockWriteBatcher
{
   friend struct DataToCommit;

public:
#if defined(_DEBUG) || defined(DEBUG )
   //use a tiny update thresholds to trigger multiple commit threads for 
   //unit tests in debug builds
   static const uint64_t UPDATE_BYTES_THRESH = 300;
#else
   static const uint64_t UPDATE_BYTES_THRESH = 50 * 1024 * 1024;
#endif
   BlockWriteBatcher(const BlockDataManagerConfig &config, 
                     LMDBBlockDatabase* iface, 
                     bool forCommit = false);
   ~BlockWriteBatcher();

   BlockWriteBatcher(BlockWriteBatcher&& bwb);
   
   void reorgApplyBlock(uint32_t hgt, uint8_t dup, 
      ScrAddrFilter& scrAddrData, BlockFileAccessor& bfa);
   void undoBlockFromDB(StoredUndoData &sud, ScrAddrFilter& scrAddrData,
      BlockFileAccessor& bfa);
   BinaryData scanBlocks(ProgressFilter &prog, 
      uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca);
   void setUpdateSDBI(bool set) { updateSDBI_ = set; }
   void setCriticalErrorLambda(function<void(string)> lbd) { criticalError_ = lbd; }

private:

   struct GrabThreadData
   {
      GrabThreadData(void) { bufferLoad_ = 0; }
      GrabThreadData(const GrabThreadData&) = delete;
      
      GrabThreadData(GrabThreadData&& gtd)
      { 
         bufferLoad_ = 0;
         block_ = gtd.block_; 
      }

      //////
      shared_ptr<PulledBlock> block_ = nullptr;
      volatile atomic<uint32_t> bufferLoad_;

      mutex assignLock_, grabLock_;
      condition_variable grabCV_;
   };

   struct LoadedBlockData
   {
      shared_ptr<PulledBlock> interruptBlock_ = nullptr;

      uint32_t startBlock_ = 0;
      uint32_t endBlock_   = 0;
      
      uint32_t topLoadedBlock_ = 0;
      const uint32_t nThreads_;
      
      ScrAddrFilter& scrAddrFilter_;

      mutex scanLock_;
      condition_variable scanCV_;

      BlockFileAccessor BFA_;
      vector<GrabThreadData> GTD_;

      ////
      LoadedBlockData(const LoadedBlockData&) = delete;

      LoadedBlockData(uint32_t start, uint32_t end, ScrAddrFilter& scf,
         uint32_t nthreads) :
         startBlock_(start), endBlock_(end), scrAddrFilter_(scf),
         BFA_(scf.getDb()->getBlkFiles()), nThreads_(nthreads)
      {
         topLoadedBlock_ = start;

         interruptBlock_ = make_shared<PulledBlock>();
         interruptBlock_->nextBlock_ = interruptBlock_;

         for (uint32_t i = 0; i < nThreads_; i++)
            GTD_.push_back(move(GrabThreadData()));
      }

      shared_ptr<PulledBlock> getNextBlock(uint32_t i, unique_lock<mutex>* mu)
      {
         if (i>endBlock_)
            return nullptr;

         shared_ptr<PulledBlock> blk;
         GrabThreadData& currGTD = GTD_[i % nThreads_];

         while (1)
         {
            {
               unique_lock<mutex> assignLock(currGTD.assignLock_);
               blk = currGTD.block_->nextBlock_;
            }

            if (blk != nullptr)
               break;

            //wakeGrabThreads in case they are sleeping
            wakeGrabThreadsIfNecessary();

            //wait for grabThread signal
            TIMER_START("scanThreadSleep");
            scanCV_.wait_for(*mu, chrono::seconds(2));
            TIMER_STOP("scanThreadSleep");
         }

         currGTD.block_ = blk;
            
         //decrement bufferload
         currGTD.bufferLoad_.fetch_sub(
            blk->numBytes_, memory_order_release);

         return blk;
      }

      shared_ptr<PulledBlock> startGrabThreads(
         LMDBBlockDatabase* db, 
         shared_ptr<LoadedBlockData>& lbd,
         unique_lock<mutex>* mu)
      {
         for (uint32_t i = 0; i < nThreads_; i++)
         {
            thread grabThread(grabBlocksFromDB, lbd, db, i);
            grabThread.detach();
         }

         //wait until the first block is available before returning
         shared_ptr<PulledBlock> blk;
         GrabThreadData& currGTD = GTD_[startBlock_ % nThreads_];

         while (1)
         {
            {
               unique_lock<mutex> assignLock(currGTD.assignLock_);
               blk = currGTD.block_;
            }

            if (blk != nullptr)
               break;

            scanCV_.wait_for(*mu, chrono::seconds(2));
         }

         currGTD.bufferLoad_.fetch_sub(
            blk->numBytes_, memory_order_release);

         return blk;
      }

      void wakeGrabThreadsIfNecessary()
      {
         for (uint32_t i=0; i < nThreads_; i++)
         {
            if (GTD_[i].bufferLoad_.load(memory_order_consume) <
               UPDATE_BYTES_THRESH / (nThreads_ * 2))
            {
               /***
               Buffer is running low. Try to take ownership of the blockData
               mutex. If that succeeds, the grab thread is sleeping, so
               signal it to wake. Otherwise the grab thread is already running
               and is lagging behind the processing thread (very unlikely)
               ***/

               unique_lock<mutex> lock(GTD_[i].grabLock_, defer_lock);
               if (lock.try_lock())
                  GTD_[i].grabCV_.notify_all();
            }
         }
      }
   };

   struct CountAndHint
   {
      uint32_t count_ = 0;
      BinaryData hash_;
   };

   // We have accumulated enough data, actually write it to the db
   thread commit(bool force = false);

   static void writeToDB(shared_ptr<BlockWriteBatcher>);

   void prepareSshToModify(const ScrAddrFilter& sasd);
   BinaryData applyBlockToDB(shared_ptr<PulledBlock> pb, ScrAddrFilter& scrAddrData);
   void applyTxToBatchWriteData(
                           PulledTx& thisSTX,
                           StoredUndoData * sud,
                           ScrAddrFilter& scrAddrMap);
   bool parseTxIns(
      PulledTx& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData);
   bool parseTxOuts(
      PulledTx& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData);

   void resetTransactions(void);
   void clearTransactions(void);
   
   static void grabBlocksFromDB(shared_ptr<LoadedBlockData>, 
      LMDBBlockDatabase* db, uint32_t threadId);
   BinaryData applyBlocksToDB(ProgressFilter &progress,
      shared_ptr<LoadedBlockData> blockData);

   bool pullBlockFromDB(PulledBlock& pb,
      uint32_t height, uint8_t dup,
      BlockFileAccessor& bfa);
   static bool pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
      LMDBBlockDatabase* db, BlockFileAccessor& bfa);

   void serializeData(
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap) 
   { dataToCommit_.serializeData(*this, subsshMap); }

   map<BinaryData, StoredScriptHistory>& getSSHMap(
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);

private:

   StoredSubHistory& makeSureSubSSHInMap(
      const BinaryData& uniqKey,
      const BinaryData& hgtX);

   StoredSubHistory& makeSureSubSSHInMap_IgnoreDB(
      const BinaryData& uniqKey,
      const BinaryData& hgtX,
      const uint32_t& currentBlockHeight);

   StoredScriptHistory& makeSureSSHInMap(
      const BinaryData& uniqKey);

   void insertSpentTxio(
      const TxIOPair& txio,
            StoredSubHistory& inHgtSubSsh,
      const BinaryData& txOutKey,
      const BinaryData& txInKey);

   void getSshHeader(StoredScriptHistory& ssh, const BinaryData& uniqKey) const;

   void resetHistoryTransaction(void);

private:

   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_ = 0;

   map<BinaryData, map<BinaryData, StoredSubHistory> > subSshMapToWrite_ ;
   map<BinaryData, map<BinaryData, StoredSubHistory> >   subSshMap_;
   shared_ptr<map<BinaryData, StoredScriptHistory> >     sshToModify_;
   
   STXOS stxos_;

   //Fullnode only
   map<BinaryData, CountAndHint>                         txCountAndHint_;
   
   DataToCommit                                          dataToCommit_;
   // incremented for each
   // applyBlockToDB and decremented for each
   // undoBlockFromDB
   uint32_t mostRecentBlockApplied_;
   
   //for the commit thread
   const bool isForCommit_;
  
   //in reorgs, for reapplying blocks after an undo
   bool forceUpdateSsh_ = false;

   //flag db transactions for reset
   atomic<shared_ptr<BlockWriteBatcher>*> resetWriterPtr_ = nullptr;

   //BWB to flag txn reset on
   BlockWriteBatcher* parent_ = nullptr;

   shared_ptr<BlockWriteBatcher> commitingObject_;

   LMDBEnv::Transaction txn_;

   //to sync commits 
   mutex writeLock_;
   bool updateSDBI_ = true;

   atomic<bool> cleanupFlag_ = false;
   condition_variable signalCleanup_;

   //
   bool haveFullUTXOList_ = true;

   //to report back fatal errors to the main thread
   function<void(string)> criticalError_ = [](string)->void{};

   BinaryData topScannedBlockHash_ = BtcUtils::EmptyHash_;
};


#endif
// kate: indent-width 3; replace-tabs on;
