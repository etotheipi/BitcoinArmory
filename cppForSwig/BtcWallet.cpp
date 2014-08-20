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
   if (scrAddr.getSize() != 21)
   {
      LOGERR << "scrAddr is " << scrAddr.getSize() << " bytes long!";
      return;
   }
   if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj addr(
      bdvPtr_->getDB(),
      &bdvPtr_->blockchain(),
      scrAddr,
      firstTimestamp, firstBlockNum,
      lastTimestamp,  lastBlockNum
   );
   
   if(bdvPtr_ != nullptr) 
      if (!bdvPtr_->registerScrAddr(addr, this))
         return;
   
   scrAddrMap_[scrAddr] = addr;

}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewScrAddress(BinaryData scrAddr)
{
   if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj addr = ScrAddrObj(bdvPtr_->getDB(), &bdvPtr_->blockchain(),
      scrAddr, 0, 0, 0, 0);

   if(bdvPtr_ != nullptr)
      if (!bdvPtr_->registerScrAddr(addr, this))
         return;
   
   scrAddrMap_[scrAddr] = addr;
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress(ScrAddrObj const & newScrAddr)
{
   if (scrAddrMap_.find(newScrAddr.getScrAddr()) != scrAddrMap_.end())
      return;

   if (newScrAddr.getScrAddr().getSize() == 0)
      return;

   if (bdvPtr_ != nullptr)
      if (!bdvPtr_->registerScrAddr(newScrAddr, this))
         return;
   
   scrAddrMap_[newScrAddr.getScrAddr()] = newScrAddr;
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
   uint32_t numLedg = ledgerAllAddr_.size();

   cout << "Wallet PPRINT:" << endl;
   cout << "Tot: " << getFullBalance() << endl;
   cout << "Spd: " << getSpendableBalance(topBlk) << endl;
   cout << "Ucn: " << getUnconfirmedBalance(topBlk) << endl;

   cout << "Ledger: " << endl;
   for(const auto ledger : ledgerAllAddr_)
      ledger.pprintOneLine();

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
   ledgerAllAddr_.clear();

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
      uint32_t sz = scr.getSize(); 
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
   uint64_t balance = 0;

   for(const auto scrAddr : scrAddrMap_)
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
vector<UnspentTxOut> BtcWallet::getSpendableTxOutList(
   uint32_t blkNum, 
   bool ignoreAllZC
) const
{
   vector<UnspentTxOut> utxoList;
   vector<UnspentTxOut> saUtxoList;

   for (const auto scrAddr : scrAddrMap_)
   {
      saUtxoList = scrAddr.second.getSpendableTxOutList();
      utxoList.insert(utxoList.end(), saUtxoList.begin(), saUtxoList.end());
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintLedger() const
{ 
   cout << "Wallet Ledger:  " << getFullBalance()/1e8 << endl;
   for(const auto ledger : ledgerAllAddr_)
      ledger.pprintOneLine();
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
vector<LedgerEntry> BtcWallet::getTxLedger(HashString const & scraddr)
   const
{
   SCOPED_TIMER("BtcWallet::getTxLedger");

   auto saIter = scrAddrMap_.find(scraddr);
   if (ITER_IN_MAP(saIter, scrAddrMap_))
   {
      const auto& saLedger = saIter->second.getTxLedger();
      vector<LedgerEntry> vle;

      for (const auto& lePair : saLedger)
         vle.push_back(lePair.second);

      return vle;
   }

   return vector<LedgerEntry>();
}

const vector<LedgerEntry>& BtcWallet::getTxLedger() const
{
   return ledgerAllAddr_;
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
                           bool reorg)
{
   merge();

   if (startBlock < endBlock)
   {
      //new top block
      if (reorg)
         updateAfterReorg(startBlock);
         
      LMDB::Transaction batch(&bdvPtr_->getDB()->dbs_[BLKDATA]);

      fetchDBScrAddrData(startBlock, endBlock);
      scanWalletZeroConf(reorg);

      updateWalletLedgersFromScrAddr(ledgerAllAddr_, scrAddrMap_, 
                          startBlock, UINT32_MAX -1);
   }
   else
   {
      //top block didnt change, only have to check for new ZC
      if (bdvPtr_->isZcEnabled())
      {
         scanWalletZeroConf();
         updateWalletLedgersFromScrAddr(ledgerAllAddr_, scrAddrMap_, 
                             startBlock, endBlock, false);

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
void BtcWallet::purgeLedgerFromHeight(uint32_t height)
{
   /***
   Remove all entries starting this height, included.
   Since ledger entries are always sorted, find the first to >= height and
   delete everything starting that index. This will always erase ZC entries.
   ***/

   uint32_t i = 0;
   for (auto le : ledgerAllAddr_)
   {
      if (le.getBlockNum() >= height)
         break;

      i++;
   }

   ledgerAllAddr_.erase(ledgerAllAddr_.begin() + i, ledgerAllAddr_.end());
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateWalletLedgersFromScrAddr(
   vector<LedgerEntry>& walletLedgers,
   const map<BinaryData, ScrAddrObj>& scrAddrMap, 
   uint32_t startBlock, 
   uint32_t endBlock,
   bool purge)
{
   //nuke every entry from startBlock onwards before adding the freshly updated
   //ledgers from each scrAddr
   if ( purge==true ) 
      purgeLedgerFromHeight(startBlock);

   uint32_t zero = 0;
   BinaryData startHgtX = DBUtils::heightAndDupToHgtx(startBlock, 0);
   BinaryData endHgtX = DBUtils::heightAndDupToHgtx(endBlock + 1, 0);

   startHgtX.append((uint8_t*)&zero, 2);
   endHgtX.append((uint8_t*)&zero, 2);
   
   if (startBlock >= endBlock)
   {
      //parsing ZC ledgers only
      startHgtX = WRITE_UINT64_BE(0xffff000000000000).getSliceCopy(0, 6);
      endHgtX   = WRITE_UINT64_BE(0xffffffffffffffff).getSliceCopy(0, 6);
   }


   map<BinaryData, vector<LedgerEntry>> arrangeByTxn;

   vector<LedgerEntry>* leVec;

   //arrange scrAddr ledger entries by transaction, within start/endBlock range
   for (const auto scrAddrPair : scrAddrMap)
   {
      const ScrAddrObj& scrAddr = scrAddrPair.second;
      const map<BinaryData, LedgerEntry>& saLe = scrAddr.getTxLedger();

      auto leRange = saLe.equal_range(startHgtX);
      map<BinaryData, LedgerEntry>::const_iterator leIter = leRange.first;
      
      while (leIter != saLe.end())
      {
         if (leIter->first < endHgtX)
         {
            leVec = &arrangeByTxn[leIter->first];
            leVec->push_back(leIter->second);

            ++leIter;
         }
         else break;
      }
   }

   //parse ledger entries per txHash
   int64_t ledgerVal;
   int64_t valIn, valOut, val;
   bool isCoinbase;
   bool isSendToSelf;
   bool isChangeBack;
   uint32_t blockNum;
   uint32_t txTime;
   uint32_t nHits;
   uint32_t txIndex;
   BinaryData txHash;

   for (const auto txLedgersPair : arrangeByTxn)
   {
      ledgerVal = valIn = valOut = 0;
      isCoinbase = false;
      isSendToSelf = false;
      isChangeBack = false;
      nHits = 0;

      auto leIter = txLedgersPair.second.begin();
      blockNum = (*leIter).getBlockNum();
      txTime = (*leIter).getTxTime();
      txIndex = (*leIter).getIndex();
      txHash = (*leIter).getTxHash();

      while (leIter != txLedgersPair.second.end())
      {
         isCoinbase |= (*leIter).isCoinbase();

         val = (*leIter).getValue();
         if (val > 0)
            valIn += val;
         else
         {
            valOut += val;
            if (hasScrAddress((*leIter).getScrAddr()))
               nHits++;
         }

         ledgerVal += val;


         ++leIter;
      }

      if (valIn + valOut == 0)
      {
         ledgerVal = valIn;
         isSendToSelf = true;
      }
      else if (nHits != 0 && (valIn + valOut) < 0)
         isChangeBack = true;

      LedgerEntry le(BinaryData(0), walletID_,
         ledgerVal,
         blockNum,
         txHash,
         txIndex,
         txTime,
         isCoinbase,
         isSendToSelf,
         isChangeBack);

      walletLedgers.push_back(le);
   }

   //sort the ledgers by blocknum and txid
   sort(walletLedgers.begin(), walletLedgers.end());

   //delete duplicates
   walletLedgers.erase(unique(walletLedgers.begin(), walletLedgers.end()), 
                       walletLedgers.end());
}

////////////////////////////////////////////////////////////////////////////////
LedgerEntry BtcWallet::getLedgerEntryForTx(const BinaryData& txHash) const
{
   for (auto& le : ledgerAllAddr_)
   {
      if (le.getTxHash() == txHash)
         return le;
   }

   return LedgerEntry();
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::preloadScrAddr(const BinaryData& scrAddr)
{
   ScrAddrObj newScrAddrObj(bdvPtr_->getDB(), 
                            &bdvPtr_->blockchain(), 
                            scrAddr);
   //build history
   LMDB::Transaction batch(&bdvPtr_->getDB()->dbs_[BLKDATA]);
   newScrAddrObj.mapHistory();

   //grab merge lock
   while (mergeLock_.fetch_or(1, memory_order_acquire));

   //add scrAddr to merge map
   scrAddrMapToMerge_[scrAddr] = newScrAddrObj;

   //mark merge flag
   mergeFlag_ = true;

   //release lock
   mergeLock_.store(0, memory_order_release);
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::merge(void)
{
   if (mergeFlag_ == true)
   {

      //grab lock
      while (mergeLock_.fetch_or(1, memory_order_acquire));


      /***TODO: make this play nice with the paging code***/
      
      //rescan last 100 blocks to account for new blocks and reorgs
      uint32_t topBlock = bdvPtr_->blockchain().top().getBlockHeight() +1;
      uint32_t bottomBlock = 0;
      if (topBlock > 99)
         bottomBlock = topBlock -100;
      for (auto& scrAddrPair : scrAddrMapToMerge_)
         scrAddrPair.second.fetchDBScrAddrData(bottomBlock, topBlock);
      

      /***NOTE: should ledgers just be wiped and fully rebuilt? If the new 
      addresses are used in shared transactions, the ledgers will be invalid
      ***/

      //update wallet ledger, pass false to not reset the other ledger entries
      updateWalletLedgersFromScrAddr(ledgerAllAddr_, scrAddrMapToMerge_, 0, 
                          bdvPtr_->blockchain().top().getBlockHeight() + 1,
                          false);
      
      //merge scrAddrMap
      for (auto& scrAddrPair : scrAddrMapToMerge_)
         scrAddrMap_[scrAddrPair.first] = scrAddrPair.second;

      //clear merge map
      scrAddrMapToMerge_.clear();

      //clear flag
      mergeFlag_ = false;

      //release lock
      mergeLock_.store(0, memory_order_release);

   }
}

////////////////////////////////////////////////////////////////////////////////
map<uint32_t, uint32_t> BtcWallet::computeScrAddrMapHistSummary()
{
   map<uint32_t, uint32_t> histSummary;
   LMDB::Transaction batch(&bdvPtr_->getDB()->dbs_[BLKDATA]);
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

   auto computeSSHsummary = [this](void)->map<uint32_t, uint32_t>
      {return this->computeScrAddrMapHistSummary(); };

   histPages_.mapHistory(computeSSHsummary);

   TIMER_STOP("mapPages");
   double mapPagesTimer = TIMER_READ_SEC("mapPages");
   LOGINFO << "mapPages done in " << mapPagesTimer << " secs";
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::getTxioForRange(uint32_t start, uint32_t end,
   map<BinaryData, TxIOPair>& outMap) const
{
   for (const auto& scrAddrPair : scrAddrMap_)
      scrAddrPair.second.getHistoryForScrAddr(start, end, outMap);
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateWalletLedgersFromTxio(map<BinaryData, LedgerEntry>& leMap,
   const map<BinaryData, TxIOPair>& txioMap,
   uint32_t startBlock, uint32_t endBlock) const
{
   //arrange txios by transaction
   map<BinaryData, vector<TxIOPair> > TxnTxIOMap;

   for (const auto& txio : txioMap)
   {
      auto txOutDBKey = txio.second.getDBKeyOfOutput().getSliceCopy(0, 6);

      auto& txioVec = TxnTxIOMap[txOutDBKey];
      txioVec.push_back(txio.second);

      if (txio.second.hasTxIn())
      {
         auto txInDBKey = txio.second.getDBKeyOfInput().getSliceCopy(0, 6);

         auto& txioVec = TxnTxIOMap[txInDBKey];
         txioVec.push_back(txio.second);
      }
   }

   uint64_t value;
   int64_t valIn, valOut;

   uint32_t blockNum;
   uint32_t txTime;
   uint32_t nHits;
   uint16_t txIndex;
   BinaryData txHash;

   bool isCoinbase;
   bool isChangeBack;
   bool isSendToSelf;

   BinaryData dbKey;

   LMDBBlockDatabase* db = bdvPtr_->getDB();
   Blockchain& bc = bdvPtr_->blockchain();

   for (const auto& txioVec : TxnTxIOMap)
   {
      //reset ledger variables
      value = valIn = valOut = 0;
      isCoinbase = isChangeBack = isSendToSelf = false;
      nHits = 0;
      
      //grab iterator
      auto txioIter = txioVec.second.cbegin();

      //get txhash, block and txIndex
      if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
      {
         txHash = txioIter->getTxHashOfOutput(db);
         blockNum = DBUtils::hgtxToHeight(txioIter->getDBKeyOfOutput().getSliceRef(0, 4));
         txIndex = READ_UINT16_BE(txioIter->getDBKeyOfOutput().getSliceRef(4, 2));
      }
      else
      {
         txHash = txioIter->getTxHashOfInput(db);
         blockNum = DBUtils::hgtxToHeight(txioIter->getDBKeyOfInput().getSliceRef(0, 4));
         txIndex = txioIter->getIndexOfInput();
         txIndex = READ_UINT16_BE(txioIter->getDBKeyOfInput().getSliceRef(4, 2));
      }

      if (blockNum < startBlock || blockNum > endBlock)
         continue;

      //get tx time
      txTime = bc.getHeaderByHeight(blockNum).getTimestamp();


      while (txioIter != txioVec.second.cend())
      {
         if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
         {
            isCoinbase |= txioIter->isFromCoinbase();
            valIn += txioIter->getValue();
            value += txioIter->getValue();
         }

         if (txioIter->getDBKeyOfInput().startsWith(txioVec.first))
         {
            valOut -= txioIter->getValue();
            value -= txioIter->getValue();

            nHits++;
         }

         ++txioIter;
      }

      if (valIn + valOut == 0)
      {
         value = valIn;
         isSendToSelf = true;
      }
      else if (nHits != 0 && (valIn + valOut) < 0)
         isChangeBack = true;

      LedgerEntry le(BinaryData(0), walletID_,
         value,
         blockNum,
         txHash,
         txIndex,
         txTime,
         isCoinbase,
         isSendToSelf,
         isChangeBack);

      leMap[txHash] = le;
   }
}

////////////////////////////////////////////////////////////////////////////////
const ScrAddrObj* BtcWallet::getScrAddrObjByKey(BinaryData key) const
{
   auto saIter = scrAddrMap_.find(key);
   if (saIter != scrAddrMap_.end())
      return &saIter->second;

   return nullptr;
}

// kate: indent-width 3; replace-tabs on;
