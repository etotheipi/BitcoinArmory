#include "BtcWallet.h"
#include "BlockUtils.h"

vector<LedgerEntry> BtcWallet::EmptyLedger_(0);


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
   ts_saMap::const_snapshot saSS(scrAddrMap_);
   if (saSS.find(scrAddr) != saSS.end())
      return;

   ScrAddrObj addrPtr(
      bdmPtr_->getIFace(),
      scrAddr,
      firstTimestamp, firstBlockNum,
      lastTimestamp,  lastBlockNum
   );
   scrAddrMap_[scrAddr] = addrPtr;

   registerImportedScrAddr(scrAddr, firstBlockNum);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewScrAddress(BinaryData scrAddr)
{
   ts_saMap::const_snapshot saSS(scrAddrMap_);
   if (saSS.find(scrAddr) != saSS.end())
      return;

   ScrAddrObj addrPtr = ScrAddrObj(bdmPtr_->getIFace(), scrAddr, 0, 0, 0, 0);
   scrAddrMap_[scrAddr] = addrPtr;

   if(bdmPtr_)
      registerNewScrAddr(scrAddr);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addScrAddress(ScrAddrObj const & newScrAddr)
{
   ts_saMap::const_snapshot saSS(scrAddrMap_);
   if (saSS.find(newScrAddr.getScrAddr()) != saSS.end())
      return;

   if(newScrAddr.getScrAddr().getSize() > 0)
      scrAddrMap_[newScrAddr.getScrAddr()] = newScrAddr;

   registerImportedScrAddr(newScrAddr.getScrAddr(), 
                                       newScrAddr.getFirstBlockNum());
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
   ts_saMap::const_snapshot saSS(scrAddrMap_);
   return (saSS.find(scrAddr) != saSS.end());
}


/////////////////////////////////////////////////////////////////////////////
pair<bool,bool> BtcWallet::isMineBulkFilter(
   Tx & tx, 
   bool withSecondOrderMultisig
) const
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
}


/////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintAlot(InterfaceToLDB *db, uint32_t topBlk, bool withAddr) const
{
   uint32_t numLedg = ledgerAllAddr_.size();
   uint32_t numLedgZC = ledgerAllAddrZC_.size();

   cout << "Wallet PPRINT:" << endl;
   cout << "Tot: " << getFullBalance() << endl;
   cout << "Spd: " << getSpendableBalance(topBlk) << endl;
   cout << "Ucn: " << getUnconfirmedBalance(topBlk) << endl;

   cout << "Ledger: " << endl;
   for(uint32_t i=0; i<numLedg; i++)
      ledgerAllAddr_[i].pprintOneLine();

   cout << "LedgerZC: " << endl;
   for(uint32_t i=0; i<numLedgZC; i++)
      ledgerAllAddrZC_[i].pprintOneLine();

   cout << "TxioMap:" << endl;
   for( const auto &txio : txioMap_)
   {
      txio.second.pprintOneLine(db);
   }

   if(withAddr)
   {
      ts_saMap::const_snapshot saSnapshot(scrAddrMap_);

      for(const auto &sa : saSnapshot)
      {
         const ScrAddrObj & addr = sa.second;
         HashString scraddr = addr.getScrAddr();
         cout << "\nAddress: " << scraddr.toHexStr().c_str() << endl;
         cout << "   Tot: " << addr.getFullBalance() << endl;
         cout << "   Spd: " << addr.getSpendableBalance(topBlk) << endl;
         cout << "   Ucn: " << addr.getUnconfirmedBalance(topBlk) << endl;
                  
         cout << "   Ledger: " << endl;
         for(uint32_t i=0; i<addr.ledger_.size(); i++)
            addr.ledger_[i].pprintOneLine();
      
         cout << "   LedgerZC: " << endl;
         for(uint32_t i=0; i<addr.ledgerZC_.size(); i++)
            addr.ledgerZC_[i].pprintOneLine();
      
         cout << "   TxioPtrs (Blockchain):" << endl;
         map<OutPoint, TxIOPair>::iterator iter;
         for(uint32_t t=0; t<addr.relevantTxIOPtrs_.size(); t++)
         {
            addr.relevantTxIOPtrs_[t]->pprintOneLine(db);
         }

         cout << "   TxioPtrs (Zero-conf):" << endl;
         for(uint32_t t=0; t<addr.relevantTxIOPtrsZC_.size(); t++)
         {
            addr.relevantTxIOPtrsZC_[t]->pprintOneLine(db);
         }
      }
   }
}

void BtcWallet::pprintAlittle(std::ostream &os) const
{
   os << "\tBalance: " << getFullBalance();
   os << "\tNAddr:   " << getNumScrAddr();
   os << "\tNTxio:   " << txioMap_.size();
   os << "\tNLedg:   " << getTxLedger().size();
   os << "\tNZC:     " << getZeroConfLedger().size() << endl;      

}

/////////////////////////////////////////////////////////////////////////////
// Pass this wallet a TxRef and current time/blknumber.  I used to just pass
// in the BlockHeader with it, but this may be a Tx not in a block yet, 
// but I still need the time/num 
//
// You must clear the zero-conf pool for this address, before you do a 
// rescan of the wallet (it's done in rescanWalletZeroConf)
void BtcWallet::scanTx(Tx & tx, 
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

   ts_saMap::snapshot saSnapshot(scrAddrMap_);
   ts_saMap::iterator addrIter;
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
         addrIter = saSnapshot.find(scraddr);
         //if( addrIter == scrAddrMap_.end())
         if(addrIter == saSnapshot.end())
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
               thisAddr.addTxIO( &txioIter->second, isZeroConf);
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
               thisAddr.addTxIO( &txioIter->second, isZeroConf);
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
            thisAddr.addTxIO( &txioIter->second, isZeroConf);
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

         addrIter.update(thisAddr);
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
}


////////////////////////////////////////////////////////////////////////////////
// Soft calculation:  does not affect the wallet at all
//
// I really need a method to scan an arbitrary tx, regardless of whether it
// is new, and return the LedgerEntry it would've created as if it were new.  
// This is mostly a rewrite of the isMineBulkFilter, and kind of replicates
// the behavior of ScanTx.  But scanTx has been exhaustively tested with all
// the crazy input variations and conditional paths, I don't want to touch 
// it to try to accommodate this use case.
LedgerEntry BtcWallet::calcLedgerEntryForTx(Tx & tx)
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
      op.unserialize(txStartPtr + tx.getTxInOffset(iin), tx.getSize()-tx.getTxInOffset(iin));

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
}


////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearBlkData(void)
{
   txioMap_.clear();
   ledgerAllAddr_.clear();
   ledgerAllAddrZC_.clear();
   nonStdTxioMap_.clear();
   nonStdUnspentOutPoints_.clear();

   ts_saMap::snapshot saSnapshot(scrAddrMap_);
   ts_saMap::iterator saIter;

   for (saIter = saSnapshot.begin();
      saIter != saSnapshot.end(); ++saIter)
   {
      ScrAddrObj sa = (*saIter).second;
      sa.clearBlkData();
      saIter.update(sa);
   }
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
      nonStdUnspentOutPoints_.insert(outpt);
      nonStdTxioMap_.insert(
         make_pair(outpt, TxIOPair(tx.getTxRef(),txoutidx))
      );
   }

}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getSpendableBalance(\
                    uint32_t currBlk, bool ignoreAllZC) const
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::const_iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isSpendable(bdmPtr_->getIFace(), currBlk, ignoreAllZC))
         balance += iter->second.getValue();      
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getUnconfirmedBalance(
                    uint32_t currBlk, bool inclAllZC) const
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::const_iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isMineButUnconfirmed(bdmPtr_->getIFace(), currBlk, inclAllZC))
         balance += iter->second.getValue();      
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getFullBalance() const
{
   if (bdmPtr_->config().armoryDbType == ARMORY_DB_SUPER)
   {
      uint64_t balance = 0;
      ts_saMap::const_snapshot saSnapshot(scrAddrMap_);

      for(const auto &sa : saSnapshot)
      {
         const ScrAddrObj & addr = sa.second;
         for(const TxIOPair &txio : getHistoryForScrAddr(addr.getScrAddr()))
         {
            if (txio.isUnspent(bdmPtr_->getIFace()))
            {
               balance += txio.getValue();
            }
         }
      }
      return balance;
   }
   else
   {
      uint64_t balance = 0;
      for(const auto &tio : txioMap_)
      {
         if(tio.second.isUnspent(bdmPtr_->getIFace()))
            balance += tio.second.getValue();      
      }
      return balance;

   }
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getSpendableTxOutList(
   uint32_t blkNum, 
   bool ignoreAllZC
) const
{
   vector<UnspentTxOut> utxoList;
   for(const auto &tio : txioMap_)
   {
      const TxIOPair & txio = tio.second;
      if(txio.isSpendable(bdmPtr_->getIFace(), blkNum, ignoreAllZC))
      {
         TxOut txout = txio.getTxOutCopy(bdmPtr_->getIFace());
         utxoList.push_back(UnspentTxOut(bdmPtr_->getIFace(), txout, blkNum) );
      }
   }
   return utxoList;
}


////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getFullTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList;
   for(const auto &tio : txioMap_)
   {
      const TxIOPair & txio = tio.second;
      if(txio.isUnspent(bdmPtr_->getIFace()))
      {
         TxOut txout = txio.getTxOutCopy(bdmPtr_->getIFace());
         utxoList.push_back(UnspentTxOut(bdmPtr_->getIFace(), txout, blkNum) );
      }
   }
   return utxoList;
}



////////////////////////////////////////////////////////////////////////////////
uint32_t BtcWallet::removeInvalidEntries(void)   
{
   vector<LedgerEntry> newLedger(0);
   uint32_t leRemoved = 0;
   for(uint32_t i=0; i<ledgerAllAddr_.size(); i++)
   {
      if(!ledgerAllAddr_[i].isValid())
         leRemoved++;
      else
         newLedger.push_back(ledgerAllAddr_[i]);
   }
   ledgerAllAddr_.clear();
   ledgerAllAddr_ = newLedger;
   return leRemoved;

}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::sortLedger()
{
   sort(ledgerAllAddr_.begin(), ledgerAllAddr_.end());
}



////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::isOutPointMine(HashString const & hsh, uint32_t idx)
{
   OutPoint op(hsh, idx);
   //return (txioMap_.find(op)!=txioMap_.end());
   return KEY_IN_MAP(op, txioMap_);
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintLedger() const
{ 
   cout << "Wallet Ledger:  " << getFullBalance()/1e8 << endl;
   for(uint32_t i=0; i<ledgerAllAddr_.size(); i++)
      ledgerAllAddr_[i].pprintOneLine();
   for(uint32_t i=0; i<ledgerAllAddrZC_.size(); i++)
      ledgerAllAddrZC_[i].pprintOneLine();
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
   for(const auto &tio : txioMap_)
   {
      const TxIOPair & txio = tio.second;

      // It's only outgoing if it has a TxIn
      if( !txio.hasTxIn() )
         continue;

      Tx thisTx = txio.getTxRefOfInput().attached(bdmPtr_->getIFace()).getTxCopy();
      HashString txHash = thisTx.getThisHash();

      if(allTxList.count(txHash) > 0)
         continue;
      else
         allTxList.insert(txHash);


      // Iterate over all TxOut in this Tx for recipients
      perTxAddrSet.clear();
      for(uint32_t iout=0; iout<thisTx.getNumTxOut(); iout++)
      {
         HashString scraddr = thisTx.getTxOutCopy(iout).getScrAddressStr();

         // Skip this address if it's in our wallet (usually change addr)
         if( hasScrAddress(scraddr) || perTxAddrSet.count(scraddr)>0)
            continue; 

         // It's someone else's address for sure, add it to the map if necessary
         if(sentToMap.count(scraddr)==0)
            sentToMap[scraddr] = AddressBookEntry(scraddr);

         sentToMap[scraddr].addTx(thisTx);
         perTxAddrSet.insert(scraddr);
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
void BtcWallet::clearZeroConfPool(void)
{
   SCOPED_TIMER("clearZeroConfPool");
   ledgerAllAddrZC_.clear();

   ts_saMap::snapshot saSnapshot(scrAddrMap_);
   ts_saMap::iterator saIter;

   for (saIter = saSnapshot.begin();
      saIter != saSnapshot.end(); ++saIter)
   {
      ScrAddrObj sa = (*saIter).second;
      sa.clearZeroConfPool();
      saIter.update(sa);
   }


   // Need to "unlock" the TxIOPairs that were locked with zero-conf txs
   vector< map<OutPoint, TxIOPair>::iterator > rmList;
   
   for(map<OutPoint, TxIOPair>::iterator iter = txioMap_.begin();
       iter != txioMap_.end();
       ++iter)
   {
      iter->second.clearZCFields();
      if(!iter->second.hasTxOut())
         rmList.push_back(iter);
   }

   // If a TxIOPair exists only because of the TxOutZC, then we should 
   // remove to ensure that it won't conflict with any logic that only 
   // checks for the *existence* of a TxIOPair, whereas the TxIOPair might 
   // actually be "empty" but would throw off some other logic.
   for(auto rmIter = rmList.begin();
       rmIter != rmList.end();
       rmIter++)
   {
      txioMap_.erase(*rmIter);
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BtcWallet::getTxLedger(HashString const & scraddr) const
{
   SCOPED_TIMER("BtcWallet::getTxLedger");

   if (bdmPtr_->config().armoryDbType == ARMORY_DB_SUPER)
   {
      vector<LedgerEntry> ledgerEntries;
      for(const TxIOPair &txio : getHistoryForScrAddr(scraddr))
      {
         const TxOut txout = txio.getTxOutCopy(bdmPtr_->getIFace());
         //const TxIn txin = txio.getTxInCopy(bdmPtr_->getIFace());
         const DBTxRef tx = txout.getParentTxRef().attached(bdmPtr_->getIFace());
         
         LedgerEntry e(
            scraddr,
            txout.getValue(),
            txout.getParentHeight(),
            tx.getThisHash(),
            tx.getBlockTxIndex(),
            tx.getBlockTimestamp()
         );
         
         ledgerEntries.push_back(e);
      }
      return ledgerEntries;
   }
   else
   {
      ts_saMap::const_snapshot saSS(scrAddrMap_);
      if(saSS.find(scraddr) == saSS.end())
         return vector<LedgerEntry>();
      else
      {
         ScrAddrObj sa = scrAddrMap_[scraddr];
         return sa.getTxLedger();
      }
   }
}

vector<LedgerEntry> BtcWallet::getTxLedger() const
{
   SCOPED_TIMER("BtcWallet::getTxLedger");

   if (bdmPtr_->config().armoryDbType == ARMORY_DB_SUPER)
   {
      vector<LedgerEntry> ledgerEntries;
      ts_saMap::const_snapshot saSnapshot(scrAddrMap_);
      for(const auto &sa : saSnapshot)
      {
         const ScrAddrObj & addr = sa.second;
         const vector<LedgerEntry> e = getTxLedger(addr.getScrAddr());
         copy(e.begin(), e.end(), back_inserter(ledgerEntries));
      }
      return ledgerEntries;
   }
   else
   {
      return ledgerAllAddr_;
   }
}


////////////////////////////////////////////////////////////////////////////////
const vector<LedgerEntry> 
   BtcWallet::getZeroConfLedger(HashString const * scraddr) const
{
   SCOPED_TIMER("BtcWallet::getZeroConfLedger");

   // Make sure to rebuild the ZC ledgers before calling this method
   if(!scraddr)
      return ledgerAllAddrZC_;
   else
   {
      ts_saMap::const_snapshot saSS(scrAddrMap_);
      if (saSS.find(*scraddr) == saSS.end())
         return vector<LedgerEntry>(0);
      else
      {
         ScrAddrObj sa = scrAddrMap_[*scraddr];
         return sa.getZeroConfLedger();
      }
   }
}

void BtcWallet::insertRegisteredTxIfNew(HashString txHash)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(txHash).second == true)
   {
      DBTxRef txref = bdmPtr_->getTxRefByHash(txHash).attached(bdmPtr_->getIFace());
      RegisteredTx regTx(txref,
                         txref.getThisHash(),
                         txref.getBlockHeight(),
                         txref.getBlockTxIndex());
      registeredTxList_.push_back(regTx);
   }
}

void BtcWallet::scanRegisteredTxList(uint32_t blkStart, uint32_t blkEnd)
{
   SCOPED_TIMER("scanRegisteredTxForWallet");

   // Make sure RegisteredTx objects have correct data, then sort.
   // TODO:  Why did I not need this with the MMAP blockchain?  Somehow
   //        I was able to sort correctly without this step, before...?


   for(RegisteredTx &rtx : registeredTxList_)
   {
      if(rtx.txIndex_ > UINT32_MAX/2)
      {
         // fix this iterator issue (assignement)
         // what iterator issue? ~CS

         // The RegisteredTx was created before the chain was organized
         rtx.blkNum_ = rtx.txRefObj_.getBlockHeight();
         rtx.txIndex_ = rtx.txRefObj_.getBlockTxIndex();
      }
   }
   registeredTxList_.sort();
   
   ///// LOOP OVER ALL RELEVANT TX ////
   for(RegisteredTx &rtx : registeredTxList_)
   {
      // Pull the tx from disk and check it for the supplied wallet
      Tx theTx = rtx.getTxCopy(bdmPtr_->getIFace());
      if( !theTx.isInitialized() )
      {
         LOGWARN << "***WARNING: How did we get a NULL tx?";
         continue;
      }

      
      const BlockHeader* bhptr;
      try
      {
         bhptr = bdmPtr_->getHeaderPtrForTx(theTx);
      }
      catch (...)
      {
         // This condition happens on invalid Tx (like invalid P2Pool coinbases)
         // or when the blockheader isn't on the main branch
         continue;
      }

      if (!bhptr->isMainBranch())
         continue;

      uint32_t thisBlk = bhptr->getBlockHeight();
      if(thisBlk < blkStart  ||  thisBlk >= blkEnd)
         continue;

      if( !bdmPtr_->isTxFinal(theTx) )
         continue;

      // If we made it here, we want to scan this tx!
      scanTx(theTx, rtx.txIndex_, bhptr->getTimestamp(), thisBlk);
   }
 
   sortLedger();


   // We should clean up any dangling TxIOs in the wallet then rescan
   if(bdmPtr_->isZcEnabled())
      rescanWalletZeroConf();
}

void BtcWallet::updateRegisteredScrAddrs(uint32_t newTopBlk)
{
   ts_rsaMap::snapshot rsaSnapshot(registeredScrAddrMap_);
   ts_rsaMap::iterator rsaIter;

   for (rsaIter = rsaSnapshot.begin(); 
      rsaIter != rsaSnapshot.end(); ++rsaIter)
   {
      RegisteredScrAddr rsa = rsaIter->second;

      rsa.alreadyScannedUpToBlk_ = newTopBlk;
      rsaIter.update(rsa);
   }
}

uint32_t BtcWallet::numBlocksToRescan(uint32_t endBlk) const
{
   SCOPED_TIMER("numBlocksToRescan");
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   uint32_t currNextBlk = bdmPtr_->getTopBlockHeight() + 1;
   endBlk = min(endBlk, currNextBlk);

   // The wallet isn't registered with the BDM, but there's a chance that 
   // each of its addresses are -- if any one is not, do rescan
   uint32_t maxAddrBehind = 0;

   ts_saMap::const_snapshot saSnapshot(scrAddrMap_);
   ts_saMap::const_iterator saIter;
   ts_rsaMap::const_snapshot rsaSS(registeredScrAddrMap_);

   for(saIter = saSnapshot.begin(); saIter != saSnapshot.end(); ++saIter)
   {
      const ScrAddrObj & addr = (*saIter).second;

      // If any address is not registered, will have to do a full scan
      if(rsaSS.find(addr.getScrAddr()) == rsaSS.end())
         return endBlk;  // Gotta do a full rescan!

      ts_rsaMap::const_iterator getRai = rsaSS.find(addr.getScrAddr());
      if (getRai == rsaSS.end())
      {
         LOGWARN << "item not found in registeredScrAddrMap_";
         continue;
      }
      const RegisteredScrAddr & ra = (*getRai).second;
      maxAddrBehind = max(maxAddrBehind, endBlk-ra.alreadyScannedUpToBlk_);
   }

   // If we got here, then all addr are already registered and current
   return maxAddrBehind;
}

///////////////////////////////////////////////////////////////////////////////
bool BtcWallet::registerNewScrAddr(HashString scraddr)
{
   ts_rsaMap::const_snapshot rsaSS(registeredScrAddrMap_);

   if(rsaSS.find(scraddr) != rsaSS.end())
      return false;

   uint32_t currBlk = bdmPtr_->getTopBlockHeight();
   registeredScrAddrMap_[scraddr] = RegisteredScrAddr(scraddr, currBlk);
   
   return true;
}

bool BtcWallet::registerImportedScrAddr(HashString scraddr,
                                                    uint32_t createBlk)
{
   SCOPED_TIMER("registerImportedScrAddr");
   
   ts_rsaMap::const_snapshot rsaSS(registeredScrAddrMap_);

   if(rsaSS.find(scraddr) != rsaSS.end())
      return false;

   // In some cases we may have used UINT32_MAX to specify "don't know"
   if(createBlk==UINT32_MAX)
      createBlk = 0;

   registeredScrAddrMap_[scraddr] = RegisteredScrAddr(scraddr, createBlk);
   allScannedUpToBlk_ = min(createBlk, allScannedUpToBlk_);

   return true;
}

///////////////////////////////////////////////////////////////////////////////

vector<TxIOPair> BtcWallet::getHistoryForScrAddr(
   BinaryDataRef uniqKey,
   bool withMultisig
)
{
   InterfaceToLDB *const iface_ = bdmPtr_->getIFace();

   StoredScriptHistory ssh;
   iface_->getStoredScriptHistory(ssh, uniqKey);

   // "withMultisig" usually refers to whether we want to get the
   // multisig outputs associated with a non-multisig scrAddr.  However,
   // if this scrAddr is, itself, a multisig scrAddr, we obviously 
   // should include its direct history
   if (uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      withMultisig = true;

   
   ts_rsaMap::snapshot rsaSS(registeredScrAddrMap_);
   ts_rsaMap::iterator iter = rsaSS.find(uniqKey);

   iter = rsaSS.find(uniqKey);
   if (ITER_IN_MAP(iter, rsaSS))
   {
      RegisteredScrAddr rsaI = iter->second;
      rsaI.alreadyScannedUpToBlk_ = ssh.alreadyScannedUpToBlk_;
      iter.update(rsaI);
   }
   
   vector<TxIOPair> outVect;
   if(!ssh.isInitialized())
      return outVect;

   outVect.reserve(ssh.totalTxioCount_);
   for(auto &subSSHEntry : ssh.subHistMap_)
   {
      StoredSubHistory & subssh = subSSHEntry.second;
      for( auto &txiop : subssh.txioSet_)
      {
         const TxIOPair & txio = txiop.second;
         if(withMultisig || !txio.isMultisig())
            outVect.push_back(txio);   
      }
   }
   
   return outVect;
}

///////////////////////////////////////////////////////////////////////////////

vector<TxIOPair> BtcWallet::getHistoryForScrAddr(
   BinaryDataRef uniqKey,
   bool withMultisig
   ) const
{
   InterfaceToLDB *const iface_ = bdmPtr_->getIFace();

   StoredScriptHistory ssh;
   iface_->getStoredScriptHistory(ssh, uniqKey);

   if (uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      withMultisig = true;

   vector<TxIOPair> outVect;
   if (!ssh.isInitialized())
      return outVect;

   outVect.reserve(ssh.totalTxioCount_);
   for (auto &subSSHEntry : ssh.subHistMap_)
   {
      StoredSubHistory & subssh = subSSHEntry.second;
      for (auto &txiop : subssh.txioSet_)
      {
         const TxIOPair & txio = txiop.second;
         if (withMultisig || !txio.isMultisig())
            outVect.push_back(txio);
      }
   }

   return outVect;
}

///////////////////////////////////////////////////////////////////////////////

void BtcWallet::eraseTx(const BinaryData& txHash)
{
   if(registeredTxSet_.erase(txHash))
   {
      removeRegisteredTx(txHash);
   }
}

void BtcWallet::fetchDBRegisteredScrAddrData()
{
   SCOPED_TIMER("fetchWalletRegisteredScrAddrData");
   ts_saMap::const_snapshot saSnapshot(scrAddrMap_);
   ts_saMap::const_iterator saIter;

   for(saIter = saSnapshot.begin(); saIter != saSnapshot.end(); ++saIter)
   {
      const ScrAddrObj & scrAddrObj = (*saIter).second;
      fetchDBRegisteredScrAddrData(scrAddrObj.getScrAddr());
   }
}

void BtcWallet::fetchDBRegisteredScrAddrData(BinaryData const & scrAddr)
{
   InterfaceToLDB *const iface = bdmPtr_->getIFace();

   const vector<TxIOPair> hist = getHistoryForScrAddr(scrAddr);

   for(uint32_t i=0; i<hist.size(); i++)
   {
      // Fetch the full tx of the arriving coins
      TxRef txref = hist[i].getTxRefOfOutput();
      StoredTx stx;
      iface->getStoredTx(stx, txref.getDBKey());
      RegisteredTx regTx(txref, stx.thisHash_, stx.blockHeight_, stx.txIndex_);
      insertRegisteredTxIfNew(regTx);
      registerOutPoint(hist[i].getOutPoint(iface));

      txref = hist[i].getTxRefOfInput();
      if(txref.isNull())
         continue;

      // If the coins were spent, also fetch the tx in which they were spent
      iface->getStoredTx(stx, txref.getDBKey());
      regTx = RegisteredTx(txref, stx.thisHash_, stx.blockHeight_, stx.txIndex_);
      insertRegisteredTxIfNew(regTx);
   }
}

void BtcWallet::reorgChangeBlkNum(uint32_t blkNum)
{
   if(blkNum<lastScanned_) 
   {
      lastScanned_ = blkNum;
   }
}

void BtcWallet::registeredScrAddrScan(
   uint8_t const * txptr,
   uint32_t txSize,
   vector<uint32_t> * txInOffsets,
   vector<uint32_t> * txOutOffsets,
   bool withSecondOrderMultisig)
{
   if (registeredScrAddrMap_.size() == 0)
      return;

   vector<uint32_t> localOffsIn;
   vector<uint32_t> localOffsOut;

   if (txSize == 0 || !txInOffsets || !txOutOffsets)
   {
      txInOffsets = &localOffsIn;
      txOutOffsets = &localOffsOut;
      BtcUtils::TxCalcLength(txptr, txSize, txInOffsets, txOutOffsets);
   }

   uint32_t nTxIn = txInOffsets->size() - 1;
   uint32_t nTxOut = txOutOffsets->size() - 1;
   
   OutPoint op; // reused for performance

   uint8_t const * txStartPtr = txptr;
   for (uint32_t iin = 0; iin<nTxIn; iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      op.unserialize(txStartPtr + (*txInOffsets)[iin], txSize - (*txInOffsets)[iin]);

      if (countOutPoints(op) > 0)
      {
         insertRegisteredTxIfNew(BtcUtils::getHash256(txptr, txSize));
         break;
      }
   }

   // We have to scan all TxOuts regardless, to make sure our list of 
   // registeredOutPoints_ is up-to-date so that we can identify TxIns that are
   // ours on future to-be-scanned transactions
   for (uint32_t iout = 0; iout<nTxOut; iout++)
   {
      uint32_t viStart = (*txOutOffsets)[iout] + 8;
      uint32_t txOutEnd = (*txOutOffsets)[iout + 1];

      BinaryRefReader brr(txStartPtr + viStart, txOutEnd - viStart);
      uint32_t scrsz = (uint32_t)brr.get_var_int();
      BinaryDataRef script = brr.get_BinaryDataRef(scrsz);

      TXOUT_SCRIPT_TYPE txoType = BtcUtils::getTxOutScriptType(script);
      BinaryData scrAddr = BtcUtils::getTxOutScrAddr(script, txoType);

      if (scrAddrIsRegistered(scrAddr))
      {
         HashString txHash = BtcUtils::getHash256(txptr, txSize);
         insertRegisteredTxIfNew(txHash);
         registerOutPoint(OutPoint(txHash, iout));
      }

      if (withSecondOrderMultisig && txoType == TXOUT_SCRIPT_MULTISIG)
      {
         BinaryRefReader  brrmsig(scrAddr);
         uint8_t PREFIX = brrmsig.get_uint8_t();
         uint8_t M = brrmsig.get_uint8_t();
         uint8_t N = brrmsig.get_uint8_t();
         for (uint8_t a = 0; a<N; a++)
         {
            BinaryDataRef bdrAddr160 = brrmsig.get_BinaryDataRef(20);
            if (scrAddrIsRegistered(HASH160PREFIX + bdrAddr160))
            {
               HashString txHash = BtcUtils::getHash256(txptr, txSize);
               insertRegisteredTxIfNew(txHash);
               registerOutPoint(OutPoint(txHash, iout));
            }
         }
      }
   }
}

void BtcWallet::registeredScrAddrScan(Tx & theTx)
{
   registeredScrAddrScan(
      theTx.getPtr(),
      theTx.getSize(),
      &theTx.offsetsTxIn_,
      &theTx.offsetsTxOut_
   );
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::scanBlocksAgainstRegisteredScrAddr(uint32_t blk0, 
                                                   uint32_t blk1)
{
   SCOPED_TIMER("scanDBForRegisteredTx");

   bool doScanProgressThing = (blk1 - blk0 > NUM_BLKS_IS_DIRTY);
   if (doScanProgressThing)
   {
      //if(BtcUtils::GetFileSize(bfile) != FILE_DOES_NOT_EXIST)
      //remove(bfile.c_str());
   }

   LDBIter ldbIter = bdmPtr_->getIterator(BLKDATA, BULK_SCAN);
   BinaryData firstKey = DBUtils::getBlkDataKey(blk0, 0);
   ldbIter.seekTo(firstKey);

   TIMER_START("ScanBlockchain");
   while (ldbIter.isValid(DB_PREFIX_TXDATA))
   {
      // Get the full block from the DB
      StoredHeader sbh;
      bdmPtr_->readStoredBlockAtIter(ldbIter, sbh);

      uint32_t hgt = sbh.blockHeight_;
      uint8_t  dup = sbh.duplicateID_;
      uint8_t  dupMain = bdmPtr_->getValidDupIDForHeight(hgt);
      if (!sbh.isMainBranch_ || dup != dupMain)
         continue;

      if (hgt >= blk1)
         break;

      // If we're here, we need to check the tx for relevance to the 
      // global scrAddr list.  Add to registered Tx map if so
      for ( auto &storedTx : sbh.stxMap_)
      {
         StoredTx & stx = storedTx.second;
         Tx tx = stx.getTxCopy();
         registeredScrAddrScan(tx.getPtr(), tx.getSize());
      }
   }
   TIMER_STOP("ScanBlockchain");
}

////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::removeRegisteredTx(BinaryData const & txHash)
{
   list<RegisteredTx>::iterator rtx
      = std::find_if(
         registeredTxList_.begin(),
         registeredTxList_.end(),
         [&txHash] (const RegisteredTx &rtx) { return rtx.txHash_ == txHash; }
      );
   if (rtx != registeredTxList_.end())
   {
      registeredTxSet_.erase(rtx->txHash_);
      registeredTxList_.erase(rtx);
      return true;
   }

   return false;
}


////////////////////////////////////////////////////////////////////////////////
void BtcWallet::updateAfterReorg(uint32_t lastValidBlockHeight)
{
   //Build list of invalidated transactions
   set<HashString> txJustInvalidated;

   for(RegisteredTx &rtx : registeredTxList_)
   {
      if (rtx.blkNum_ > lastValidBlockHeight)
         txJustInvalidated.insert(rtx.txHash_);
   }

   for (const HashString &invalidTx : txJustInvalidated)
   {
      removeRegisteredTx(invalidTx);
   }

   // turning this thing off for now, as calling getTxLedger without
   // an arg results in returning an empty ledger
   /*vector<LedgerEntry> & ledg = getTxLedger();
   for (uint32_t i = 0; i<ledg.size(); i++)
   {
      HashString const & txHash = ledg[i].getTxHash();
      if (txJustInvalidated.count(txHash) > 0)
         ledg[i].setValid(false);
   }*/

   // Now fix the individual address ledgers
   ts_saMap::snapshot saSnapshot(scrAddrMap_);
   ts_saMap::iterator saIter;

   for (saIter = saSnapshot.begin(); saIter != saSnapshot.end(); ++saIter)
   {
      ScrAddrObj addr = (*saIter).second;
      vector<LedgerEntry> & addrLedg = addr.getTxLedger();
      for (uint32_t i = 0; i<addrLedg.size(); i++)
      {
         HashString const & txHash = addrLedg[i].getTxHash();
         if (txJustInvalidated.count(txHash) > 0)
            addrLedg[i].setValid(false);
      }

      saIter.update(addr);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::rescanWalletZeroConf()
{
   SCOPED_TIMER("rescanWalletZeroConf");
   // Clear the whole list, rebuild
   clearZeroConfPool();

   const ts_BinDataMap *zeroConfRawTxMap = bdmPtr_->getZeroConfRawTxMap();
   const ts_ZCMap *zeroConfMap = bdmPtr_->getZeroConfMap();


   HashString txHash(32);
   ts_BinDataMap::const_snapshot zcListSS(*zeroConfRawTxMap);
   ts_ZCMap::const_snapshot zcSS(*zeroConfMap);

   for (ts_BinDataMap::const_iterator iter = zcListSS.begin();
      iter != zcListSS.end();
      ++iter)
   {

      if (iter->second.getSize() == 0)
         continue;

      ts_ZCMap::const_iterator zcdFR = zcSS.find(iter->first);

      if (zcdFR != zcSS.end())
      {
         if (!bdmPtr_->isTxFinal(zcdFR->second.txobj_))
            continue;

         Tx &tx = const_cast<Tx&>(zcdFR->second.txobj_);
         scanTx(tx, 0, zcdFR->second.txtime_,
            UINT32_MAX);
      }
   }
}

uint32_t BtcWallet::evalLowestBlockNextScan(void) const
{
   SCOPED_TIMER("evalLowestBlockNextScan");

   uint32_t lowestBlk = UINT32_MAX;

   ts_rsaMap::const_snapshot rsaSnapshot(registeredScrAddrMap_);
   ts_rsaMap::const_iterator rsaIter;

   for (rsaIter = rsaSnapshot.begin(); rsaIter != rsaSnapshot.end();
         ++rsaIter)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, (*rsaIter).second.alreadyScannedUpToBlk_);
   }
   
   return lowestBlk;
}

void BtcWallet::saveScrAddrHistories()
{
   if (bdmPtr_->config().armoryDbType != ARMORY_DB_BARE)
   {
      LOGERR << "Should only use saveScrAddrHistories in ARMORY_DB_BARE mode";
      LOGERR << "Aborting save operation.";
      return;
   }

   InterfaceToLDB* iface = bdmPtr_->getIFace();
   InterfaceToLDB::Batch batch(iface, BLKDATA);

   ts_saMap::const_snapshot saSnapshot(scrAddrMap_);
   ts_saMap::const_iterator saIter;
   ts_rsaMap::const_snapshot rsaSS(registeredScrAddrMap_);

   for (saIter = saSnapshot.begin(); saIter != saSnapshot.end(); ++saIter)
   {
      const ScrAddrObj & scrAddr = (*saIter).second;
      BinaryData uniqKey = scrAddr.getScrAddr();

      if (rsaSS.find(uniqKey) == rsaSS.end())
      {
         LOGERR << "How does the wallet have a non-registered ScrAddr?";
         LOGERR << uniqKey.toHexStr().c_str();
         continue;
      }

      const RegisteredScrAddr & rsa = getRegisteredScrAddr(uniqKey);
      const vector<TxIOPair*> & txioList = scrAddr.getTxIOList();

      StoredScriptHistory ssh;
      ssh.uniqueKey_ = scrAddr.getScrAddr();
      ssh.version_ = ARMORY_DB_VERSION;
      ssh.alreadyScannedUpToBlk_ = rsa.alreadyScannedUpToBlk_;
      for (uint32_t t = 0; t<txioList.size(); t++)
         ssh.insertTxio(bdmPtr_->getIFace(), *txioList[t]);

      iface->putStoredScriptHistory(ssh);
   }

   LOGINFO << "Saved wallet history to DB";
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::scanWallet(uint32_t startBlock, uint32_t endBlock, 
                           bool forceScan)
{
   /***All purpose wallet scanning call.
   This call is meant to completely separate blockchain maintenance from
   wallet scanning.

   Blockchain maintenance should be limited to reading last sync state from DB,
   adding missing blocks to the DB, reading new blocks and dealing with reorgs

   Wallet scanning is meant to maintain the list of registered Tx, ledger
   entries and balance for each wallet object.

   The arguments are:
      
      startBlock: The height scanning should start at. For initializing purposes
      or forcedScan, should be 0. To scan newly found blocks, should be set to 
      the last valid scanned block height. Default to UINT32_MAX, which will be 
      replaced by lastScannedBlock_

      endBlock: The height scanning should stop at. For scanning maintenance
      purpose, always pass the highest block heigh in DB. Default to
      UINT32_MAX, which will be replaced by the current top block height.

      forceScan: set to true to force scanning DB against registered scrAddr map
      from block 0. Defaults to false.

   Uninitialized wallets will first call fetchDBRegisteredScrAddrData,
   to look for existing scrAddr data in the DB.

   The maintenance process then breaks down into 3 calls:
   
   1) scanBlocksAgainstRegisteredScrAddr: parses blocks in the DB, updates DB 
   with scrAddr data, starting from startBlock. 
   When new blocks appear, scanWallet should be called with the last scanned
   valid block height, passed as startBlock so that each wallet parses the 
   transactions found in the new blocks, and updates the DB with the relevant 
   scrAddr data.

   If forceScan is set to true, each wallet will call 
   scanBlocksAgainstRegisteredScrAddr(0), to rescan the wallet and rebuild all 
   scrAddr data up to the current block.
   
   If the DB is in supernode, scanBlocksAgainstRegisteredScrAddr shoudln't be 
   called, as scrAddr data is updated for all encountered scrAddr 
   (not just those registered by wallets)

   This call also updates the registeredTxList object for each block it parses.
   In this regard, fetchDBRegisteredScrAddrData is only useful as an initial
   DB scan call.
   
   2) udpateRegisteredScrAddr: updates alreadyScannedUpToBlk_ member for each
   registered scrAddr object in the wallet. Fairly simple call, not sure why
   it isnt part of scanBlocksAgainstRegisteredScrAddr, no harm leaving it as 
   is for now.

   This call is passed endBlock, which is the highest known block.

   3) scanRegisteredTxList: builds registered Txs Ledger and wallet balance.
   Should always be called with the last scanned valid block height, and the 
   current top height.
   ***/

   pthread_t thrSelf = pthread_self();
   threadIDs_.push_back(thrSelf);

   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = bdmPtr_->getTopBlockHeight() + 1;

   if (startBlock < endBlock)
   {
      if (bdmPtr_->config().armoryDbType != ARMORY_DB_SUPER)
      {
         uint32_t scanDBFrom = startBlock;

         if (forceScan)
         {
            //reset the wallet block data
            clearBlkData();
            updateRegisteredScrAddrs(0);
            isInitialized_ = false;

            //scan wallets registered scrAddr from block 0
            scanBlocksAgainstRegisteredScrAddr(0);
            startBlock = 0;
            scanDBFrom = 0;
         }

         if (!isInitialized_)
         {
            //look for existing scrAddr data in DB
            fetchDBRegisteredScrAddrData();

            //then evaluate the lowest unscanned block from the DB scrAddr data
            scanDBFrom = evalLowestBlockNextScan();

            //take 4 days off for the good measure
            scanDBFrom = max(0, (int32_t)scanDBFrom - 576);

            isInitialized_ = true;
         }


         if (!forceScan)
         {
            if (lastScanned_ > startBlock)
            {
               //reorg
               updateAfterReorg(startBlock);
            }

            scanBlocksAgainstRegisteredScrAddr(scanDBFrom);
         }
      }
      else
      {
         fetchDBRegisteredScrAddrData();
         isInitialized_ = true;
      }

      updateRegisteredScrAddrs(endBlock);

      //scan the registered Tx list for balance and history
      scanRegisteredTxList(startBlock, endBlock);

      //save scanned scrAddr dat to DB
      saveScrAddrHistories();

      lastScanned_ = endBlock;
   }
   else
   {
      //no new block, only have to check for new ZC
      if (bdmPtr_->isZcEnabled())
         rescanWalletZeroConf();
   }

   threadIDs_.erase(thrSelf);
}

void BtcWallet::terminateThreads()
{
   while (threadIDs_.size())
   {
      LOGINFO << "terminating " << threadIDs_.size() << " threads";
      ts_threadIDs::const_snapshot thrSS(threadIDs_);
      ts_threadIDs::const_iterator iter;

      for (iter = thrSS.begin(); iter != thrSS.end(); ++iter)
      {
         pthread_cancel(*iter);
      }

      threadIDs_.clear();
   }
}

void BtcWallet::reset()
{
   terminateThreads();
   clearBlkData();
   updateRegisteredScrAddrs(0);
   isInitialized_ = false;
}

// kate: indent-width 3; replace-tabs on;
