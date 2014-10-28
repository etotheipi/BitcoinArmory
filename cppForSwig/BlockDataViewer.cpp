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
}

/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
   for (auto wlt : registeredWallets_)
      wlt.second->unregister();

   for (auto wlt : registeredLockboxes_)
      wlt.second->unregister();
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.size() == 0)
      return nullptr;

   LOGINFO << "Registering Wallet " << IDstr;

   // Check if the wallet is already registered
   BinaryData id(IDstr);

   auto regWlt = registeredWallets_.find(id);
   if (regWlt != registeredWallets_.end())
      return regWlt->second.get();
   
   shared_ptr<BtcWallet> newWallet;

   if (bdmPtr_->hasInjectPtr())
   {
      //Main thread is running, save the wallet in queue.
      //No need to notify the main thread, the address registration
      //will trigger it
      
      walletInfo wltInfo;

      wltInfo.register_ = true;
      wltInfo.ID_ = id;
      wltInfo.type_ = 0;

      wltInfo.wallet_ = shared_ptr<BtcWallet>(new BtcWallet(this, id));
      newWallet = wltInfo.wallet_;
      
      {
         unique_lock<mutex> l(walletRegistrationMutex_);
         walletRegistrationQueue_.push_back(wltInfo);
      }
   }
   else
   {
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
   for (const auto& scrAddrPair : newWallet->getScrAddrMap())
      saVec.push_back(scrAddrPair.first);

   saf_->registerAddresses(saVec, newWallet, wltIsNew);

   //tell the wallet it is registered
   newWallet->setRegistered();

   return newWallet.get();
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataViewer::registerLockbox(
   vector<BinaryData> const & scrAddrVec, string IDstr, bool wltIsNew)
{
   if (IDstr.size() == 0)
      return nullptr;

   LOGINFO << "Registering Lockbox " << IDstr;

   // Check if the lockbox is already registered
   BinaryData id(IDstr);
   
   auto regLB = registeredLockboxes_.find(id);
   if (regLB!= registeredLockboxes_.end())
      return regLB->second.get();

   shared_ptr<BtcWallet> newLockbox;

   if (bdmPtr_->hasInjectPtr())
   {
      //Main thread is running, save the wallet in queue.
      //No need to notify the main thread, the address registration
      //will trigger it

      walletInfo wltInfo;

      wltInfo.register_ = true;
      wltInfo.ID_ = id;
      wltInfo.type_ = 1;

      wltInfo.wallet_ = shared_ptr<BtcWallet>(new BtcWallet(this, id));
      newLockbox = wltInfo.wallet_;

      {
         unique_lock<mutex> l(walletRegistrationMutex_);
         walletRegistrationQueue_.push_back(wltInfo);
      }
   }
   else
   {
      // Main thread isnt ruuning, just register the wallet
      // Add it to the list of wallets to watch
      // Instantiate the object through insert.
      auto insertResult = registeredLockboxes_.insert(make_pair(
         id, shared_ptr<BtcWallet>(new BtcWallet(this, id))
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

   return newLockbox.get();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterWallet(string IDstr)
{
   LOGINFO << "Unregistering Wallet " << IDstr;

   BinaryData id(IDstr);

   auto wltIter = registeredWallets_.find(id);

   if (bdmPtr_->hasInjectPtr())
   {
      //main thread is running, save wallet unreg in queue and notify.
      walletInfo wltInfo;

      wltInfo.register_ = false;
      wltInfo.ID_ = BinaryData(id);
      wltInfo.type_ = 0;
      wltInfo.wallet_ = wltIter->second;

      {
         unique_lock<mutex> l(walletRegistrationMutex_);
         walletRegistrationQueue_.push_back(wltInfo);
      }
      
      bdmPtr_->notifyMainThread();
   }
   else
      registeredWallets_.erase(wltIter);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterLockbox(string IDstr)
{
   LOGINFO << "Unregistering Lockbox " << IDstr;

   BinaryData id(IDstr);

   auto wltIter = registeredLockboxes_.find(id);

   if (bdmPtr_->hasInjectPtr())
   {
      //main thread is running, save wallet unreg in queue and notify.
      walletInfo wltInfo;

      wltInfo.register_ = false;
      wltInfo.ID_ = BinaryData(id);
      wltInfo.type_ = 1;
      wltInfo.wallet_ = wltIter->second;

      {
         unique_lock<mutex> l(walletRegistrationMutex_);
         walletRegistrationQueue_.push_back(wltInfo);
      }

      bdmPtr_->notifyMainThread();
   }
   else
      registeredLockboxes_.erase(id);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanWallets(uint32_t startBlock,
   uint32_t endBlock, uint32_t forceRefresh)
{
   uint32_t i = 0;
   bool reorg = false;

   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = getTopBlockHeight() + 1;


   for (auto& wltPair : registeredWallets_)
      wltPair.second->merge();

   for (auto& lbPair : registeredLockboxes_)
      lbPair.second->merge();


   if (initialized_ == false)
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

   if (lastScanned_ > startBlock)
      reorg = true;

   for (auto& wltPair : registeredWallets_)
   {
      //LOGINFO << "Processing wallet #" << i;
      i++;

      wltPair.second->scanWallet(startBlock, endBlock, reorg,
                            invalidatedZCKeys);
   }

   i = 0;
   for (auto& lbPair : registeredLockboxes_)
   {
      //LOGINFO << "Processing Lockbox #" << i;
      i++;

      lbPair.second->scanWallet(startBlock, endBlock, reorg,
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

      for (auto& wltPair : registeredWallets_)
      {
         map<BinaryData, TxIOPair> txioMap;
         wltPair.second->getTxioForRange(startBlock, UINT32_MAX, txioMap);

         map<BinaryData, LedgerEntry> leMap;
         wltPair.second->updateWalletLedgersFromTxio(leMap, txioMap, startBlock, UINT32_MAX);

         if (wltPair.second->uiFilter_ == false)
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
   return registeredWallets_.find(ID) != registeredWallets_.end();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintRegisteredWallets(void) const
{
   for (const auto& wltPair : registeredWallets_)
   {
      cout << "Wallet:";
      wltPair.second->pprintAlittle(cout);
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

   for (auto& wltPair : registeredWallets_)
   {
      wltPair.second->purgeZeroConfTxIO(invalidatedTxIOKeys);
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
   if (saVec.size() == 0)
      return false;
   
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
   for (const auto& wltPair : registeredWallets_)
   {
      const LedgerEntry& le = wltPair.second->getLedgerEntryForTx(txHash);
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
   for (auto& wltPair : registeredWallets_)
      wltPair.second->reset();

   for (auto& lbPair : registeredLockboxes_)
      lbPair.second->reset();

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

   for (auto& wltPair : registeredWallets_)
   {      
      if (forcePaging)
         wltPair.second->mapPages();
      
      if(wltPair.second->uiFilter_ == false)
         continue;
            
      const auto& wltSummary = wltPair.second->getSSHSummary();

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
   for (auto& lbPair : registeredLockboxes_)
      lbPair.second->mapPages();
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
      for (auto& wltPair : registeredWallets_)
      {
         map<BinaryData, LedgerEntry> leMap;

         auto getTxio = [&](uint32_t start, uint32_t end,
            map<BinaryData, TxIOPair>& outMap)->void
         { return wltPair.second->getTxioForRange(start, end, outMap); };

         auto buildLedgers = [&](map<BinaryData, LedgerEntry>& le,
            const map<BinaryData, TxIOPair>& txioMap,
            uint32_t startBlock, uint32_t endBlock)->void
         { wltPair.second->updateWalletLedgersFromTxio(le, txioMap, startBlock, endBlock); };

         hist_.getPageLedgerMap(getTxio, buildLedgers, pageId, leMap);
      
         //this should be locked to a single thread

         if (wltPair.second->uiFilter_ == false)
            continue;

         for (const auto& lePair : leMap)
            globalLedger_.push_back(lePair.second);
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
   for (auto scrAddrPair : scrAddrMap)
      saf->regScrAddrForScan(scrAddrPair.first, startBlock);

   //compute blockHeightCutOff
   saf->scanFrom();

   //scan addresses
   saf->applyBlockRangeToDB(startBlock, endBlock, nullptr);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::updateWalletFilters(const vector<BinaryData>& walletsList)
{
   for (auto& wltPair : registeredWallets_)
      wltPair.second->uiFilter_ = false;

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
bool BlockDataViewer::hasItemInWalletQueue(void) const
{ 
   return walletRegistrationQueue_.size() != 0; 
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::processWalletRegistrationQueue(void)
{
   //grab mutex
   unique_lock<mutex> l(walletRegistrationMutex_);

   for (const auto& wltInfo : walletRegistrationQueue_)
   {
      if (wltInfo.type_ == 0)
      {
         //wallet
         if (wltInfo.register_)
         {  //register
            registeredWallets_[wltInfo.ID_] = wltInfo.wallet_;
         }
         else
         {
            //unregister
            registeredWallets_.erase(wltInfo.ID_);
            int abc = 0;
         }
      }
      else if (wltInfo.type_ == 1)
      {
         //lockbox
         if (wltInfo.register_)
         {
            //register
            registeredLockboxes_[wltInfo.ID_] = wltInfo.wallet_;
         }
         else
         {
            //unregister
            registeredLockboxes_.erase(wltInfo.ID_);
         }
      }
   }

   walletRegistrationQueue_.clear();
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BlockDataViewer::getUnpsentTxoutsForAddr160List(
   const vector<BinaryData>& scrAddrVec) const throw(std::range_error)
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
