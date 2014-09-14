#include "ScrAddrObj.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(LMDBBlockDatabase *db, Blockchain *bc,
                       HashString    addr, 
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp,
                       uint32_t      lastBlockNum,
                       uint32_t      lastTimestamp) :
      db_(db),
      bc_(bc),
      scrAddr_(addr), 
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp),
      lastBlockNum_(lastBlockNum), 
      lastTimestamp_(lastTimestamp),
      utxos_(this)
{ 
   relevantTxIO_.clear();
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getSpendableBalance(
   uint32_t currBlk, bool ignoreAllZC
) const
{
   //ignoreing the currBlk for now, until the partial history loading is solid
   uint64_t balance = getFullBalance();

   for (auto txio : relevantTxIO_)
   {
      if (!txio.second.hasTxIn() &&
          !txio.second.isSpendable(db_, currBlk, ignoreAllZC))
         balance -= txio.second.getValue();
   }

   return balance;
}


////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getUnconfirmedBalance(
   uint32_t currBlk, bool inclAllZC
) const
{
   /***may need some help with the paging system in place***/

   uint64_t balance = 0;
   for (auto txio : relevantTxIO_)
   {
      if(txio.second.isMineButUnconfirmed(db_, currBlk, inclAllZC))
         balance += txio.second.getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getFullBalance() const
{
   StoredScriptHistory ssh;
   db_->getStoredScriptHistorySummary(ssh, scrAddr_);
   uint64_t balance = ssh.getScriptBalance(false);

   for (auto txio : relevantTxIO_)
   {
      if (txio.second.hasTxOutZC())
         balance += txio.second.getValue();
      if (txio.second.hasTxInZC())
         balance -= txio.second.getValue();
   }

   return balance;
}
   
////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addTxIO(TxIOPair& txio, bool isZeroConf)
{ 
   relevantTxIO_[txio.getDBKeyOfOutput()] = txio;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::pprintLedger() const 
{ 
   cout << "Address Ledger: " << getScrAddr().toHexStr() << endl;
   for(const auto ledger : *ledger_)
      ledger.second.pprintOneLine();
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearBlkData(void)
{
   relevantTxIO_.clear();
   hist_.reset();
   ledger_ = nullptr;
   totalTxioCount_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateTxIOMap(map<BinaryData, TxIOPair>& txio_map)
{
   for (auto txio : txio_map)
      relevantTxIO_[txio.first] = txio.second;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::scanZC(const map<HashString, TxIOPair>& zcTxIOMap)
{
   for (auto txioPair : zcTxIOMap)
      relevantTxIO_[txioPair.first] = txioPair.second;
   
   updateLedgers(*ledger_, zcTxIOMap, 0, UINT32_MAX, false);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::purgeZC(const vector<BinaryData>& invalidatedTxOutKeys)
{
   for (auto zc : invalidatedTxOutKeys)
   {
      auto txioIter = relevantTxIO_.find(zc);

      if (ITER_IN_MAP(txioIter, relevantTxIO_))
      {
         TxIOPair& txio = txioIter->second;

         if (txio.hasTxInZC())
         {
            //since the txio has a ZC txin, there is a scrAddr ledger entry for that key
            ledger_->erase(txio.getTxRefOfInput().getDBKey());
            
            txio.setTxIn(BinaryData(0));
            txio.setTxHashOfInput(BinaryData(0));
         }

         if (txio.hasTxOutZC())
         {
            //purged ZC chain, remove the TxIO
            relevantTxIO_.erase(txioIter);
            ledger_->erase(zc.getSliceRef(0, 6));
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateAfterReorg(uint32_t lastValidBlockHeight)
{
   auto txioIter = relevantTxIO_.begin();

   uint32_t height;
   while (txioIter != relevantTxIO_.end())
   {
      //txio pairs are saved by TxOut DBkey, if the key points to a block 
      //higher than the reorg point, delete the txio
      height = DBUtils::hgtxToHeight(txioIter->first.getSliceCopy(0, 4));

      if (height >= 0xFF000000)
      {
         //ZC chain, already dealt with by the call to purgeZC from 
         //readBlkFileUpdate
         continue;
      }
      else if (height <= lastValidBlockHeight)
      {
         TxIOPair& txio = txioIter->second;
         if (txio.hasTxIn())
         {
            //if the txio is spent, check the block of the txin
            height = DBUtils::hgtxToHeight(
               txio.getDBKeyOfInput().getSliceCopy(0, 4));

            if (height > lastValidBlockHeight && height < 0xFF000000)
            {
               //clear the TxIn by setting it to an empty BinaryData
               txio.setTxIn(BinaryData(0));
               txio.setTxHashOfInput(BinaryData(0));
            }
         }

         ++txioIter;
      }
      else
         relevantTxIO_.erase(txioIter++);
   }

   //clean up ledgers
   BinaryData cutOffHghtX = DBUtils::heightAndDupToHgtx(lastValidBlockHeight + 1, 0);
   uint16_t zero = 0;
   cutOffHghtX.append((uint8_t*)&zero, 2);

   auto leRange = ledger_->equal_range(cutOffHghtX);
   ledger_->erase(leRange.first, ledger_->end());
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateLedgers(map<BinaryData, LedgerEntry>& leMap,
                               const map<BinaryData, TxIOPair>& txioMap,
                               uint32_t startBlock, uint32_t endBlock,
                               bool purge) const
{
   LedgerEntry::computeLedgerMap(leMap, txioMap, startBlock, endBlock,
                                 scrAddr_, db_, bc_, purge);
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getTxioCountFromSSH(void) const
{
   StoredScriptHistory ssh;
   db_->getStoredScriptHistorySummary(ssh, scrAddr_);

   return ssh.totalTxioCount_;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::fetchDBScrAddrData(uint32_t startBlock,
                                    uint32_t endBlock)
{
   //maintains first page worth of TxIO in RAM. This call purges ZC, so you 
   //should rescan ZC right after

   map<BinaryData, TxIOPair> hist;
   getHistoryForScrAddr(startBlock, endBlock, hist, true);
   
   updateTxIOMap(hist);
   updateLedgers(*ledger_, hist, startBlock, endBlock, false);
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::getHistoryForScrAddr(
   uint32_t startBlock, uint32_t endBlock,
   map<BinaryData, TxIOPair>& outMap,
   bool update,
   bool withMultisig) const
{
   //check ScrAddrObj::relevantTxio_ first to see if it has some of the TxIOs
   uint32_t localTxioBottom = hist_.getPageBottom(0);
   if (update==false && endBlock > localTxioBottom)
   {
      if (startBlock <= localTxioBottom)
      {
         outMap.insert(relevantTxIO_.begin(), relevantTxIO_.end());
      }
      else
      {
         BinaryData startHeight = DBUtils::heightAndDupToHgtx(startBlock, 0);
         startHeight.append(WRITE_UINT16_BE(0));

         for (auto txioPair : relevantTxIO_)
         {
            if (txioPair.second >= startHeight)
               outMap.insert(txioPair);
         }
      }
         
      if (startBlock >= localTxioBottom)
         return;

      endBlock = localTxioBottom -1;
   }

   //grab txio range from SSH
   StoredScriptHistory ssh;
   db_->getStoredScriptHistory(ssh, scrAddr_, startBlock, endBlock);

   //update scrAddrObj containers
   totalTxioCount_ = ssh.totalTxioCount_;
   lastSeenBlock_ = endBlock;

   if (scrAddr_[0] == SCRIPT_PREFIX_MULTISIG)
      withMultisig = true;

   if (!ssh.isInitialized())
      return;

   //serve content as a map
   for (auto &subSSHEntry : ssh.subHistMap_)
   {
      StoredSubHistory & subssh = subSSHEntry.second;

      for (auto &txiop : subssh.txioMap_)
      {
         const TxIOPair & txio = txiop.second;
         if (withMultisig || !txio.isMultisig())
            outMap[txiop.first] = txio;
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> ScrAddrObj::getHistoryPageById(uint32_t id)
{
   if (id < 0)
   {
      return vector<LedgerEntry>();
   }

   auto getTxio = [this](uint32_t start, 
                         uint32_t end, 
                         map<BinaryData, TxIOPair>& outMap)->void
      { this->getHistoryForScrAddr(start, end, outMap, false); };

   auto buildLedgers = [this](map<BinaryData, LedgerEntry>& leMap,
                              const map<BinaryData, TxIOPair>& txioMap,
                              uint32_t cutoff)->void
      { this->updateLedgers(leMap, txioMap, cutoff, UINT32_MAX, false); };


   return getTxLedgerAsVector(hist_.getPageLedgerMap(getTxio, buildLedgers, id));
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::mapHistory()
{
   ledger_ = &LedgerEntry::EmptyLedgerMap_;

   //create history map
   auto getSummary = [this](void)->map<uint32_t, uint32_t>
      { return db_->getSSHSummary(this->getScrAddr(), UINT32_MAX); };

   hist_.mapHistory(getSummary); 

   //grab first page and point ScrAddrObj's ledger at it
   auto getTxio = [this](uint32_t start, 
                         uint32_t end, 
                         map<BinaryData, TxIOPair>& outMap)->void
      { this->getHistoryForScrAddr(start, end, outMap, true); };

   auto buildLedgers = [this](map<BinaryData, LedgerEntry>& leMap,
                              const map<BinaryData, TxIOPair>& txioMap,
                              uint32_t cutoff)->void
      { this->updateLedgers(leMap, txioMap, cutoff, UINT32_MAX, false); };

   ledger_ = &hist_.getPageLedgerMap(getTxio, buildLedgers, 0, &relevantTxIO_);
}

////////////////////////////////////////////////////////////////////////////////
ScrAddrObj& ScrAddrObj::operator= (const ScrAddrObj& rhs)
{
   if (&rhs == this)
      return *this;

   this->db_ = rhs.db_;
   this->bc_ = rhs.bc_;

   this->scrAddr_ = rhs.scrAddr_;
   this->firstBlockNum_ = rhs.firstBlockNum_;
   this->firstTimestamp_ = rhs.firstTimestamp_;
   this->lastBlockNum_ = rhs.lastBlockNum_;
   this->lastTimestamp_ = rhs.lastTimestamp_;

   this->hasMultisigEntries_ = rhs.hasMultisigEntries_;

   this->relevantTxIO_ = rhs.relevantTxIO_;

   this->totalTxioCount_ = rhs.totalTxioCount_;
   this->lastSeenBlock_ = rhs.lastSeenBlock_;

   //prebuild history indexes for quick fetch from SSH
   this->hist_ = rhs.hist_;
   
   this->ledger_ = &LedgerEntry::EmptyLedgerMap_;
   if (this->hist_.getPageCount() != 0)
      this->ledger_ = &this->hist_.getPageLedgerMap(0);

   return *this;
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> ScrAddrObj::getTxLedgerAsVector(
   map<BinaryData, LedgerEntry>& leMap) const
{
   vector<LedgerEntry>le;

   for (auto& lePair : leMap)
      le.push_back(lePair.second);

   return le;
}

