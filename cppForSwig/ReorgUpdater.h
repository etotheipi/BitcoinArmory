////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "Blockchain.h"
#include "BDM_supportClasses.h"
#include "BlockWriteBatcher.h"
#include "Progress.h"

#include <thread>

#ifdef _MSC_VER
#define NOEXCEPT _NOEXCEPT
#else
#define NOEXCEPT noexcept
#endif

////////////////////////////////////////////////////////////////////////////////
// For now, we will call createUndoDataFromBlock(), and then pass that data to 
// undoBlockFromDB(), even though it will result in accessing the DB data 
// twice --
//    (1) LevelDB does an excellent job caching results, so the second lookup
//        should be instantaneous
//    (2) We prefer to integrate StoredUndoData objects now, which will be 
//        needed for pruning even though we don't strictly need it for no-prune
//        now (and could save a lookup by skipping it).  But I want unified
//        code flow for both pruning and non-pruning. 
static void createUndoDataFromBlock(
   LMDBBlockDatabase* iface,
   uint32_t hgt,
   uint8_t  dup,
   StoredUndoData & sud
   )
{
   SCOPED_TIMER("createUndoDataFromBlock");

   // Fetch the full, stored block
   StoredHeader sbh;
   iface->getStoredHeader(sbh, hgt, dup, true);
   if (!sbh.haveFullBlock())
      throw runtime_error("Cannot get undo data for block because not full!");

   sud.blockHash_ = sbh.thisHash_;
   sud.blockHeight_ = sbh.blockHeight_;
   sud.duplicateID_ = sbh.duplicateID_;

   // Go through tx list, fetch TxOuts that are spent, record OutPoints added
   for (uint32_t itx = 0; itx<sbh.numTx_; itx++)
   {
      StoredTx & stx = sbh.stxMap_[itx];

      // Convert to a regular tx to make accessing TxIns easier
      Tx regTx = stx.getTxCopy();
      for (uint32_t iin = 0; iin<regTx.getNumTxIn(); iin++)
      {
         TxIn txin = regTx.getTxInCopy(iin);
         BinaryData prevHash = txin.getOutPoint().getTxHash();
         uint16_t   prevIndex = txin.getOutPoint().getTxOutIndex();

         // Skip if coinbase input
         if (prevHash == BtcUtils::EmptyHash())
            continue;

         // Above we checked the block to be undone is full, but we
         // still need to make sure the prevTx we just fetched has our data.
         StoredTx prevStx;
         iface->getStoredTx(prevStx, prevHash);
         if (KEY_NOT_IN_MAP(prevIndex, prevStx.stxoMap_))
         {
            throw runtime_error("Cannot get undo data for block because not full!");
         }

         // 
         sud.stxOutsRemovedByBlock_.push_back(prevStx.stxoMap_[prevIndex]);
      }

      // Use the stxoMap_ to iterate through TxOuts
      for (uint32_t iout = 0; iout<stx.numTxOut_; iout++)
      {
         OutPoint op(stx.thisHash_, iout);
         sud.outPointsAddedByBlock_.push_back(op);
      }
   }
}


class ReorgUpdater
{
   Blockchain *const blockchain_;
   LMDBBlockDatabase* const iface_;

   set<HashString> txJustInvalidated_;
   set<HashString> txJustAffected_;
   vector<BlockHeader*> previouslyValidBlockHeaderPtrs_;

   BlockHeader* oldTopPtr_;
   BlockHeader* newTopPtr_;
   BlockHeader* branchPtr_;
   ScrAddrFilter *scrAddrData_;
   bool onlyUndo_;

   //list<StoredTx> removedTxes_, addedTxes_;

   const BlockDataManagerConfig &config_;

public:
   class MissingBlockToApply : public std::exception
   {
      const uint32_t height_;
      const uint8_t dup_;
   public:
      MissingBlockToApply(uint32_t height, uint8_t dup)
         : height_(height), dup_(dup) { }

      virtual const char* what() const NOEXCEPT //getting noexcept to compile for MSVS
      { return "A block could not be applied because it's missing"; }

      uint32_t height() const
      {
         return height_;
      }
      uint8_t dup() const
      {
         return dup_;
      }

   };

public:
   ReorgUpdater(
      const Blockchain::ReorganizationState& state,
      Blockchain *blockchain,
      LMDBBlockDatabase* iface,
      const BlockDataManagerConfig &config,
      ScrAddrFilter *scrAddrData,
      bool onlyUndo = false
      )
      : blockchain_(blockchain)
      , iface_(iface)
      , config_(config)
   {
      oldTopPtr_ = state.prevTopBlock;
      newTopPtr_ = &blockchain_->top();
      branchPtr_ = state.reorgBranchPoint;
      if (!branchPtr_)
         branchPtr_ = oldTopPtr_;
      scrAddrData_ = scrAddrData;
      onlyUndo_ = onlyUndo;

      /***
      reassessThread needs a write access to the DB. Most transactions
      created in the main thead are read only, and based on user request, a
      real only transaction may be opened. Since LMDB doesn't support different
      transaction types running concurently within the same thread, this whole
      code is ran in a new thread, while the calling thread joins on it, to
      guarantee control over the transactions in the running thread.
      ***/
      auto reassessThread = [this]()
      { this->reassessAfterReorgThread(); };
      thread reorgthread(reassessThread);
      reorgthread.join();

      if (errorProcessing_)
         throw *errorProcessing_;
   }

private:
   shared_ptr<std::exception> errorProcessing_;

   void undoBlocksFromDB()
   {
      // Walk down invalidated chain first, until we get to the branch point
      // Mark transactions as invalid

      NullProgressReporter nullProgress;
      ProgressReporterFilter nullFilter((ProgressReporter*)(&nullProgress));
      ProgressFilter progressFilter(&nullFilter, 0);

      LOGINFO << "Invalidating old-chain transactions...";
      BlockWriteBatcher blockWrites(config_, iface_, *scrAddrData_, true);
      blockWrites.scanBlocks(progressFilter, oldTopPtr_->getBlockHeight(),
         branchPtr_->getBlockHeight()+1, *scrAddrData_);
   }

   void updateBlockDupIDs(void)
   {
      //create a readwrite tx to update the dupIDs
      LMDBEnv::Transaction tx;
      iface_->beginDBTransaction(&tx, HEADERS, LMDB::ReadWrite);

      BlockHeader* thisHeaderPtr = branchPtr_;

      while (thisHeaderPtr->getNextHash() != BtcUtils::EmptyHash() &&
         thisHeaderPtr->getNextHash().getSize() > 0)
      {
         thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getNextHash());
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();
         iface_->markBlockHeaderValid(hgt, dup);
      }
   }

   void applyBlocksFromBranchPoint(void)
   {
      // Walk down the newly-valid chain and mark transactions as valid.  If 
      // a tx is in both chains, it will still be valid after this process
      // UPDATE for LevelDB upgrade:
      //       This used to start from the new top block and walk down, but 
      //       I need to apply the blocks in order, so I switched it to start
      //       from the branch point and walk up

      NullProgressReporter nullProgress;
      ProgressReporterFilter nullFilter((ProgressReporter*)(&nullProgress));
      ProgressFilter progressFilter(&nullFilter, 0);
      
      BlockWriteBatcher blockWrites(config_, iface_, *scrAddrData_);
      blockWrites.scanBlocks(progressFilter, branchPtr_->getBlockHeight() +1,
         newTopPtr_->getBlockHeight(), *scrAddrData_);
   }

   void reassessAfterReorgThread()
   {
      try
      {
         SCOPED_TIMER("reassessAfterReorg");
         LOGINFO << "Reassessing Tx validity after reorg";

         undoBlocksFromDB();

         if (onlyUndo_)
            return;

         updateBlockDupIDs();

         applyBlocksFromBranchPoint();

         LOGWARN << "Done reassessing tx validity";
      }
      catch (runtime_error&e)
      {
         errorProcessing_ = make_shared<runtime_error>(e);
      }
      catch (exception&e)
      {
         errorProcessing_ = make_shared<exception>(e);
      }
   }
};
