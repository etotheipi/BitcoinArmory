#include "BtcWallet.h"
#include "BlockUtils.h"

vector<LedgerEntry> BtcWallet::EmptyLedger_;


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
   if(bdmPtr_)
      bdmPtr_->unregisterWallet(this);
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
      bdmPtr_->getIFace(),
      &bdmPtr_->blockchain(),
      scrAddr,
      firstTimestamp, firstBlockNum,
      lastTimestamp,  lastBlockNum
   );
   
   if(bdmPtr_ != nullptr) 
      if (!bdmPtr_->registerScrAddr(addr, this))
         return;
   
   scrAddrMap_[scrAddr] = addr;

}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewScrAddress(BinaryData scrAddr)
{
   if (scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj addr = ScrAddrObj(bdmPtr_->getIFace(), &bdmPtr_->blockchain(),
      scrAddr, 0, 0, 0, 0);

   if(bdmPtr_ != nullptr)
      if (!bdmPtr_->registerScrAddr(addr, this))
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

   if (bdmPtr_ != nullptr)
      if (!bdmPtr_->registerScrAddr(newScrAddr, this))
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

/////////////////////////////////////////////////////////////////////////////
// Pass this wallet a TxRef and current time/blknumber.  I used to just pass
// in the BlockHeader with it, but this may be a Tx not in a block yet, 
// but I still need the time/num 
//
// You must clear the zero-conf pool for this address, before you do a 
// rescan of the wallet (it's done in rescanWalletZeroConf)
/*void BtcWallet::scanTx(Tx & tx, 
                       uint32_t txIndex,
                       uint32_t txtime,
                       uint32_t blknum)
{
   
   int64_t totalLedgerAmt = 0;
   bool isZeroConf = blknum==UINT32_MAX;

   vector<bool> thisTxOutIsOurs(tx.getNumTxOut(), false);

   const pair<bool,bool> boolPair = isMineBulkFilter(tx);
   const bool txIsRelevant  = boolPair.first;
   const bool anyTxInIsOurs = boolPair.second;

   if( !txIsRelevant )
      return;

   // We distinguish "any" from "anyNew" because we want to avoid re-adding
   // transactions/TxIOPairs that are already part of the our tx list/ledger
   // but we do need to determine if this was sent-to-self, regardless of 
   // whether it was new.
   bool anyNewTxInIsOurs   = false;
   bool anyNewTxOutIsOurs  = false;
   bool isCoinbaseTx       = false;

   map<BinaryData, ScrAddrObj>::iterator addrIter;
   ScrAddrObj         thisAddr;
   HashString         scraddr;

   bool savedAsTxIn = false;
   ///// LOOP OVER ALL TXIN IN TX /////
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      
      TxIn txin = tx.getTxInCopy(iin);
      OutPoint outpt = txin.getOutPoint();
      // Empty hash in Outpoint means it's a COINBASE tx --> no addr inputs
      if(outpt.getTxHashRef() == BtcUtils::EmptyHash())
      {
         isCoinbaseTx = true;
         continue;
      }

      // We have the txin, now check if it contains one of our TxOuts
      map<OutPoint, TxIOPair>::iterator txioIter = txioMap_.find(outpt);
      //bool txioWasInMapAlready = (txioIter != txioMap_.end());
      bool txioWasInMapAlready = ITER_IN_MAP(txioIter, txioMap_);
      if(txioWasInMapAlready)
      {
         // If we are here, we know that this input is spending an 
         // output owned by this wallet.
         // We will get here for every address in the search, even 
         // though it is only relevant to one of the addresses.
         TxIOPair & txio  = txioIter->second;
         TxOut txout = txio.getTxOutCopy(bdmPtr_->getIFace());

         // It's our TxIn, so address should be in this wallet
         scraddr  = txout.getScrAddressStr();
         addrIter = scrAddrMap_.find(scraddr);
         //if( addrIter == scrAddrMap_.end())
         if(ITER_NOT_IN_MAP(addrIter, scrAddrMap_))
         {
            // Have TxIO but address is not in the map...?
            LOGERR << "ERROR: TxIn in TxIO map, but addr not in wallet...?";
            continue;
         }
         
         thisAddr = addrIter->second;

         // We need to make sure the ledger entry makes sense, and make
         // sure we update TxIO objects appropriately
         int64_t thisVal = (int64_t)txout.getValue();
         totalLedgerAmt -= thisVal;

         // Skip, if zero-conf-spend, but it's already got a zero-conf
         if( isZeroConf && txio.hasTxInZC() )
            return; // this tx can't be valid, might as well bail now

         if( !txio.hasTxInInMain(bdmPtr_->getIFace()) && !(isZeroConf && txio.hasTxInZC())  )
         {
            // isValidNew only identifies whether this set-call succeeded
            // If it didn't, it's because this is from a zero-conf tx but this 
            // TxIn already exists in the blockchain spending the same output.
            // (i.e. we have a ref to the prev output, but it's been spent!)
            bool isValidNew;
            if(isZeroConf)
               isValidNew = txio.setTxInZC(bdmPtr_->getIFace(), &tx, iin);
            else
               isValidNew = txio.setTxIn(tx.getTxRef(), iin);

            if(!isValidNew)
               continue;

            anyNewTxInIsOurs = true;

            LedgerEntry newEntry(scraddr, 
                                -(int64_t)thisVal,
                                 blknum, 
                                 tx.getThisHash(), 
                                 iin,
                                 txtime,
                                 isCoinbaseTx,
                                 false,  // SentToSelf is meaningless for addr ledger
                                 false); // "isChangeBack" is meaningless for TxIn
            thisAddr.addLedgerEntry(newEntry, isZeroConf);

            txLedgerForComments_.push_back(newEntry);
            savedAsTxIn = true;

            // Update last seen on the network
            thisAddr.setLastTimestamp(txtime);
            thisAddr.setLastBlockNum(blknum);

            addrIter.update(thisAddr);
         }
      }
      else
      {
         // Lots of txins that we won't have, this is a normal conditional
         // But we should check the non-std txio list since it may actually
         // be there
         //if(nonStdTxioMap_.find(outpt) != nonStdTxioMap_.end())
         if(KEY_IN_MAP(outpt, nonStdTxioMap_))
         {
            if(isZeroConf)
               nonStdTxioMap_[outpt].setTxInZC(bdmPtr_->getIFace(), &tx, iin);
            else
               nonStdTxioMap_[outpt].setTxIn(tx.getTxRef(), iin);
            nonStdUnspentOutPoints_.erase(outpt);
         }
      }
   } // loop over TxIns

   ///// LOOP OVER ALL TXOUT IN TX /////
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      TxOut txout = tx.getTxOutCopy(iout);
      if( txout.getScriptType() == TXOUT_SCRIPT_NONSTANDARD )
      {
         continue;
      }

      scraddr   = txout.getScrAddressStr();
      addrIter = saSnapshot.find(scraddr);
      if(ITER_IN_MAP(addrIter, saSnapshot))
      {
         thisAddr = addrIter->second;
         // If we got here, at least this TxOut is for this address.
         // But we still need to find out if it's new and update
         // ledgers/TXIOs appropriately
         int64_t thisVal = (int64_t)(txout.getValue());
         totalLedgerAmt += thisVal;

         OutPoint outpt(tx.getThisHash(), iout);      
         map<OutPoint, TxIOPair>::iterator txioIter = txioMap_.find(outpt);
         bool txioWasInMapAlready = ITER_IN_MAP(txioIter, txioMap_);
         bool doAddLedgerEntry = false;
         if(txioWasInMapAlready)
         {
            if(isZeroConf) 
            {
               // This is a real txOut, in the blockchain
               if(
                  txioIter->second.hasTxOutZC()
                     || txioIter->second.hasTxOutInMain(bdmPtr_->getIFace())
               )
                  continue; 

               // If we got here, somehow the Txio existed already, but 
               // there was no existing TxOut referenced by it.  Probably,
               // there was, but that TxOut was invalidated due to reorg
               // and now being re-added
               txioIter->second.setTxOutZC(bdmPtr_->getIFace(), &tx, iout);
               txioIter->second.setValue((uint64_t)thisVal);
               thisAddr.addTxIO(txioIter->second, isZeroConf);
               doAddLedgerEntry = true;
            }
            else
            {
               if(txioIter->second.hasTxOutInMain(bdmPtr_->getIFace())) // ...but we already have one
                  continue;

               // If we got here, we have an in-blockchain TxOut that is 
               // replacing a zero-conf txOut.  Reset the txio to have 
               // only this real TxOut, blank out the ZC TxOut.  And the addr 
               // relevantTxIOPtrs_ does not have this yet so it needs 
               // to be added (it's already part of the relevantTxIOPtrsZC_
               // but that will be removed)
               txioIter->second.setTxOut(tx.getTxRef(), iout);
               txioIter->second.setValue((uint64_t)thisVal);
               thisAddr.addTxIO(txioIter->second, isZeroConf);
               doAddLedgerEntry = true;
            }
         }
         else
         {
            // TxIO is not in the map yet -- create and add it
            TxIOPair newTxio(thisVal);
            if(isZeroConf)
               newTxio.setTxOutZC(bdmPtr_->getIFace(), &tx, iout);
            else
               newTxio.setTxOut(tx.getTxRef(), iout);

            txioIter = txioMap_.insert(make_pair(outpt, newTxio)).first;
            thisAddr.addTxIO(txioIter->second, isZeroConf);
            doAddLedgerEntry = true;
         }

         if(anyTxInIsOurs)
            txioIter->second.setTxOutFromSelf(true);
        
         if(isCoinbaseTx)
            txioIter->second.setFromCoinbase(true);

         anyNewTxOutIsOurs = true;
         thisTxOutIsOurs[iout] = true;

         if(doAddLedgerEntry)
         {
            LedgerEntry newLedger(scraddr, 
                                  thisVal, 
                                  blknum, 
                                  tx.getThisHash(), 
                                  iout,
                                  txtime,
                                  isCoinbaseTx, // input was coinbase/generation
                                  false,   // sentToSelf meaningless for addr ledger
                                  false);  // we don't actually know
            thisAddr.addLedgerEntry(newLedger, isZeroConf);

            if(!savedAsTxIn) txLedgerForComments_.push_back(newLedger);
         }
         // Check if this is the first time we've seen this
         if(thisAddr.getFirstTimestamp() == 0)
         {
            thisAddr.setFirstBlockNum( blknum );
            thisAddr.setFirstTimestamp( txtime );
         }
         // Update last seen on the network
         thisAddr.setLastTimestamp(txtime);
         thisAddr.setLastBlockNum(blknum);
      }
   } // loop over TxOuts


   bool allTxOutIsOurs = true;
   bool anyTxOutIsOurs = false;
   for(uint32_t i=0; i<tx.getNumTxOut(); i++)
   {
      if( thisTxOutIsOurs[i] )
         anyTxOutIsOurs = true;
      else
         allTxOutIsOurs = false;
   }

   bool isSentToSelf = (anyTxInIsOurs && allTxOutIsOurs);
   bool isChangeBack = (anyTxInIsOurs && anyTxOutIsOurs && !isSentToSelf);

   if(anyNewTxInIsOurs || anyNewTxOutIsOurs)
   {
      LedgerEntry le( BinaryData(0),
                      totalLedgerAmt, 
                      blknum, 
                      tx.getThisHash(), 
                      txIndex,
                      txtime,
                      isCoinbaseTx,
                      isSentToSelf,
                      isChangeBack);

      if(isZeroConf)
         ledgerAllAddrZC_.push_back(le);
      else
         ledgerAllAddr_.push_back(le);
   }
}*/


////////////////////////////////////////////////////////////////////////////////
// Soft calculation:  does not affect the wallet at all
//
// I really need a method to scan an arbitrary tx, regardless of whether it
// is new, and return the LedgerEntry it would've created as if it were new.  
// This is mostly a rewrite of the isMineBulkFilter, and kind of replicates
// the behavior of ScanTx.  But scanTx has been exhaustively tested with all
// the crazy input variations and conditional paths, I don't want to touch 
// it to try to accommodate this use case.
/*LedgerEntry BtcWallet::calcLedgerEntryForTx(Tx & tx)
{
   int64_t totalValue = 0;
   uint8_t const * txStartPtr = tx.getPtr();
   bool anyTxInIsOurs = false;
   bool allTxOutIsOurs = true;
   bool isCoinbaseTx = false;
   OutPoint op; // reused
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      op.unserialize(txStartPtr + tx.getTxInOffset(iin), 
                     tx.getSize()-tx.getTxInOffset(iin));

      if(op.getTxHashRef() == BtcUtils::EmptyHash())
         isCoinbaseTx = true;

      //if(txioMap_.find(op) != txioMap_.end())
      if(KEY_IN_MAP(op, txioMap_))
      {
         anyTxInIsOurs = true;
         totalValue -= txioMap_[op].getValue();
      }
   }


   // This became much simpler once we implemented arbirtrary scrAddrs
   for (uint32_t iout = 0; iout<tx.getNumTxOut(); iout++)
   {
      uint32_t valOffset = tx.getTxOutOffset(iout);
      if (hasScrAddress(tx.getTxOutCopy(iout).getScrAddressStr()))
         totalValue += READ_UINT64_LE(txStartPtr + valOffset);
      else
         allTxOutIsOurs = false;
   }


   bool isSentToSelf = (anyTxInIsOurs && allTxOutIsOurs);

   if (!anyTxInIsOurs && totalValue == 0)
      return LedgerEntry();

   return LedgerEntry(BinaryData(0),
      totalValue,
      0,
      tx.getThisHash(),
      0,
      0,
      isCoinbaseTx,
      isSentToSelf,
      false);
}

////////////////////////////////////////////////////////////////////////////////
LedgerEntry BtcWallet::calcLedgerEntryForTx(TxRef & txref)
{
   Tx theTx = txref.attached(bdmPtr_->getIFace()).getTxCopy();
   return calcLedgerEntryForTx(theTx);
}

////////////////////////////////////////////////////////////////////////////////
LedgerEntry BtcWallet::calcLedgerEntryForTxStr(BinaryData txStr)
{
   Tx tx(txStr);
   return calcLedgerEntryForTx(tx);
}*/


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

         Tx thisTx = txio.getTxRefOfInput().attached(bdmPtr_->getIFace()).getTxCopy();
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

   const Blockchain* bc = &bdmPtr_->blockchain();

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
      bdmPtr_->getNewZeroConfTxIOMap();

   if (withReorg==true)
   {
      //scanning ZC after a reorg, Everything beyond the last valid block has
      //been wiped out of RAM, thus grab the full ZC txio map. Still need a call
      //to getNewZeroConfTxIOMap to clear the new ZC map
      ZCtxioMap = bdmPtr_->getFullZeroConfTxIOMap();
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
void BtcWallet::scanWallet(uint32_t startBlock, uint32_t endBlock, 
                           bool forceScan)
{
   merge();

   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = bdmPtr_->getTopBlockHeight() + 1;

   if (isInitialized_ == false)
   {
      calculateTxioDensity();
      int32_t step = uint32_t((float)txnPerPage_ / txioDensity_) + 1;

      int32_t top = bdmPtr_->getTopBlockHeight() + 1;
      int32_t bottom = bdmPtr_->getTopBlockHeight() + 1;

      LOGINFO << "fetching history. step: " << step << " txioDensity: " << txioDensity_;
      do
      {
         bottom -= step;
         if (bottom < 0)
            bottom = 0;

         fetchWalletHistoryRange(ledgerAllAddr_, bottom, top);
         top -= step;

         LOGINFO << "ledge size " << ledgerAllAddr_.size();
      } while (ledgerAllAddr_.size() < txnPerPage_ && bottom > 0);

      LOGINFO << "bottom: " << bottom;
      histBottomHeight_ = bottom;

      if (bottom != 0)
         mapPages();

      LOGINFO << "updating ZC";
      scanWalletZeroConf();

      lastScanned_ = endBlock;
      isInitialized_ = true;
   }
   else if (startBlock < endBlock)
   {
      //new top block
      bool withReorg = false;

      if (lastScanned_ > startBlock)
      {
         //reorg
         updateAfterReorg(startBlock);
         withReorg = true;
      }
         
      fetchDBScrAddrData(startBlock, endBlock);
      scanWalletZeroConf();

      updateWalletLedgers(ledgerAllAddr_, scrAddrMap_, 
                          startBlock, UINT32_MAX -1);

      lastScanned_ = endBlock;
   }
   else
   {
      //top block didnt change, only have to check for new ZC
      if (bdmPtr_->isZcEnabled())
      {
         scanWalletZeroConf();
         updateWalletLedgers(ledgerAllAddr_, scrAddrMap_, 
                             startBlock, endBlock, false);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::reset()
{
   merge();

   clearBlkData();
   isInitialized_ = false;
   histBottomHeight_ = 0;
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
void BtcWallet::updateWalletLedgers(
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

      /*** NOTE: Need a wallet to define STS and ChangeBack (as opposed
      to a single scrAddr). STS is signifiant at both address and wallet
      level, but ChangeBack is only relevant at address level.
      ***/
      if (valIn + valOut == 0)
      {
         ledgerVal = valIn;
         isSendToSelf = true;
      }
      else if (nHits != 0 && (valIn + valOut) < 0)
         isChangeBack = true;

      LedgerEntry le(BinaryData(0),
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
   ScrAddrObj newScrAddrObj(bdmPtr_->getIFace(), 
                            &bdmPtr_->blockchain(), 
                            scrAddr);

   //fetch scrAddrData
   newScrAddrObj.fetchDBScrAddrData(0, bdmPtr_->getTopBlockHeight());

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
      
      //rescan last 100 blocks to account for new blocks and reorgs
      uint32_t topBlock = bdmPtr_->blockchain().top().getBlockHeight() + 1;
      for (auto& scrAddrPair : scrAddrMapToMerge_)
         scrAddrPair.second.fetchDBScrAddrData(topBlock - 100, topBlock);
      

      /***NOTE: should ledgers just be wiped and fully rebuilt? If the new 
      addresses are used in shared transactions, the ledgers will be invalid
      ***/

      //update wallet ledger, pass false to not reset the other ledger entries
      updateWalletLedgers(ledgerAllAddr_, scrAddrMapToMerge_, 0, 
                          bdmPtr_->blockchain().top().getBlockHeight() + 1,
                          false);
      
      //merge scrAddrMap
      scrAddrMap_.insert(scrAddrMapToMerge_.begin(), scrAddrMapToMerge_.end());

      //clear merge map
      scrAddrMapToMerge_.clear();

      //clear flag
      mergeFlag_ = false;

      //release lock
      mergeLock_.store(0, memory_order_release);

   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::calculateTxioDensity()
{
   /***
   Evaluates how many blocks of history are needed starting from endBlock to
   display approximately histLength transactions
   ***/

   //we start from the assumption that there isn't enough history in this wallet
   //to fulfill histLength of history, so we're starting at bottom = 0, to cover 
   //the entire wallet history
   uint64_t totalTxio = 0;

   LMDBBlockDatabase* db = bdmPtr_->getIFace();

   //parse all SSH summaries
   for (auto& scrAddrPair : scrAddrMap_)
   {
      StoredScriptHistory ssh;
      db->getStoredScriptHistorySummary(ssh, scrAddrPair.first);

      scrAddrPair.second.setTxioCount(ssh.totalTxioCount_);

      totalTxio += ssh.totalTxioCount_;
   }

   txioDensity_ = float(totalTxio * 2) / 
                  float(bdmPtr_->blockchain().top().getBlockHeight());
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::fetchWalletHistoryRange(vector<LedgerEntry>& le, 
                                            uint32_t startBlock,
                                            uint32_t endBlock)
{
   /***grab txios for all addresses from startBlock to endBlock, build the ledger
   entries in le
   ***/
   
   fetchDBScrAddrData(startBlock, endBlock);
   updateWalletLedgers(le, scrAddrMap_, startBlock, endBlock, false);
}

////////////////////////////////////////////////////////////////////////////////
void* mapPagesThread(void *in)
{
   BtcWallet *wlt = static_cast<BtcWallet*>(in);

   uint32_t wltFirstHistoryBlock = wlt->getHistBottomHeight(); 
   uint32_t txnPerPage = wlt->getTxnPerPage();
   
   //grab merge lock, make a copy of the addrMap then release
   wlt->grabMergeLock();
   map<BinaryData, ScrAddrObj*> addrMap;
   for (auto& addrPair : wlt->getScrAddrMap())
      addrMap[addrPair.first] = &addrPair.second;

   wlt->releaseMergeLock();

   LMDBBlockDatabase* db = wlt->getBdmPtr()->getIFace();
   map<uint32_t, uint32_t> histSummary;

   for (auto scrAddrPair : addrMap)
   {
      scrAddrPair.second->mapHistory();
      const map<uint32_t, uint32_t>& txioSum = 
         scrAddrPair.second->getHistSSHsummary();

      for (const auto& histPair : txioSum)
      {
         if (histPair.first >= wltFirstHistoryBlock)
            break;
         histSummary[histPair.first] += histPair.second;
      }
   }

   HistoryPages &pages = wlt->getHistoryPages();
   pages.reset();

   auto histIter = histSummary.cbegin();
   uint32_t threshold = 0;
   uint32_t top;
   
   while (histIter != histSummary.cend())
   {
      if (threshold == 0)
         top = histIter->first;

      threshold += histIter->second;
      if (threshold > txnPerPage)
      {
         pages.addPage(threshold, histIter->first, top);

         threshold = 0;
      }
      
      ++histIter;
   }

   if (threshold != 0)
      pages.addPage(threshold, 0, top);

   pages.sortPages();

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::mapPages()
{
   pthread_t tid;
   pthread_create(&tid, nullptr, mapPagesThread, static_cast<void*>(this));
   //pthread_join(tid, nullptr);
}



// kate: indent-width 3; replace-tabs on;
