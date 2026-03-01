////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "BlockDataViewer.h"


/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(BlockDataManager* bdm) :
   zeroConfCont_(bdm->zeroConfCont()), rescanZC_(false)
{
   db_ = bdm->getIFace();
   bc_ = bdm->blockchain();
   saf_ = bdm->getScrAddrFilter().get();

   bdmPtr_ = bdm;

   groups_.push_back(WalletGroup(this, saf_));
   groups_.push_back(WalletGroup(this, saf_));

   flagRescanZC(false);
}

/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
   groups_.clear();
}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BtcWallet> BlockDataViewer::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
      return nullptr;

   return groups_[group_wallet].registerWallet(scrAddrVec, IDstr, wltIsNew);
}

/////////////////////////////////////////////////////////////////////////////
shared_ptr<BtcWallet> BlockDataViewer::registerLockbox(
   vector<BinaryData> const & scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
      return nullptr;
   
   return groups_[group_lockbox].registerWallet(scrAddrVec, IDstr, wltIsNew);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterWallet(const string& IDstr)
{
   groups_[group_wallet].unregisterWallet(IDstr);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterLockbox(const string& IDstr)
{
   groups_[group_lockbox].unregisterWallet(IDstr);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanWallets(shared_ptr<BDV_Notification> action)
{
   uint32_t startBlock = UINT32_MAX;
   uint32_t endBlock = UINT32_MAX;

   bool reorg = false;
   bool refresh = false;

   BDV_Notification_ZC::zcMapType zcMap;
   ScanWalletStruct scanData;
   map<BinaryData, LedgerEntry>* leMapPtr = nullptr;

   switch (action->action_type())
   {
   case BDV_Init:
   {
      startBlock = 0;
      endBlock = blockchain().top()->getBlockHeight();
      refresh = true;
      break;
   }

   case BDV_NewBlock:
   {
      auto reorgNotif =
         dynamic_pointer_cast<BDV_Notification_NewBlock>(action);
      auto& reorgState = reorgNotif->reorgState_;
         
      if (!reorgState.hasNewTop_)
         return;
    
      if (!reorgState.prevTopStillValid_)
      {
         //reorg
         reorg = true;
         startBlock = reorgState.reorgBranchPoint_->getBlockHeight();
      }
      else
      {
         startBlock = reorgState.prevTop_->getBlockHeight();
      }
         
      endBlock = reorgState.newTop_->getBlockHeight();

      //feed current valid zc map to scanwallet as well
      auto&& actionStruct = createZcStruct();
      zcMap = move(actionStruct->scrAddrZcMap_);

      break;
   }
   
   case BDV_ZC:
   {
      auto zcAction = 
         dynamic_pointer_cast<BDV_Notification_ZC>(action);
      
      zcMap = move(zcAction->scrAddrZcMap_);
      leMapPtr = &zcAction->leMap_;

      startBlock = endBlock = blockchain().top()->getBlockHeight();

      break;
   }

   case BDV_Refresh:
   {
      //feed current valid zc map to scanwallet as well
      auto&& actionStruct = createZcStruct();
      zcMap = move(actionStruct->scrAddrZcMap_);
      refresh = true;
      break;
   }

   default:
      return;
   }
   

   scanData.endBlock_ = endBlock;
   scanData.action_ = action->action_type();
   scanData.saStruct_.zcMap_ = move(zcMap);
   scanData.reorg_ = reorg;

   //get set of valid zc keys
   auto validkeymap = zeroConfCont_->getKeyToSpentScrAddrMap();

   //get current set of zc keys for wallet
   for (auto& group : groups_)
   {
      auto& groupZcSet = group.getValidZcSet();

      //intersect with validkeymap
      for (auto& zcKey : groupZcSet)
      {
         auto keyIter = validkeymap->find(zcKey);
         if (keyIter != validkeymap->end())
            continue;

         scanData.saStruct_.invalidatedZCKeys_.insert(zcKey);
      }
   }

   vector<uint32_t> startBlocks;
   for (auto& group : groups_)
      startBlocks.push_back(startBlock);

   auto sbIter = startBlocks.begin();
   for (auto& group : groups_)
   {
      if (group.pageHistory(refresh, false))
      {
         *sbIter = group.hist_.getPageBottom(0);
      }
         
      sbIter++;
   }

   //increment update id
   ++updateID_;

   sbIter = startBlocks.begin();
   for (auto& group : groups_)
   {
      scanData.startBlock_ = *sbIter;
      group.scanWallets(scanData, updateID_);

      if (leMapPtr != nullptr)
         leMapPtr->insert(scanData.saStruct_.zcLedgers_.begin(),
                          scanData.saStruct_.zcLedgers_.end());
      sbIter++;
   }

   lastScanned_ = endBlock;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasWallet(const BinaryData& ID) const
{
   return groups_[group_wallet].hasID(ID);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::registerAddresses(const vector<BinaryData>& saVec,
   const string& walletID, bool areNew)
{
   if (saVec.empty())
      return false;
   
   for (auto& group : groups_)
   {
      if (group.hasID(walletID))
         return group.registerAddresses(saVec, walletID, areNew);
   }

   return false;
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::registerArbitraryAddressVec(
   const vector<BinaryData>& saVec,
   const string& walletID)
{
   auto callback = [this, walletID](bool refresh)->void
   {
      if (!refresh)
         return;

      flagRefresh(BDV_refreshAndRescan, walletID);
   };

   shared_ptr<ScrAddrFilter::WalletInfo> wltInfo =
      make_shared<ScrAddrFilter::WalletInfo>();
   wltInfo->callback_ = callback;
   wltInfo->ID_ = walletID;

   for (auto& sa : saVec)
      wltInfo->scrAddrSet_.insert(sa);

   vector<shared_ptr<ScrAddrFilter::WalletInfo>> wltInfoVec;
   wltInfoVec.push_back(move(wltInfo));
   saf_->registerAddressBatch(move(wltInfoVec), false);
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BlockDataViewer::getTxLedgerByHash_FromWallets(
   const BinaryData& txHash) const
{
   return groups_[group_wallet].getTxLedgerByHash(txHash);
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BlockDataViewer::getTxLedgerByHash_FromLockboxes(
   const BinaryData& txHash) const
{
   return groups_[group_lockbox].getTxLedgerByHash(txHash);
}

////////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getTxByHash(HashString const & txhash) const
{
   StoredTx stx;
   if (db_->getStoredTx_byHash(txhash, &stx))
      return stx.getTxCopy();
   else
      return zeroConfCont_->getTxByHash(txhash);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::isTxMainBranch(const Tx &tx) const
{
   if (!tx.hasTxRef())
      return false;

   DBTxRef dbTxRef(tx.getTxRef(), db_);
   return dbTxRef.isMainBranch();
}

////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getPrevTxOut(TxIn & txin) const
{
   if (txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   if (!theTx.isInitialized())
      throw runtime_error("couldn't find prev tx");

   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOutCopy(idx);
}

////////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getPrevTx(TxIn & txin) const
{
   if (txin.isCoinbase())
      return Tx();

   OutPoint op = txin.getOutPoint();
   return getTxByHash(op.getTxHash());
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataViewer::getSenderScrAddr(TxIn & txin) const
{
   if (txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getScrAddressStr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataViewer::getSentValue(TxIn & txin) const
{
   if (txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}

////////////////////////////////////////////////////////////////////////////////
LMDBBlockDatabase* BlockDataViewer::getDB(void) const
{
   return db_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataViewer::getTopBlockHeight(void) const
{
   return bc_->top()->getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::reset()
{
   for (auto& group : groups_)
      group.reset();

   rescanZC_   = false;
   lastScanned_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanScrAddrVector(
   const map<BinaryData, ScrAddrObj>& scrAddrMap,
   uint32_t startBlock, uint32_t endBlock) const
{
   //create new ScrAddrFilter for the occasion
   shared_ptr<ScrAddrFilter> saf(saf_->copy());

   //register scrAddr with it
   vector<pair<BinaryData, unsigned>> saVec;
   for (auto& scrAddrPair : scrAddrMap)
      saVec.push_back(make_pair(scrAddrPair.first, startBlock));
   saf->regScrAddrVecForScan(saVec);

   //scan addresses
   saf->applyBlockRangeToDB(startBlock, endBlock, vector<string>(), true);
}

////////////////////////////////////////////////////////////////////////////////
size_t BlockDataViewer::getWalletsPageCount(void) const
{
   return groups_[group_wallet].getPageCount();
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BlockDataViewer::getWalletsHistoryPage(uint32_t pageId,
   bool rebuildLedger, bool remapWallets)
{
   return groups_[group_wallet].getHistoryPage(pageId, 
      rebuildLedger, remapWallets);
}

////////////////////////////////////////////////////////////////////////////////
size_t BlockDataViewer::getLockboxesPageCount(void) const
{
   return groups_[group_lockbox].getPageCount();
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BlockDataViewer::getLockboxesHistoryPage(uint32_t pageId,
   bool rebuildLedger, bool remapWallets)
{
   return groups_[group_lockbox].getHistoryPage(pageId,
      rebuildLedger, remapWallets);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::updateWalletsLedgerFilter(
   const vector<BinaryData>& walletsList)
{
   groups_[group_wallet].updateLedgerFilter(walletsList);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::updateLockboxesLedgerFilter(
   const vector<BinaryData>& walletsList)
{
   groups_[group_lockbox].updateLedgerFilter(walletsList);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::flagRefresh(BDV_refresh refresh, 
   const BinaryData& refreshID)
{ 
   auto notif = make_unique<BDV_Notification_Refresh>(refresh, refreshID);

   pushNotification(move(notif));
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataViewer::getMainBlockFromDB(uint32_t height) const
{
   uint8_t dupID = db_->getValidDupIDForHeight(height);
   
   return getBlockFromDB(height, dupID);
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataViewer::getBlockFromDB(
   uint32_t height, uint8_t dupID) const
{
   StoredHeader sbh;
   db_->getStoredHeader(sbh, height, dupID, true);

   return sbh;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::scrAddressIsRegistered(const BinaryData& scrAddr) const
{
   auto scrAddrMap = saf_->getScrAddrMap();
   auto saIter = scrAddrMap->find(scrAddr);

   if (saIter == scrAddrMap->end())
      return false;

   return true;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockHeader> BlockDataViewer::getHeaderByHash(
   const BinaryData& blockHash) const
{
   return bc_->getHeaderByHash(blockHash);
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BlockDataViewer::getUnspentTxoutsForAddr160List(
   const vector<BinaryData>& scrAddrVec, bool ignoreZc) const
{
   ScrAddrFilter* saf = bdmPtr_->getScrAddrFilter().get();

   auto scrAddrMap = saf_->getScrAddrMap();

   if (bdmPtr_->config().armoryDbType_ != ARMORY_DB_SUPER)
   {
      for (const auto& scrAddr : scrAddrVec)
      {
         auto saIter = scrAddrMap->find(scrAddr);
         if (saIter == scrAddrMap->end())
            throw std::range_error("Don't have this scrAddr tracked");
      }
   }

   vector<UnspentTxOut> UTXOs;

   for (const auto& scrAddr : scrAddrVec)
   {
      const auto& zcTxioMap = zeroConfCont_->getUnspentZCforScrAddr(scrAddr);

      StoredScriptHistory ssh;
      db_->getStoredScriptHistory(ssh, scrAddr);

      map<BinaryData, UnspentTxOut> scrAddrUtxoMap;
      db_->getFullUTXOMapForSSH(ssh, scrAddrUtxoMap);

      for (const auto& utxoPair : scrAddrUtxoMap)
      {
         auto zcIter = zcTxioMap.find(utxoPair.first);
         if (zcIter != zcTxioMap.end())
            if (zcIter->second.hasTxInZC())
               continue;

         UTXOs.push_back(utxoPair.second);
      }

      if (ignoreZc)
         continue;

      for (const auto& zcTxio : zcTxioMap)
      {
         if (!zcTxio.second.hasTxOutZC())
            continue;
         
         if (zcTxio.second.hasTxInZC())
            continue;

         TxOut txout = zcTxio.second.getTxOutCopy(db_);
         UnspentTxOut UTXO = UnspentTxOut(db_, txout, UINT32_MAX);

         UTXOs.push_back(UTXO);
      }
   }

   return UTXOs;
}

////////////////////////////////////////////////////////////////////////////////
WalletGroup BlockDataViewer::getStandAloneWalletGroup(
   const vector<BinaryData>& wltIDs, HistoryOrdering order)
{
   WalletGroup wg(this, this->saf_);
   wg.order_ = order;

   auto wallets   = groups_[group_wallet].getWalletMap();
   auto lockboxes = groups_[group_lockbox].getWalletMap();

   for (const auto& wltid : wltIDs)
   {
      auto wltIter = wallets.find(wltid);
      if (wltIter != wallets.end())
      {
         wg.wallets_[wltid] = wltIter->second;
      }

      else
      {
         auto lbIter = lockboxes.find(wltid);
         if (lbIter != lockboxes.end())
         {
            wg.wallets_[wltid] = lbIter->second;
         }
      }
   }

   wg.pageHistory(true, false);

   return wg;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataViewer::getBlockTimeByHeight(uint32_t height) const
{
   auto bh = blockchain().getHeaderByHeight(height);

   return bh->getTimestamp();
}

////////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForWallets()
{
   auto getHist = [this](uint32_t pageID)->vector<LedgerEntry>
   { return this->getWalletsHistoryPage(pageID, false, false); };

   auto getBlock = [this](uint32_t block)->uint32_t
   { return this->groups_[group_wallet].getBlockInVicinity(block); };

   auto getPageId = [this](uint32_t block)->uint32_t
   { return this->groups_[group_wallet].getPageIdForBlockHeight(block); };

   return LedgerDelegate(getHist, getBlock, getPageId);
}

////////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForLockboxes()
{
   auto getHist = [this](uint32_t pageID)->vector<LedgerEntry>
   { return this->getLockboxesHistoryPage(pageID, false, false); };

   auto getBlock = [this](uint32_t block)->uint32_t
   { return this->groups_[group_lockbox].getBlockInVicinity(block); };

   auto getPageId = [this](uint32_t block)->uint32_t
   { return this->groups_[group_lockbox].getPageIdForBlockHeight(block); };

   return LedgerDelegate(getHist, getBlock, getPageId);
}

////////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForScrAddr(
   const BinaryData& wltID, const BinaryData& scrAddr)
{
   BtcWallet* wlt = nullptr;
   for (auto& group : groups_)
   {
      ReadWriteLock::WriteLock wl(group.lock_);

      auto wltIter = group.wallets_.find(wltID);
      if (wltIter != group.wallets_.end())
      {
         wlt = wltIter->second.get();
         break;
      }
   }

   if (wlt == nullptr)
      throw runtime_error("Unregistered wallet ID");

   ScrAddrObj& sca = wlt->getScrAddrObjRef(scrAddr);

   auto getHist = [&](uint32_t pageID)->vector<LedgerEntry>
   { return sca.getHistoryPageById(pageID); };

   auto getBlock = [&](uint32_t block)->uint32_t
   { return sca.getBlockInVicinity(block); };

   auto getPageId = [&](uint32_t block)->uint32_t
   { return sca.getPageIdForBlockHeight(block); };

   return LedgerDelegate(getHist, getBlock, getPageId);
}


////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataViewer::getClosestBlockHeightForTime(uint32_t timestamp)
{
   //get timestamp of genesis block
   auto genBlock = blockchain().getGenesisBlock();
   
   //sanity check
   if (timestamp < genBlock->getTimestamp())
      return 0;

   //get time diff and divide by average time per block (600 sec for Bitcoin)
   uint32_t diff = timestamp - genBlock->getTimestamp();
   int32_t blockHint = diff/600;

   //look for a block in the hint vicinity with a timestamp lower than ours
   while (blockHint > 0)
   {
      auto block = blockchain().getHeaderByHeight(blockHint);
      if (block->getTimestamp() < timestamp)
         break;

      blockHint -= 1000;
   }

   //another sanity check
   if (blockHint < 0)
      return 0;

   for (uint32_t id = blockHint; id < blockchain().top()->getBlockHeight() - 1; id++)
   {
      //not looking for a really precise block, 
      //anything within the an hour of the timestamp is enough
      auto block = blockchain().getHeaderByHeight(id);
      if (block->getTimestamp() + 3600 > timestamp)
         return block->getBlockHeight();
   }

   return blockchain().top()->getBlockHeight() - 1;
}

////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getTxOutCopy(
   const BinaryData& txHash, uint16_t index) const
{
   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, STXO, LMDB::ReadOnly);
      

   BinaryData bdkey = db_->getDBKeyForHash(txHash);

   if (bdkey.getSize() == 0)
      return TxOut();

   return db_->getTxOutCopy(bdkey, index);
}

////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getTxOutCopy(const BinaryData& dbKey) const
{
   if (dbKey.getSize() != 8)
      throw runtime_error("invalid txout key length");

   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, STXO, LMDB::ReadOnly);

   auto&& bdkey = dbKey.getSliceRef(0, 6);
   auto index = READ_UINT16_BE(dbKey.getSliceRef(6, 2));

   return db_->getTxOutCopy(bdkey, index);
}

////////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getSpenderTxForTxOut(uint32_t height, uint32_t txindex,
   uint16_t txoutid) const
{
   StoredTxOut stxo;
   db_->getStoredTxOut(stxo, height, txindex, txoutid);

   if (!stxo.isSpent())
      return Tx();

   TxRef txref(stxo.spentByTxInKey_.getSliceCopy(0, 6));
   DBTxRef dbTxRef(txref, db_);
   return dbTxRef.getTxCopy();
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::isRBF(const BinaryData& txHash) const
{
   auto&& zctx = zeroConfCont_->getTxByHash(txHash);
   if (!zctx.isInitialized())
      return false;

   return zctx.isRBF();
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasScrAddress(const BinaryData& scrAddr) const
{
   //TODO: make sure this is thread safe

   for (auto& group : groups_)
   {
      ReadWriteLock::WriteLock wl(group.lock_);

      for (auto& wlt : group.wallets_)
      {
         if (wlt.second->hasScrAddress(scrAddr))
            return true;
      }
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BtcWallet> BlockDataViewer::getWalletOrLockbox(
   const BinaryData& id) const
{
   auto wallet = groups_[group_wallet].getWalletByID(id);
   if (wallet != nullptr)
      return wallet;

   return groups_[group_lockbox].getWalletByID(id);
}

///////////////////////////////////////////////////////////////////////////////
unique_ptr<BDV_Notification_ZC> BlockDataViewer::createZcStruct()
{
   BDV_Notification_ZC::zcMapType zcmap;
   auto txiomap = zeroConfCont_->getFullTxioMap();

   for (auto& txiopair : *txiomap)
   {
      if (!hasScrAddress(txiopair.first))
         continue;

      zcmap[txiopair.first] = txiopair.second;
   }

   auto notif = make_unique<BDV_Notification_ZC>(move(zcmap));

   return move(notif);
}

///////////////////////////////////////////////////////////////////////////////
tuple<uint64_t, uint64_t> BlockDataViewer::getAddrFullBalance(
   const BinaryData& scrAddr)
{
   StoredScriptHistory ssh;
   db_->getStoredScriptHistorySummary(ssh, scrAddr);

   return move(make_tuple(ssh.totalUnspent_, ssh.totalTxioCount_));
}

////////////////////////////////////////////////////////////////////////////////
//// WalletGroup
////////////////////////////////////////////////////////////////////////////////
WalletGroup::~WalletGroup()
{
   for (auto& wlt : wallets_)
      wlt.second->unregister();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BtcWallet> WalletGroup::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
   {
      return nullptr;
   }
   
   shared_ptr<BtcWallet> theWallet;

   {
      ReadWriteLock::WriteLock wl(lock_);
      BinaryData id(IDstr);


      auto wltIter = wallets_.find(id);
      if (wltIter != wallets_.end())
      {
         theWallet = wltIter->second;
      }
      else
      {
         auto insertResult = wallets_.insert(make_pair(
            id, shared_ptr<BtcWallet>(new BtcWallet(bdvPtr_, id))
            ));
         theWallet = insertResult.first->second;
      }
   }

   registerAddresses(scrAddrVec, IDstr, wltIsNew);

   theWallet->resetCounters();
   return theWallet;
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::unregisterWallet(const string& IDstr)
{
   ReadWriteLock::WriteLock wl(lock_);

   BinaryData id(IDstr);

   {
      auto wltIter = wallets_.find(id);
      if (wltIter == wallets_.end())
         return;
   }

   wallets_.erase(id);
}

////////////////////////////////////////////////////////////////////////////////
bool WalletGroup::registerAddresses(const vector<BinaryData>& saVec,
   const string& IDstr, bool areNew)
{
   if (saVec.empty())
      return false;

   shared_ptr<BtcWallet> theWallet;

   {
      ReadWriteLock::ReadLock rl(lock_);

      BinaryData walletID(IDstr);

      auto wltIter = wallets_.find(walletID);
      if (wltIter == wallets_.end())
         return false;

      theWallet = wltIter->second;
   }

   auto addrMap = theWallet->scrAddrMap_.get();

   set<BinaryData> saSet;
   set<BinaryDataRef> saSetRef;
   map<BinaryData, shared_ptr<ScrAddrObj>> saMap;
   
   //strip collisions from set of addresses to register
   for (auto& sa : saVec)
   {
      saSetRef.insert(BinaryDataRef(sa));
      if (addrMap->find(sa) != addrMap->end())
         continue;

      saSet.insert(sa);
      
      auto saObj = make_shared<ScrAddrObj>(
         bdvPtr_->getDB(), &bdvPtr_->blockchain(), sa);
      saMap.insert(make_pair(sa, saObj));
   }

   //remove registered addresses missing in new address vector
   vector<BinaryData> removeAddrVec;
   for (auto addrPair : *addrMap)
   {
      auto setIter = saSetRef.find(addrPair.first.getRef());
      if (setIter != saSetRef.end())
         continue;

      removeAddrVec.push_back(addrPair.first);
   }

   auto callback = [&, saMap, removeAddrVec, theWallet](bool refresh)->void
   {
      theWallet->scrAddrMap_.update(saMap);

      if (removeAddrVec.size() > 0)
         theWallet->scrAddrMap_.erase(removeAddrVec);

      theWallet->setRegistered();
      theWallet->needsRefresh(refresh);
   };

   return saf_->registerAddresses(saSet, IDstr, areNew, callback);
}

////////////////////////////////////////////////////////////////////////////////
bool WalletGroup::hasID(const BinaryData& ID) const
{
   ReadWriteLock::ReadLock rl(lock_);
   return wallets_.find(ID) != wallets_.end();
}

/////////////////////////////////////////////////////////////////////////////
const LedgerEntry& WalletGroup::getTxLedgerByHash(
   const BinaryData& txHash) const
{
   ReadWriteLock::ReadLock rl(lock_);
   for (const auto& wlt : values(wallets_))
   {
      const LedgerEntry& le = wlt->getLedgerEntryForTx(txHash);
      if (le.getTxTime() != 0)
         return le;
   }

   return LedgerEntry::EmptyLedger_;
}

/////////////////////////////////////////////////////////////////////////////
void WalletGroup::reset()
{
   ReadWriteLock::ReadLock rl(lock_);
   for (const auto& wlt : values(wallets_))
      wlt->reset();
}

////////////////////////////////////////////////////////////////////////////////
map<uint32_t, uint32_t> WalletGroup::computeWalletsSSHSummary(
   bool forcePaging, bool pageAnyway)
{
   map<uint32_t, uint32_t> fullSummary;

   ReadWriteLock::ReadLock rl(lock_);

   bool isAlreadyPaged = true;
   for (auto& wlt : values(wallets_))
   {
      if(forcePaging)
         wlt->mapPages();

      if (wlt->isPaged())
         isAlreadyPaged = false;
      else
         wlt->mapPages();
   }

   if (isAlreadyPaged)
   {
      if (!forcePaging && !pageAnyway)
         throw AlreadyPagedException();
   }

   for (auto& wlt : values(wallets_))
   {
      if (wlt->uiFilter_ == false)
         continue;

      const auto& wltSummary = wlt->getSSHSummary();

      for (auto summary : wltSummary)
         fullSummary[summary.first] += summary.second;
   }

   return fullSummary;
}

////////////////////////////////////////////////////////////////////////////////
bool WalletGroup::pageHistory(bool forcePaging, bool pageAnyway)
{
   auto computeSummary = [&](void)->map<uint32_t, uint32_t>
   { return this->computeWalletsSSHSummary(forcePaging, pageAnyway); };

   return hist_.mapHistory(computeSummary);
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> WalletGroup::getHistoryPage(uint32_t pageId,
   bool rebuildLedger, bool remapWallets)
{
   unique_lock<mutex> mu(globalLedgerLock_);

   if (pageId >= hist_.getPageCount())
      throw std::range_error("pageId out of range");

   if (order_ == order_ascending)
      pageId = hist_.getPageCount() - pageId - 1;

   //if (pageId == hist_.getCurrentPage() && !rebuildLedger && !remapWallets)
      //return globalLedger_;

   if (rebuildLedger || remapWallets)
      pageHistory(remapWallets, false);

   hist_.setCurrentPage(pageId);

   vector<LedgerEntry> vle;

   {
      //globalLedger_.clear();
      ReadWriteLock::ReadLock rl(lock_);
      for (auto& wlt : values(wallets_))
      {
         auto getTxio = [&wlt](uint32_t start, uint32_t end,
            map<BinaryData, TxIOPair>& outMap)->void
         { return wlt->getTxioForRange(start, end, outMap); };

         auto buildLedgers = [&wlt](map<BinaryData, LedgerEntry>& le,
            const map<BinaryData, TxIOPair>& txioMap,
            uint32_t startBlock, uint32_t endBlock)->void
         { wlt->updateWalletLedgersFromTxio(le, txioMap, startBlock, endBlock); };

         if (!wlt->uiFilter_)
            continue;

         map<BinaryData, LedgerEntry> leMap;
         hist_.getPageLedgerMap(getTxio, buildLedgers, pageId, leMap);

         for (const LedgerEntry& le : values(leMap))
            vle.push_back(le);
      }
   }

   if (order_ == order_ascending)
      sort(vle.begin(), vle.end());
   else
   {
      LedgerEntry_DescendingOrder desc;
      sort(vle.begin(), vle.end(), desc);
   }

   return vle;
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::updateLedgerFilter(const vector<BinaryData>& walletsList)
{
   ReadWriteLock::ReadLock rl(lock_);

   vector<BinaryData> enabledIDs;
   for (auto& wlt_pair : wallets_)
   {
      if (wlt_pair.second->uiFilter_)
         enabledIDs.push_back(wlt_pair.first);
      wlt_pair.second->uiFilter_ = false;
   }


   for (auto walletID : walletsList)
   {
      auto iter = wallets_.find(walletID);
      if (iter == wallets_.end())
         continue;

      iter->second->uiFilter_ = true;
   }
   
   auto vec_copy = walletsList;
   sort(vec_copy.begin(), vec_copy.end());
   sort(enabledIDs.begin(), enabledIDs.end());

   if (vec_copy == enabledIDs)
      return;

   pageHistory(false, true);
   bdvPtr_->flagRefresh(BDV_filterChanged, BinaryData());
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::scanWallets(ScanWalletStruct& scanData, 
   int32_t updateID)
{
   ReadWriteLock::ReadLock rl(lock_);

   for (auto& wlt : wallets_)
   {
      wlt.second->scanWallet(scanData, updateID);
      validZcSet_.insert(
         wlt.second->validZcKeys_.begin(), wlt.second->validZcKeys_.end());
   }
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::updateGlobalLedgerFirstPage(uint32_t startBlock,
   uint32_t endBlock, BDV_refresh forceRefresh)
{
   //There is a fundamental difference between the first history page and all
   //the others: the first page maintains ZC, new blocks and can undergo
   //reorgs while every other history page is purely static

   ReadWriteLock::ReadLock rl(lock_);


   if (forceRefresh == BDV_refreshSkipRescan)
      getHistoryPage(0, true, false);
   else if (forceRefresh == BDV_refreshAndRescan)
      getHistoryPage(0, true, true);
   else if (hist_.getCurrentPage() == 0)
   {
      unique_lock<mutex> mu(globalLedgerLock_);

      LedgerEntry::purgeLedgerVectorFromHeight(globalLedger_, startBlock);

      for (auto& wlt : values(wallets_))
      {
         map<BinaryData, TxIOPair> txioMap;
         wlt->getTxioForRange(startBlock, UINT32_MAX, txioMap);

         map<BinaryData, LedgerEntry> leMap;
         wlt->updateWalletLedgersFromTxio(leMap, txioMap, startBlock, UINT32_MAX);

         if (!wlt->uiFilter_)
            continue;

         for (const auto& lePair : leMap)
            globalLedger_.push_back(lePair.second);
      }

      if (order_ == order_ascending)
         sort(globalLedger_.begin(), globalLedger_.end());
      else
      {
         LedgerEntry_DescendingOrder desc;
         sort(globalLedger_.begin(), globalLedger_.end(), desc);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, shared_ptr<BtcWallet> > WalletGroup::getWalletMap(void) const
{
   ReadWriteLock::ReadLock rl(lock_);
   return wallets_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BtcWallet> WalletGroup::getWalletByID(const BinaryData& ID) const
{
   auto iter = wallets_.find(ID);
   if (iter != wallets_.end())
      return iter->second;

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t WalletGroup::getBlockInVicinity(uint32_t blk) const
{
   //expect history has been computed, it will throw otherwise
   return hist_.getBlockInVicinity(blk);
}

////////////////////////////////////////////////////////////////////////////////
uint32_t WalletGroup::getPageIdForBlockHeight(uint32_t blk) const
{
   //same as above
   return hist_.getPageIdForBlockHeight(blk);
}
