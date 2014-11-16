#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "BlockUtils.h"
#include "log.h"

#include <thread>
#include <condition_variable>

class StoredHeader;
class StoredUndoData;
class StoredTx;
class StoredScriptHistory;
struct BlockDataManagerConfig;
class ProgressFilter;

/*
 This class accumulates changes to write to the database,
 and will do so when it gets to a certain threshold
*/
class BlockWriteBatcher
{
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
      vector<StoredHeader*> sbhVec_;

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

      ~LoadedBlockData(void)
      {
         for (auto& sbhPtr : sbhVec_)
            delete sbhPtr;
      }
   };

   // We have accumulated enough data, actually write it to the db
   thread commit(bool force = false);
   static void* commitThread(void*);
   
   // search for entries in sshToModify_ that are empty and should
   // be deleted, removing those empty ones from sshToModify
   void searchForSSHKeysToDelete(map<BinaryData, StoredScriptHistory>& sshToModify);

   void preloadSSH(const ScrAddrFilter& sasd);
   BinaryData applyBlockToDB(StoredHeader &sbh, ScrAddrFilter& scrAddrData,
                             bool forceUpdateValue = false);
   bool applyTxToBatchWriteData(
                           StoredTx &       thisSTX,
                           StoredUndoData * sud,
                           ScrAddrFilter& scrAddrMap,
                           bool forceUpdateValue);

   bool parseTxIns(
      StoredTx& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData,
      bool forceUpdateValue);
   bool parseTxOuts(
      StoredTx& thisSTX,
      StoredUndoData * sud,
      ScrAddrFilter& scrAddrData,
      bool forceUpdateValue);

   void resetTransactions(void);
   void clearTransactions(void);
   
   static void* grabBlocksFromDB(void *in);
   BinaryData applyBlocksToDB(ProgressFilter &prog);
   void cleanUpSshToModify(void);

private:
   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_;
   map<BinaryData, StoredTx*>             stxToModify_;
   vector<StoredTx*>                      stxPulledFromDB_;
   map<BinaryData, StoredScriptHistory>   sshToModify_;
   vector<StoredHeader*>                  sbhToUpdate_;
   set<BinaryData>                        keysToDelete_;

   map<BinaryData, BinaryWriter>          serialuzedSubSshToApply_;
   map<BinaryData, BinaryWriter>          serializedSshToModify_;
   map<BinaryData, BinaryWriter>          serializedStxOutToModify_;
   
   // (theoretically) incremented for each
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
