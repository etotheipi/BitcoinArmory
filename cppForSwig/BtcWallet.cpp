#include "BtcWallet.h"
#include "BlockUtils.h"
#include "BlockDataViewer.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////
BtcWallet::~BtcWallet(void)
{
   //how am I gonna fit this in the threading model?
   if(bdvPtr_ && isRegistered_)
      bdvPtr_->unregisterWallet(this);
}


// If the wallet is not registered with the BDM, the following two methods do
// the exact same thing.  The only difference is to tell the BDM whether it 
// should do a rescan of the blockchain, or if we know there's nothing to find
// so don't bother (perhaps because we just created the address)...
void BtcWallet::addScrAddress(HashString    scrAddr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum,
                              uint32_t      lastTimestamp,
                              uint32_t      lastBlockNum)
{
   if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj addr(
      bdvPtr_->getDB(),
      &bdvPtr_->blockchain(),
      scrAddr,
      firstTimestamp, firstBlockNum,
      lastTimestamp,  lastBlockNum
   );
   
   //do not register the address with the BDM if this wallet isnt registered
   //yet. All of its scrAddr will be registered with the BDM when the wallet is
   if (isRegistered_)
   {
      if (bdvPtr_ != nullptr)
      {
         vector<BinaryData> saVec;
         saVec.push_back(scrAddr);

         if (!bdvPtr_->registerAddresses(saVec, this, false))
            return;
      }
   }

   scrAddrMap_[scrAddr] = addr;
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewScrAddress(BinaryData scrAddr)
{
   if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj addr = ScrAddrObj(bdvPtr_->getDB(), &bdvPtr_->blockchain(),
      scrAddr, 0, 0, 0, 0);

   if (isRegistered_)
   {
      if (bdvPtr_ != nullptr)
      {
         vector<BinaryData> saVec;
         saVec.push_back(scrAddr);

         if (!bdvPtr_->registerAddresses(saVec, this, true))
            return;
      }
   }

   scrAddrMap_[scrAddr] = addr;
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress(ScrAddrObj const & newScrAddr)
{
   if (scrAddrMap_.find(newScrAddr.getScrAddr()) != scrAddrMap_.end())
      return;

   if (newScrAddr.getScrAddr().getSize() == 0)
      return;

   if (isRegistered_)
   {
      if (bdvPtr_ != nullptr)
      {
         vector<BinaryData> saVec;
         saVec.push_back(newScrAddr.getScrAddr());

         if (!bdvPtr_->registerAddresses(saVec, this, false))
            return;
      }
   }

   scrAddrMap_[newScrAddr.getScrAddr()] = newScrAddr;
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddressBulk(vector<BinaryData> const & scrAddrBulk,
                               bool areNew)
{
   vector<BinaryData> addrToReg;

   for (const auto& scrAddr : scrAddrBulk)
   {
      if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
         continue;

      if (scrAddr.getSize() == 0)
         continue;

      addrToReg.push_back(scrAddr);

   }

   if (isRegistered_)
   {
      if (bdvPtr_ != nullptr)
      {
         if (!bdvPtr_->registerAddresses(addrToReg, this, areNew))
            return;
      }
   }

   for (const auto& scrAddr : addrToReg)
   {
      ScrAddrObj sca(bdvPtr_->getDB(), &bdvPtr_->blockchain(), scrAddr);
      scrAddrMap_.insert(make_pair(scrAddr, sca));
   }

   //should init new addresses
}



/////////////////////////////////////////////////////////////////////////////
// SWIG has some serious problems with typemaps and variable arg lists
// Here I just create some extra functions that sidestep all the problems
// but it would be nice to figure out "typemap typecheck" in SWIG...
void BtcWallet::addScrAddress_ScrAddrObj_(ScrAddrObj const & newScrAddr)
{ 
   addScrAddress(newScrAddr); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress_1_(HashString scrAddr)
{  
   addScrAddress(scrAddr); 
} 

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress_3_(HashString    scrAddr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum)
{  
   addScrAddress(scrAddr, firstBlockNum, firstTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress_5_(HashString    scrAddr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum,
                              uint32_t      lastTimestamp,
                              uint32_t      lastBlockNum)
{
   addScrAddress(scrAddr, firstBlockNum, firstTimestamp, 
                          lastBlockNum,  lastTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasScrAddress(HashString const & scrAddr) const
{
   return (scrAddrMap_.find(scrAddr) != scrAddrMap_.end());
}

/////////////////////////////////////////////////////////////////////////////
/*void BtcWallet::pprintAlot(LMDBBlockDatabase *db, 
                           uint32_t topBlk, bool withAddr) const
{
   map<OutPoint, TxIOPair> const & txiomap = txioMap_;
   
   // Since 99.999%+ of all transactions are not ours, let's do the 
   // fastest bulk filter possible, even though it will add 
   // redundant computation to the tx that are ours.  In fact,
   // we will skip the TxIn/TxOut convenience methods and follow the
   // pointers directly to the data we want

   OutPoint op; // reused
   uint8_t const * txStartPtr = tx.getPtr();
   for (uint32_t iin = 0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      op.unserialize(txStartPtr + tx.getTxInOffset(iin),
         tx.getSize() - tx.getTxInOffset(iin));
      if (KEY_IN_MAP(op, txiomap))
         return make_pair(true, true);
   }

   // Simply convert the TxOut scripts to scrAddrs and check if registered
   for (uint32_t iout = 0; iout<tx.getNumTxOut(); iout++)
   {
      TxOut txout = tx.getTxOutCopy(iout);
      BinaryData scrAddr = txout.getScrAddressStr();
      if (hasScrAddress(scrAddr))
         return make_pair(true, false);

      // It's still possible this is a multisig addr involving one of our 
      // existing scrAddrs, even if we aren't explicitly looking for this multisig
      if (withSecondOrderMultisig && txout.getScriptType() == TXOUT_SCRIPT_MULTISIG)
      {
         BinaryRefReader brrmsig(scrAddr);
         uint8_t PREFIX = brrmsig.get_uint8_t();
         uint8_t M = brrmsig.get_uint8_t();
         uint8_t N = brrmsig.get_uint8_t();
         for (uint8_t a = 0; a<N; a++)
         if (hasScrAddress(HASH160PREFIX + brrmsig.get_BinaryDataRef(20)))
            return make_pair(true, false);
      }
   }

   // If we got here, it's either non std or not ours
   return make_pair(false, false);
}*/

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintAlot(LMDBBlockDatabase *db, uint32_t topBlk, bool withAddr) const
{
   cout << "Wallet PPRINT:" << endl;
   cout << "Tot: " << getFullBalance() << endl;
   cout << "Spd: " << getSpendableBalance(topBlk) << endl;
   cout << "Ucn: " << getUnconfirmedBalance(topBlk) << endl;

   cout << "Ledger: " << endl;
   for(const auto ledger : *ledgerAllAddr_)
      ledger.second.pprintOneLine();

   /*cout << "TxioMap:" << endl;
   for( const auto &txio : txioMap_)
   {
      txio.second.pprintOneLine(db);
   }*/

   if(withAddr)
   {
      for(const auto &sa : scrAddrMap_)
      {
         const ScrAddrObj & addr = sa.second;
         HashString scraddr = addr.getScrAddr();
         cout << "\nAddress: " << scraddr.toHexStr().c_str() << endl;
         cout << "   Tot: " << addr.getFullBalance() << endl;
         cout << "   Spd: " << addr.getSpendableBalance(topBlk) << endl;
         cout << "   Ucn: " << addr.getUnconfirmedBalance(topBlk) << endl;
                  
         cout << "   Ledger: " << endl;
         const auto& saLedgers = addr.getTxLedger();
         for(const auto ledger : saLedgers)
            ledger.second.pprintOneLine();
            
         cout << "   TxioPtrs (Blockchain):" << endl;
         map<OutPoint, TxIOPair>::iterator iter;
         for(auto txio : addr.relevantTxIO_)
         {
            txio.second.pprintOneLine(db);
         }
      }
   }
}

void BtcWallet::pprintAlittle(std::ostream &os) const
{
   os << "\tBalance: " << getFullBalance();
   os << "\tNAddr:   " << getNumScrAddr();
//   os << "\tNTxio:   " << .size();
   os << "\tNLedg:   " << getTxLedger().size();
 //  os << "\tNZC:     " << getZeroConfLedger().size() << endl;      

}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearBlkData(void)
{
   ledgerAllAddr_ = &LedgerEntry::EmptyLedgerMap_;

   for (auto saIter = scrAddrMap_.begin();
      saIter != scrAddrMap_.end(); ++saIter)
   { saIter->second.clearBlkData(); }

   histPages_.reset();
}


////////////////////////////////////////////////////////////////////////////////
// Make a separate method here so we can get creative with how to handle these
// scripts and not clutter the regular scanning code
void BtcWallet::scanNonStdTx(uint32_t blknum, 
                             uint32_t txidx, 
                             Tx &     tx,
                             uint32_t txoutidx,
                             ScrAddrObj& thisAddr)
{
   TxOut txout = tx.getTxOutCopy(txoutidx);
   int findIdx = txout.getScriptRef().find(thisAddr.getScrAddr());
   if(findIdx > -1)
   {
      LOGERR << "ALERT:  Found non-standard transaction referencing";
      LOGERR << "        an address in your wallet.  There is no way";
      LOGERR << "        for this program to determine if you can";
      LOGERR << "        spend these BTC or not.  Please email the";
      LOGERR << "        following information to support@bitcoinarmory.com";
      LOGERR << "        for help identifying the transaction and how";
      LOGERR << "        to spend it:";
      LOGERR << "   Block Number: " << blknum;
      LOGERR << "   Tx Hash:      " << tx.getThisHash().copySwapEndian().toHexStr() 
                               << " (BE)";
      LOGERR << "   TxOut Index:  " << txoutidx;
      LOGERR << "   PubKey Hash:  " << thisAddr.getScrAddr().toHexStr() << " (LE)";
      LOGERR << "   RawScript:    ";
      BinaryDataRef scr = txout.getScriptRef();
      size_t sz = scr.getSize(); 
      for(uint32_t i=0; i<sz; i+=32)
      {
         if( i < sz-32 )
            LOGERR << "      " << scr.getSliceCopy(i,sz-i).toHexStr();
         else
            LOGERR << "      " << scr.getSliceCopy(i,32).toHexStr();
      }
      LOGERR << "   Attempting to interpret script:";
      BtcUtils::pprintScript(scr);


      OutPoint outpt(tx.getThisHash(), txoutidx);      
      /*nonStdUnspentOutPoints_.insert(outpt);
      nonStdTxioMap_.insert(
         make_pair(outpt, TxIOPair(tx.getTxRef(),txoutidx))
      );*/
   }

}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getSpendableBalance(\
                    uint32_t currBlk, bool ignoreAllZC) const
{
   uint64_t balance = 0;
   for(const auto scrAddr : scrAddrMap_)
      balance += scrAddr.second.getSpendableBalance(currBlk, ignoreAllZC);
   
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getUnconfirmedBalance(
                    uint32_t currBlk, bool inclAllZC) const
{
   uint64_t balance = 0;
   for (const auto scrAddr : scrAddrMap_)
      balance += scrAddr.second.getUnconfirmedBalance(currBlk, inclAllZC);
   
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getFullBalance() const
{
   return balance_;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getFullBalanceFromDB() const
{
   uint64_t balance = 0;

   for (const auto scrAddr : scrAddrMap_)
      balance += scrAddr.second.getFullBalance();

   return balance;
}
////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getAddrTotalTxnCount(const BinaryData& addr) const
{
   const ScrAddrObj* addrPtr = getScrAddrObjByKey(addr);
   if (addrPtr != nullptr)
      return addrPtr->getTxioCountFromSSH();

   return 0;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::prepareTxOutHistory(uint64_t val)
{
   uint64_t value;
   uint32_t count;

   while (1)
   {
      value = 0;
      count = 0;

      for (const auto& scrAddr : scrAddrMap_)
      {
         value += scrAddr.second.getLoadedTxOutsValue();
         count += scrAddr.second.getLoadedTxOutsCount();
      }

      //grab at least MIN_UTXO_PER_TXN to cover for twice the requested value
      if (value * 2 < val || count < MIN_UTXO_PER_TXN)
      {
         /***getMoreUTXOs returns true if it found more. As long as one
         ScrAddrObj, reassess the utxo state, otherwise get out of the loop
         ***/

         bool hasMore = false;
         for (auto& scrAddr : scrAddrMap_)
            hasMore |= scrAddr.second.getMoreUTXOs();

         if (hasMore == false)
            return;
      }
      else return;
   } 
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::prepareFullTxOutHistory()
{
   while (1)
   {
      bool hasMore = false;
      for (auto& scrAddr : scrAddrMap_)
         hasMore |= scrAddr.second.getMoreUTXOs();

      if (hasMore == false)
         return;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::resetTxOutHistory()
{
   for (auto& scrAddr : scrAddrMap_)
      scrAddr.second.resetTxOutHistory();
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getSpendableTxOutListForValue(uint64_t val)
{
   /***
   Only works with DB so it naturally ignores ZC 
   Use getSpendableTxOutListFromZC to spend from ZC

   Only the TxIOPairs (DB keys) are saved in RAM. The full TxOuts are pulled only
   on demand since there is a high probability that at least a few of them will 
   be consumed.
   ***/

   prepareTxOutHistory(val);
   LMDBBlockDatabase *db = bdvPtr_->getDB();

   //start a RO txn to grab the txouts from DB
   LMDBEnv::Transaction tx(&db->dbEnv_, LMDB::ReadOnly);

   vector<UnspentTxOut> utxoList;
   uint32_t blk = bdvPtr_->getTopBlockHeight();

   for (const auto& scrAddr : scrAddrMap_)
   {
      const auto& utxoMap = scrAddr.second.getSpendableTxOutList();

      for (const auto& txioPair : utxoMap)
      {
         TxOut txout = txioPair.second.getTxOutCopy(db);
         UnspentTxOut UTXO = UnspentTxOut(db, txout, blk);
         utxoList.push_back(UTXO);
      }
   }

   //Shipped a list of TxOuts, time to reset the entire TxOut history, since 
   //dont know if any TxOut will be spent

   resetTxOutHistory();
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintLedger() const
{ 
   cout << "Wallet Ledger:  " << getFullBalance()/1e8 << endl;
   for(const auto ledger : *ledgerAllAddr_)
      ledger.second.pprintOneLine();
}

////////////////////////////////////////////////////////////////////////////////
// Return a list of addresses this wallet has ever sent to (w/o change addr)
// Does not include zero-conf tx
//
// TODO:  should spend the time to pass out a tx list with it the addrs so
//        that I don't have to re-search for them later...
vector<AddressBookEntry> BtcWallet::createAddressBook(void) const
{
   SCOPED_TIMER("createAddressBook");
   // Collect all data into a map -- later converted to vector and sort it
   map<HashString, AddressBookEntry> sentToMap;
   set<HashString> allTxList;
   set<HashString> perTxAddrSet;

   // Go through all TxIO for this wallet, collect outgoing transactions
   for (const auto scrAddr : scrAddrMap_)
   {
      const auto& scrAddrTxioMap = scrAddr.second.getTxIOMap();

      for (const auto &tio : scrAddrTxioMap)
      {
         const TxIOPair & txio = tio.second;

         // It's only outgoing if it has a TxIn
         if (!txio.hasTxIn())
            continue;

         Tx thisTx = txio.getTxRefOfInput().attached(bdvPtr_->getDB()).getTxCopy();
         HashString txHash = thisTx.getThisHash();

         if (allTxList.count(txHash) > 0)
            continue;
         else
            allTxList.insert(txHash);


         // Iterate over all TxOut in this Tx for recipients
         perTxAddrSet.clear();
         for (uint32_t iout = 0; iout<thisTx.getNumTxOut(); iout++)
         {
            HashString scraddr = thisTx.getTxOutCopy(iout).getScrAddressStr();

            // Skip this address if it's in our wallet (usually change addr)
            if (hasScrAddress(scraddr) || perTxAddrSet.count(scraddr)>0)
               continue;

            // It's someone else's address for sure, add it to the map if necessary
            if (sentToMap.count(scraddr) == 0)
               sentToMap[scraddr] = AddressBookEntry(scraddr);

            sentToMap[scraddr].addTx(thisTx);
            perTxAddrSet.insert(scraddr);
         }
      }
   }

   vector<AddressBookEntry> outputVect;
   for(const auto &entry : sentToMap)
   {
      outputVect.push_back(entry.second);
   }

   sort(outputVect.begin(), outputVect.end());
   return outputVect;
}

////////////////////////////////////////////////////////////////////////////////
vector<const LedgerEntry*> BtcWallet::getTxLedger(
   HashString const & scraddr)
   const
{
   vector<const LedgerEntry*> leVec;
   SCOPED_TIMER("BtcWallet::getTxLedger");

   auto saIter = scrAddrMap_.find(scraddr);
   if (ITER_IN_MAP(saIter, scrAddrMap_))
   {
      const auto& leMap = saIter->second.getTxLedger();
      for (const auto& lePair : leMap)
         leVec.push_back(&lePair.second);
   }
   else
      leVec.push_back(&LedgerEntry::EmptyLedger_);
   return leVec;
}

////////////////////////////////////////////////////////////////////////////////
vector<const LedgerEntry*> BtcWallet::getTxLedger() const
{
   vector<const LedgerEntry*> leVec;

   for (const auto& lePair : *ledgerAllAddr_)
      leVec.push_back(&lePair.second);

   return leVec;
}

///////////////////////////////////////////////////////////////////////////////
void BtcWallet::fetchDBScrAddrData(uint32_t startBlock, 
                                             uint32_t endBlock)
{
   SCOPED_TIMER("fetchWalletRegisteredScrAddrData");

   for (auto saIter = scrAddrMap_.begin(); 
      saIter != scrAddrMap_.end(); 
      saIter++)
   {
      saIter->second.fetchDBScrAddrData(startBlock, endBlock);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateAfterReorg(uint32_t lastValidBlockHeight)
{
   for (auto& scrAddr : scrAddrMap_)
   {
      scrAddr.second.updateAfterReorg(lastValidBlockHeight);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::scanWalletZeroConf(bool withReorg)
{
   /***
   Scanning ZC will update the scrAddr ledger with the ZC txio. Ledgers require
   a block height, which should be the current top block.
   ***/
   SCOPED_TIMER("rescanWalletZeroConf");

   map<BinaryData, map<BinaryData, TxIOPair> > ZCtxioMap = 
      bdvPtr_->getNewZeroConfTxIOMap();

   if (withReorg==true)
   {
      //scanning ZC after a reorg, Everything beyond the last valid block has
      //been wiped out of RAM, thus grab the full ZC txio map. Still need a call
      //to getNewZeroConfTxIOMap to clear the new ZC map
      ZCtxioMap = bdvPtr_->getFullZeroConfTxIOMap();
   }

   for (auto& scrAddrTxio : ZCtxioMap)
   {
      map<BinaryData, ScrAddrObj>::iterator scrAddr = 
	      scrAddrMap_.find(scrAddrTxio.first);

      if (scrAddr != scrAddrMap_.end())
         scrAddr->second.scanZC(scrAddrTxio.second);
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::scanWallet(uint32_t startBlock, uint32_t endBlock, 
   bool reorg, const map<BinaryData, vector<BinaryData> >& invalidatedZCKeys)
{
   if (startBlock < endBlock)
   {
      purgeZeroConfTxIO(invalidatedZCKeys);

      //new top block
      if (reorg)
         updateAfterReorg(startBlock);
         
      LMDBEnv::Transaction tx(&bdvPtr_->getDB()->dbEnv_, LMDB::ReadOnly);

      fetchDBScrAddrData(startBlock, endBlock);
      scanWalletZeroConf(reorg);

      map<BinaryData, TxIOPair> txioMap;
      getTxioForRange(startBlock, UINT32_MAX, txioMap);
      updateWalletLedgersFromTxio(*ledgerAllAddr_, txioMap, 
                          startBlock, UINT32_MAX, true);
   
      balance_ = getFullBalanceFromDB();
   }
   else
   {
      //top block didnt change, only have to check for new ZC
      if (bdvPtr_->isZcEnabled())
      {
         scanWalletZeroConf();
         map<BinaryData, TxIOPair> txioMap;
         getTxioForRange(endBlock +1, UINT32_MAX, txioMap);
         updateWalletLedgersFromTxio(*ledgerAllAddr_, txioMap, 
                             endBlock +1, UINT32_MAX);

         balance_ = getFullBalanceFromDB();

         //return false because no new block was parsed
         return false;
      }
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::reset()
{
   merge();

   clearBlkData();
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::purgeZeroConfTxIO(
   const map<BinaryData, vector<BinaryData> >& invalidatedTxIO)
{
   for (auto& txioVec : invalidatedTxIO)
   {
      map<BinaryData, ScrAddrObj>::iterator scrAddr = 
	      scrAddrMap_.find(txioVec.first);

      if (scrAddr != scrAddrMap_.end())
         scrAddr->second.purgeZC(txioVec.second);
   }
}

////////////////////////////////////////////////////////////////////////////////
const LedgerEntry& BtcWallet::getLedgerEntryForTx(const BinaryData& txHash) const
{
   for (auto& le : *ledgerAllAddr_)
   {
      if (le.second.getTxHash() == txHash)
         return le.second;
   }

   return LedgerEntry::EmptyLedger_;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::prepareScrAddrForMerge(const vector<BinaryData>& scrAddrVec, bool isNew)
{
   //pass isNew = true for supernode too, since that's the same behavior

   map<BinaryData, ScrAddrObj> newScrAddrMap;

   for (const auto& scrAddr : scrAddrVec)
   {
      ScrAddrObj newScrAddrObj(bdvPtr_->getDB(),
                               &bdvPtr_->blockchain(),
                               scrAddr);
      newScrAddrMap.insert(make_pair(scrAddr, newScrAddrObj));
   }

   //grab merge lock
   while (mergeLock_.fetch_or(1, memory_order_acquire));

   //add scrAddr to merge map
   scrAddrMapToMerge_.insert(newScrAddrMap.begin(), newScrAddrMap.end());

   //mark merge flag, 2 for fresh scrAddr
   mergeFlag_ = (isNew ? 2 : 1);

   //release lock
   mergeLock_.store(0, memory_order_release);
}

////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::merge()
{
   if (mergeFlag_ > 0)
   {
      bool rt = false;

      //grab lock
      while (mergeLock_.fetch_or(1, memory_order_acquire));

      if (mergeFlag_ == 1) //addresses with history
      {
         //rescan last 100 blocks to account for new blocks and reorgs
         uint32_t topBlock = bdvPtr_->blockchain().top().getBlockHeight() + 1;
         uint32_t bottomBlock = 0;
         if (topBlock > 99)
            bottomBlock = topBlock - 100;

         bdvPtr_->scanScrAddrVector(scrAddrMapToMerge_, bottomBlock, topBlock);
         
         //make sure this returns true so that the upper BDV object re-inits the wallet
         rt = true;
      }
      else if (mergeFlag_ == 2)
      {
         LMDBEnv::Transaction tx(&bdvPtr_->getDB()->dbEnv_, LMDB::ReadOnly);
         
         //fresh addresses, just have to run mapHistory to initialize the ScrAddrObj
         for (auto& scrAddrPair : scrAddrMapToMerge_)
            scrAddrPair.second.mapHistory();
      }
      
      //merge scrAddrMap
      for (auto& scrAddrPair : scrAddrMapToMerge_)
         scrAddrMap_.insert(scrAddrPair); //no need to override existing ScrAddrObj

      //clear merge map
      scrAddrMapToMerge_.clear();

      //clear flag
      mergeFlag_ = 0;

      //release lock
      mergeLock_.store(0, memory_order_release);

      return rt;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
map<uint32_t, uint32_t> BtcWallet::computeScrAddrMapHistSummary()
{
   map<uint32_t, uint32_t> histSummary;
   LMDBEnv::Transaction tx(&bdvPtr_->getDB()->dbEnv_, LMDB::ReadOnly);
   for (auto& scrAddrPair : scrAddrMap_)
   {
      scrAddrPair.second.mapHistory();
      const map<uint32_t, uint32_t>& txioSum =
         scrAddrPair.second.getHistSSHsummary();

      for (const auto& histPair : txioSum)
         histSummary[histPair.first] += histPair.second;
   }

   return histSummary;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::mapPages()
{
    /***mapPages seems rather fast (0.6~0.3sec to map the history of wallet
   with 1VayNert, 1Exodus and 100k empty addresses.

   My original plan was to grab the first 100 txn of a wallet to have the first
   page of its history ready for rendering, and parse its history in a side 
   thread, as I was expecting that process to be long.

   Since my original assumption understimated LMDB's speed, I can instead map 
   the history first, then create the first page, as it results in a more 
   consistent txn distribution per page.

   Also taken in consideration is the code in updateLedgers. Ledgers are built
   by ScrAddrObj. The particular call, updateLedgers, expects to receive parse
   txioPairs in ascending order (lowest to highest height). 

   By gradually parsing history from the top block downward, updateLedgers is
   fed both ascending and descending sets of txioPairs, which would require
   certain in depth amendments to its code to satisfy a behavior that takes 
   place only once per wallet per load.
   ***/
   TIMER_START("mapPages");
   ledgerAllAddr_ = &LedgerEntry::EmptyLedgerMap_;

   auto computeSSHsummary = [this](bool)->map<uint32_t, uint32_t>
      {return this->computeScrAddrMapHistSummary(); };

   histPages_.mapHistory(computeSSHsummary);

   auto getTxio = [this](uint32_t start, uint32_t end, map<BinaryData, TxIOPair>& txioMap)->void
   { this->getTxioForRange(start, end, txioMap); };

   auto computeLedgers = [this](map<BinaryData, LedgerEntry>& leMap, 
                               const map<BinaryData, TxIOPair>& txioMap,
                               uint32_t start)->void
   { this->updateWalletLedgersFromTxio(leMap, txioMap, start, UINT32_MAX, false); };

   ledgerAllAddr_ = &histPages_.getPageLedgerMap(getTxio, computeLedgers, 0);

   TIMER_STOP("mapPages");
   double mapPagesTimer = TIMER_READ_SEC("mapPages");
   LOGINFO << "mapPages done in " << mapPagesTimer << " secs";
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::getTxioForRange(uint32_t start, uint32_t end,
   map<BinaryData, TxIOPair>& outMap) const
{
   for (const auto& scrAddrPair : scrAddrMap_)
      scrAddrPair.second.getHistoryForScrAddr(start, end, outMap, false);
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateWalletLedgersFromTxio(
   map<BinaryData, LedgerEntry>& leMap,
   const map<BinaryData, TxIOPair>& txioMap,
   uint32_t startBlock, uint32_t endBlock,
   bool purge) const
{
   LedgerEntry::computeLedgerMap(leMap, txioMap, startBlock, endBlock, walletID_,
                                 bdvPtr_->getDB(), &bdvPtr_->blockchain(), purge);
}

////////////////////////////////////////////////////////////////////////////////
const ScrAddrObj* BtcWallet::getScrAddrObjByKey(BinaryData key) const
{
   auto saIter = scrAddrMap_.find(key);
   if (saIter != scrAddrMap_.end())
      return &saIter->second;

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
const map<BinaryData, LedgerEntry>& BtcWallet::getHistoryPage(uint32_t pageId)
{
   auto getTxio = [this](uint32_t start, uint32_t end, map<BinaryData, TxIOPair>& txioMap)->void
   { this->getTxioForRange(start, end, txioMap); };

   auto computeLedgers = [this](map<BinaryData, LedgerEntry>& leMap,
      const map<BinaryData, TxIOPair>& txioMap,
      uint32_t start)->void
   { this->updateWalletLedgersFromTxio(leMap, txioMap, start, UINT32_MAX, false); };

   return histPages_.getPageLedgerMap(getTxio, computeLedgers, pageId);
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::needsRefresh(void)
{ 
   bdvPtr_->flagRefresh(true, walletID_); 
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::forceScan(void)
{
   //force scan all the addresses registered in this wallet in a side thread
   vector<BinaryData> saVec;

   for (const auto& sa : scrAddrMap_)
      saVec.push_back(sa.first);

   bdvPtr_->registerAddresses(saVec, this, -1);
}
// kate: indent-width 3; replace-tabs on;
