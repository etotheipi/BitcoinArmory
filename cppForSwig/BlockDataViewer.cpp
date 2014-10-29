#include "BlockDataViewer.h"


/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(BlockDataManager_LevelDB* bdm) :
   rescanZC_(false), zeroConfCont_(bdm->getIFace())
{
   db_ = bdm->getIFace();
   bc_ = &bdm->blockchain();
   saf_ = bdm->getScrAddrFilter();
   config_ = bdm->config();

   bdmPtr_ = bdm;

   zcEnabled_ = false;
   zcLiteMode_ = false;
}

/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
   ReadWriteLock::WriteLock wl(registeredWalletsLock_);
   for (auto wlt : registeredWallets_)
      wlt.second->unregister();

   for (auto wlt : registeredLockboxes_)
      wlt.second->unregister();
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
      return nullptr;

   LOGINFO << "Registering Wallet " << IDstr;

   // Check if the wallet is already registered
   BinaryData id(IDstr);

   {
      ReadWriteLock::ReadLock rl(registeredWalletsLock_);
      
      auto regWlt = registeredWallets_.find(id);
      if (regWlt != registeredWallets_.end())
         return regWlt->second.get();
   }
   
   shared_ptr<BtcWallet> newWallet;

   {
      ReadWriteLock::WriteLock wl(registeredWalletsLock_);
      // Main thread isnt ruuning, just register the wallet
      // Add it to the list of wallets to watch
      // Instantiate the object through insert.
      auto insertResult = registeredWallets_.insert(make_pair(
         id, shared_ptr<BtcWallet>(new BtcWallet(this, id))
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

   bdmPtr_->notifyMainThread();
   return newWallet.get();
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerLockbox(
   vector<BinaryData> const & scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.empty())
      return nullptr;

   LOGINFO << "Registering Lockbox " << IDstr;

   // Check if the lockbox is already registered
   BinaryData id(IDstr);
   
   {
      ReadWriteLock::ReadLock rl(registeredWalletsLock_);
      
      auto regLB = registeredLockboxes_.find(id);
      if (regLB!= registeredLockboxes_.end())
         return regLB->second.get();
   }
   
   shared_ptr<BtcWallet> newLockbox;

   {
      ReadWriteLock::WriteLock wl(registeredWalletsLock_);
      // Main thread isnt ruuning, just register the wallet
      // Add it to the list of wallets to watch
      // Instantiate the object through insert.
      auto insertResult = registeredLockboxes_.insert(make_pair(
         id, make_shared<BtcWallet>(this, id)
      ));
      newLockbox = insertResult.first->second;
   }

   newLockbox->addAddressBulk(scrAddrVec, wltIsNew);

   //register all scrAddr in the wallet with the BDM. It doesn't matter if
   //the data is overwritten
   vector<BinaryData> saVec;
   for (const auto& scrAddrPair : newLockbox->getScrAddrMap())
      saVec.push_back(scrAddrPair.first);

   saf_->registerAddresses(saVec, newLockbox, wltIsNew);

   newLockbox->setRegistered();
   
   bdmPtr_->notifyMainThread();

   return newLockbox.get();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterWallet(string IDstr)
{
   LOGINFO << "Unregistering Wallet " << IDstr;

   BinaryData id(IDstr);

   {
      ReadWriteLock::ReadLock rl(registeredWalletsLock_);
      auto wltIter = registeredWallets_.find(id);
      if (wltIter == registeredWallets_.end())
         return;
   }
   
   {
      ReadWriteLock::WriteLock wl(registeredWalletsLock_);
      registeredWallets_.erase(id);
   }
   
   bdmPtr_->notifyMainThread();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterLockbox(string IDstr)
{
   LOGINFO << "Unregistering Lockbox " << IDstr;

   BinaryData id(IDstr);

   {
      ReadWriteLock::ReadLock rl(registeredWalletsLock_);
      auto wltIter = registeredLockboxes_.find(id);
      if (wltIter == registeredWallets_.end())
         return;
   }

   {
      ReadWriteLock::WriteLock wl(registeredWalletsLock_);
      registeredLockboxes_.erase(id);
   }
   bdmPtr_->notifyMainThread();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanWallets(uint32_t startBlock,
   uint32_t endBlock, uint32_t forceRefresh)
{
   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = getTopBlockHeight() + 1;


   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   const map<BinaryData, shared_ptr<BtcWallet>> registeredWallets
      = registeredWallets_;
   const map<BinaryData, shared_ptr<BtcWallet>> registeredLockboxes
      = registeredLockboxes_;
   rl.unlock();
   
   for (auto& wlt : values(registeredWallets))
      wlt->merge();

   for (auto& wlt : values(registeredLockboxes))
      wlt->merge();


   if (!initialized_)
   {
      //out of date history, page all wallets' history
      pageWalletsHistory();
      pageLockboxesHistory();

      //Now that the history is computed, we need to grab the starting block
      //range for the first page (0), and have all wallets load their ledger
      //from that height.
      startBlock = hist_.getPageBottom(0);

      initialized_ = true;
   }

   map<BinaryData, vector<BinaryData> > invalidatedZCKeys;
   if (startBlock != endBlock)
   {
      invalidatedZCKeys = zeroConfCont_.purge(
         [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });
   }

   const bool reorg = (lastScanned_ > startBlock);

   for (auto& wlt : values(registeredWallets))
   {
      wlt->scanWallet(startBlock, endBlock, reorg,
                            invalidatedZCKeys);
   }

   for (auto& wlt : values(registeredLockboxes))
   {
      wlt->scanWallet(startBlock, endBlock, reorg,
                            invalidatedZCKeys);
   }

   zeroConfCont_.resetNewZC();
   lastScanned_ = endBlock;

   if (forceRefresh == 1)
      getHistoryPage(0, true, false);
   else if(forceRefresh == 2)
      getHistoryPage(0, true, true);
   else if (hist_.getCurrentPage() == 0)
   {
      //There is a fundamental difference between the first history page and all
      //the others: the first page maintains ZC, new blocks and can undergo
      //reorgs while every other history page is purely static.

      LedgerEntry::purgeLedgerVectorFromHeight(globalLedger_, startBlock);

      for (auto& wlt : values(registeredWallets_))
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

      sort(globalLedger_.begin(), globalLedger_.end());
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasWallet(BinaryData ID)
{
   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   return registeredWallets_.find(ID) != registeredWallets_.end();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintRegisteredWallets(void) const
{
   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   for (const auto& wlt : values(registeredWallets_))
   {
      cout << "Wallet:";
      wlt->pprintAlittle(cout);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::addNewZeroConfTx(BinaryData const & rawTx,
   uint32_t txtime,
   bool writeToFile)
{
   SCOPED_TIMER("addNewZeroConfTx");

   if (txtime == 0)
      txtime = (uint32_t)time(nullptr);

   zeroConfCont_.addRawTx(rawTx, txtime);
   rescanZC_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::enableZeroConf()
{
   SCOPED_TIMER("enableZeroConf");
   LOGINFO << "Enabling zero-conf tracking ";
   zcEnabled_ = true;
   //zcLiteMode_ = zcLite;

   auto zcFilter = [this](const BinaryData& scrAddr)->bool
   { return this->bdmPtr_->getScrAddrFilter()->hasScrAddress(scrAddr); };

   zeroConfCont_.loadZeroConfMempool(zcFilter);
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

   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   for (auto& wlt : values(registeredWallets_))
   {
      wlt->purgeZeroConfTxIO(invalidatedTxIOKeys);
   }
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::rewriteZeroConfFile(void)
{
   /*SCOPED_TIMER("rewriteZeroConfFile");
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);
   ;

   for(ts_BinDataMap::const_iterator iter = listSS.begin();
   iter != listSS.end();
   ++iter)
   {
   const ZeroConfData& zcd = zeroConfMap_[iter->first].get();
   zcFile.write( (char*)(&zcd.txtime_), sizeof(uint64_t) );
   zcFile.write( (char*)(zcd.txobj_.getPtr()),  zcd.txobj_.getSize());
   }

   zcFile.close();*/

}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintZeroConfPool(void) const
{
   /*ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);

   for (ts_BinDataMap::const_iterator iter = listSS.begin();
   iter != listSS.end(); ++iter
   )
   {
   const ZeroConfData & zcd = zeroConfMap_[iter->first];
   const Tx & tx = zcd.txobj_;
   cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
   for(uint32_t i=0; i<tx.getNumTxOut(); i++)
   cout << tx.getTxOutCopy(i).getValue() << " ";
   cout << endl;
   }*/
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::parseNewZeroConfTx()
{
   return zeroConfCont_.parseNewZC(
      [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::registerAddresses(const vector<BinaryData>& saVec,
   BinaryData walletID, int32_t doScan)
{
   if (saVec.empty())
      return false;
   
   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   
   auto wltIter = registeredWallets_.find(walletID);
   if (wltIter == registeredWallets_.end())
   {
      wltIter = registeredLockboxes_.find(walletID);
      if (wltIter == registeredWallets_.end())
         return false;
   }

   return saf_->registerAddresses(saVec, wltIter->second, doScan);
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BlockDataViewer::getTxLedgerByHash(
   const BinaryData& txHash) const
{
   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   
   for (const auto& wlt : values(registeredWallets_))
   {
      const LedgerEntry& le = wlt->getLedgerEntryForTx(txHash);
      if (le.getTxTime() != 0)
         return le;
   }

   return LedgerEntry::EmptyLedger_;
}

/////////////////////////////////////////////////////////////////////////////
TX_AVAILABILITY BlockDataViewer::getTxHashAvail(BinaryDataRef txHash)
{
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
Tx BlockDataViewer::getTxByHash(HashString const & txhash)
{
   LMDBEnv::Transaction tx(&db_->dbEnv_, LMDB::ReadOnly);

   TxRef txrefobj = db_->getTxRef(txhash);

   if (!txrefobj.isNull())
      return txrefobj.attached(db_).getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      return zeroConfCont_.getTxByHash(txhash);
   }
}

bool BlockDataViewer::isTxMainBranch(const Tx &tx) const
{
   if (!tx.hasTxRef())
      return false;
   return tx.getTxRef().attached(db_).isMainBranch();
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getPrevTxOut(TxIn & txin)
{
   if (txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOutCopy(idx);
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getPrevTx(TxIn & txin)
{
   if (txin.isCoinbase())
      return Tx();

   OutPoint op = txin.getOutPoint();
   return getTxByHash(op.getTxHash());
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataViewer::getSenderScrAddr(TxIn & txin)
{
   if (txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getScrAddressStr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataViewer::getSentValue(TxIn & txin)
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
   return bc_->top().getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::reset()
{
   ReadWriteLock::WriteLock wl(registeredWalletsLock_);
   for (auto& wlt : values(registeredWallets_))
      wlt->reset();

   for (auto& wlt : values(registeredLockboxes_))
      wlt->reset();

   rescanZC_   = false;
   zcEnabled_  = false;
   zcLiteMode_ = false;
   
   zeroConfCont_.clear();

   lastScanned_ = 0;
   initialized_ = false;
}

////////////////////////////////////////////////////////////////////////////////
map<uint32_t, uint32_t> BlockDataViewer::computeWalletsSSHSummary(
   bool forcePaging)
{
   map<uint32_t, uint32_t> fullSummary;

   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   
   for (auto& wlt : values(registeredWallets_))
   {      
      if (forcePaging)
         wlt->mapPages();
      
      if(wlt->uiFilter_ == false)
         continue;
            
      const auto& wltSummary = wlt->getSSHSummary();

      for (auto summary : wltSummary)
         fullSummary[summary.first] += summary.second;
   }

   return fullSummary;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pageWalletsHistory(bool forcePaging)
{
   auto computeSummary = [this](bool force)->map<uint32_t, uint32_t>
      { return this->computeWalletsSSHSummary(force); };
   
   hist_.mapHistory(computeSummary, forcePaging);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pageLockboxesHistory()
{
   for (auto& wlt : values(registeredLockboxes_))
      wlt->mapPages();
}


////////////////////////////////////////////////////////////////////////////////
const vector<LedgerEntry>& BlockDataViewer::getHistoryPage(uint32_t pageId, 
   bool rebuildLedger, bool remapWallets)
{
   if (pageId == hist_.getCurrentPage() && !rebuildLedger && !remapWallets)
      return globalLedger_;

   if (rebuildLedger || remapWallets)
      pageWalletsHistory(remapWallets);

   hist_.setCurrentPage(pageId);

   {
      globalLedger_.clear();
      ReadWriteLock::ReadLock rl(registeredWalletsLock_);
      for (auto& wlt : values(registeredWallets_))
      {
         auto getTxio = [&wlt](uint32_t start, uint32_t end,
            map<BinaryData, TxIOPair>& outMap)->void
         { return wlt->getTxioForRange(start, end, outMap); };

         auto buildLedgers = [&wlt](map<BinaryData, LedgerEntry>& le,
            const map<BinaryData, TxIOPair>& txioMap,
            uint32_t startBlock, uint32_t endBlock)->void
         { wlt->updateWalletLedgersFromTxio(le, txioMap, startBlock, endBlock); };

         map<BinaryData, LedgerEntry> leMap;
         hist_.getPageLedgerMap(getTxio, buildLedgers, pageId, leMap);
      
         //this should be locked to a single thread

         if (!wlt->uiFilter_)
            continue;

         for (const LedgerEntry& le : values(leMap))
            globalLedger_.push_back(le);
      }
   }

   sort(globalLedger_.begin(), globalLedger_.end());

   return globalLedger_;
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

   //compute blockHeightCutOff
   saf->scanFrom();

   //scan addresses
   saf->applyBlockRangeToDB(startBlock, endBlock, nullptr);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::updateWalletFilters(const vector<BinaryData>& walletsList)
{
   ReadWriteLock::ReadLock rl(registeredWalletsLock_);
   for (auto& wlt : values(registeredWallets_))
      wlt->uiFilter_ = false;

   for (auto walletID : walletsList)
      registeredWallets_[walletID]->uiFilter_ = true;

   flagRefresh(false, BinaryData());
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::flagRefresh(bool withRemap, BinaryData refreshID) 
{ 
   if (saf_->bdmIsRunning() < 2)
      return;

   if (withRemap == true)
      refresh_ = 2;
   else
      refresh_ = 1;

   refreshID_ = refreshID;

   bdmPtr_->notifyMainThread();
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataViewer::getMainBlockFromDB(uint32_t height) const
{
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
   if (bc_->hasHeaderWithHash(blockHash))
      return bc_->getHeaderByHash(blockHash);

   return BlockHeader();
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BlockDataViewer::getUnpsentTxoutsForAddr160List(
   const vector<BinaryData>& scrAddrVec) const
{
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
      StoredScriptHistory ssh;
      db_->getStoredScriptHistory(ssh, scrAddr);

      map<BinaryData, UnspentTxOut> scrAddrUtxoMap;
      db_->getFullUTXOMapForSSH(ssh, scrAddrUtxoMap);

      for (const auto& utxoPair : scrAddrUtxoMap)
         UTXOs.push_back(utxoPair.second);
   }

   return UTXOs;
}

// kate: indent-width 3; replace-tabs on;
