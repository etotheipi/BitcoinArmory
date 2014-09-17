#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "BlockUtils.h"
#include "log.h"

class StoredHeader;
class StoredUndoData;
class StoredTx;
class StoredScriptHistory;
struct BlockDataManagerConfig;

/*
 This class accumulates changes to write to the database,
 and will do so when it gets to a certain threshold
*/
class BlockWriteBatcher
{
public:
   static const uint64_t UPDATE_BYTES_THRESH = 96 * 1024 * 1024;

   BlockWriteBatcher(const BlockDataManagerConfig &config, 
                     LMDBBlockDatabase* iface,
                     bool forCommit = false);
   ~BlockWriteBatcher();
   
   void applyBlockToDB(uint32_t hgt, uint8_t dup, ScrAddrFilter& scrAddrData);
   void undoBlockFromDB(StoredUndoData &sud, ScrAddrFilter& scrAddrData);
   void scanBlocks(uint32_t startBlock, uint32_t endBlock, ScrAddrFilter& sca);

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
   pthread_t commit(void);
   static void* commitThread(void*);
   
   // search for entries in sshToModify_ that are empty and should
   // be deleted, removing those empty ones from sshToModify
   set<BinaryData> searchForSSHKeysToDelete();

   void preloadSSH(const ScrAddrFilter& sasd);
   void applyBlockToDB(StoredHeader &sbh, ScrAddrFilter& scrAddrData);
   bool applyTxToBatchWriteData(
                           StoredTx &       thisSTX,
                           StoredUndoData * sud,
                           ScrAddrFilter& scrAddrMap);

   void resetTransactions(void);
   void clearTransactions(void);
   
   static void* grabBlocksFromDB(void *in);
   static void* applyBlockToDBThread(void *in);

private:
   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_;
   map<BinaryData, StoredTx>              stxToModify_;
   map<BinaryData, StoredScriptHistory>   sshToModify_;
   vector<StoredHeader>                   sbhToUpdate_;
   
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

   LMDB::Transaction* txnHeaders_ = nullptr;
   LMDB::Transaction* txnBlkdata_ = nullptr;

   //for managing SSH in supernode
   uint32_t commitId_ = 0;
   uint32_t deleteId_ = 0;
};


#endif
// kate: indent-width 3; replace-tabs on;
