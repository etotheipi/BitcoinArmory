#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "BlockUtils.h"
#include "log.h"

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
   vector<size_t> txInIndexes_;

   ////
   virtual StoredTxOut& getStxoByIndex(uint16_t index)
   {
      auto stxoIter = stxoMap_.find(index);
      if (stxoIter != stxoMap_.end())
         return *(stxoIter->second.get());

      shared_ptr<StoredTxOut> thisStxo(new StoredTxOut);
      stxoMap_.insert({ index, thisStxo });

      return *(thisStxo.get());
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
   map<uint16_t, shared_ptr<PulledTx> > stxMap_;

   ////
   virtual DBTx& getTxByIndex(uint16_t index)
   {
      auto txIter = stxMap_.find(index);
      if (txIter != stxMap_.end())
         return *(txIter->second.get());

      shared_ptr<PulledTx> thisTx(new PulledTx);
      stxMap_.insert({ index, thisTx });

      return *(thisTx.get());
   }
};

class BlockWriteBatcher;

struct DataToCommit
{
   map<BinaryData, BinaryWriter> serialuzedSubSshToApply_;
   map<BinaryData, BinaryWriter> serializedSshToModify_;
   map<BinaryData, BinaryWriter> serializedStxOutToModify_;
   map<BinaryData, BinaryWriter> serializedSbhToUpdate_;

   uint32_t mostRecentBlockApplied_;
   BinaryData topBlockHash_;

   bool isSerialized_ = false;

   void serializeData(BlockWriteBatcher &bwb);

   void putSSH(LMDBBlockDatabase* db);
   void putSTX(LMDBBlockDatabase* db);
   void putSBH(LMDBBlockDatabase* db);

   void updateSDBI(LMDBBlockDatabase* db);
};

class BlockWriteBatcher
{
   friend struct DataToCommit;

public:
#if defined(_DEBUG) || defined(DEBUG )
   //use a tiny update threshold to trigger multiple commit threads for 
   //unit tests in debug builds
   static const uint64_t UPDATE_BYTES_THRESH = 300;
#else
   static const uint64_t UPDATE_BYTES_THRESH = 96 * 1024 * 1024;
#endif
   BlockWriteBatcher(const BlockDataManagerConfig &config, 
                     LMDBBlockDatabase* iface, 
                     bool forCommit = false);
   ~BlockWriteBatcher();
   
   void applyBlockToDB(uint32_t hgt, uint8_t dup, ScrAddrFilter& scrAddrData);
   void undoBlockFromDB(StoredUndoData &sud, ScrAddrFilter& scrAddrData);
   BinaryData scanBlocks(ProgressFilter &prog, 
      uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca);
   void setUpdateSDBI(bool set) { updateSDBI_ = set; }

private:

   struct LoadedBlockData
   {
      vector<shared_ptr<PulledBlock> > pbVec_;

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
   
   // search for entries in sshToModify_ that are empty and should
   // be deleted, removing those empty ones from sshToModify
   void searchForSSHKeysToDelete(map<BinaryData, StoredScriptHistory>& sshToModify);

   void preloadSSH(const ScrAddrFilter& sasd);
   BinaryData applyBlockToDB(shared_ptr<PulledBlock>& pb, ScrAddrFilter& scrAddrData,
                             bool forceUpdateValue = false);
   bool applyTxToBatchWriteData(
                           shared_ptr<PulledTx>& thisSTX,
                           StoredUndoData * sud,
                           ScrAddrFilter& scrAddrMap,
                           bool forceUpdateValue);

   bool parseTxIns(
      shared_ptr<PulledTx>& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData,
      bool forceUpdateValue);
   bool parseTxOuts(
      shared_ptr<PulledTx>& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData,
      bool forceUpdateValue);

   void resetTransactions(void);
   void clearTransactions(void);
   
   static void* grabBlocksFromDB(void *in);
   BinaryData applyBlocksToDB(ProgressFilter &prog);
   void cleanUpSshToModify(void);

   bool pullBlockFromDB(shared_ptr<PulledBlock>& pb, uint32_t height, uint8_t dup);

   shared_ptr<StoredTxOut>& makeSureSTXOInMap(
      LMDBBlockDatabase* iface,
      BinaryDataRef txHash,
      uint16_t txoId);

   void addStxToSTXOMap(const shared_ptr<PulledTx>& thisTx);
   bool lookForSTXOInMap(const BinaryData& txHash, const uint16_t& txoId,
      shared_ptr<StoredTxOut>& txOut) const;
   void addStxoToSTXOMap(const shared_ptr<StoredTxOut>& thisTxOut);

   void serializeData(void) { dataToCommit_.serializeData(*this); }

   static void executeWrite(BlockWriteBatcher* ptr);

private:

   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_;
   map<BinaryData, map<uint16_t, shared_ptr<StoredTxOut>>> stxoToModify_;
   map<BinaryData, StoredScriptHistory>                    sshToModify_;
   vector<shared_ptr<PulledBlock> >                        sbhToUpdate_;
   set<BinaryData>                                         keysToDelete_;

   DataToCommit                                            dataToCommit_;
   // incremented for each
   // applyBlockToDB and decremented for each
   // undoBlockFromDB
   uint32_t mostRecentBlockApplied_;
   
   //for the commit thread
   bool isForCommit_;

   //flag db transactions for reset
   bool resetTxn_ = false;

   //BWB to flag txn reset on
   BlockWriteBatcher* parent_ = nullptr;

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
};


#endif
// kate: indent-width 3; replace-tabs on;
