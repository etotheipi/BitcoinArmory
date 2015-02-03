////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "BlockDataViewer.h"


/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(BlockDataManager_LevelDB* bdm) :
   rescanZC_(false), zeroConfCont_(bdm->getIFace())
{
   db_ = bdm->getIFace();
   bc_ = &bdm->blockchain();
   saf_ = bdm->getScrAddrFilter();

   bdmPtr_ = bdm;

   zcEnabled_ = false;
   zcLiteMode_ = false;

   groups_.push_back(WalletGroup(this, saf_));
   groups_.push_back(WalletGroup(this, saf_));
}

/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
   groups_.clear();
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
      return nullptr;

   return groups_[group_wallet].registerWallet(scrAddrVec, IDstr, wltIsNew);
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerLockbox(
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
void BlockDataViewer::scanWallets(uint32_t startBlock,
   uint32_t endBlock, BDV_refresh forceRefresh)
{
   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = getTopBlockHeight() + 1;
   
   for (auto& group : groups_)
      group.merge();

   vector<uint32_t> startBlocks;
   for (auto& group : groups_)
      startBlocks.push_back(startBlock);


   auto sbIter = startBlocks.begin();
   if (!initialized_)
   {
      //out of date history, page all wallets' history
      for (auto& group : groups_)
      {
         *sbIter = group.pageHistory();
         sbIter++;
      }

      initialized_ = true;
   }

   map<BinaryData, vector<BinaryData> > invalidatedZCKeys;
   if (startBlock != endBlock)
   {
      invalidatedZCKeys = zeroConfCont_.purge(
         [this](const BinaryData& sa)->bool 
         { return saf_->hasScrAddress(sa); });
   }
   const bool reorg = (lastScanned_ > startBlock);

   sbIter = startBlocks.begin();
   for (auto& group : groups_)
   {

      group.scanWallets(*sbIter, endBlock, 
         reorg, invalidatedZCKeys);

      group.updateGlobalLedgerFirstPage(*sbIter, endBlock,
         forceRefresh);

      sbIter++;
   }

   zeroConfCont_.resetNewZC();
   lastScanned_ = endBlock;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasWallet(const BinaryData& ID) const
{
   return groups_[group_wallet].hasID(ID);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintRegisteredWallets(void) const
{
   groups_[group_wallet].pprintRegisteredWallets();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::addNewZeroConfTx(BinaryData const & rawTx,
   uint32_t txtime,
   bool writeToFile)
{
   if (!zcEnabled_)
      return;

   SCOPED_TIMER("addNewZeroConfTx");

   if (txtime == 0)
      txtime = (uint32_t)time(nullptr);

   zeroConfCont_.addRawTx(rawTx, txtime);
   rescanZC_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::enableZeroConf(bool clearMempool)
{
   SCOPED_TIMER("enableZeroConf");
   LOGINFO << "Enabling zero-conf tracking ";
   zcEnabled_ = true;
   //zcLiteMode_ = zcLite;

   auto zcFilter = [this](const BinaryData& scrAddr)->bool
   { return this->bdmPtr_->getScrAddrFilter()->hasScrAddress(scrAddr); };

   zeroConfCont_.loadZeroConfMempool(zcFilter, clearMempool);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::disableZeroConf(void)
{
   SCOPED_TIMER("disableZeroConf");
   zcEnabled_ = false;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::purgeZeroConfPool()
{
   const map<BinaryData, vector<BinaryData> > invalidatedTxIOKeys
      = zeroConfCont_.purge(
      [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });

   for (auto& group : groups_)
      group.purgeZeroConfPool(invalidatedTxIOKeys);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::parseNewZeroConfTx()
{
   return zeroConfCont_.parseNewZC(
      [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::registerAddresses(const vector<BinaryData>& saVec,
   BinaryData walletID, bool areNew)
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

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::registerAddressBatch(
   const map < BinaryData, vector<BinaryData>>& wltNAddrMap, 
   bool areNew)
{
   //if called from python, feed it a dict such as:
   //{wltID1:[addrList1], wltID2:[addrList2]}

   map<shared_ptr<BtcWallet>, vector<BinaryData>> wlt_addr;

   for (auto& batch : wltNAddrMap)
   {
      for (auto& group : groups_)
      {
         auto wlt = group.getWalletByID(batch.first);
         if (wlt != nullptr)
         {
            wlt_addr.insert(make_pair(wlt, batch.second));
            break;
         }
      }
   }

   saf_->registerAddressBatch(wlt_addr, areNew);
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BlockDataViewer::getTxLedgerByHash_FromWallets(
   const BinaryData& txHash) const
{
   checkBDMisReady();
   return groups_[group_wallet].getTxLedgerByHash(txHash);
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BlockDataViewer::getTxLedgerByHash_FromLockboxes(
   const BinaryData& txHash) const
{
   checkBDMisReady();
   return groups_[group_lockbox].getTxLedgerByHash(txHash);
}

/////////////////////////////////////////////////////////////////////////////
TX_AVAILABILITY BlockDataViewer::getTxHashAvail(BinaryDataRef txHash) const
{
   checkBDMisReady();

   if (db_->getTxRef(txHash).isNull())
   {
      if (!zeroConfCont_.hasTxByHash(txHash))
         return TX_DNE;  // No tx at all
      else
         return TX_ZEROCONF;  // Zero-conf tx
   }
   else
      return TX_IN_BLOCKCHAIN; // In the blockchain already
}

/////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getTxByHash(HashString const & txhash) const
{
   checkBDMisReady();

   if (config().armoryDbType == ARMORY_DB_SUPER)
   {
      LMDBEnv::Transaction tx(db_->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);

   TxRef txrefobj = db_->getTxRef(txhash);

   if (!txrefobj.isNull())
      return txrefobj.attached(db_).getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      return zeroConfCont_.getTxByHash(txhash);
   }
}
   else
   {
      StoredTx stx;
      if (db_->getStoredTx_byHash(txhash, &stx))
         return stx.getTxCopy();
      else
         return zeroConfCont_.getTxByHash(txhash);
   }
}

bool BlockDataViewer::isTxMainBranch(const Tx &tx) const
{
   checkBDMisReady();

   if (!tx.hasTxRef())
      return false;
   return tx.getTxRef().attached(db_).isMainBranch();
}

////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getPrevTxOut(TxIn & txin) const
{
   checkBDMisReady();

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
   checkBDMisReady();

   if (txin.isCoinbase())
      return Tx();

   OutPoint op = txin.getOutPoint();
   return getTxByHash(op.getTxHash());
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataViewer::getSenderScrAddr(TxIn & txin) const
{
   checkBDMisReady();

   if (txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getScrAddressStr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataViewer::getSentValue(TxIn & txin) const
{
   checkBDMisReady();

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
   checkBDMisReady();

   return bc_->top().getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::reset()
{
   for (auto& group : groups_)
      group.reset();

   rescanZC_   = false;
   zcEnabled_  = false;
   zcLiteMode_ = false;
   
   zeroConfCont_.clear();

   lastScanned_ = 0;
   initialized_ = false;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanScrAddrVector(
   const map<BinaryData, ScrAddrObj>& scrAddrMap,
   uint32_t startBlock, uint32_t endBlock) const
{
   //create new ScrAddrFilter for the occasion
   shared_ptr<ScrAddrFilter> saf(saf_->copy());

   //register scrAddr with it
   for (auto& scrAddrPair : scrAddrMap)
      saf->regScrAddrForScan(scrAddrPair.first, startBlock);

   //scan addresses
   saf->applyBlockRangeToDB(startBlock, endBlock, vector<string>());
}

////////////////////////////////////////////////////////////////////////////////
size_t BlockDataViewer::getWalletsPageCount(void) const
{
   checkBDMisReady();

   return groups_[group_wallet].getPageCount();
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BlockDataViewer::getWalletsHistoryPage(uint32_t pageId,
   bool rebuildLedger, bool remapWallets)
{
   checkBDMisReady();

   return groups_[group_wallet].getHistoryPage(pageId, 
      rebuildLedger, remapWallets);
}

////////////////////////////////////////////////////////////////////////////////
size_t BlockDataViewer::getLockboxesPageCount(void) const
{
   checkBDMisReady();

   return groups_[group_lockbox].getPageCount();
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BlockDataViewer::getLockboxesHistoryPage(uint32_t pageId,
   bool rebuildLedger, bool remapWallets)
{
   checkBDMisReady();

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
void BlockDataViewer::flagRefresh(BDV_refresh refresh, const BinaryData& refreshID)
{ 
   if (saf_->bdmIsRunning() == false)
      return;

   unique_lock<mutex> lock(refreshLock_);

   if (refresh_ != BDV_refreshAndRescan)
   {
      if (refresh == BDV_refreshAndRescan)
         refresh_ = BDV_refreshAndRescan;
      else
         refresh_ = BDV_refreshSkipRescan;
   }

   if (refreshID.getSize())
      refreshIDSet_.insert(refreshID);
   
   if (refresh == BDV_filterChanged)
      refreshIDSet_.insert(BinaryData("wallet_filter_changed"));

   notifyMainThread();
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataViewer::getMainBlockFromDB(uint32_t height) const
{
   checkBDMisReady();

   uint8_t dupID = db_->getValidDupIDForHeight(height);
   
   return getBlockFromDB(height, dupID);
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataViewer::getBlockFromDB(uint32_t height, uint8_t dupID) const
{
   StoredHeader sbh;
   db_->getStoredHeader(sbh, height, dupID, true);

   return sbh;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::scrAddressIsRegistered(const BinaryData& scrAddr) const
{
   return saf_->hasScrAddress(scrAddr);
}

////////////////////////////////////////////////////////////////////////////////
BlockHeader BlockDataViewer::getHeaderByHash(const BinaryData& blockHash) const
{
   checkBDMisReady();

   return bc_->getHeaderByHash(blockHash);
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BlockDataViewer::getUnspentTxoutsForAddr160List(
   const vector<BinaryData>& scrAddrVec, bool ignoreZc) const
{
   checkBDMisReady();

   ScrAddrFilter* saf = bdmPtr_->getScrAddrFilter();

   if (bdmPtr_->config().armoryDbType != ARMORY_DB_SUPER)
   {
      for (const auto& scrAddr : scrAddrVec)
      {
         if (!saf->hasScrAddress(scrAddr))
            throw std::range_error("Don't have this scrAddr tracked");
      }
   }

   vector<UnspentTxOut> UTXOs;

   for (const auto& scrAddr : scrAddrVec)
   {
      const auto& zcTxioMap = zeroConfCont_.getZCforScrAddr(scrAddr);

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
  checkBDMisReady();

   WalletGroup wg(this, this->saf_);
   wg.order_ = order;

   auto wallets   = groups_[group_wallet].getWalletMap();
   auto lockboxes = groups_[group_lockbox].getWalletMap();

   for (const auto& wltid : wltIDs)
   {
      auto wltIter = wallets.find(wltid);
      if (wltIter != wallets.end())
         wg.wallets_[wltid] = wltIter->second;
      else
      {
         auto lbIter = lockboxes.find(wltid);
         if (lbIter != lockboxes.end())
            wg.wallets_[wltid] = lbIter->second;
      }
   }

   wg.pageHistory(false);

   return wg;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataViewer::getBlockTimeByHeight(uint32_t height) const
{
   auto bh = blockchain().getHeaderByHeight(height);

   return bh.getTimestamp();
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
   auto& genBlock = blockchain().getGenesisBlock();
   
   //sanity check
   if (timestamp < genBlock.getTimestamp())
      return 0;

   //get time diff and divide by average time per block (600 sec for Bitcoin)
   uint32_t diff = timestamp - genBlock.getTimestamp();
   int32_t blockHint = diff/600;

   //look for a block in the hint vicinity with a timestamp lower than ours
   while (blockHint > 0)
   {
      auto& block = blockchain().getHeaderByHeight(blockHint);
      if (block.getTimestamp() < timestamp)
         break;

      blockHint -= 1000;
   }

   //another sanity check
   if (blockHint < 0)
      return 0;

   for (uint32_t id = blockHint; id < blockchain().top().getBlockHeight() - 1; id++)
   {
      //not looking for a really precise block, 
      //anything within the an hour of the timestamp is enough
      auto& block = blockchain().getHeaderByHeight(id);
      if (block.getTimestamp() + 3600 > timestamp)
         return block.getBlockHeight();
   }

   return blockchain().top().getBlockHeight() - 1;
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
BtcWallet* WalletGroup::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
   {
      return nullptr;
   }

   // Check if the wallet is already registered
   ReadWriteLock::WriteLock wl(lock_);
   BinaryData id(IDstr);

   {
      auto regWlt = wallets_.find(id);
      if (regWlt != wallets_.end())
      {
         bdvPtr_->flagRefresh(BDV_refreshSkipRescan, id);
         return regWlt->second.get();
      }
   }

   shared_ptr<BtcWallet> newWallet;

   {
      // Main thread isnt running, just register the wallet
      // Add it to the list of wallets to watch
      // Instantiate the object through insert.
      auto insertResult = wallets_.insert(make_pair(
         id, shared_ptr<BtcWallet>(new BtcWallet(bdvPtr_, id))
         ));
      newWallet = insertResult.first->second;
   }

   newWallet->addAddressBulk(scrAddrVec, wltIsNew);

   //register all scrAddr in the wallet with the BDM. It doesn't matter if
   //the data is overwritten
   vector<BinaryData> saVec;
   saVec.reserve(newWallet->getScrAddrMap().size());
   for (const auto& scrAddrPair : newWallet->getScrAddrMap())
      saVec.push_back(scrAddrPair.first);

   saf_->registerAddresses(saVec, newWallet, wltIsNew);

   //tell the wallet it is registered
   newWallet->setRegistered();

   return newWallet.get();
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

   bdvPtr_->notifyMainThread();
}

////////////////////////////////////////////////////////////////////////////////
bool WalletGroup::registerAddresses(const vector<BinaryData>& saVec,
   BinaryData walletID, bool areNew)
{
   if (saVec.empty())
      return false;

   ReadWriteLock::ReadLock rl(lock_);

   auto wltIter = wallets_.find(walletID);
   if (wltIter == wallets_.end())
      return false;

   return saf_->registerAddresses(saVec, wltIter->second, areNew);
}

////////////////////////////////////////////////////////////////////////////////
bool WalletGroup::hasID(const BinaryData& ID) const
{
   ReadWriteLock::ReadLock rl(lock_);
   return wallets_.find(ID) != wallets_.end();
}

/////////////////////////////////////////////////////////////////////////////
void WalletGroup::pprintRegisteredWallets(void) const
{
   ReadWriteLock::ReadLock rl(lock_);
   for (const auto& wlt : values(wallets_))
   {
      cout << "Wallet:";
      wlt->pprintAlittle(cout);
   }
}

/////////////////////////////////////////////////////////////////////////////
void WalletGroup::purgeZeroConfPool(
   const map<BinaryData, vector<BinaryData> >& invalidatedTxIOKeys)
{
   ReadWriteLock::ReadLock rl(lock_);
   for (auto& wlt : values(wallets_))
      wlt->purgeZeroConfTxIO(invalidatedTxIOKeys);
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
   bool forcePaging)
{
   map<uint32_t, uint32_t> fullSummary;

   ReadWriteLock::ReadLock rl(lock_);

   for (auto& wlt : values(wallets_))
   {
      if (forcePaging)
         wlt->mapPages();

      if (wlt->uiFilter_ == false)
         continue;

      const auto& wltSummary = wlt->getSSHSummary();

      for (auto summary : wltSummary)
         fullSummary[summary.first] += summary.second;
   }

   return fullSummary;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t WalletGroup::pageHistory(bool forcePaging)
{
   auto computeSummary = [this](bool force)->map<uint32_t, uint32_t>
   { return this->computeWalletsSSHSummary(force); };

   hist_.mapHistory(computeSummary, forcePaging);

   return hist_.getPageBottom(0);
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
      pageHistory(remapWallets);

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
   for (auto& wlt : values(wallets_))
      wlt->uiFilter_ = false;

   for (auto walletID : walletsList)
      wallets_[walletID]->uiFilter_ = true;

   bdvPtr_->flagRefresh(BDV_filterChanged, BinaryData());
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::merge()
{
   ReadWriteLock::ReadLock rl(lock_);
   for (auto& wlt : values(wallets_))
      wlt->merge();
}

////////////////////////////////////////////////////////////////////////////////
void WalletGroup::scanWallets(uint32_t startBlock, uint32_t endBlock, 
   bool reorg, map<BinaryData, vector<BinaryData> > invalidatedZCKeys)
{
   ReadWriteLock::ReadLock rl(lock_);
   for (auto& wlt : values(wallets_))
      wlt->scanWallet(startBlock, endBlock, reorg, invalidatedZCKeys);
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
