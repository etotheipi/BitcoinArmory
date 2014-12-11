#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "BlockUtils.h"
#include "log.h"
#include "txio.h"

#include <thread>
#include <condition_variable>

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

   ////
   virtual StoredTxOut& initAndGetStxoByIndex(uint16_t index)
   {
      auto& thisStxo = stxoMap_[index];
      thisStxo.reset(new StoredTxOut);
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
      DBTx::unserialize(brr, isFragged);

      computeTxInIndexes();
   }
   
   ////
   void computeTxInIndexes()
   {
      BtcUtils::TxInCalcLength(dataCopy_.getPtr(), dataCopy_.getSize(),
         &txInIndexes_);
   }
};

struct PulledBlock : public DBBlock
{
   map<uint16_t, PulledTx> stxMap_;

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

   void preprocessStxo(ARMORY_DB_TYPE dbType)
   {
      for (auto& stx : stxMap_)
      {
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

struct DataToCommit
{
   map<BinaryData, BinaryWriter> serializedSubSshToApply_;
   map<BinaryData, BinaryWriter> serializedSshToModify_;
   map<BinaryData, BinaryWriter> serializedStxOutToModify_;
   map<BinaryData, BinaryWriter> serializedSbhToUpdate_;
   set<BinaryData>               keysToDelete_;

   uint32_t mostRecentBlockApplied_;
   BinaryData topBlockHash_;

   bool isSerialized_ = false;
   bool sshReady_ = false;

   mutex lock_;
   condition_variable condVar_;

   ////
   void serializeData(BlockWriteBatcher& bwb,
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);
   set<BinaryData> serializeSSH(BlockWriteBatcher& bwb,
      const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap);
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

class BlockWriteBatcher
{
   friend struct DataToCommit;

public:
#if defined(_DEBUG) || defined(DEBUG )
   //use a tiny update threshold to trigger multiple commit threads for 
   //unit tests in debug builds
   static const uint64_t UPDATE_BYTES_THRESH = 300;
   static const uint32_t UTXO_THRESHOLD = 5;
#else
   static const uint64_t UPDATE_BYTES_THRESH = 50 * 1024 * 1024;
   static const uint32_t UTXO_THRESHOLD = 100000;
#endif
   BlockWriteBatcher(const BlockDataManagerConfig &config, 
                     LMDBBlockDatabase* iface, 
                     bool forCommit = false);
   ~BlockWriteBatcher();
   
   void reorgApplyBlock(uint32_t hgt, uint8_t dup, ScrAddrFilter& scrAddrData);
   void undoBlockFromDB(StoredUndoData &sud, ScrAddrFilter& scrAddrData);
   BinaryData scanBlocks(ProgressFilter &prog, 
      uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca);
   void setUpdateSDBI(bool set) { updateSDBI_ = set; }

private:

   struct LoadedBlockData
   {
      vector<PulledBlock> pbVec_;

      uint32_t startBlock_ = 0;
      uint32_t endBlock_   = 0;
      uint32_t bufferLoad_ = 0;
      
      uint32_t topLoadedBlock_ = 0;
      uint32_t currentBlock_   = 0;
      uint32_t blockOffset_    = 0;
      
      bool fetching_        = false;
      atomic<int32_t> lock_;

      ScrAddrFilter& scrAddrFilter_;

      LoadedBlockData(uint32_t start, uint32_t end, ScrAddrFilter& scf) :
         startBlock_(start), endBlock_(end), scrAddrFilter_(scf)
      {
	      lock_ = 0;
         topLoadedBlock_ = start;
         currentBlock_   = start;
         blockOffset_    = start;
      }
   };

   // We have accumulated enough data, actually write it to the db
   thread commit(bool force = false);
   void writeToDB(void);
   
   void prepareSshToModify(const ScrAddrFilter& sasd);
   BinaryData applyBlockToDB(PulledBlock& pb, ScrAddrFilter& scrAddrData);
   bool applyTxToBatchWriteData(
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
   
   static void* grabBlocksFromDB(void *in);
   BinaryData applyBlocksToDB(ProgressFilter &prog);
   void clearSubSshMap(uint32_t id);

   bool pullBlockFromDB(PulledBlock& pb, uint32_t height, uint8_t dup);

   StoredTxOut* makeSureSTXOInMap(
      LMDBBlockDatabase* iface,
      BinaryDataRef txHash,
      uint16_t txoId);

   StoredTxOut* lookForUTXOInMap(const BinaryData& txHash, const uint16_t& txoId);

   void moveStxoToUTXOMap(const shared_ptr<StoredTxOut>& thisTxOut);

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

private:

   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_ = 0;

   map<BinaryData, shared_ptr<StoredTxOut>>  utxoMap_;
   map<BinaryData, shared_ptr<StoredTxOut>>  utxoMapBackup_;
   vector<shared_ptr<StoredTxOut> >          stxoToUpdate_;

   map<BinaryData, map<BinaryData, StoredSubHistory> >   subSshMapToWrite_;
   map<BinaryData, map<BinaryData, StoredSubHistory> >   subSshMap_;
   shared_ptr<map<BinaryData, StoredScriptHistory> >     sshToModify_;
   vector<PulledBlock>                                   sbhToUpdate_;

   DataToCommit                                          dataToCommit_;
   // incremented for each
   // applyBlockToDB and decremented for each
   // undoBlockFromDB
   uint32_t mostRecentBlockApplied_;
   
   //for the commit thread
   bool isForCommit_;
  
   //in reorgs, for reapplying blocks after an undo
   bool forceUpdateSsh_ = false;

   //flag db transactions for reset
   uint32_t resetTxn_ = 0;

   //BWB to flag txn reset on
   BlockWriteBatcher* parent_ = nullptr;

   shared_ptr<BlockWriteBatcher> commitingObject_;

   LoadedBlockData*   tempBlockData_ = nullptr;

   LMDBEnv::Transaction txn_;

   //for managing SSH in supernode
   uint32_t commitId_ = 0;
   uint32_t deleteId_ = 0;

   //to sync commits 
   mutex writeLock_;
   bool updateSDBI_ = true;

   //to sync the block reading thread with the scanning thread
   mutex              grabThreadLock_;
   condition_variable grabThreadCondVar_; 

   //
   bool haveFullUTXOList_ = true;
   uint32_t utxoFromHeight_ = 0;
};


#endif
// kate: indent-width 3; replace-tabs on;
