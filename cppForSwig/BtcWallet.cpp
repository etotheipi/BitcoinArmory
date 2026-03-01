////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "BtcWallet.h"
#include "BlockUtils.h"
#include "txio.h"
#include "BlockDataViewer.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress(const BinaryData& scrAddr)
{
   auto addrMap = scrAddrMap_.get();
   if (addrMap->find(scrAddr) != addrMap->end())
      return;

   vector<BinaryData> saVec;
   saVec.push_back(scrAddr);

   {
      auto scrAddrMap = scrAddrMap_.get();
      for (auto& scraddr : *scrAddrMap)
         saVec.push_back(scraddr.first);
   }

   string IDstr(walletID_.getCharPtr(), walletID_.getSize());

   bdvPtr_->registerAddresses(saVec, IDstr, false);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::removeAddressBulk(vector<BinaryData> const & scrAddrBulk)
{
   scrAddrMap_.erase(scrAddrBulk);
   needsRefresh(true);
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasScrAddress(HashString const & scrAddr) const
{
   auto addrMap = scrAddrMap_.get();
   return (addrMap->find(scrAddr) != addrMap->end());
}

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

   auto addrMap = scrAddrMap_.get();

   if(withAddr)
   {
      for(auto &sa : *addrMap)
      {
         const ScrAddrObj & addr = *sa.second;
         HashString scraddr = addr.getScrAddr();
         cout << "\nAddress: " << scraddr.copySwapEndian().toHexStr() << endl;
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
   auto addrMap = scrAddrMap_.get();

   os << "\tBalance: " << getFullBalance();
   os << "\tNAddr:   " << addrMap->size();
//   os << "\tNTxio:   " << .size();
   os << "\tNLedg:   " << getTxLedger().size();
 //  os << "\tNZC:     " << getZeroConfLedger().size() << endl;      

}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearBlkData(void)
{
   ledgerAllAddr_ = &LedgerEntry::EmptyLedgerMap_;

   auto addrMap = scrAddrMap_.get();

   for (auto saPair : *addrMap)
   { saPair.second->clearBlkData(); }

   histPages_.reset();
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getSpendableBalance(uint32_t currBlk) const
{
   auto addrMap = scrAddrMap_.get();

   uint64_t balance = 0;
   for(const auto scrAddr : *addrMap)
      balance += scrAddr.second->getSpendableBalance(currBlk);
   
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getUnconfirmedBalance(uint32_t currBlk) const
{
   auto addrMap = scrAddrMap_.get();

   uint64_t balance = 0;
   for (const auto scrAddr : *addrMap)
      balance += scrAddr.second->getUnconfirmedBalance(currBlk);
   
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

   auto addrMap = scrAddrMap_.get();

   for (auto& scrAddr : *addrMap)
      balance += scrAddr.second->getFullBalance();

   return balance;
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, uint32_t> BtcWallet::getAddrTxnCounts(int32_t updateID) const
{
   map<BinaryData, uint32_t> countMap;

   auto addrMap = scrAddrMap_.get();
   for (auto& sa : *addrMap)
   {
      if (sa.second->updateID_ <= lastPulledCountsID_)
         continue;

      auto count = sa.second->getTxioCountForLedgers();
      if (count == 0 || count == UINT32_MAX)
         continue;

      countMap[sa.first] = count;
   }

   lastPulledCountsID_ = updateID;

   return countMap;
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, tuple<uint64_t, uint64_t, uint64_t>> 
   BtcWallet::getAddrBalances(int32_t updateID, unsigned blockHeight) const
{
   map<BinaryData, tuple<uint64_t, uint64_t, uint64_t>> balanceMap;

   auto addrMap = scrAddrMap_.get();
   for (auto& sa : *addrMap)
   {
      if (sa.second->updateID_ <= lastPulledBalancesID_)
         continue;

      auto full = sa.second->getFullBalance();
      auto spendable = sa.second->getSpendableBalance(blockHeight);
      auto unconf = sa.second->getUnconfirmedBalance(blockHeight);

      if (lastPulledBalancesID_ <= 0)
      {
         if (full == 0 && spendable == 0 && unconf == 0)
            continue;
      }

      balanceMap[sa.first] = move(make_tuple(full, spendable, unconf));
   }
   
   lastPulledBalancesID_ = updateID;

   return balanceMap;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::prepareTxOutHistory(uint64_t val)
{
   uint64_t value;
   uint32_t count;
      
   auto addrMap = scrAddrMap_.get();

   auto spentByZC = [this](const BinaryData& dbkey)->bool
   { return this->bdvPtr_->isTxOutSpentByZC(dbkey); };

   while (1)
   {
      value = 0;
      count = 0;


      for (const auto& scrAddr : *addrMap)
      {
         value += scrAddr.second->getLoadedTxOutsValue();
         count += scrAddr.second->getLoadedTxOutsCount();
      }

      //grab at least MIN_UTXO_PER_TXN and cover for twice the requested value
      if (value * 2 < val || count < MIN_UTXO_PER_TXN)
      {
         /***getMoreUTXOs returns true if it found more. As long as one
         ScrAddrObj has more, reassess the utxo state, otherwise get out of 
         the loop
         ***/

         bool hasMore = false;
         for (auto& scrAddr : *addrMap)
            hasMore |= scrAddr.second->getMoreUTXOs(spentByZC);

         if (!hasMore)
            break;
      }
      else 
         break;
   } 
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::prepareFullTxOutHistory(bool ignoreZC)
{
   auto spentByZC = [this](BinaryData dbkey)->bool
   { return this->bdvPtr_->isTxOutSpentByZC(dbkey); };

   auto addrMap = scrAddrMap_.get();

   while (1)
   {
      bool hasMore = false;
      for (auto& scrAddr : *addrMap)
         hasMore |= scrAddr.second->getMoreUTXOs(spentByZC);

      if (hasMore == false)
         return;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::resetTxOutHistory()
{
   auto addrMap = scrAddrMap_.get();

   for (auto& scrAddr : *addrMap)
      scrAddr.second->resetTxOutHistory();
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::resetCounters()
{
   lastPulledCountsID_ = -1;
   lastPulledBalancesID_ = -1;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getSpendableTxOutListForValue(uint64_t val)
{
   /***
   Only works with DB so it naturally ignores ZC 
   Use getSpendableTxOutListZC get unconfirmed outputs

   Only the TxIOPairs (DB keys) are saved in RAM. The full TxOuts are pulled only
   on demand since there is a high probability that at least a few of them will 
   be consumed.

   Grabs at least 100 UTXOs with enough spendable balance to cover 2x val (if 
   available of course), otherwise returns the full UTXO list for the wallet.

   val defaults to UINT64_MAX, so not passing val will result in 
   grabbing all UTXOs in the wallet
   ***/

   prepareTxOutHistory(val);
   LMDBBlockDatabase *db = bdvPtr_->getDB();

   //start a RO txn to grab the txouts from DB
   LMDBEnv::Transaction tx;
   db->beginDBTransaction(&tx, STXO, LMDB::ReadOnly);

   vector<UnspentTxOut> utxoList;
   uint32_t blk = bdvPtr_->getTopBlockHeight();

   auto addrMap = scrAddrMap_.get();

   for (const auto& scrAddr : *addrMap)
   {
      const auto& utxoMap = scrAddr.second->getPreparedTxOutList();

      for (const auto& txioPair : utxoMap)
      {
         if (!txioPair.second.isSpendable(db, blk))
            continue;

         TxOut txout = txioPair.second.getTxOutCopy(db);
         UnspentTxOut UTXO = UnspentTxOut(db, txout, blk);
         utxoList.push_back(UTXO);
      }
   }

   //Shipped a list of TxOuts, time to reset the entire TxOut history, since 
   //we dont know if any TxOut will be spent

   resetTxOutHistory();
   return move(utxoList);
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getSpendableTxOutListZC()
{
   set<BinaryData> txioKeys;

   {
      auto addrMap = scrAddrMap_.get();
      for (auto& scrAddr : *addrMap)
      {
         auto&& zcTxioMap = bdvPtr_->getUnspentZCForScrAddr(
            scrAddr.second->getScrAddr());

         for (auto& zcTxio : zcTxioMap)
            txioKeys.insert(zcTxio.first);
      }
   }

   auto&& txoutVec = bdvPtr_->getZcTxOutsForKeys(txioKeys);

   //convert TxOut to UnspentTxOut
   vector<UnspentTxOut> utxoVec;
   for (auto& txout : txoutVec)
   {
      UnspentTxOut utxo;
      utxo.txHash_ = txout.getParentHash();
      utxo.txHeight_ = txout.getParentHeight();

      utxo.txIndex_ = txout.getParentIndex();
      utxo.txOutIndex_ = txout.getIndex();

      utxo.value_ = txout.getValue();
      utxo.script_ = txout.getScript();
      utxo.txOutIndex_ = txout.getIndex();

      utxoVec.push_back(move(utxo));
   }

   return utxoVec;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getRBFTxOutList()
{
   set<BinaryData> zcKeys;
   set<BinaryData> txoutKeys;

   {
      auto addrMap = scrAddrMap_.get();
      for (auto& scrAddr : *addrMap)
      {
         auto&& zcTxioMap = bdvPtr_->getRBFTxIOsforScrAddr(
            scrAddr.second->getScrAddr());

         for (auto& zcTxio : zcTxioMap)
         {
            if (zcTxio.second.hasTxOutZC())
               zcKeys.insert(zcTxio.second.getDBKeyOfOutput());
            else
               txoutKeys.insert(zcTxio.second.getDBKeyOfOutput());
         }
      }
   }

   auto&& txoutVec = bdvPtr_->getZcTxOutsForKeys(zcKeys);
   BinaryDataRef prevTxKey;
   BinaryDataRef prevTxHash;
   for (auto& txoutkey : txoutKeys)
   {
      auto&& txout = bdvPtr_->getTxOutCopy(txoutkey);
      
      auto txkey = txoutkey.getSliceRef(0, 6);
      if (txkey == prevTxKey)
      {
         txout.setParentHash(prevTxHash);
      }
      else
      {
         auto&& txhash = bdvPtr_->getTxHashForDbKey(txkey);
         prevTxKey = txkey;
         if (txhash.getSize() == 0)
            throw runtime_error("failed to get hash for dbkey");
         txout.setParentHash(txhash);
      }

      txoutVec.push_back(move(txout));
      prevTxHash.setRef(txoutVec.back().getParentHash());
   }

   //convert TxOut to UnspentTxOut
   vector<UnspentTxOut> utxoVec;
   for (auto& txout : txoutVec)
   {
      UnspentTxOut utxo;
      utxo.txHash_ = txout.getParentHash();
      utxo.txHeight_ = txout.getParentHeight();

      utxo.txIndex_ = txout.getParentIndex();
      utxo.txOutIndex_ = txout.getIndex();

      utxo.value_ = txout.getValue();
      utxo.script_ = txout.getScript();
      utxo.txOutIndex_ = txout.getIndex();

      utxoVec.push_back(move(utxo));
   }

   return utxoVec;
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
// TODO: make this scalable!
//
vector<AddressBookEntry> BtcWallet::createAddressBook(void)
{
   // Collect all data into a map -- later converted to vector and sort it
   map<BinaryData, set<BinaryData>> sentToMap;
   map<BinaryData, BinaryData> keyToHash;

   auto scrAddrMap = scrAddrMap_.get();

   for (auto& saPair : *scrAddrMap)
   {
      auto& txioMap = saPair.second->relevantTxIO_;

      for (auto& txioPair : txioMap)
      {
         //skip unspent and zc spends
         if (!txioPair.second.hasTxIn() || txioPair.second.hasTxInZC())
            continue;

         //skip already processed tx
         auto&& dbKey = txioPair.second.getDBKeyOfInput();
         auto& txHash = keyToHash[dbKey];
         if (txHash.getSize() == 32)
            continue;

         //grab tx
         auto&& fullTx = bdvPtr_->getDB()->getFullTxCopy(dbKey.getSliceRef(0, 6));
         txHash = fullTx.getThisHash();

         auto nOut = fullTx.getNumTxOut();
         auto txPtr = fullTx.getPtr();

         for (unsigned i = 0; i < nOut; i++)
         {
            unsigned offset = fullTx.getTxOutOffset(i);
            unsigned outputSize = fullTx.getTxOutOffset(i + 1) - offset;
            BinaryDataRef outputRef(txPtr + offset + 8, outputSize);
            
            BinaryRefReader brr(outputRef);
            auto scriptSize = brr.get_var_int();

            auto&& scrRef = 
               BtcUtils::getTxOutScrAddrNoCopy(brr.get_BinaryDataRef(scriptSize));
            auto&& scrAddr = scrRef.getScrAddr();

            if (hasScrAddress(scrRef.getScrAddr()))
               continue;

            auto&& hashSet = sentToMap[scrAddr];
            hashSet.insert(txHash);
         }
      }
   }

   vector<AddressBookEntry> outputVect;
   for (const auto &entry : sentToMap)
   {
      AddressBookEntry abe(entry.first);
      for (auto& hash : entry.second)
         abe.addTxHash(move(hash));

      outputVect.push_back(move(abe));
   }

   sort(outputVect.begin(), outputVect.end());
   return outputVect;
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BtcWallet::getTxLedger(
   HashString const & scraddr)
   const
{
   vector<LedgerEntry> leVec;

   auto addrMap = scrAddrMap_.get();

   auto saIter = addrMap->find(scraddr);
   if (saIter != addrMap->end())
   {
      const auto& leMap = saIter->second->getTxLedger();
      for (const auto& lePair : leMap)
         leVec.push_back(lePair.second);
   }

   return leVec;
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BtcWallet::getTxLedger() const
{
   vector<LedgerEntry> leVec;

   for (const auto& lePair : *ledgerAllAddr_)
      leVec.push_back(lePair.second);

   return leVec;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateAfterReorg(uint32_t lastValidBlockHeight)
{
   auto addrMap = scrAddrMap_.get();

   for (auto& scrAddr : *addrMap)
   {
      scrAddr.second->updateAfterReorg(lastValidBlockHeight);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::scanWalletZeroConf(const ScanWalletStruct& scanInfo,
   int32_t updateID)
{
   /***
   Scanning ZC will update the scrAddr ledger with the ZC txio. Ledgers require
   a block height, which should be the current top block.
   ***/
   auto isZcFromWallet = [this](const BinaryDataRef zcKey)->bool
   {
      const auto& spentSAforZCKey = bdvPtr_->getSpentSAforZCKey(zcKey);

      for (const auto& spentSA : spentSAforZCKey)
      {
         if (this->hasScrAddress(spentSA))
            return true;
      }

      return false;
   };

   auto addrMap = scrAddrMap_.get();
   validZcKeys_.clear();

   for (auto& saPair : *addrMap)
   {
      saPair.second->scanZC(scanInfo.saStruct_, isZcFromWallet, updateID);
      for (auto& zckeypair : saPair.second->validZCKeys_)
      {
         validZcKeys_.insert(
            move(zckeypair.first.getSliceCopy(0, 6)));
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::scanWallet(ScanWalletStruct& scanInfo, int32_t updateID)
{
   if (scanInfo.action_ != BDV_ZC)
   {
      //new top block
      if (scanInfo.reorg_)
         updateAfterReorg(scanInfo.startBlock_);
         
      LMDBEnv::Transaction tx;
      bdvPtr_->getDB()->beginDBTransaction(&tx, SSH, LMDB::ReadOnly);

      auto addrMap = scrAddrMap_.get();
      for (auto& scrAddrPair : *addrMap)
         scrAddrPair.second->fetchDBScrAddrData(
            scanInfo.startBlock_, scanInfo.endBlock_, updateID);

      scanWalletZeroConf(scanInfo, updateID);

      map<BinaryData, TxIOPair> txioMap;
      getTxioForRange(scanInfo.startBlock_, UINT32_MAX, txioMap);
      updateWalletLedgersFromTxio(*ledgerAllAddr_, txioMap, 
         scanInfo.startBlock_, UINT32_MAX, true);

   
      balance_ = getFullBalanceFromDB();
   }
  
   if (scanInfo.saStruct_.zcMap_.size() > 0)
   {
      //top block didnt change, only have to check for new ZC
      if (bdvPtr_->isZcEnabled())
      {
         scanWalletZeroConf(scanInfo, updateID);
         map<BinaryData, TxIOPair> txioMap;
         getTxioForRange(scanInfo.endBlock_ + 1, UINT32_MAX, txioMap);
         
         BinaryData lastLedgerEntryKey;
         if (ledgerAllAddr_->size() > 0)
            lastLedgerEntryKey = ledgerAllAddr_->rbegin()->first;

         updateWalletLedgersFromTxio(*ledgerAllAddr_, txioMap, 
            scanInfo.endBlock_ + 1, UINT32_MAX, true);

         auto iter = ledgerAllAddr_->rbegin();
         while (iter != ledgerAllAddr_->rend())
         {
            if (iter->first > lastLedgerEntryKey)
            {
               scanInfo.saStruct_.zcLedgers_.insert(
                  make_pair(iter->first, iter->second));

               ++iter;
            }

            break;
         }

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
   clearBlkData();
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
map<uint32_t, uint32_t> BtcWallet::computeScrAddrMapHistSummary()
{
   struct preHistory
   {
      uint32_t txioCount_;
      vector<const BinaryData*> scrAddrs_;

      preHistory(void) : txioCount_(0) {}
   };

   map<uint32_t, preHistory> preHistSummary;

   auto addrMap = scrAddrMap_.get();

   LMDBEnv::Transaction sshtx;
   bdvPtr_->getDB()->beginDBTransaction(&sshtx, SSH, LMDB::ReadOnly);
   
   LMDBEnv::Transaction subtx;
   bdvPtr_->getDB()->beginDBTransaction(&subtx, SUBSSH, LMDB::ReadOnly);

   
   for (auto& scrAddrPair : *addrMap)
   {
      scrAddrPair.second->mapHistory();
      const map<uint32_t, uint32_t>& txioSum =
         scrAddrPair.second->getHistSSHsummary();

      //keep count of txios at each height with a vector of all related scrAddr
      for (const auto& histPair : txioSum)
      {
         auto& preHistAtHeight = preHistSummary[histPair.first];

         preHistAtHeight.txioCount_ += histPair.second;
         preHistAtHeight.scrAddrs_.push_back(&scrAddrPair.first);
      }
   }

   map<uint32_t, uint32_t> histSummary;
   for (auto& preHistAtHeight : preHistSummary)
   {
      if (preHistAtHeight.second.scrAddrs_.size() > 1)
      {
         //get hgtX for height
         uint8_t dupID = bdvPtr_->getDB()->getValidDupIDForHeight(preHistAtHeight.first);
         const BinaryData& hgtX = DBUtils::heightAndDupToHgtx(preHistAtHeight.first, dupID);

         set<BinaryData> txKeys;

         //this height has several txio for several scrAddr, let's look at the
         //txios in detail to reduce the total count for repeating txns.
         for (auto scrAddr : preHistAtHeight.second.scrAddrs_)
         {
            StoredSubHistory subssh;
            if (bdvPtr_->getDB()->getStoredSubHistoryAtHgtX(subssh, *scrAddr, hgtX))
            {
               for (auto& txioPair : subssh.txioMap_)
               {
                  if (txioPair.second.hasTxIn())
                     txKeys.insert(txioPair.second.getTxRefOfInput().getDBKey());
                  else
                     txKeys.insert(txioPair.second.getTxRefOfOutput().getDBKey());
               }
            }
         }

         preHistAtHeight.second.txioCount_ = txKeys.size();
      }
   
      histSummary[preHistAtHeight.first] = preHistAtHeight.second.txioCount_;
   }

   return histSummary;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::mapPages()
{
    /***mapPages seems rather fast (0.6~0.3sec to map the history of wallet
   with 1VayNert, 1Exodus and 100k empty addresses.

   My original plan was to grab the first 100 txn of a wallet to have the first
   page of its history ready for rendering, and parse the rest in a side 
   thread, as I was expecting that process to be long.

   Since my original assumption understimated LMDB's speed, I can instead map 
   the history entirely, then create the first page, as it results in a more 
   consistent txn distribution per page.

   Also taken in consideration is the code in updateLedgers. Ledgers are built
   by ScrAddrObj. The particular call, updateLedgers, expects to parse
   txioPairs in ascending order (lowest to highest height). 

   By gradually parsing history from the top block downward, updateLedgers is
   fed both ascending and descending sets of txioPairs, which would require
   certain in depth amendments to its code to satisfy a behavior that takes 
   place only once per wallet per load.
   ***/
   TIMER_START("mapPages");
   ledgerAllAddr_ = &LedgerEntry::EmptyLedgerMap_;

   auto computeSSHsummary = [this](void)->map<uint32_t, uint32_t>
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
   //double mapPagesTimer = TIMER_READ_SEC("mapPages");
   //LOGINFO << "mapPages done in " << mapPagesTimer << " secs";
}

////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::isPaged() const
{
   //get address map
   auto addrMap = scrAddrMap_.get();

   for (auto& saPair : *addrMap)
   {
      if (!saPair.second->hist_.isInitiliazed())
         return false;
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::getTxioForRange(uint32_t start, uint32_t end,
   map<BinaryData, TxIOPair>& outMap) const
{
   auto addrMap = scrAddrMap_.get();

   for (const auto& scrAddrPair : *addrMap)
      scrAddrPair.second->getHistoryForScrAddr(start, end, outMap, false);
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
const ScrAddrObj* BtcWallet::getScrAddrObjByKey(const BinaryData& key) const
{
   auto addrMap = scrAddrMap_.get();

   auto saIter = addrMap->find(key);
   if (saIter != addrMap->end())
   {
      return saIter->second.get();
   }
  
   throw std::runtime_error("invalid address");
}

////////////////////////////////////////////////////////////////////////////////
ScrAddrObj& BtcWallet::getScrAddrObjRef(const BinaryData& key)
{
   auto addrMap = scrAddrMap_.get();

   auto saIter = addrMap->find(key);
   if (saIter != addrMap->end())
   {
      return *saIter->second;
   }

   std::ostringstream ss;
   ss << "no ScrAddr matches key " << key.toBinStr() << 
      " in Wallet " << walletID_.toBinStr();
   LOGERR << ss.str();
   throw std::runtime_error(ss.str());
}

////////////////////////////////////////////////////////////////////////////////
const map<BinaryData, LedgerEntry>& BtcWallet::getHistoryPage(uint32_t pageId) 
{
   if (!bdvPtr_->isBDMRunning())
      return LedgerEntry::EmptyLedgerMap_;

   if (pageId >= getHistoryPageCount())
      throw std::range_error("pageID is out of range");

   auto getTxio = 
      [this](uint32_t start, uint32_t end, map<BinaryData, TxIOPair>& txioMap)->void
   { this->getTxioForRange(start, end, txioMap); };

   auto computeLedgers = [this](map<BinaryData, LedgerEntry>& leMap,
      const map<BinaryData, TxIOPair>& txioMap,
      uint32_t start)->void
   { this->updateWalletLedgersFromTxio(leMap, txioMap, start, UINT32_MAX, false); };

   return histPages_.getPageLedgerMap(getTxio, computeLedgers, pageId);
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BtcWallet::getHistoryPageAsVector(uint32_t pageId)
{
   try
   {
      auto& ledgerMap = getHistoryPage(pageId);
      
      vector<LedgerEntry> ledgerVec;

      for (const auto& ledgerPair : ledgerMap)
         ledgerVec.push_back(ledgerPair.second);

      return ledgerVec;
   }
   catch (std::range_error &e)
   {
      throw e;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::needsRefresh(bool refresh)
{ 
   //merge addresses in

   //notify BDV
   if (refresh && isRegistered_)
      bdvPtr_->flagRefresh(BDV_refreshAndRescan, walletID_);

   //call custom callback
   doneRegisteringCallback_();
   doneRegisteringCallback_ = [](void)->void{};
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getWltTotalTxnCount(void) const
{
   uint64_t ntxn = 0;

   auto addrMap = scrAddrMap_.get();

   for (const auto& scrAddrPair : *addrMap)
      ntxn += scrAddrPair.second->getTxioCountFromSSH();

   return ntxn;
}
