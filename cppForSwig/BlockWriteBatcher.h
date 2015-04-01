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

#if defined(_DEBUG) || defined(DEBUG )
//use a tiny update thresholds to trigger multiple commit threads for 
//unit tests in debug builds
static const uint64_t UPDATE_BYTES_THRESH = 300;
#else
static const uint64_t UPDATE_BYTES_THRESH = 50 * 1024 * 1024;
#endif


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
class BlockDataProcessor;
class BlockDataContainer;
class LoadedBlockData;
struct GrabThreadData;

class BlockDataFeed
{
   struct BlockPacket
   {
      vector<shared_ptr<PulledBlock>> blocks_;
      size_t byteSize_ = 0;
   };

public:
   BlockDataFeed(uint32_t nThreads) :
      nThreads_(nThreads)
   {
      blockPackets_.resize(nThreads);
   }

   void chargeFeed(shared_ptr<LoadedBlockData> blockData);

private:
   const uint32_t nThreads_;

public:
   shared_ptr<BlockDataFeed> next_;
   vector<BlockPacket> blockPackets_;

   BinaryData topBlockHash_;
   uint32_t topBlockHeight_;
   uint32_t bottomBlockHeight_;
   uint32_t totalSizeInBytes_;

   bool hasData_ = false;
};

class LoadedBlockData
{
   friend struct GrabThreadData;

private:

   uint32_t startBlock_ = 0;
   uint32_t endBlock_ = 0;
   int32_t currentHeight_ = 0;

   uint32_t topLoadedBlock_ = 0;
   const uint32_t nThreads_;

   ScrAddrFilter& scrAddrFilter_;

   BlockFileAccessor BFA_;
   vector<GrabThreadData> GTD_;


public:
   mutex grabLock_, feedLock_;
   condition_variable grabCV_, feedCV_;

   shared_ptr<PulledBlock> interruptBlock_ = nullptr;

   shared_ptr<BlockDataFeed> blockDataFeed_;
   shared_ptr<BlockDataFeed> interruptFeed_ = nullptr;

   static int32_t getOffsetHeight(LoadedBlockData&, uint32_t);
   static bool isHeightValid(LoadedBlockData&, int32_t);
   static void nextHeight(LoadedBlockData&, int32_t&);
   static uint32_t getTopHeight(LoadedBlockData& lbd, PulledBlock&);
   static BinaryData getTopHash(LoadedBlockData& lbd, PulledBlock&);

private:
   LoadedBlockData(const LoadedBlockData&) = delete;

public:
   ~LoadedBlockData(void)
   {
      interruptBlock_->nextBlock_.reset();
      interruptBlock_.reset();

      interruptFeed_->next_.reset();
      interruptFeed_.reset();
   }

   LoadedBlockData(uint32_t start, uint32_t end, ScrAddrFilter& scf,
      uint32_t nthreads) :
      startBlock_(start), endBlock_(end), scrAddrFilter_(scf),
      BFA_(scf.getDb()->getBlkFiles()), nThreads_(nthreads)
   {
      currentHeight_ = start;
      topLoadedBlock_ = start;

      interruptBlock_ = make_shared<PulledBlock>();
      interruptBlock_->nextBlock_ = interruptBlock_;

      interruptFeed_ = make_shared<BlockDataFeed>(1);
      interruptFeed_->next_ = interruptFeed_;

      GTD_.resize(nThreads_);
   }

   shared_ptr<PulledBlock> getNextBlock(unique_lock<mutex>* mu);
   void startGrabThreads(shared_ptr<LoadedBlockData>& lbd);
   void wakeGrabThreadsIfNecessary();

   shared_ptr<BlockDataFeed> getNextFeed(void);
};

struct GrabThreadData
{
   GrabThreadData(void) 
   { 
      bufferLoad_ = 0; 
      block_.reset(new PulledBlock());
   }

   GrabThreadData(const GrabThreadData&) = delete;

   GrabThreadData(GrabThreadData&& gtd)
   {
      bufferLoad_ = 0;
      block_ = gtd.block_;
   }

   //////
   static void grabBlocksFromDB(shared_ptr<LoadedBlockData>, uint32_t threadId);

   static bool pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
      LMDBBlockDatabase* db, BlockFileAccessor& bfa);

   //////
   shared_ptr<PulledBlock> block_ = nullptr;
   volatile atomic<uint32_t> bufferLoad_;

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

class SSHheaders
{
public:
   SSHheaders(uint32_t nThreads)
      : nThreads_(nThreads)
   {}

   unique_lock<mutex>* getSshHeaders(shared_ptr<BlockDataContainer>);
   void buildSshHeadersFromSAF(const ScrAddrFilter& SAF);

private:
   void processSshHeaders(
      shared_ptr<BlockDataContainer>,
      const map<BinaryData, StoredScriptHistory>&);
   void fetchSshHeaders(map<BinaryData, StoredScriptHistory>& sshMap,
      const vector<const BinaryData*>& saVec);
   void checkForSubKeyCollisions(void);
   
   ///////
public:
   shared_ptr<map<BinaryData, StoredScriptHistory> > sshToModify_;
   mutex mu_;

private:
   const uint32_t nThreads_;
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

   shared_ptr<SSHheaders> sshHeaders_;

   uint32_t mostRecentBlockApplied_;
   BinaryData topBlockHash_;

   bool isSerialized_ = false;

   ////
   DataToCommit(void) {}

   DataToCommit(DataToCommit&&);

   ////
   void serializeData(shared_ptr<BlockDataContainer>);
   void serializeSSH(shared_ptr<BlockDataContainer>);
   void serializeStxo(STXOS& stxos);
   void serializeDataToCommit(shared_ptr<BlockDataContainer>);

   void putSSH();
   void putSubSSH(uint32_t keyLength);
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
   DataToCommit dataToCommit_;

   STXOS* parent_ = nullptr;
   mutex writeMutex_;
   thread committhread_;

   ///
   STXOS(void) 
   { 
      utxoMapBackup_.reset(new map<BinaryData, shared_ptr<StoredTxOut>>());
   }

   STXOS(STXOS& parent)
   {
      parent_ = &parent;
      utxoMapBackup_ = parent.utxoMapBackup_;
   }

   ///
   StoredTxOut* getStoredTxOut(const BinaryData& txHash, uint16_t utxoid);
   StoredTxOut* lookForUTXOInMap(const BinaryData& txHashAndId34, bool forceFetch=false);

   void moveStxoToUTXOMap(const shared_ptr<StoredTxOut>& thisTxOut);

   void commit(shared_ptr<BlockDataContainer> bdp);
   thread commitStxo(shared_ptr<BlockDataContainer> bdp);
   static void writeStxoToDB(shared_ptr<STXOS>);
};

class BlockDataThread
{
   friend class BlockDataContainer;
   friend class BlockDataProcessor;
   friend class SSHheaders;
   friend struct DataToCommit;
   friend struct STXOS;

public:

   BlockDataThread(BlockDataContainer& parent);

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

private:

   BlockDataThread(BlockDataThread& bdp) = delete;

   struct CountAndHint
   {
      uint32_t count_ = 0;
      BinaryData hash_;
   };


   thread tID_;
   BlockDataContainer* parent_;

   vector<shared_ptr<PulledBlock>> blocks_;

   map<BinaryData, map<BinaryData, StoredSubHistory> > subSshMap_;
   STXOS stxos_;

   function<void(shared_ptr<PulledBlock>)> processMethod_;

   bool workDone_ = false;
   const bool undo_;

   //Fullnode only
   map<BinaryData, CountAndHint> txCountAndHint_;
};

class BlockDataContainer
{
   friend class BlockDataProcessor;
   friend class BlockDataThread;
   friend class SSHheaders;
   friend struct DataToCommit;

private:
   DataToCommit dataToCommit_;

   BlockDataProcessor *parent_;
   bool updateSDBI_ = true;
   bool forceUpdateSsh_ = false;

public:
   STXOS commitStxos_;
   
   uint32_t highestBlockProcessed_ = 0;
   uint32_t lowestBlockProcessed_ = 0;
   BinaryData topScannedBlockHash_ = BtcUtils::EmptyHash_;
   
   const uint32_t nThreads_;
   vector<shared_ptr<BlockDataThread>> threads_;

   const bool undo_;

public:
   BlockDataContainer(BlockDataProcessor* bdpPtr);

   void startThreads(void)
   {
      auto processThread = [this](uint32_t i)->void
      { threads_[i]->processBlockFeed(); };

      for (uint32_t i = 0; i < nThreads_; i++)
      {
         threads_[i]->tID_ = thread(processThread, i);
         threads_[i]->tID_.detach();
      }
   }
};

class BlockDataProcessor
{
   friend class BlockDataContainer;
private:

   const uint32_t nThreads_;
   const bool undo_;
   
public:
   shared_ptr<SSHheaders> sshHeaders_;

   shared_ptr<BlockDataContainer> worker_;
   shared_ptr<BlockDataContainer> writer_;
   
   mutex workMutex_;
   mutex writeMutex_;
   condition_variable workCV_;

   bool forceUpdateSSH_ = false;
   uint32_t forceUpdateSshAtHeight_ = UINT32_MAX;
   BinaryData lastScannedBlockHash_;

public:
   BlockDataProcessor(uint32_t nThreads, bool undo)
      : nThreads_(nThreads), undo_(undo)
   {
      if (undo)
      {
         sshHeaders_.reset(new SSHheaders(1));
         sshHeaders_->sshToModify_.reset(
            new map<BinaryData, StoredScriptHistory>());
      }
   }

   ~BlockDataProcessor()
   {
      unique_lock<mutex> lock(workMutex_);
   }

   thread startThreads(shared_ptr<LoadedBlockData>);
   void processBlockData(shared_ptr<LoadedBlockData>);
   thread commit(bool force = false);

   map<BinaryData, map<BinaryData, StoredSubHistory>> getSubSSHMap(void) const
   {
      if (nThreads_ != 1)
         throw runtime_error(
            "do not call this method with several processing threads");

      return worker_->threads_[0]->subSshMap_;
   }

   STXOS stxos_;

private:
   static void writeToDB(shared_ptr<BlockDataContainer>);
};

class BlockWriteBatcher
{
   friend class SSHheaders;
   friend struct DataToCommit;

public:
   BlockWriteBatcher(const BlockDataManagerConfig &config, 
      LMDBBlockDatabase* iface, ScrAddrFilter&, bool undo=false);
   
   BinaryData scanBlocks(ProgressFilter &prog, 
      uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca,
      bool forceUpdateFromHeight=false);
   
   void setCriticalErrorLambda(function<void(string)> lbd) 
   { criticalError_ = lbd; }
   static void criticalError(string msg)
   { criticalError_(msg); }

private:
   void prepareSshToModify(const ScrAddrFilter& sasd);

   BinaryData applyBlocksToDB(ProgressFilter &progress,
      shared_ptr<LoadedBlockData> blockData);
   
   bool pullBlockFromDB(PulledBlock& pb,
      uint32_t height, uint8_t dup,
      BlockFileAccessor& bfa);

private:
   void insertSpentTxio(
      const TxIOPair& txio,
            StoredSubHistory& inHgtSubSsh,
      const BinaryData& txOutKey,
      const BinaryData& txInKey);

public:
   static ARMORY_DB_TYPE armoryDbType_;
   static LMDBBlockDatabase* iface_;
   static ScrAddrFilter* scrAddrData_;
   
private:
   //to report back fatal errors to the main thread
   static function<void(string)> criticalError_;

   ////
   BlockDataProcessor dataProcessor_;
};

#endif
// kate: indent-width 3; replace-tabs on;
