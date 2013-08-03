////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "BlockUtils.h"




BlockDataManager_LevelDB* BlockDataManager_LevelDB::theOnlyBDM_ = NULL;
vector<LedgerEntry> BtcWallet::EmptyLedger_(0);


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator<(LedgerEntry const & le2) const
{
   // TODO: I wanted to update this with txTime_, but I didn't want to c
   //       complicate the mess of changes going in, yet.  Do this later
   //       once everything is stable again.
   //if(       blockNum_ != le2.blockNum_)
      //return blockNum_  < le2.blockNum_;
   //else if(  index_    != le2.index_)
      //return index_     < le2.index_;
   //else if(  txTime_   != le2.txTime_)
      //return txTime_    < le2.txTime_;
   //else
      //return false;
   
   if( blockNum_ != le2.blockNum_)
      return blockNum_ < le2.blockNum_;
   else if( index_ != le2.index_)
      return index_ < le2.index_;
   else
      return false;
   
}

//////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator==(LedgerEntry const & le2) const
{
   //TODO
   //return (blockNum_ == le2.blockNum_ && 
           //index_    == le2.index_ && 
           //txTime_   == le2.txTime_);
   return (blockNum_ == le2.blockNum_ && index_ == le2.index_);
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprint(void)
{
   cout << "LedgerEntry: " << endl;
   cout << "   ScrAddr : " << getScrAddr().toHexStr() << endl;
   cout << "   Value   : " << getValue()/1e8 << endl;
   cout << "   BlkNum  : " << getBlockNum() << endl;
   cout << "   TxHash  : " << getTxHash().toHexStr() << endl;
   cout << "   TxIndex : " << getIndex() << endl;
   cout << "   isValid : " << (isValid() ? 1 : 0) << endl;
   cout << "   Coinbase: " << (isCoinbase() ? 1 : 0) << endl;
   cout << "   sentSelf: " << (isSentToSelf() ? 1 : 0) << endl;
   cout << "   isChange: " << (isChangeBack() ? 1 : 0) << endl;
   cout << endl;
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprintOneLine(void)
{
   printf("   Addr:%s Tx:%s:%02d   BTC:%0.3f   Blk:%06d\n", 
                           "   ",
                           getTxHash().getSliceCopy(0,8).toHexStr().c_str(),
                           getIndex(),
                           getValue()/1e8,
                           getBlockNum());
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(HashString    addr, 
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp,
                       uint32_t      lastBlockNum,
                       uint32_t      lastTimestamp) :
      scrAddr_(addr), 
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp),
      lastBlockNum_(lastBlockNum), 
      lastTimestamp_(lastTimestamp)
{ 
   relevantTxIOPtrs_.clear();
   relevantTxIOPtrsZC_.clear();
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getSpendableBalance(uint32_t currBlk)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isSpendable(currBlk))
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      if(relevantTxIOPtrsZC_[i]->isSpendable(currBlk))
         balance += relevantTxIOPtrsZC_[i]->getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getUnconfirmedBalance(uint32_t currBlk)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isMineButUnconfirmed(currBlk))
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      if(relevantTxIOPtrsZC_[i]->isMineButUnconfirmed(currBlk))
         balance += relevantTxIOPtrsZC_[i]->getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getFullBalance(void)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isUnspent())
         balance += txio.getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isUnspent())
         balance += txio.getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getSpendableTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isSpendable(blkNum))
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back( UnspentTxOut(txout, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isSpendable(blkNum))
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back( UnspentTxOut(txout, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getFullTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isUnspent())
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back( UnspentTxOut(txout, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isUnspent())
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back( UnspentTxOut(txout, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t ScrAddrObj::removeInvalidEntries(void)   
{
   vector<LedgerEntry> newLedger(0);
   uint32_t leRemoved = 0;
   for(uint32_t i=0; i<ledger_.size(); i++)
   {
      if(!ledger_[i].isValid())
         leRemoved++;
      else
         newLedger.push_back(ledger_[i]);
   }
   ledger_.clear();
   ledger_ = newLedger;
   return leRemoved;
}
   
////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::sortLedger(void)
{
   sort(ledger_.begin(), ledger_.end());
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addLedgerEntry(LedgerEntry const & le, bool isZeroConf)
{ 
   if(isZeroConf)
      ledgerZC_.push_back(le);
   else
      ledger_.push_back(le);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addTxIO(TxIOPair * txio, bool isZeroConf)
{ 
   if(isZeroConf)
      relevantTxIOPtrsZC_.push_back(txio);
   else
      relevantTxIOPtrs_.push_back(txio);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addTxIO(TxIOPair & txio, bool isZeroConf)
{ 
   if(isZeroConf)
      relevantTxIOPtrsZC_.push_back(&txio);
   else
      relevantTxIOPtrs_.push_back(&txio);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::pprintLedger(void)
{ 
   cout << "Address Ledger: " << getScrAddr().toHexStr() << endl;
   for(uint32_t i=0; i<ledger_.size(); i++)
      ledger_[i].pprintOneLine();
   for(uint32_t i=0; i<ledgerZC_.size(); i++)
      ledgerZC_[i].pprintOneLine();
}



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// If the wallet is not registered with the BDM, the following two methods do
// the exact same thing.  The only difference is to tell the BDM whether it 
// should do a rescan of the blockchain, or if we know there's nothing to find
// so don't bother (perhaps because we just created the address)...
void BtcWallet::addScrAddr(HashString    scrAddr, 
                           uint32_t      firstTimestamp,
                           uint32_t      firstBlockNum,
                           uint32_t      lastTimestamp,
                           uint32_t      lastBlockNum)
{

   if(scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj* addrPtr = &(scrAddrMap_[scrAddr]);
   *addrPtr = ScrAddrObj(scrAddr, firstTimestamp, firstBlockNum,
                                  lastTimestamp,  lastBlockNum);
   addrPtrVect_.push_back(addrPtr);

   // Default behavior is "don't know, must rescan" if no firstBlk is spec'd
   if(bdmPtr_!=NULL)
      bdmPtr_->registerImportedAddress(scrAddr, firstBlockNum);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewScrAddr(BinaryData scrAddr)
{
   if(scrAddrMap_.find(scrAddr) != scrAddrMap_.end())
      return;

   ScrAddrObj* addrPtr = &(scrAddrMap_[scrAddr]);
   *addrPtr = ScrAddrObj(scrAddr, 0,0, 0,0); 
   addrPtrVect_.push_back(addrPtr);

   if(bdmPtr_!=NULL)
      bdmPtr_->registerNewAddress(scrAddr);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress(ScrAddrObj const & newScrAddr)
{
   if(scrAddrMap_.find(newScrAddr.getScrAddr()) != scrAddrMap_.end())
      return;

   if(newAddr.getScrAddr().getSize() > 0)
   {            
      ScrAddrObj * addrPtr = &(scrAddrMap_[newAddr.getScrAddr()]);
      *addrPtr = newAddr;
      addrPtrVect_.push_back(addrPtr);
   }

   if(bdmPtr_!=NULL)
      bdmPtr_->registerImportedAddress(newAddr.getScrAddr(), 
                                       newAddr.getFirstBlockNum());
}


/////////////////////////////////////////////////////////////////////////////
// SWIG has some serious problems with typemaps and variable arg lists
// Here I just create some extra functions that sidestep all the problems
// but it would be nice to figure out "typemap typecheck" in SWIG...
void BtcWallet::addAddress_ScrAddrObj_(ScrAddrObj const & newScrAddr)
{ 
   addScrAddr(newScrAddr); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_1_(HashString scrAddr)
{  
   PDEBUG("Adding address to BtcWallet");
   addAddress(scrAddr); 
} 

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_3_(HashString    scrAddr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum)
{  
   addAddress(scrAddr, firstBlockNum, firstTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_5_(HashString    scrAddr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum,
                              uint32_t      lastTimestamp,
                              uint32_t      lastBlockNum)
{  
   addAddress(scrAddr, firstBlockNum, firstTimestamp, 
                        lastBlockNum,  lastTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasScrAddr(HashString const & scrAddr)
{
   return scrAddrMap_.find(scrAddr) != scrAddrMap_.end();
}


/////////////////////////////////////////////////////////////////////////////
// Determine, as fast as possible, whether this tx is relevant to us
// Return  <IsOurs, InputIsOurs>
pair<bool,bool> BtcWallet::isMineBulkFilter(Tx & tx, bool withMultiSig)
{
   // Since 99.999%+ of all transactions are not ours, let's do the 
   // fastest bulk filter possible, even though it will add 
   // redundant computation to the tx that are ours.  In fact,
   // we will skip the TxIn/TxOut convenience methods and follow the
   // pointers directly the data we want

   uint8_t const * txStartPtr = tx.getPtr();
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + tx.getTxInOffset(iin));
      if(txioMap_.find(op) != txioMap_.end())
         return pair<bool,bool>(true,true);
   }

   // TxOuts are a little more complicated, because we have to process each
   // different type separately.  Nonetheless, 99% of transactions use the
   // 25-byte repr which is ridiculously fast
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      static uint8_t scriptLenFirstByte;
      static HashString scrAddr(20);

      uint8_t const * ptr = (txStartPtr + tx.getTxOutOffset(iout) + 8);
      scriptLenFirstByte = *(uint8_t*)ptr;
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         scrAddr.copyFrom(ptr+4, 20);
         if( hasScrAddr(HASH160PREFIX + scrAddr) )
            return pair<bool,bool>(true,false);
      }
      if(scriptLenFirstByte == 23)
      {
         // Std P2SH with 23-byte script
         scrAddr.copyFrom(ptr+3, 20);
         if( hasScrAddr(P2SHPREFIX + scrAddr) )
            return pair<bool,bool>(true,false);
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         static HashString scrAddr(20);
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 65, scrAddr);
         if( hasScrAddr(HASH160PREFIX + scrAddr) )
            return pair<bool,bool>(true,false);
      }
      else if(scriptLenFirstByte==35)
      {
         // Std spend-coinbase TxOut script
         static HashString scrAddr(20);
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 33, scrAddr);
         if( hasScrAddr(HASH160PREFIX + scrAddr) )
            return pair<bool,bool>(true,false);
      }
      else if(withMultiSig)
      {
         // This branch may be compute-intensive, so it's opt-in only
         uint32_t viStart  = tx.getTxOutOffset(iout) + 8;
         uint32_t txOutEnd = tx.getTxOutOffset(iout+1);
         BinaryRefReader brr(viStart, txOutEnd-viStart);
         uint64_t scrsz = brr.get_var_int()
         BinaryDataRef scr = brr.get_BinaryDataRef((uint32_t)vi);

         BinaryData msigkey = getMultisigUniqueKey(scr); 
         if(msigkey.getSize() == 0)
            continue
        
         if(hasScrAddr(MSIGPREFIX + msigkey))
            return pair<bool,bool>(true,false);

         BinaryRefReader brrmsig(msigkey);
         uint8_t M = brrmsig.get_uint8_t();
         uint8_t N = brrmsig.get_uint8_t();
         for(uint8_t a=0; a<N; a++)
            if(hasScrAddr(HASH160PREFIX + brr.get_BinaryDataRef(20))
               return pair<bool,bool>(true,false);
      }

       
      // Try to flag non-standard scripts
      //TxOut txout = tx.getTxOut(iout);
      //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
      //{
         //ScrAddrObj & thisAddr = *(addrPtrVect_[i]);
         //HashString const & addr20 = thisAddr.getScrAddr();
         //if(txout.getScriptRef().find(thisAddr.getScrAddr()) > -1)
            //scanNonStdTx(0, 0, tx, iout, thisAddr);
         //continue;
      //}
      //break;
   }

   // If we got here, it's either non std or not ours
   return pair<bool,bool>(false,false);
}


/////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintAlot(uint32_t topBlk, bool withAddr)
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
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      iter->second.pprintOneLine();
   }

   if(withAddr)
   {
      for(uint32_t i=0; i<getNumScrAddr(); i++)
      {
         ScrAddrObj & addr = getScrAddrByIndex(i);
         HashString addr160 = addr.getScrAddr();
         cout << "\nAddress: " << addr160.toHexStr().c_str() << endl;
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
            addr.relevantTxIOPtrs_[t]->pprintOneLine();
         }

         cout << "   TxioPtrs (Zero-conf):" << endl;
         for(uint32_t t=0; t<addr.relevantTxIOPtrsZC_.size(); t++)
         {
            addr.relevantTxIOPtrsZC_[t]->pprintOneLine();
         }
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
// This method is used in the registeredAddrScan to conditionally create and
// insert a transaction into the registered list 
void BlockDataManager_LevelDB::insertRegisteredTxIfNew(HashString txHash)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(txHash).second == true)
   {
      TxRef tx_ptr = getTxRefByHash(txHash);
      RegisteredTx regTx(tx_ptr,
                         tx_ptr->getThisHash(),
                         tx_ptr->getBlockHeight(),
                         tx_ptr->getBlockTxIndex());
      registeredTxList_.push_back(regTx);
      regTx.writeToLDB(transientDB_);
   }
}



/////////////////////////////////////////////////////////////////////////////
//  This basically does the same thing as the bulk filter, but it's for the
//  BDM to collect data on registered wallets/addresses during bulk
//  blockchain scaning.  It needs to track relevant OutPoints and produce 
//  a list of transactions that are relevant to the registered wallets.
//
//  Also, this takes a raw pointer to memory, because it is assumed that 
//  the data is being buffered and not converted/parsed for Tx objects, yet.
//
//  If the txSize and offsets have been pre-calculated, you can pass them 
//  in, or pass {0, NULL, NULL} to have it calculated for you.
//  
void BlockDataManager_LevelDB::registeredAddrScan( uint8_t const * txptr,
                                                   uint32_t txSize,
                                                   vector<uint32_t> * txInOffsets,
                                                   vector<uint32_t> * txOutOffsets)
{
   // Probably doesn't matter, but I'll keep these on the heap between calls
   static vector<uint32_t> localOffsIn;
   static vector<uint32_t> localOffsOut;

   if(txSize==0 || txInOffsets==NULL || txOutOffsets==NULL)
   {
      txInOffsets  = &localOffsIn;
      txOutOffsets = &localOffsOut;
      uint32_t txSize = BtcUtils::TxCalcLength(txptr, txInOffsets, txOutOffsets);
   }
   
   uint32_t nTxIn  = txInOffsets->size()-1;
   uint32_t nTxOut = txOutOffsets->size()-1;
   

   if(registeredScrAddrMap_.size() == 0)
      return;

   uint8_t const * txStartPtr = txptr;
   for(uint32_t iin=0; iin<nTxIn; iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + (*txInOffsets)[iin]);
      if(registeredOutPoints_.count(op) > 0)
      {
         insertRegisteredTxIfNew(BtcUtils::getHash256(txptr, txSize));
         break; // we only care if ANY txIns are ours, not which ones
      }
   }

   // We have to scan all TxOuts regardless, to make sure our list of 
   // registeredOutPoints_ is up-to-date so that we can identify TxIns that are
   // ours on future to-be-scanned transactions
   for(uint32_t iout=0; iout<nTxOut; iout++)
   {
      static uint8_t scriptLenFirstByte;
      static HashString addr20(20);

      uint8_t const * ptr = (txStartPtr + (*txOutOffsets)[iout] + 8);
      scriptLenFirstByte = *(uint8_t*)ptr;
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         addr20.copyFrom(ptr+4, 20);
         if( addressIsRegistered(addr20) )
         {
            HashString txHash = BtcUtils::getHash256(txptr, txSize);
            insertRegisteredTxIfNew(txHash);
            registeredOutPoints_.insert(OutPoint(txHash, iout));
         }
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         static HashString addr20(20);
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 65, addr20);
         if( addressIsRegistered(addr20) )
         {
            HashString txHash = BtcUtils::getHash256(txptr, txSize);
            insertRegisteredTxIfNew(txHash);
            registeredOutPoints_.insert(OutPoint(txHash, iout));
         }
      }
      else
      {
         /* TODO:  Right now we will just ignoring non-std tx
                   I don't do anything with them right now, anyway
         TxOut txout = tx.getTxOut(iout);
         for(uint32_t i=0; i<addrPtrVect_.size(); i++)
         {
            ScrAddrObj & thisAddr = *(addrPtrVect_[i]);
            HashString const & addr20 = thisAddr.getScrAddr();
            if(txout.getScriptRef().find(thisAddr.getScrAddr()) > -1)
               scanNonStdTx(0, 0, tx, iout, thisAddr);
            continue;
         }
         //break;
         */
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::registeredAddrScan( Tx & theTx )
{
   registeredAddrScan(theTx.getPtr(),
                      theTx.getSize(),
                      &theTx.offsetsTxIn_, 
                      &theTx.offsetsTxOut_);
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

   pair<bool,bool> boolPair = isMineBulkFilter(tx);
   bool txIsRelevant  = boolPair.first;
   bool anyTxInIsOurs = boolPair.second;

   if( !txIsRelevant )
      return;

   // We distinguish "any" from "anyNew" because we want to avoid re-adding
   // transactions/TxIOPairs that are already part of the our tx list/ledger
   // but we do need to determine if this was sent-to-self, regardless of 
   // whether it was new.
   bool anyNewTxInIsOurs   = false;
   bool anyNewTxOutIsOurs  = false;
   bool isCoinbaseTx       = false;

   map<HashString, ScrAddrObj>::iterator addrIter;
   ScrAddrObj* thisAddrPtr;
   HashString  addr20;
   //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   //{
      //ScrAddrObj & thisAddr = *(addrPtrVect_[i]);
      //HashString const & addr20 = thisAddr.getScrAddr();

      ///// LOOP OVER ALL TXIN IN BLOCK /////
      for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
      {
         TxIn txin = tx.getTxIn(iin);
         OutPoint outpt = txin.getOutPoint();
         // Empty hash in Outpoint means it's a COINBASE tx --> no addr inputs
         if(outpt.getTxHashRef() == BtcUtils::EmptyHash_)
         {
            isCoinbaseTx = true;
            continue;
         }

         // We have the txin, now check if it contains one of our TxOuts
         map<OutPoint, TxIOPair>::iterator txioIter = txioMap_.find(outpt);
         bool txioWasInMapAlready = (txioIter != txioMap_.end());
         if(txioWasInMapAlready)
         {
            // If we are here, we know that this input is spending an 
            // output owned by this wallet.
            // We will get here for every address in the search, even 
            // though it is only relevant to one of the addresses.
            TxIOPair & txio  = txioIter->second;
            TxOut txout = txio.getTxOut();

            // It's our TxIn, so address should be in this wallet
            addr20   = txout.getRecipientAddr();
            addrIter = scrAddrMap_.find(addr20);
            if( addrIter == scrAddrMap_.end())
            {
               // Have TxIO but address is not in the map...?
               LOGERR << "ERROR: TxIn in TxIO map, but addr not in wallet...?";
               continue;
            }
            thisAddrPtr = &addrIter->second;

            // We need to make sure the ledger entry makes sense, and make
            // sure we update TxIO objects appropriately
            int64_t thisVal = (int64_t)txout.getValue();
            totalLedgerAmt -= thisVal;

            // Skip, if this is a zero-conf-spend, but it's already got a zero-conf
            if( isZeroConf && txio.hasTxInZC() )
               return; // this tx can't be valid, might as well bail now

            if( !txio.hasTxInInMain() && !(isZeroConf && txio.hasTxInZC())  )
            {
               // isValidNew only identifies whether this set-call succeeded
               // If it didn't, it's because this is from a zero-conf tx but this 
               // TxIn already exists in the blockchain spending the same output.
               // (i.e. we have a ref to the prev output, but it's been spent!)
               bool isValidNew;
               if(isZeroConf)
                  isValidNew = txio.setTxInZC(&tx, iin);
               else
                  isValidNew = txio.setTxIn(tx.getTxRef(), iin);

               if(!isValidNew)
                  continue;

               anyNewTxInIsOurs = true;

               LedgerEntry newEntry(addr20, 
                                   -(int64_t)thisVal,
                                    blknum, 
                                    tx.getThisHash(), 
                                    iin,
                                    txtime,
                                    isCoinbaseTx,
                                    false,  // SentToSelf is meaningless for addr ledger
                                    false); // "isChangeBack" is meaningless for TxIn
               thisAddrPtr->addLedgerEntry(newEntry, isZeroConf);

               // Update last seen on the network
               thisAddrPtr->setLastTimestamp(txtime);
               thisAddrPtr->setLastBlockNum(blknum);
            }
         }
         else
         {
            // Lots of txins that we won't have, this is a normal conditional
            // But we should check the non-std txio list since it may actually
            // be there
            if(nonStdTxioMap_.find(outpt) != nonStdTxioMap_.end())
            {
               if(isZeroConf)
                  nonStdTxioMap_[outpt].setTxInZC(&tx, iin);
               else
                  nonStdTxioMap_[outpt].setTxIn(tx.getTxRef(), iin);
               nonStdUnspentOutPoints_.erase(outpt);
            }
         }
      } // loop over TxIns
   //}


   //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   //{
      //ScrAddrObj & thisAddr = *(addrPtrVect_[i]);
      //HashString const & addr20 = thisAddr.getScrAddr();

      ///// LOOP OVER ALL TXOUT IN TX /////
      for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
      {
         TxOut txout = tx.getTxOut(iout);
         if( txout.getScriptType() == TXOUT_SCRIPT_UNKNOWN )
         {
            //if(txout.getScriptRef().find(addr20) > -1)
               //scanNonStdTx(blknum, txIndex, tx, iout, *thisAddrPtr);
            continue;
         }

         addr20   = txout.getRecipientAddr();
         addrIter = scrAddrMap_.find(addr20);
         if( addrIter != scrAddrMap_.end())
         {
            thisAddrPtr = &addrIter->second;
            // If we got here, at least this TxOut is for this address.
            // But we still need to find out if it's new and update
            // ledgers/TXIOs appropriately
            int64_t thisVal = (int64_t)(txout.getValue());
            totalLedgerAmt += thisVal;

            OutPoint outpt(tx.getThisHash(), iout);      
            map<OutPoint, TxIOPair>::iterator txioIter = txioMap_.find(outpt);
            bool txioWasInMapAlready = (txioIter != txioMap_.end());
            bool doAddLedgerEntry = false;
            if(txioWasInMapAlready)
            {
               if(isZeroConf) 
               {
                  // This is a real txOut, in the blockchain
                  if(txioIter->second.hasTxOutZC() || txioIter->second.hasTxOutInMain())
                     continue; 

                  // If we got here, somehow the Txio existed already, but 
                  // there was no existing TxOut referenced by it.  Probably,
                  // there was, but that TxOut was invalidated due to reorg
                  // and now being re-added
                  txioIter->second.setTxOutZC(&tx, iout);
                  thisAddrPtr->addTxIO( txioIter->second, isZeroConf);
                  doAddLedgerEntry = true;
               }
               else
               {
                  if(txioIter->second.hasTxOutInMain()) // ...but we already have one
                     continue;

                  // If we got here, we have an in-blockchain TxOut that is 
                  // replacing a zero-conf txOut.  Reset the txio to have 
                  // only this real TxOut, blank out the ZC TxOut.  And the addr 
                  // relevantTxIOPtrs_ does not have this yet so it needs 
                  // to be added (it's already part of the relevantTxIOPtrsZC_
                  // but that will be removed)
                  txioIter->second.setTxOut(tx.getTxRef(), iout);
                  thisAddrPtr->addTxIO( txioIter->second, isZeroConf);
                  doAddLedgerEntry = true;
               }
            }
            else
            {
               // TxIO is not in the map yet -- create and add it
               TxIOPair newTxio;
               if(isZeroConf)
                  newTxio.setTxOutZC(&tx, iout);
               else
                  newTxio.setTxOut(tx.getTxRef(), iout);
   
               pair<OutPoint, TxIOPair> toBeInserted(outpt, newTxio);
               txioIter = txioMap_.insert(toBeInserted).first;
               thisAddrPtr->addTxIO( txioIter->second, isZeroConf);
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
               LedgerEntry newLedger(addr20, 
                                     thisVal, 
                                     blknum, 
                                     tx.getThisHash(), 
                                     iout,
                                     txtime,
                                     isCoinbaseTx, // input was coinbase/generation
                                     false,   // sentToSelf meaningless for addr ledger
                                     false);  // we don't actually know
               thisAddrPtr->addLedgerEntry(newLedger, isZeroConf);
            }
            // Check if this is the first time we've seen this
            if(thisAddrPtr->getFirstTimestamp() == 0)
            {
               thisAddrPtr->setFirstBlockNum( blknum );
               thisAddrPtr->setFirstTimestamp( txtime );
            }
            // Update last seen on the network
            thisAddrPtr->setLastTimestamp(txtime);
            thisAddrPtr->setLastBlockNum(blknum);
         }
      } // loop over TxOuts

   //} // loop over all wallet addresses

   bool allTxOutIsOurs = true;
   bool anyTxOutIsOurs = false;
   for(int i=0; i<tx.getNumTxOut(); i++)
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
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + tx.getTxInOffset(iin));

      if(op.getTxHashRef() == BtcUtils::EmptyHash_)
         isCoinbaseTx = true;

      if(txioMap_.find(op) != txioMap_.end())
      {
         anyTxInIsOurs = true;
         totalValue -= txioMap_[op].getValue();
      }
   }


   // TxOuts are a little more complicated, because we have to process each
   // different type separately.  Nonetheless, 99% of transactions use the
   // 25-byte repr which is ridiculously fast
   HashString addr20(20);
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      static uint8_t scriptLenFirstByte;

      uint8_t const * ptr = txStartPtr + tx.getTxOutOffset(iout);
      scriptLenFirstByte = *(uint8_t*)(ptr+8);
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         addr20.copyFrom(ptr+12, 20);
         if( hasScrAddr(addr20) )
            totalValue += READ_UINT64_LE(ptr);
         else
            allTxOutIsOurs = false;
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         BtcUtils::getHash160_NoSafetyCheck(ptr+10, 65, addr20);
         if( hasScrAddr(addr20) )
            totalValue += READ_UINT64_LE(ptr);
         else
            allTxOutIsOurs = false;
      }
      else
         allTxOutIsOurs = false;
   }


   bool isSentToSelf = (anyTxInIsOurs && allTxOutIsOurs);

   if( !anyTxInIsOurs && totalValue==0 )
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
   Tx theTx = txref.getTxCopy();
   return calcLedgerEntryForTx(theTx);
}

////////////////////////////////////////////////////////////////////////////////
LedgerEntry BtcWallet::calcLedgerEntryForTxStr(BinaryData txStr)
{
   Tx tx(txStr);
   return calcLedgerEntryForTx(tx);
}


////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearBlkData(void)
{
   relevantTxIOPtrs_.clear();
   relevantTxIOPtrsZC_.clear();
   ledger_.clear();
   ledgerZC_.clear();
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearBlkData(void)
{
   txioMap_.clear();
   ledgerAllAddr_.clear();
   ledgerAllAddrZC_.clear();
   nonStdTxioMap_.clear();
   nonStdUnspentOutPoints_.clear();

   for(uint32_t a=0; a<addrPtrVect_.size(); a++)
      addrPtrVect_[a]->clearBlkData();
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
   TxOut txout = tx.getTxOut(txoutidx);
   int findIdx = txout.getScriptRef().find(thisAddr.getScrAddr());
   if(findIdx > -1)
   {
      LOGERR << "ALERT:  Found non-standard transaction referencing";
      LOGERR << "        an address in your wallet.  There is no way";
      LOGERR << "        for this program to determine if you can";
      LOGERR << "        spend these BTC or not.  Please email the";
      LOGERR << "        following information to etotheipi@gmail.com";
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
      pair< map<OutPoint, TxIOPair>::iterator, bool> insResult;
      pair<OutPoint, TxIOPair> toBeInserted(outpt, TxIOPair(tx.getTxRef(),txoutidx));
      insResult = nonStdTxioMap_.insert(toBeInserted);
      //insResult = txioMap_.insert(toBeInserted);
   }

}

////////////////////////////////////////////////////////////////////////////////
//uint64_t BtcWallet::getBalance(bool blockchainOnly)

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getSpendableBalance(uint32_t currBlk)
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isSpendable(currBlk))
         balance += iter->second.getValue();      
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getUnconfirmedBalance(uint32_t currBlk)
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isMineButUnconfirmed(currBlk))
         balance += iter->second.getValue();      
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getFullBalance(void)
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isUnspent())
         balance += iter->second.getValue();      
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getSpendableTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      TxIOPair & txio = iter->second;
      if(txio.isSpendable(blkNum))
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back(UnspentTxOut(txout, blkNum) );
      }
   }
   return utxoList;
}


////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcWallet::getFullTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      TxIOPair & txio = iter->second;
      if(txio.isUnspent())
      {
         TxOut txout = txio.getTxOut();
         utxoList.push_back(UnspentTxOut(txout, blkNum) );
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
void BtcWallet::sortLedger(void)
{
   sort(ledgerAllAddr_.begin(), ledgerAllAddr_.end());
}



////////////////////////////////////////////////////////////////////////////////
bool BtcWallet::isOutPointMine(HashString const & hsh, uint32_t idx)
{
   OutPoint op(hsh, idx);
   return (txioMap_.find(op)!=txioMap_.end());
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintLedger(void)
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
vector<AddressBookEntry> BtcWallet::createAddressBook(void)
{
   SCOPED_TIMER("createAddressBook");
   // Collect all data into a map -- later converted to vector and sort it
   map<HashString, AddressBookEntry> sentToMap;
   set<HashString> allTxList;
   set<HashString> perTxAddrSet;

   // Go through all TxIO for this wallet, collect outgoing transactions
   map<OutPoint, TxIOPair>::iterator txioIter;
   for(txioIter  = txioMap_.begin();  
       txioIter != txioMap_.end();  
       txioIter++)
   {
      TxIOPair & txio = txioIter->second;

      // It's only outgoing if it has a TxIn
      if( !txio.hasTxIn() )
         continue;

      Tx thisTx = txio.getTxRefOfInput().getTxCopy();
      HashString txHash = thisTx.getThisHash();

      if(allTxList.count(txHash) > 0)
         continue;
      else
         allTxList.insert(txHash);


      // Iterate over all TxOut in this Tx for recipients
      perTxAddrSet.clear();
      for(uint32_t iout=0; iout<thisTx.getNumTxOut(); iout++)
      {
         HashString addr160 = thisTx.getTxOut(iout).getRecipientAddr();

         // Skip this address if it's in our wallet (usually change addr)
         if( hasScrAddr(addr160) || perTxAddrSet.count(addr160)>0)
            continue; 

         // It's someone else's address for sure, add it to the map if necessary
         if(sentToMap.count(addr160)==0)
            sentToMap[addr160] = AddressBookEntry(addr160);

         sentToMap[addr160].addTx(thisTx);
         perTxAddrSet.insert(addr160);
      }
      
   }



   vector<AddressBookEntry> outputVect;
   map<HashString, AddressBookEntry>::iterator mapIter;
   for(mapIter  = sentToMap.begin();
       mapIter != sentToMap.end();
       mapIter++)
   {
      outputVect.push_back(mapIter->second);
   }

   sort(outputVect.begin(), outputVect.end());
   return outputVect;
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start BlockDataManager_LevelDB methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::BlockDataManager_LevelDB(void) : 
      totalBlockchainBytes_(0),
      endOfPrevLastBlock_(0),
      topBlockPtr_(NULL),
      genBlockPtr_(NULL),
      lastBlockWasReorg_(false),
      isInitialized_(false),
      GenesisHash_(0),
      GenesisTxHash_(0),
      MagicBytes_(0),
      allScannedUpToBlk_(0)
{
   headerMap_.clear();
   headerDB_ = NULL;
   txHintDB_ = NULL;
   transientDB_ = NULL;
   isNetParamsSet_ = false;
   isBlkParamsSet_ = false;
   isLevelDBSet_ = false;

   zeroConfRawTxList_.clear();
   zeroConfMap_.clear();
   zcEnabled_ = false;
   zcFilename_ = string("");

   headersByHeight_.clear();
   blkFileList_.clear();
   previouslyValidBlockHeaderPtrs_.clear();
   orphanChainStartBlocks_.clear();
}

/////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::~BlockDataManager_LevelDB(void)
{
   set<BtcWallet*>::iterator iter;
   for(iter  = registeredWallets_.begin();
       iter != registeredWallets_.end();
       iter++)
   {
      delete *iter;
   }
}

/////////////////////////////////////////////////////////////////////////////
// We must set the network-specific data for this blockchain
//
// bdm.SetBtcNetworkParams( READHEX(MAINNET_GENESIS_HASH_HEX),
//                          READHEX(MAINNET_GENESIS_TX_HASH_HEX),
//                          READHEX(MAINNET_MAGIC_BYTES));
//
// The above call will work 
void BlockDataManager_LevelDB::SetBtcNetworkParams(
                                    BinaryData const & GenHash,
                                    BinaryData const & GenTxHash,
                                    BinaryData const & MagicBytes)
{
   PDEBUG("SetBtcNetworkParams");
   GenesisHash_.copyFrom(GenHash);
   GenesisTxHash_.copyFrom(GenTxHash);
   MagicBytes_.copyFrom(MagicBytes);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SetLevelDBPaths(string headerPath,
                                                string txHintPath,
                                                string transientPath)
{
   SCOPED_TIMER("SetLevelDBPaths");
   headerPath_ = headerPath;
   txHintPath_ = txHintPath;

   leveldb::Status stat;

   // Header databse
   leveldb::Options opts1;
   opts1.create_if_missing = true;
   stat = leveldb::DB::Open(opts1, headerPath_.c_str(), &headerDB_);
   leveldb::ldbCheckStatus(stat);

   // TxRef database
   leveldb::Options opts2;
   opts2.create_if_missing = true;
   stat = leveldb::DB::Open(opts2, txHintPath_.c_str(), &txHintDB_);
   leveldb::ldbCheckStatus(stat);

   // Registered addr/tx database
   leveldb::Options opts3;
   opts3.create_if_missing = true;
   stat = leveldb::DB::Open(opts3, transientPath_.c_str(), &transientDB_);
   leveldb::ldbCheckStatus(stat);


   isLevelDBSet_ = true;
}



/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SetHomeDirLocation(string homeDir)
{
   // This will eventually be used to store blocks/DB
   PDEBUG("SetHomeDirLocation");
   armoryHomeDir_ = homeDir; 
}

/////////////////////////////////////////////////////////////////////////////
// Bitcoin-Qt/bitcoind 0.8+ changed the location and naming convention for 
// the blkXXXX.dat files.  The first block file use to be:
//
//    ~/.bitcoin/blk0001.dat   
//
// Now it has been changed to:
//
//    ~/.bitcoin/blocks/blk00000.dat   
//
// In addition to base dir, also need the number of digits and start index
//
bool BlockDataManager_LevelDB::SetBlkFileLocation(string   blkdir,
                                                  uint32_t blkdigits,
                                                  uint32_t blkstartidx,
                                                  uint64_t cacheSize)
{
   SCOPED_TIMER("SetBlkFileLocation");
   blkFileDir_    = blkdir; 
   blkFileDigits_ = blkdigits; 
   blkFileStart_  = blkstartidx; 
   isBlkParamsSet_ = true;


   // Next thing we need to do is find all the blk000X.dat files.
   // BtcUtils::GetFileSize uses only ifstreams, and thus should be
   // able to determine if a file exists in an OS-independent way.
   numBlkFiles_=0;
   totalBlockchainBytes_ = 0;
   blkFileList_.clear();

   while(numBlkFiles_ < UINT16_MAX)
   {
      string path = BtcUtils::getBlkFilename(blkFileDir_,
                                             blkFileDigits_, 
                                             numBlkFiles_+blkFileStart_);
      numBlkFiles_++;
      if(BtcUtils::GetFileSize(path) == FILE_DOES_NOT_EXIST)
         break;

      blkFileList_.push_back(string(path));
      totalBlockchainBytes_ += globalCache.openFile(numBlkFiles_-1, path);
   }
   numBlkFiles_--;

   if(numBlkFiles_!=UINT16_MAX)
      LOGERR << "Highest blkXXXX.dat file: " << numBlkFiles_;
   else
      LOGERR << "Error finding blockchain files (blkXXXX.dat)";

   return (numBlkFiles_!=UINT16_MAX);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SelectNetwork(string netName)
{
   if(netName.compare("Main") == 0)
   {
      SetBtcNetworkParams( READHEX(MAINNET_GENESIS_HASH_HEX),
                           READHEX(MAINNET_GENESIS_TX_HASH_HEX),
                           READHEX(MAINNET_MAGIC_BYTES)         );
   }
   else if(netName.compare("Test") == 0)
   {
      SetBtcNetworkParams( READHEX(TESTNET_GENESIS_HASH_HEX),
                           READHEX(TESTNET_GENESIS_TX_HASH_HEX),
                           READHEX(TESTNET_MAGIC_BYTES)         );
   }
   else
      LOGERR << "ERROR: Unrecognized network name";

   isNetParamsSet_ = true;
}



/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::checkLdbStatus(leveldb::Status stat)
{
   if( stat.ok() )
      return true;

   LOGERR << "***LevelDB Error: " << stat.ToString();
   return false;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::initializeDBInterface(ARMORY_DB_TYPE dbtype,
                                                     DB_PRUNE_TYPE  prtype)
{
   SCOPED_TIMER("initializeDBInterface");
   if(!isBlkParamsSet_ || !isLevelDBSet_)
   {
      LOGERR << "Cannot sync DB until blkfile and LevelDB paths are set. ";
      return false;
   }


   iface_->openDatabases(blkFileDir_, 
                         GenesisHash_, 
                         GenesisTxHash_, 
                         MagicBytes_,
                         dbtype, 
                         prtype);

   // (1) Read all headers from the HEADERS DB
   headerMap_.clear();
   map<HashString, StoredHeader> sbhMap;
   iface_->readAllHeaders(headerMap_, sbhMap);

   // Organize them into the longest chain
   organizeChain(true);

   // Now go through and check that the stored headers match the reorganized
   uint32_t topBlockDB = getTopBlockHeight();
   TIMER_START("initializeDBInterface::checkAllHeaders");
   for(uint32_t i=0; i<=headersByHeight_.size(); i++)
   {
      // Go through all valid headers and make sure they are stored correctly
      BinaryDataRef headHash = headersByHeight_[i]->getThisHashRef();
      StoredHeader & sbh = sbhMap[headHash];
      if(!sbh.isMainBranch_)
      {
         LOGWARN << "StoredHeader was not properly marked as valid";
         LOGWARN << "(hgt, dup) = (" << sbh.blockHeight_ << ", " 
                 << sbh.duplicateID_ << ")";
         sbh.isMainBranch_ = true;
         iface_->putStoredHeader(sbh, false);
      }
      iface_->setValidDupIDForHeight(sbh.duplicateID_);
   }
   TIMER_STOP("initializeDBInterface::checkAllHeaders");

}


////////////////////////////////////////////////////////////////////////////////
// The name of this function reflects that we are going to implement headers-
// first "verification."  Rather, we are going to organize the chain of headers
// before we add any blocks, and then only add blocks that are on the main 
// chain.  Return false if these headers induced a reorg.
bool BlockDataManager_LevelDB::addHeadersFirst(BinaryDataRef rawHeader)
{
   vector<BinaryData> toAdd(1);
   toAdd[0] = rawHeader.copy();
   return addHeadersFirst(toAdd);
}

////////////////////////////////////////////////////////////////////////////////
// Add the headers to the DB, which is required before putting raw blocks.
// Can only put raw blocks when we know their height and dupID.  After we 
// put the headers, then we put raw blocks.  Then we go through the valid
// headers and applyToDB the raw blocks.
bool BlockDataManager_LevelDB::addHeadersFirst(vector<StoredHeader> const & headVect)
{
   vector<BlockHeader*> headersToDB;
   headersToDB.reserve(headVect.size());
   for(uint32_t h=0; h<headVect.size(); h++)
   {
      pair<HashString, BlockHeader>                      bhInputPair;
      pair<map<HashString, BlockHeader>::iterator, bool> bhInsResult;

      // Actually insert it.  Take note of whether it was already there.
      bhInputPair.second.unserialize(headVect[h]);
      bhInputPair.first = bhInputPair.second.getThisHash();
      bhInsResult       = headerMap_.insert(bhInputPair);

      //if(bhInsResult.second) // true means didn't exist before
      headersToDB.push_back(&(bhInsResult.first->second));
   }

   // Organize the chain with the new headers, note whether a reorg occurred
   bool prevTopBlockStillValid = organizeChain();

   // Add the main-branch headers to the DB.  We will handle reorg ops later.
   // The batching is safe since we never write multiple blocks at the same hgt
   iface_->startBatch(HEADERS);
   for(uint32_t h=0; h<headersToDB.size(); h++)
   {
      if(!headersToDB[i]->isMainBranch())
         continue;

      StoredHeader sbh;
      sbh.CreateFromBlockHeader(*headersToDB[i]);
      uint8_t dup = iface_->putBareHeader(sbh);
      headersToDB[i]->setDuplicateID(dup);
   }
   iface_->commitBatch(HEADERS);

   // We need to add the non-main-branch headers, too.  
   for(uint32_t h=0; h<headersToDB.size(); h++)
   {
      if(headersToDB[i]->isMainBranch())
         continue;

      StoredHeader sbh;
      sbh.CreateFromBlockHeader(*headersToDB[i]);
      uint8_t dup = iface_->putBareHeader(sbh);
      headersToDB[i]->setDuplicateID(dup);
   }
   return prevTopBlockStillValid;
}




   // 
   // This is an ancient first shot at some DB code... it doesn't match 
   // any of the infrastructure we have now, but I left it in case I need
   // to go back and look at my thought process back then.
   /*
   // (2) Now let's make sure the blk files are the same ones used to construct
   //     these databases, originally.
   //uint32_t topBlockSyncd = ldbSyncHeightWithBlkFiles();

   TIMER_START("findHighestSyncBlock");
   // Check every 1000th block header starting from the top, working down
   uint32_t syncStepSize = 1000;
   uint32_t top = getTopBlockHeight();
   uint32_t topBlockSyncd = top;
   bool prevIterSyncd = false;
   for(int32_t h=top; h>=0; h-=syncStepSize)
   {
      BinaryData & dbCopy   = getHeaderByHeight(h)->serialize();
      BinaryData   diskCopy = headPtr->getBlockFilePtr().getDataCopy();
      if(dbCopy == diskCopy)
      {
         if(prevIterSyncd)
            topBlockSyncd = h;
         prevIterSyncd = true;
      }
      else if(prevIterSyncd)
         prevIterSyncd = false;
   }

   if(topBlockSyncd <= syncStepSize)
      topBlockSyncd = 0;

   TIMER_STOP("findHighestSyncBlock");
   LOGERR << "TopHeaderInDB: "           << topBlockDB << ", "
          << "TopHeaderFoundInBlkFile: " << topBlockSyncd;
  

   // I know I just found where the synchronization diverged... but really,
   // it's fairly complicated to do partial rebuilds.  If there's ANY 
   // divergence, I'll just do a full rebuild.
   if(topBlockDB != topBlockSyncd)
   {
      // (3a) Rebuild databases from blockchain files
      rebuildDatabases();
   }
   else
   {
      // (3b) Simply fetch all updates to the blockchain files since last exit
      // We have to make sure our next readBlkFileUpdate starts at the correct 
      // place (one block past the current top block).
      BlockHeader * bhptr = &getTopBlockHeader();
      uint32_t topBlkSize  = bhptr->getBlockSize();
      uint32_t topBlkStart = bhptr->getBlockFilePtr()->getStartByte();
      lastBlkFileBytes_ = topBlkStart + topBlkSize; // magic bytes & blk sz
      lastTopBlock_ = topBlockDB;
   }

   //updateRegisteredAddresses(topBlock - 12);
   //readBlkFileUpdate();
}
*/



// Same as above... this code is ancient!
/*
void readTransientDB(void)
{
   // All the transient data from the last time Armory was running:
   //    Registered Adddresses (and to what block they've been sync'd)
   //    Registered Tx's (all blockchain tx relevant to this wallet)
   //    Registered OutPoints (basically, the UTXO set for these wallets)
   //    Registered OutPoints (basically, the UTXO set for these wallets)
   leveldb::Iterator* it;
   //it = transientDB_->NewIterator(leveldb::ReadOptions());
   BinaryData entryType(4);
   BinaryData entryKey;
   BinaryData ADDR(string("ADDR"));  // Registered Addresses
   BinaryData RGTX(string("RGTX"));  // Registered Transactions
   BinaryData RGOP(string("RGOP"));  // Registered OutPoints
   BinaryData ZCTX(string("ZCTX"));  // Zero-confirmation transactions

   registeredScrAddrMap_.clear();
   registeredTxList_.clear();
   registeredTxSet_.clear();
   registeredOutPoints_.clear();

   for(it->SeekToFirst(); it->Valid(); it->Next())
   {
      
      keyPtr  = (uint8_t const *)(it->key().data());
      dataPtr = (uint8_t const *)(it->value().data());
   
      uint32_t keySz  = (uint32_t)(it->key().size());
      uint32_t dataSz = (uint32_t)(it->value().size());
   
      entryType.copyFrom(keyPtr + 0, 4);
      if(keySz>4)
         entryKey.copyFrom(keyPtr+4, keySz-4);

      if(entryType==ADDR)
      {
         // REGISTERED ADDRESS   { "ADDR"|HASH160 --> BLKCREATED4|ALREADYSCANNED4 }
         if( entryKey.getSize() != 20 )
            continue;

         // Will overwrite the blkCreated and alreadyScannedUpToBlk_ vars on
         // addresses that were registered before this was called.
         RegisteredAddress ra(entryKey, READ_UINT32_LE((dataPtr+0)));
         ra.alreadyScannedUpToBlk_ = READ_UINT32_LE((dataPtr+4));
         registeredScrAddrMap_[entryKey] = ra;
      }
      else if(entryType==RGTX)
      {
         // REGISTERED TRANSACTION  { "RGTX"|TXHASH --> BLKNUM4|TXINDEX4 }
         if( entryKey.getSize() != 32 )
            continue;

         if(registeredTxSet_.insert(entryKey).second == true)
         {
            RegisteredTx rtx(entryKey, READ_UINT32_LE(dataPtr+0), READ_UINT32_LE(dataPtr+4));
            registeredTxList_.push_back(rtx);
         }
         
      }
      else if(entryType==RGOP)
      {
         // REGISTERED OUTPOINT (list)  { "RGOP"|OUTPOINT36 --> "" }
         registeredOutPoints_.insert(OutPoint(entryKey));
      }
      else if(entryType==ZCTX)
      {
         // ZERO-CONF TRANSACTION   { "ZCTX"|TXHASH32 --> TXTIME8|RAWTX }
         if( entryKey.getSize() != 32 )
            continue;

         uint64_t   txtime = READ_UINT64_LE(dataPtr+0);
         BinaryData rawTx(dataPtr+8, dataSz-8);
         if( BtcUtils::getHash256(rawTx) != entryKey)
         {
            LOGERR << "WARNING:  Zero-conf tx does not match its own hash!";
            continue;
         }

         zeroConfMap_[entryKey] = ZeroConfData();
         ZeroConfData & zc = zeroConfMap_[entryKey];

         zc.iter_ = zeroConfRawTxList_.insert(zeroConfRawTxList_.end(), rawTx);
         zc.txobj_.unserialize(*(zc.iter_));
         zc.txtime_ = txtime;
      }
   }

   // We assume that wallets have already been registered with the BDM.  If 
   // all addresses in the wallet are the same as they were before the last 
   // shutdown, then our minimum alreadyScannedUpToBlk should be the current
   // top block.  Otherwise, we get zero and know we have to rescan
   allScannedUpToBlk_ = UINT32_MAX;
   map<HashString,RegisteredAddress>::iterator iter;
   for(iter  = registeredScrAddrMap_.begin(); 
       iter != registeredScrAddrMap_.end(); 
       iter++)
   {
      alreadyBlk = min(alreadyBlk, iter->second.alreadyScannedUpToBlk_);
   }
}
*/


/////////////////////////////////////////////////////////////////////////////
// We may, at a later time try to optimize the amount of the blockchain 
// being rescanned.  But for now, if the top DB header is not sync'd with
// the blkfiles, we'll just rebuild everything (it's unlikely we'll save 
// too much time in the rare cases this is needed, and the partial rebuild
// will be much more reliable).  Nonetheless, we could theoretically 
/*
bool BlockDataManager_LevelDB::rebuildDatabases(uint32_t startAtBlk)
{
   SCOPED_TIMER("rebuildDatabases");
   
   if(!isBlkParamsSet_ || !isLevelDBSet_)
   {
      LOGERR << "Cannot rebuild databases until blockfile params and LevelDB"
             << "paths are set. ";
      return false;
   }

   
   // For now, if we
   if(startAtBlk!=0)
   {
      LOGERR << "RebuildDB: Partial rebuilds not supported yet.  "
             << "Doing full rebuild";
   }

   delete headerDB_;  
   delete txHintDB_;  

   //leveldb::DestroyDB(headerPath_);
   //leveldb::DestroyDB(txHintPath_);
   isLevelDBSet_ = false;

   // The rebuilt DBs will go in the same place, but they'll be referencing
   // the correct blkfiles this time.
   //SetLevelDBPaths(headerPath_, txHintPath_);
   headerMap_.clear();

   lastTopBlock_ = 0;
   numBlkFiles_ = 0;
   //lastBlkFileBytes_ = 0;
   totalBlockchainBytes_ = 0;
   bytesReadSoFar_ = 0;
   blocksReadSoFar_ = 0;
   filesReadSoFar_ = 0;
   
   // Modified from RAM implementation to write scanned data directly to DB
   parseEntireBlockchain();
}
*/



/////////////////////////////////////////////////////////////////////////////
// The only way to "create" a BDM is with this method, which creates it
// if one doesn't exist yet, or returns a reference to the only one
// that will ever exist
BlockDataManager_LevelDB & BlockDataManager_LevelDB::GetInstance(void) 
{
   static bool bdmCreatedYet_ = false;
   if( !bdmCreatedYet_ )
   {
      theOnlyBDM_ = new BlockDataManager_LevelDB;
      bdmCreatedYet_ = true;
      iface_ = LevelDBWrapper::GetInterfacePtr();
   }
   return (*theOnlyBDM_);
}




/////////////////////////////////////////////////////////////////////////////
/*
void BlockDataManager_LevelDB::insertRegOutPoint(OutPoint& op) 
{

   BinaryWriter keyWriter(4+32);
   keyWriter.put_BinaryData( string("RGOP").data(), 4);
   keyWriter.put_BinaryData( op.serialize() );

   leveldb::Slice key(keyWriter.ToString());
   leveldb::Slice val(string(""));
      
   // Put it in the database
   leveldb::Status stat = db->Put(leveldb::WriteOptions(), key, val);

   // ...and then add it to the RAM map
   registeredOutPoints_.insert(op);
}
*/


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::Reset(void)
{
   SCOPED_TIMER("BDM::Reset");

   // Clear out all the "real" data in the blkfile
   blkFileDir_ = "";
   headerMap_.clear();
   //txHintMap_.clear();

   // These are not used at the moment, but we should clear them anyway
   blkFileList_.clear();


   // These should be set after the blockchain is organized
   headersByHeight_.clear();
   topBlockPtr_ = NULL;
   genBlockPtr_ = NULL;

   // Reorganization details
   lastBlockWasReorg_ = false;
   reorgBranchPoint_ = NULL;
   txJustInvalidated_.clear();
   txJustAffected_.clear();

   // Reset orphan chains
   previouslyValidBlockHeaderPtrs_.clear();
   orphanChainStartBlocks_.clear();
   
   totalBlockchainBytes_ = 0;
   endOfPrevLastBlock_ = 0;

   isInitialized_ = false;

   zcEnabled_ = false;
   zcFilename_ = "";
   zeroConfMap_.clear();
   zeroConfRawTxList_.clear();

   // Clear out any of the registered tx data we have collected so far.
   // Doesn't take any time to recollect if it we have to rescan, anyway.

   registeredWallets_.clear();
   registeredScrAddrMap_.clear();
   registeredTxSet_.clear();
   registeredTxList_.clear(); 
   registeredOutPoints_.clear(); 
   allScannedUpToBlk_ = 0;
}



/////////////////////////////////////////////////////////////////////////////
int32_t BlockDataManager_LevelDB::getNumConfirmations(HashString txHash)
{
   TxRef txrefobj = getTxRefByHash(txHash);
   if(txrefobj.isNull())
      return TX_NOT_EXIST;
   else
   {
      if(txrefobj->getHeaderPtr() == NULL)
         return TX_0_UNCONFIRMED; 
      else
      { 
         BlockHeader & txbh = *(txrefobj->getHeaderPtr());
         if(!txbh.isMainBranch())
            return TX_OFF_MAIN_BRANCH;

         int32_t txBlockHeight  = txbh.getBlockHeight();
         int32_t topBlockHeight = getTopBlockHeight();
         return  topBlockHeight - txBlockHeight + 1;
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
BlockHeader & BlockDataManager_LevelDB::getTopBlockHeader(void) 
{
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &(getGenesisBlock());
   return *topBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
BlockHeader & BlockDataManager_LevelDB::getGenesisBlock(void) 
{
   if(genBlockPtr_ == NULL)
      genBlockPtr_ = &(headerMap_[GenesisHash_]);
   return *genBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
BlockHeader * BlockDataManager_LevelDB::getHeaderByHeight(int index)
{
   if( index<0 || index>=(int)headersByHeight_.size())
      return NULL;
   else
      return headersByHeight_[index];
}


/////////////////////////////////////////////////////////////////////////////
// The most common access method is to get a block by its hash
BlockHeader * BlockDataManager_LevelDB::getHeaderByHash(HashString const & blkHash)
{
   map<HashString, BlockHeader>::iterator it = headerMap_.find(blkHash);
   if(it==headerMap_.end())
      return NULL;
   else
      return &(it->second);
}



/////////////////////////////////////////////////////////////////////////////
TxRef BlockDataManager_LevelDB::getTxRefByHash(HashString const & txhash) 
{
   return iface_->getTxRef(txhash);

   //typedef multimap<HashString,TxRef>::iterator hintMapIter;

   //static HashString hash4(4);
   //hash4.copyFrom(txhash.getPtr(), 4);
   //pair<hintMapIter, hintMapIter> eqRange = txHintMap_.equal_range(hash4);

   //if(eqRange.first==eqRange.second)
      //return NULL;
   //else
   //{
      //hintMapIter iter;
      //for( iter = eqRange.first; iter != eqRange.second; iter++ )
      //{
         //if(iter->second.getThisHash() == txhash)
            //return &(iter->second);
      //}

      //// If we got here, we have some matching prefixes, but no tx that
      //// match the full requested tx-hash
      //return NULL;
   //}
}

/////////////////////////////////////////////////////////////////////////////
// Returns a pointer to the TxRef as it resides in the multimap node
// There should only ever be exactly one copy
// NOTE:  This method was created because multimaps allow duplicate 
//        elements (which are nodes with the same 4-byte prefix). 
//        However, we don't want to allow two identical transactions
//        at different locations in the blkfile lead to duplicate
//        multimap nodes.  
//
//        i.e. transactions with same 4-byte prefix -- OK
//             transactions with same 32-byte hash  -- NOT OK
/* I don't think this is needed anymore after the LevelDB upgrade
TxRef * BlockDataManager_LevelDB::insertTxRef(HashString const & txHash, 
                                              FileDataPtr & fdp,
                                              BlockHeader * bhptr)
{
   static multimap<HashString, TxRef>::iterator lowerBound;
   static multimap<HashString, TxRef>::iterator upperBound;
   static pair<HashString, TxRef>               txInputPair;
   static multimap<HashString, TxRef>::iterator txInsResult;

   txInputPair.first.copyFrom(txHash.getPtr(), 4);
   lowerBound = txHintMap_.lower_bound(txInputPair.first);
   upperBound = txHintMap_.upper_bound(txInputPair.first);

   bool needInsert = false;
   if(lowerBound!=upperBound)
   {
      multimap<HashString, TxRef>::iterator iter;
      for(iter = lowerBound; iter != upperBound; iter++)
         if(iter->second.getThisHash() == txHash)
            return &(iter->second);
   }

   // If we got here, the tx doesn't exist in the multimap yet,
   // and lowerBound is an appropriate hint for inserting the TxRef
   txInputPair.second.setBlkFilePtr(fdp);
   txInputPair.second.setHeaderPtr(bhptr);
   txInsResult = txHintMap_.insert(lowerBound, txInputPair);
   return &(txInsResult->second);
}
*/

/////////////////////////////////////////////////////////////////////////////
Tx BlockDataManager_LevelDB::getTxByHash(HashString const & txhash)
{

   TxRef txrefobj = getTxRefByHash(txhash);

   if(!txrefobj.isNull())
      return txrefobj->getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      map<HashString, ZeroConfData>::const_iterator iter = zeroConfMap_.find(txhash);
      if(iter==zeroConfMap_.end())
         return Tx();
      else
         return iter->second.txobj_;
   }
}


/////////////////////////////////////////////////////////////////////////////
int BlockDataManager_LevelDB::hasTxWithHash(BinaryData const & txhash)
{
   if(getTxRefByHash(txhash)==NULL)
   {
      if(zeroConfMap_.find(txhash)==zeroConfMap_.end())
         return 0;  // No tx at all
      else
         return 1;  // Zero-conf tx
   }
   else
      return 2;     // In the blockchain already
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::hasHeaderWithHash(HashString const & txhash) const
{
   return (headerMap_.find(txhash) != headerMap_.end());
}

/////////////////////////////////////////////////////////////////////////////
vector<BlockHeader*> BlockDataManager_LevelDB::prefixSearchHeaders(BinaryData const & searchStr)
{
   vector<BlockHeader*> outList(0);
   uint32_t lenSearch = searchStr.getSize();
   if(lenSearch < 2)
      return outList;  // don't search unless we have at least two bytes

   BinaryData searchLow(32);
   BinaryData searchHigh(32);
   for(uint32_t i=0; i<lenSearch; i++)
   {
      searchLow[i]  = searchStr[i];
      searchHigh[i] = searchStr[i];
   }
   for(uint32_t i=lenSearch; i<32; i++)
   {
      searchLow[i]  = 0;
      searchHigh[i] = 255;
   }

   map<HashString, BlockHeader>::iterator iter;
   for(iter  = headerMap_.lower_bound(searchLow);
       iter != headerMap_.upper_bound(searchHigh);
       iter++)
   {
      outList.push_back(&(iter->second));
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
vector<TxRef*> BlockDataManager_LevelDB::prefixSearchTx(BinaryData const & searchStr)
{
   vector<TxRef*> outList(0);
   uint32_t lenSearch = searchStr.getSize();
   if(lenSearch < 2)
      return outList;  // don't search unless we have at least two bytes

   BinaryData searchLow(32);
   BinaryData searchHigh(32);
   for(uint32_t i=0; i<lenSearch; i++)
   {
      searchLow[i]  = searchStr[i];
      searchHigh[i] = searchStr[i];
   }
   for(uint32_t i=lenSearch; i<32; i++)
   {
      searchLow[i]  = 0;
      searchHigh[i] = 255;
   }

   BinaryData searchLow4  = searchLow.getSliceCopy(0,4);
   BinaryData searchHigh4 = searchHigh.getSliceCopy(0,4);
   multimap<HashString, TxRef>::iterator iter;
   for(iter  = txHintMap_.lower_bound(searchLow4);
       iter != txHintMap_.upper_bound(searchHigh4);
       iter++)
   {
      if(iter->second.getThisHash().startsWith(searchStr))
         outList.push_back(&(iter->second));
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
// Since the cpp code doesn't have full addresses (only 20-byte hashes),
// that's all we can search for.  
vector<BinaryData> BlockDataManager_LevelDB::prefixSearchAddress(BinaryData const & searchStr)
{
   // Actually, we can't even search for this, because we don't have a list
   // of addresses in the blockchain.  We could construct one, but it would
   // take up a lot of RAM (and time)... I will need to create a separate 
   // call to allow the caller to create a set<BinaryData> of addresses 
   // before calling this method
   return vector<BinaryData>(0);
}





/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerWallet(BtcWallet* wltPtr, bool wltIsNew)
{
   SCOPED_TIMER("registerWallet");

   // Check if the wallet is already registered
   if(registeredWallets_.find(wltPtr) != registeredWallets_.end())
      return false;

   // Add it to the list of wallets to watch
   registeredWallets_.insert(wltPtr);

   // Now add all the individual addresses from the wallet
   for(uint32_t i=0; i<wltPtr->getNumScrAddr(); i++)
   {
      // If this is a new wallet, the value of getFirstBlockNum is irrelevant
      ScrAddrObj & addr = wltPtr->getScrAddrByIndex(i);

      if(wltIsNew)
         registerNewAddress(addr.getScrAddr());
      else
         registerImportedAddress(addr.getScrAddr(), addr.getFirstBlockNum());
   }

   // We need to make sure the wallet can tell the BDM when an address is added
   wltPtr->setBdmPtr(this);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerAddress(HashString addr160, 
                                                bool addrIsNew,
                                                uint32_t firstBlk)
{
   SCOPED_TIMER("registerAddress");
   if(registeredScrAddrMap_.find(addr160) != registeredScrAddrMap_.end())
   {
      // Address is already registered.  Don't think there's anything to do 
      return false;
   }

   if(addrIsNew)
      firstBlk = getTopBlockHeight() + 1;

   registeredScrAddrMap_[addr160] = RegisteredAddress(addr160, firstBlk);
   allScannedUpToBlk_  = min(firstBlk, allScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerNewAddress(HashString addr160)
{
   SCOPED_TIMER("registerNewAddress");
   if(registeredScrAddrMap_.find(addr160) != registeredScrAddrMap_.end())
      return false;

   uint32_t currBlk = getTopBlockHeight();
   registeredScrAddrMap_[addr160] = RegisteredAddress(addr160, currBlk);

   // New address cannot affect allScannedUpToBlk_, so don't bother
   //allScannedUpToBlk_  = min(currBlk, allScannedUpToBlk_);
   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerImportedAddress(HashString addr160,
                                                    uint32_t createBlk)
{
   SCOPED_TIMER("registerImportedAddress");
   if(registeredScrAddrMap_.find(addr160) != registeredScrAddrMap_.end())
      return false;

   // In some cases we may have used UINT32_MAX to specify "don't know"
   if(createBlk==UINT32_MAX)
      createBlk = 0;

   registeredScrAddrMap_[addr160] = RegisteredAddress(addr160, createBlk);
   allScannedUpToBlk_ = min(createBlk, allScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::unregisterAddress(HashString addr160)
{
   SCOPED_TIMER("unregisterAddress");
   if(registeredScrAddrMap_.find(addr160) == registeredScrAddrMap_.end())
      return false;
   
   registeredScrAddrMap_.erase(addr160);
   allScannedUpToBlk_ = evalLowestBlockNextScan();
   return true;
}


/////////////////////////////////////////////////////////////////////////////
BtcWallet::~BtcWallet(void)
{
   if(bdmPtr_!=NULL)
      bdmPtr_->unregisterWallet(this);
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::evalLowestBlockNextScan(void)
{
   SCOPED_TIMER("evalLowestBlockNextScan");

   uint32_t lowestBlk = UINT32_MAX;
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredScrAddrMap_.begin();
       raIter != registeredScrAddrMap_.end();
       raIter++)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, raIter->second.alreadyScannedUpToBlk_);
   }
   return lowestBlk;
}

/////////////////////////////////////////////////////////////////////////////
// This method isn't really used yet...
uint32_t BlockDataManager_LevelDB::evalLowestAddressCreationBlock(void)
{
   SCOPED_TIMER("evalLowestAddressCreationBlock");

   uint32_t lowestBlk = UINT32_MAX;
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredScrAddrMap_.begin();
       raIter != registeredScrAddrMap_.end();
       raIter++)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, raIter->second.blkCreated_);
   }
   return lowestBlk;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::evalRescanIsRequired(void)
{
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   allScannedUpToBlk_ = evalLowestBlockNextScan();
   return (allScannedUpToBlk_ < getTopBlockHeight()+1);
}


/////////////////////////////////////////////////////////////////////////////
// This method needs to be callable from another thread.  Therefore, I don't
// seek an exact answer, instead just estimate it based on the last block, 
// and the set of currently-registered addresses.  The method called
// "evalRescanIsRequired()" answers a different question, and iterates 
// through the list of registered addresses, which may be changing in 
// another thread.  
bool BlockDataManager_LevelDB::isDirty( 
                              uint32_t numBlocksToBeConsideredDirty ) const
{
   if(!isInitialized_)
      return false;
   
   uint32_t numBlocksBehind = lastTopBlock_-allScannedUpToBlk_;
   return (numBlocksBehind > numBlocksToBeConsideredDirty);
  
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::numBlocksToRescan( BtcWallet & wlt,
                                                       uint32_t endBlk)
{
   SCOPED_TIMER("numBlocksToRescan");
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   uint32_t currNextBlk = getTopBlockHeight() + 1;
   endBlk = min(endBlk, currNextBlk);

   // If wallet is registered and current, no rescan necessary
   if(walletIsRegistered(wlt))
      return (endBlk - allScannedUpToBlk_);

   // The wallet isn't registered with the BDM, but there's a chance that 
   // each of its addresses are -- if any one is not, do rescan
   uint32_t maxAddrBehind = 0;
   for(uint32_t i=0; i<wlt.getNumScrAddr(); i++)
   {
      ScrAddrObj & addr = wlt.getScrAddrByIndex(i);

      // If any address is not registered, will have to do a full scan
      if(registeredScrAddrMap_.find(addr.getScrAddr()) == registeredScrAddrMap_.end())
         return endBlk;  // Gotta do a full rescan!

      RegisteredAddress & ra = registeredScrAddrMap_[addr.getScrAddr()];
      maxAddrBehind = max(maxAddrBehind, endBlk-ra.alreadyScannedUpToBlk_);
   }

   // If we got here, then all addr are already registered and current
   return maxAddrBehind;
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateRegisteredAddresses(uint32_t newTopBlk)
{
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredScrAddrMap_.begin();
       raIter != registeredScrAddrMap_.end();
       raIter++)
   {
      raIter->second.alreadyScannedUpToBlk_ = newTopBlk;
   }
   
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::resetRegisteredWallets(void)
{
   SCOPED_TIMER("resetRegisteredWallets");

   set<BtcWallet*>::iterator wltPtrIter;
   for(wltPtrIter  = registeredWallets_.begin();
       wltPtrIter != registeredWallets_.end();
       wltPtrIter++)
   {
      // I'm not sure if there's anything else to do
      // I think it's all encapsulated in this call!
      (*wltPtrIter)->clearBlkData();
   }

   // Reset all addresses to "new"
   updateRegisteredAddresses(0);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::walletIsRegistered(BtcWallet & wlt)
{
   return (registeredWallets_.find(&wlt)!=registeredWallets_.end());
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::addressIsRegistered(HashString addr160)
{
   return (registeredScrAddrMap_.find(addr160)!=registeredScrAddrMap_.end());
}



/////////////////////////////////////////////////////////////////////////////
// This method is now a hybrid of the original, Blockchain-in-RAM code,
// and the new mmap()-based blockchain operations.  The initial blockchain
// scan will look for wallet-relevant transactions, and keep track of what 
// blocks still need to be scanned given the registered wallets
// 
// Therefore, when we scan, we will first scan the registered tx list,
// then any raw blocks that haven't been filtered yet, then all the 
// zero-conf tx list.
//
// If the wallet contains any addresses that are not part of the prefiltered
// tx-hash-list, then the entire blockchain will have to be rescanned, anyway.
// It doesn't take any less time to search for one address than it does 
// all of them.
//
//
//  Some new notes on this method ...
//     We will ONLY scan transactions from the registeredTxList_
//
//     Therefore, we need to make sure that registeredTxList_ is
//     completely up-to-date FIRST. 
//
//     Then we can sort it and scanTx all of them with the wallet.
//
//     We need to scan from blocks X-->Y.  Assume X is 1000 and Y is 2000
//     If allScannedUpToBlk_==1500:
//
//     registeredAddrScan from 1500-->2000
//     sort registered list
//     scanTx all tx in registered list between 1000 and 2000
void BlockDataManager_LevelDB::scanBlockchainForTx(BtcWallet & myWallet,
                                                    uint32_t startBlknum,
                                                    uint32_t endBlknum)
{
   SCOPED_TIMER("scanBlockchainForTx");

   // The BDM knows the highest block to which ALL CURRENT REGISTERED ADDRESSES
   // are up-to-date in the registeredTxList_ list.  
   // If this wallet is not registered, it needs to be, before we start
   if(!walletIsRegistered(myWallet))
      registerWallet( &myWallet );

   
   // Check whether we can get everything we need from the registered tx list
   endBlknum = min(endBlknum, getTopBlockHeight()+1);
   uint32_t numRescan = numBlocksToRescan(myWallet, endBlknum);


   // This is the part that might take a while...
   rescanBlocks(allScannedUpToBlk_, endBlknum);

   allScannedUpToBlk_ = endBlknum;
   updateRegisteredAddresses(endBlknum);


   // *********************************************************************** //
   // Finally, walk through all the registered tx
   scanRegisteredTxForWallet(myWallet, startBlknum, endBlknum);

   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(myWallet);

}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rescanBlocks(uint32_t blk0, uint32_t blk1)
{
   // TODO:   I am assuming this will be too slow, but I will test/time it
   //         before making that conclusion:  perhaps pre-caching is enough
   //         to avoid complicating this to the level of parseEntireBlockchain
   // UPDATE: (3 months later) It appears to be working fine.  A full rescan
   //         using pre-caching as I have done seems to have no noticeable 
   //         impact on performance.  That means this code block could 
   //         probably be reused, and is fairly simple.
   SCOPED_TIMER("rescanBlocks");

   blk1 = min(blk1, getTopBlockHeight()+1);

   // Using the same file-writing hack to communicate progress to python
   string bfile = armoryHomeDir_ + string("/blkfiles.txt");
   if(blk1-blk0 > 10000 &&
      BtcUtils::GetFileSize(bfile) != FILE_DOES_NOT_EXIST)
   {
      remove(bfile.c_str());
   }

   /*
   TIMER_START("LoadProgress");
   bytesReadSoFar_ = 0;
   for(uint32_t h=blk0; h<blk1; h++)
   {
      BlockHeader & bhr = *(headersByHeight_[h]);
      vector<TxRef> const & txlist = bhr.getTxRefPtrList();

      bytesReadSoFar_ += bhr.getBlockSize();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         Tx thisTx = txlist[itx]->getTxCopy();
         registeredAddrScan(thisTx);
      }

         
      if( (h<120000 && h%10000==0) || (h>=120000 && h%1000==0) )
      {
         if(armoryHomeDir_.size() > 0)
         {
            ofstream topblks(bfile.c_str(), ios::app);
            double t = TIMER_READ_SEC("LoadProgress");
            topblks << bytesReadSoFar_ << " " 
                    << totalBlockchainBytes_ << " " 
                    << t << endl;
         }
      }
   }
   TIMER_STOP("LoadProgress");
   */

   BinaryData startKey = ARMDB.getBlkDataKey(blk0, 0);
   BinaryData endKey   = ARMDB.getBlkDataKey(blk1, 0);
   iface_->seekTo(BLKDATA, startKey);

   // Start scanning and timer
   TIMER_START("LoadProgress");

   do
   {
      StoredHeader sbh;
      iface_->readStoredBlockAtIter(sbh);
      uint32_t hgt = shb.blockHeight_;
      uint8_t  dup = shb.duplicateID_;
      if(blk0 > hgt || hgt >= blk1)
         break;

      if(dup != iface_->getValidDupIDForHeight(hgt))
         continue;

      applyBlockToDB(hgt, dup); 

      // Track the byte count 
      bytesReadSoFar_ += sbh.numBytes_;

      writeScanStatusFile(hgt, bfile, string("LoadProgress"));

   } while(advanceIterAndRead(BLKDATA, DB_PREFIX_TXDATA));

   TIMER_STOP("LoadProgress");
   

   allScannedUpToBlk_ = blk1;
   //updateRegisteredAddresses(blk1);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::writeScanStatusFile(uint32_t hgt, 
                                                   string bfile, 
                                                   string timerName)
{
   if( (hgt<120000 && hgt%10000==0) || (hgt>=120000 && hgt%1000==0) )
   {
      if(armoryHomeDir_.size() > 0)
      {
         ofstream topblks(bfile.c_str(), ios::app);
         double t = TIMER_READ_SEC(timerName);
         topblks << bytesReadSoFar_ << " " 
                 << totalBlockchainBytes_ << " " 
                 << t << endl;
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintRegisteredWallets(void)
{
   set<BtcWallet*>::iterator iter;
   for(iter  = registeredWallets_.begin(); 
       iter != registeredWallets_.end(); 
       iter++)
   {
      cout << "Wallet:";
      cout << "\tBalance: " << (*iter)->getFullBalance();
      cout << "\tNAddr:   " << (*iter)->getNumScrAddr();
      cout << "\tNTxio:   " << (*iter)->getTxIOMap().size();
      cout << "\tNLedg:   " << (*iter)->getTxLedger().size();
      cout << "\tNZC:     " << (*iter)->getZeroConfLedger().size() << endl;      
   }
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataManager_LevelDB::createNewWallet(void)
{
   BtcWallet* newWlt = new BtcWallet(this);
   registeredWallets_.insert(newWlt);  
   return newWlt;
}


/////////////////////////////////////////////////////////////////////////////
// This assumes that registeredTxList_ has already been populated from 
// the initial blockchain scan.  The blockchain contains millions of tx,
// but this list will at least 3 orders of magnitude smaller
void BlockDataManager_LevelDB::scanRegisteredTxForWallet( BtcWallet & wlt,
                                                           uint32_t blkStart,
                                                           uint32_t blkEnd)
{
   SCOPED_TIMER("scanRegisteredTxForWallet");

   // Make sure RegisteredTx objects have correct data, then sort.
   // TODO:  Why did I not need this with the MMAP blockchain?  Somehow
   //        I was able to sort correctly without this step, before...?
   list<RegisteredTx>::iterator txIter;
   for(txIter  = registeredTxList_.begin();
       txIter != registeredTxList_.end();
       txIter++)
   {
      if(txIter->txIndex_ > UINT32_MAX/2)
      {
         // The RegisteredTx was created before the chain was organized
         txIter->blkNum_ = txIter->txrefPtr_->getBlockHeight();
         txIter->txIndex_ = txIter->txrefPtr_->getBlockTxIndex();
      }
   }
   registeredTxList_.sort();

   ///// LOOP OVER ALL RELEVANT TX ////
   for(txIter  = registeredTxList_.begin();
       txIter != registeredTxList_.end();
       txIter++)
   {
      // Pull the tx from disk and check it for the supplied wallet
      Tx theTx = txIter->getTxCopy();
      if( !theTx.isInitialized() )
      {
         LOGWARN << "***WARNING: How did we get a NULL tx?";
         continue;
      }

      BlockHeader* bhptr = theTx.getHeaderPtr();
      // This condition happens on invalid Tx (like invalid P2Pool coinbases)
      if( bhptr==NULL )
         continue;

      if( !bhptr->isMainBranch() )
         continue;

      uint32_t thisBlk = bhptr->getBlockHeight();
      if(thisBlk < blkStart  ||  thisBlk >= blkEnd)
         continue;

      if( !isTxFinal(theTx) )
         continue;

      // If we made it here, we want to scan this tx!
      wlt.scanTx(theTx, txIter->txIndex_, bhptr->getTimestamp(), thisBlk);
   }
 
   wlt.sortLedger();


   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(wlt);

}



/////////////////////////////////////////////////////////////////////////////
/*  This is not currently being used, and is actually likely to change 
 *  a bit before it is needed, so I have just disabled it.
vector<TxRef*> BlockDataManager_LevelDB::findAllNonStdTx(void)
{
   PDEBUG("Finding all non-std tx");
   vector<TxRef*> txVectOut(0);
   uint32_t nHeaders = headersByHeight_.size();

   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<nHeaders; h++)
   {
      BlockHeader & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX /////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         ///// LOOP OVER ALL TXIN IN BLOCK /////
         for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
         {
            TxIn txin = tx.getTxIn(iin);
            if(txin.getScriptType() == TXIN_SCRIPT_UNKNOWN)
            {
               txVectOut.push_back(&tx);
               cout << "Attempting to interpret TXIN script:" << endl;
               cout << "Block: " << h << " Tx: " << itx << endl;
               cout << "PrevOut: " << txin.getOutPoint().getTxHash().toHexStr()
                    << ", "        << txin.getOutPoint().getTxOutIndex() << endl;
               cout << "Raw Script: " << txin.getScript().toHexStr() << endl;
               cout << "Raw Tx: " << txin.getParentTxPtr()->serialize().toHexStr() << endl;
               cout << "pprint: " << endl;
               BtcUtils::pprintScript(txin.getScript());
               cout << endl;
            }
         }

         ///// LOOP OVER ALL TXOUT IN BLOCK /////
         for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
         {
            
            TxOut txout = tx.getTxOut(iout);
            if(txout.getScriptType() == TXOUT_SCRIPT_UNKNOWN)
            {
               txVectOut.push_back(&tx);               
               cout << "Attempting to interpret TXOUT script:" << endl;
               cout << "Block: " << h << " Tx: " << itx << endl;
               cout << "ThisOut: " << txout.getParentTxPtr()->getThisHash().toHexStr() 
                    << ", "        << txout.getIndex() << endl;
               cout << "Raw Script: " << txout.getScript().toHexStr() << endl;
               cout << "Raw Tx: " << txout.getParentTxPtr()->serialize().toHexStr() << endl;
               cout << "pprint: " << endl;
               BtcUtils::pprintScript(txout.getScript());
               cout << endl;
            }

         }
      }
   }

   PDEBUG("Done finding all non-std tx");
   return txVectOut;
}
*/



/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::processHeadersInFile(string filename)
{
   SCOPED_TIMER("processHeadersInFile");

   if(BtcUtils::GetFileSize(filename) != FILE_DOES_NOT_EXIST)
   {
      LOGERR << "File does not exist: " << filename.c_str();
      return false;
   }

   ifstream is(filename.c_str(), ios::in | ios::binary);
   BinaryData fileMagic(4);
   is.read((char*)(fileMagic.getPtr()), 4);
   is.seekg(0, ios::beg);

   if( !(fileMagic == MagicBytes_ ) )
   {
      LOGERR << "Block file is the wrong network!  MagicBytes: "
             << fileMagic.toHexStr().c_str();
      return false;
   }

   // Now have a bunch of blockchain data buffered
   BinaryStreamBuffer bsb;
   bsb.attachAsStreamBuffer(is, filesize);

   bool alreadyRead8B = false;
   uint32_t nextBlkSize;
   bool isEOF = false;
   BinaryData firstFour(4);
   BinaryData rawHeader(HEADER_SIZE);

   // Some objects to help insert header data efficiently
   pair<HashString, BlockHeader>                      bhInputPair;
   pair<map<HashString, BlockHeader>::iterator, bool> bhInsResult;

   // Pull 32 MB at a time from the file and extract headers from each block
   while(bsb.streamPull())
   {
      while(bsb.reader().getSizeRemaining() > 8)
      {
         if(!alreadyRead8B)
         {
            bsb.reader().get_BinaryData(firstFour, 4);
            if(firstFour!=MagicBytes_)
            {
               isEOF = true; 
               break;
            }
            nextBlkSize = bsb.reader().get_uint32_t();
         }

         if(bsb.reader().getSizeRemaining() < nextBlkSize)
         {
            alreadyRead8B = true;
            break;
         }
         alreadyRead8B = false;

         // Create a reader for the entire block, grab header, skip rest
         BinaryRefReader brr(bsb.reader().getCurrPtr(), nextBlkSize);
         bhInputPair.second.unserialize(brr);
         bhInputPair.first = bhInputPair.second.getThisHash();
         bhInsResult = headerMap_.insert(bhInputPair);
         if(!bhInsResult.second)
            LOGERR << "Somehow tried to add header that's already in map";
         
         brr.advance(nextBlkSize - HEADER_SIZE);
      }

      if(isEOF) 
         break;
   }

   is.close();
   return true;
}



/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::parseEntireBlockchain(uint32_t cacheSize)
{
   SCOPED_TIMER("parseEntireBlockchain");
   LOGINFO << "Number of registered addr: " << registeredScrAddrMap_.size();

   // Remove this file
   string bfile     = armoryHomeDir_ + string("/blkfiles.txt");
   string abortFile = armoryHomeDir_ + string("/abortload.txt");
   if(BtcUtils::GetFileSize(bfile) != FILE_DOES_NOT_EXIST)
      remove(bfile.c_str());
   if(BtcUtils::GetFileSize(abortFile) != FILE_DOES_NOT_EXIST)
      remove(abortFile.c_str());


   // Next thing we need to do is find all the blk000X.dat files.
   // BtcUtils::GetFileSize uses only ifstreams, and thus should be
   // able to determine if a file exists in an OS-independent way.
   numBlkFiles_=0;
   totalBlockchainBytes_ = 0;
   blkFileList_.clear();


   while(numBlkFiles_ < UINT16_MAX)
   {
      string path = BtcUtils::getBlkFilename(blkFileDir_,
                                             blkFileDigits_, 
                                             numBlkFiles_+blkFileStart_);
      numBlkFiles_++;
      if(BtcUtils::GetFileSize(path) == FILE_DOES_NOT_EXIST)
         break;

      blkFileList_.push_back(string(path));
      totalBlockchainBytes_ += globalCache.openFile(numBlkFiles_-1, path);
   }
   numBlkFiles_--;

   if(numBlkFiles_==UINT16_MAX)
   {
      LOGERR << "Error finding blockchain files (blkXXXX.dat)";
      return 0;
   }
   LOGINFO << "Highest blkXXXX.dat file: " << numBlkFiles_;



   if(GenesisHash_.getSize() == 0)
   {
      LOGERR << "***ERROR: Set net params before loading blockchain!";
      return 0;
   }

   // Read headers 
   for(uint32_t fnum=1; fnum<=numBlkFiles_; fnum++)
      processHeadersInFile(blkFileList_[fnum-1]);

   // This will return true unless genesis block was reorg'd...
   bool prevTopBlkStillValid = organizeChain(true);
   if(!prevTopBlkStillValid)
      LOGERR << "Somehow reorged on a full header organization";


   /////////////////////////////////////////////////////////////////////////////
   // Now we start the meat of this process...
   uint32_t blocksReadSoFar_ = 0;
   uint32_t bytesReadSoFar_ = 0;
   TIMER_START("LoadProgress");
   for(uint32_t fnum=1; fnum<=numBlkFiles_; fnum++)
   {
      string blkfile = blkFileList_[fnum-1];
      LOGINFO << "Attempting to read blockchain file: " << blkfile.c_str();
      //uint64_t filesize = globalCache.getFileSize(fnum-1);

      // Open the file, and check the magic bytes on the first block
      ifstream is(blkfile.c_str(), ios::in | ios::binary);
      BinaryData fileMagic(4);
      is.read((char*)(fileMagic.getPtr()), 4);
      is.seekg(0, ios::beg);
      LOGINFO << blkfile.c_str() << " is " 
              << BtcUtils::numToStrWCommas(filesize).c_str() << " bytes";

      if( !(fileMagic == MagicBytes_ ) )
      {
         LOGERR << "Block file is the wrong network!  MagicBytes: "
                << fileMagic.toHexStr().c_str();
         return 0;
      }

      // This is a hack of hacks, but I can't seem to pass this data 
      // out through getLoadProgress* methods, because they don't 
      // update properly when the BDM is actively loading/scanning in a 
      // separate thread
      // We'll watch for this file from the python code...
      if(armoryHomeDir_.size() > 0)
      {
         if(BtcUtils::GetFileSize(abortFile) != FILE_DOES_NOT_EXIST)
            return 0;
         ofstream topblks(bfile.c_str(), ios::app);
         double t = TIMER_READ_SEC("LoadProgress");
         topblks << fnum-1 << " " << numBlkFiles_ << " " << t << endl;
      }

      // Now have a bunch of blockchain data buffered
      BinaryStreamBuffer bsb;
      bsb.attachAsStreamBuffer(is, filesize);
   
      bool alreadyRead8B = false;
      uint32_t nextBlkSize;
      bool isEOF = false;
      BinaryData firstFour(4);
      while(bsb.streamPull())
      {
         while(bsb.reader().getSizeRemaining() > 8)
         {
            if(!alreadyRead8B)
            {
               bsb.reader().get_BinaryData(firstFour, 4);
               if(firstFour!=MagicBytes_)
               {
                  isEOF = true; 
                  break;
               }
               nextBlkSize = bsb.reader().get_uint32_t();
               bytesReadSoFar_ += 8;
            }
   
            if(bsb.reader().getSizeRemaining() < nextBlkSize)
            {
               alreadyRead8B = true;
               break;
            }
            alreadyRead8B = false;
   
            BinaryRefReader brr(bsb.reader().getCurrPtr(), nextBlkSize);

            bool addRaw = addRawBlockToDB(brr);
            //parseNewBlock(brr, fnum-1, bsb.getFileByteLocation(), nextBlkSize);
            blocksReadSoFar_++;
            bytesReadSoFar_ += nextBlkSize;
            bsb.reader().advance(nextBlkSize);
         }
   
         if(isEOF) 
            break;
      }
      TIMER_STOP("while(bsb.streamPull())");



   }
   TIMER_STOP("LoadProgress");


   
   // We now have a map of all blocks, let's organize them into a chain.
   organizeChain(true);


   // We need to maintain the physical size of all blkXXXX.dat files together
   totalBlockchainBytes_ = bytesReadSoFar_;



   // Update registered address list so we know what's already been scanned
   lastTopBlock_ = getTopBlockHeight() + 1;
   allScannedUpToBlk_ = lastTopBlock_;
   updateRegisteredAddresses(lastTopBlock_);
   

   // Since loading takes so long, there's a good chance that new block data
   // came in... let's get it.
   readBlkFileUpdate();

   // Return the number of blocks read from blkfile (this includes invalids)
   isInitialized_ = true;
   purgeZeroConfPool();

   TIMER_STOP("parseEntireBlockchain");

   #ifdef _DEBUG
      UniversalTimer::instance().printCSV(cout,true);
      UniversalTimer::instance().printCSV(string("timings.csv"));
   #endif

   return blocksReadSoFar_;
}


////////////////////////////////////////////////////////////////////////////////
// This method checks whether your blk0001.dat file is bigger than it was when
// we first read in the blockchain.  If so, we read the new data and add it to
// the memory pool.  Return value is how many blocks were added.
//
// NOTE:  You might want to check lastBlockWasReorg_ variable to know whether 
//        to expect some previously valid headers/txs to still be valid
//
uint32_t BlockDataManager_LevelDB::readBlkFileUpdate(void)
{
   SCOPED_TIMER("readBlkFileUpdate");

   // Make sure the file exists and is readable
   string filename = blkFileList_[blkFileList_.size()-1];

   uint64_t filesize = FILE_DOES_NOT_EXIST;
   ifstream is(filename.c_str(), ios::in|ios::binary);
   if(is.is_open())
   {
      is.seekg(0, ios::end);
      filesize = (size_t)is.tellg();
   }
      

   uint64_t currBlkBytesToRead;

   if( filesize == FILE_DOES_NOT_EXIST )
   {
      LOGERR << "***ERROR:  Cannot open " << filename.c_str();
      return 0;
   }
   else if((int64_t)filesize-(int64_t)endOfPrevLastBlock_ < 8)
   {
      // This condition triggers if we hit the end of the file -- will
      // usually only be triggered by Bitcoin-Qt/bitcoind pre-0.8
      currBlkBytesToRead = 0;
   }
   else
   {
      // For post-0.8, the filesize will almost always be larger (padded).
      // Keep checking where we expect to see magic bytes, we know we're 
      // at the end if we see zero-bytes instead.
      uint64_t endOfNewLastBlock = endOfPrevLastBlock_;
      BinaryData fourBytes(4);
      while((int64_t)filesize - (int64_t)endOfNewLastBlock >= 8)
      {
         is.seekg(endOfNewLastBlock, ios::beg);
         is.read((char*)fourBytes.getPtr(), 4);

         if(fourBytes!=MagicBytes_)
            break;
         else
         {
            is.read((char*)fourBytes.getPtr(), 4);
            endOfNewLastBlock += READ_UINT32_LE((fourBytes.getPtr()) + 8;
         }
      }

      currBlkBytesToRead = endOfNewLastBlock - endOfPrevLastBlock_;
   }
      


   // Check to see if there was a blkfile split, and we have to switch
   // to tracking the new file..  this condition may trigger only once a year...
   string nextFilename = BtcUtils::getBlkFilename(blkFileDir_, 
                                                  blkFileDigits_,
                                                  numBlkFiles_+blkFileStart_);
   uint64_t nextBlkBytesToRead = BtcUtils::GetFileSize(nextFilename);
   if( nextBlkBytesToRead == FILE_DOES_NOT_EXIST )
      nextBlkBytesToRead = 0;
   else
      cout << "New block file split! " << nextFilename << endl;


   // If there is no new data, no need to continue
   if(currBlkBytesToRead==0 && nextBlkBytesToRead==0)
      return 0;
   
   // Observe if everything was up to date when we started, because we're 
   // going to add new blockchain data and don't want to trigger a rescan 
   // if this is just a normal update.
   uint32_t nextBlk = getTopBlockHeight() + 1;
   bool prevRegisteredUpToDate = allScannedUpToBlk_==nextBlk;
   
   // Pull in the remaining data in old/curr blkfile, and beginning of new
   BinaryData newBlockDataRaw(currBlkBytesToRead + nextBlkBytesToRead);

   // Seek to the beginning of the new data and read it
   if(currBlkBytesToRead>0)
   {
      ifstream is(filename.c_str(), ios::in | ios::binary);
      is.seekg(endOfPrevLastBlock_, ios::beg);
      is.read((char*)newBlockDataRaw.getPtr(), currBlkBytesToRead);
      is.close();
   }

   // If a new block file exists, read that one too
   // nextBlkBytesToRead will include up to 16 MB of padding if our gateway
   // is a bitcoind/qt 0.8+ node.  Either way, it will be easy to detect when
   // we've reached the end of the real data, as long as there is no gap 
   // between the end of currBlk data and the start of newBlk data (there isn't)
   if(nextBlkBytesToRead>0)
   {
      uint8_t* ptrNextData = newBlockDataRaw.getPtr() + currBlkBytesToRead;
      ifstream is(nextFilename.c_str(), ios::in | ios::binary);
      is.read((char*)ptrNextData, nextBlkBytesToRead);
      is.close();
   }


   // Use the specialized "addNewBlockData()" methods to add the data
   // to the permanent memory pool and parse it into our header/tx maps
   BinaryRefReader brr(newBlockDataRaw);
   BinaryData fourBytes(4);
   uint32_t nBlkRead = 0;
   vector<bool> blockAddResults;
   bool keepGoing = true;
   while(keepGoing)
   {
      // We concatenated all data together, even if across two files
      // Check which file data belongs to and set FileDataPtr appropriately
      uint32_t useFileIndex0Idx = numBlkFiles_-1;
      uint32_t blockHeaderOffset = endOfPrevLastBlock_ + 8;
      if(brr.getPosition() >= currBlkBytesToRead)
      {
         useFileIndex0Idx = numBlkFiles_;
         blockHeaderOffset = brr.getPosition() - currBlkBytesToRead + 8;
      }
      

      ////////////
      // The reader should be at the start of magic bytes of the new block
      brr.get_BinaryData(fourBytes, 4);
      if(fourBytes != MagicBytes_)
         break;
         
      uint32_t nextBlockSize = brr.get_uint32_t();
      blockAddResults = addNewBlockData( brr, nextBlockSize);


      bool blockAddSucceeded = blockAddResults[0];
      bool blockIsNewTop     = blockAddResults[1];
      bool blockchainReorg   = blockAddResults[2];

      if(blockAddSucceeded)
         nBlkRead++;

      if(!blockIsNewTop)
      {
         cout << "Block data did not extend the main chain!" << endl;
         // TODO:  add anything extra to do here (is there anything?)
      }

      if(blockchainReorg)
      {
         // Update all the registered wallets...
         cout << "This block forced a reorg!" << endl;
         updateWalletsAfterReorg(registeredWallets_);
         // TODO:  Any other processing to do on reorg?
      }
      
      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }
   lastTopBlock_ = getTopBlockHeight()+1;


   if(prevRegisteredUpToDate)
   {
      allScannedUpToBlk_ = getTopBlockHeight()+1;
      updateRegisteredAddresses(allScannedUpToBlk_);
   }

   // If the blk file split, switch to tracking it
   cout << "Added new blocks to memory pool: " << nBlkRead << endl;
   if(nextBlkBytesToRead>0)
   {
      numBlkFiles_ += 1;
      blkFileList_.push_back(nextFilename);
   }

   // We'll stop the timer here so it will stop before printing
   // It will be stopped again when the TimerToken goes out of scope,
   // but it does no harm to stop a timer multiple times.
   TIMER_STOP("readBlkFileUpdate");

   #ifdef _DEBUG
      UniversalTimer::instance().printCSV(cout,true);
      UniversalTimer::instance().printCSV(string("timings.csv"));
   #endif

   return nBlkRead;

}


////////////////////////////////////////////////////////////////////////////////
// BDM detects the reorg, but is wallet-agnostic so it can't update any wallets
// You have to call this yourself after you check whether the last organizeChain
// call indicated that a reorg happened
void BlockDataManager_LevelDB::updateWalletAfterReorg(BtcWallet & wlt)
{
   SCOPED_TIMER("updateWalletAfterReorg");

   // Fix the wallet's ledger
   vector<LedgerEntry> & ledg = wlt.getTxLedger();
   for(uint32_t i=0; i<ledg.size(); i++)
   {
      HashString const & txHash = ledg[i].getTxHash();
      if(txJustInvalidated_.count(txHash) > 0)
         ledg[i].setValid(false);

      if(txJustAffected_.count(txHash) > 0)
         ledg[i].changeBlkNum(getTxRefByHash(txHash)->getBlockHeight());
   }

   // Now fix the individual address ledgers
   for(uint32_t a=0; a<wlt.getNumScrAddr(); a++)
   {
      ScrAddrObj & addr = wlt.getScrAddrByIndex(a);
	  vector<LedgerEntry> & addrLedg = addr.getTxLedger();
      for(uint32_t i=0; i<addrLedg.size(); i++)
      {
         HashString const & txHash = addrLedg[i].getTxHash();
         if(txJustInvalidated_.count(txHash) > 0)
            addrLedg[i].setValid(false);
   
         if(txJustAffected_.count(txHash) > 0) 
            addrLedg[i].changeBlkNum(getTxRefByHash(txHash)->getBlockHeight());
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateWalletsAfterReorg(vector<BtcWallet*> wltvect)
{
   for(uint32_t i=0; i<wltvect.size(); i++)
      updateWalletAfterReorg(*wltvect[i]);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateWalletsAfterReorg(set<BtcWallet*> wltset)
{
   set<BtcWallet*>::iterator iter;
   for(iter = wltset.begin(); iter != wltset.end(); iter++)
      updateWalletAfterReorg(**iter);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::verifyBlkFileIntegrity(void)
{
   SCOPED_TIMER("updateWalletAfterReorg");
   PDEBUG("Verifying blk0001.dat integrity");

   bool isGood = true;
   map<HashString, BlockHeader>::iterator headIter;
   for(headIter  = headerMap_.begin();
       headIter != headerMap_.end();
       headIter++)
   {
      BlockHeader & bhr = headIter->second;
      bool thisHeaderIsGood = bhr.verifyIntegrity();
      if( !thisHeaderIsGood )
      {
         cout << "Blockfile contains incorrect header or tx data:" << endl;
         cout << "  Block number:    " << bhr.getBlockHeight() << endl;
         cout << "  Block hash (BE):   " << endl;
         cout << "    " << bhr.getThisHash().copySwapEndian().toHexStr() << endl;
         cout << "  Num Tx :         " << bhr.getNumTx() << endl;
         cout << "  Tx Hash List: (compare to raw tx data on blockexplorer)" << endl;
         for(uint32_t t=0; t<bhr.getNumTx(); t++)
            cout << "    " << bhr.getTxRefPtrList()[t]->getThisHash().copySwapEndian().toHexStr() << endl;
      }
      isGood = isGood && thisHeaderIsGood;
   }
   return isGood;
   PDEBUG("Done verifying blockfile integrity");
}



/////////////////////////////////////////////////////////////////////////////
// Pass in a BRR that starts at the beginning of the serialized block,
// i.e. the first 80 bytes of this BRR is the blockheader
bool BlockDataManager_LevelDB::parseNewBlock(BinaryRefReader & brr,
                                              uint32_t fileIndex0Idx,
                                              uint32_t thisHeaderOffset,
                                              uint32_t blockSize)
{
   if(brr.getSizeRemaining() < blockSize || brr.isEndOfStream())
   {
      cout << "***ERROR:  parseNewBlock did not get enough data..." << endl;
      cerr << "***ERROR:  parseNewBlock did not get enough data..." << endl;
      return false;
   }

   // Create the objects once that will be used for insertion
   // (txInsResult always succeeds--because multimap--so only iterator returns)
   static pair<HashString, TxRef>                            txInputPair;
   static pair<HashString, BlockHeader>                      bhInputPair;
   static multimap<HashString, TxRef>::iterator              txInsResult;
   static pair<map<HashString, BlockHeader>::iterator, bool> bhInsResult;
   txInputPair.first.resize(4);

   
   // Read off the header 
   bhInputPair.second.unserialize(brr);
   bhInputPair.first = bhInputPair.second.getThisHash();
   bhInsResult = headerMap_.insert(bhInputPair);
   BlockHeader * bhptr = &(bhInsResult.first->second);

   // Note where we will start looking for the next block, later
   endOfPrevLastBlock_ = thisHeaderOffset + blockSize;

   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brr.get_var_int(&viSize);

   // The file offset of the first tx in this block is after the var_int
   uint32_t txOffset = thisHeaderOffset + HEADER_SIZE + viSize; 

   // Read each of the Tx
   //bhptr->txPtrList_.resize(nTx);
   uint32_t txSize;
   static vector<uint32_t> offsetsIn;
   static vector<uint32_t> offsetsOut;
   static BinaryData hashResult(32);

   for(uint32_t i=0; i<nTx; i++)
   {
      // We get a little funky here because I need to avoid ALL unnecessary
      // copying -- therefore everything is pointers...and confusing...
      uint8_t const * ptrToRawTx = brr.getCurrPtr();
      
      txSize = BtcUtils::TxCalcLength(ptrToRawTx, &offsetsIn, &offsetsOut);

      // Insert the FileDataPtr into the multimap
      BtcUtils::getHash256_NoSafetyCheck(ptrToRawTx, txSize, hashResult);

      // Insert TxRef into txHintMap_, making sure there's no duplicates 
      // of this exactly transaction (which happens on one-block forks).
      // Store the pointer to the newly-added txref, save it with the header
      //bhptr->txPtrList_[i] = insertTxRef(hashResult, fdpThisTx, NULL);

      // We don't set this tx's headerPtr because there could be multiple
      // headers that reference this tx... we will wait until the chain
      // is organized and then go through and set these pointers after we 
      // know what the main chain is...
      // <...>

      // Figure out, as quickly as possible, whether this tx has any relevance
      // to any of the registered addresses.  Again, using pointers...
      registeredAddrScan(ptrToRawTx, txSize, &offsetsIn, &offsetsOut);

      // Prepare for the next tx.  Manually advance brr since used ptr directly
      txOffset += txSize;
      brr.advance(txSize);
   }
   return true;
}
   


////////////////////////////////////////////////////////////////////////////////
// This method returns three booleans:
//    (1)  Block data was added to memory pool successfully
//    (2)  New block added is at the top of the chain
//    (3)  Adding block data caused blockchain reorganization
//
// This method assumes the data is not in the permanent memory pool yet, and
// we will need to copy it to its permanent memory location before parsing it.
// Btw, yes I know I could've used a bitset here, but I was too lazy to add
// the #include and look up the members for using it...
vector<bool> BlockDataManager_LevelDB::addNewBlockData(BinaryRefReader & brrRawBlock,
                                                       uint32_t blockSize)
{
   SCOPED_TIMER("addNewBlockData");
   uint8_t const * startPtr = brrRawBlock.getCurrPtr();
   HashString newHeadHash = BtcUtils::getHash256(startPtr, HEADER_SIZE);

   // Now parse the block data and record where it will be on disk
   bool addDataSucceeded = parseNewBlock(brrRawBlock, 
                                         fileIndex0Idx,
                                         thisHeaderOffset,
                                         blockSize);


   vector<bool> vb(3);
   if( !addDataSucceeded ) 
   {
      cout << "Adding new block data to memory pool failed!";
      vb[ADD_BLOCK_SUCCEEDED]     = false;  // Added to memory pool
      vb[ADD_BLOCK_NEW_TOP_BLOCK] = false;  // New block is new top of chain
      vb[ADD_BLOCK_CAUSED_REORG]  = false;  // Add caused reorganization
      return vb;
   }

   // Finally, let's re-assess the state of the blockchain with the new data
   // Check the lastBlockWasReorg_ variable to see if there was a reorg
   PDEBUG("New block!  Re-assess blockchain state after adding new data...");
   bool prevTopBlockStillValid = organizeChain(); 
   lastBlockWasReorg_ = false;

   // I cannot just do a rescan:  the user needs this to be done manually so
   // that we can identify headers/txs that were previously valid, but no more
   if(!prevTopBlockStillValid)
   {
      lastBlockWasReorg_ = true;
      cout << "Blockchain Reorganization detected!" << endl;
      reassessAfterReorg(prevTopBlockPtr_, topBlockPtr_, reorgBranchPoint_);
      cout << "Done reassessing tx validity " << endl;
   }
   

   // Since this method only adds one block, if it's not on the main branch,
   // then it's not the new head
   bool newBlockIsNewTop = getHeaderByHash(newHeadHash)->isMainBranch();

   // Need to purge the zero-conf pool and re-evaluate -- the new block 
   // probably included some of the transactions in the pool
   purgeZeroConfPool();

   // This method passes out 3 booleans
   vb[ADD_BLOCK_SUCCEEDED]     =  addDataSucceeded;
   vb[ADD_BLOCK_NEW_TOP_BLOCK] =  newBlockIsNewTop;
   vb[ADD_BLOCK_CAUSED_REORG]  = !prevTopBlockStillValid;
   return vb;
}



// This piece may be useful for adding new data, but I don't want to enforce it,
// yet
/*
#ifndef _DEBUG
   // In the real client, we want to execute these checks.  But we may want
   // to pass in hand-made data when debugging, and don't want to require
   // the hand-made blocks to have leading zeros.
   if(! (headHash.getSliceCopy(28,4) == BtcUtils::EmptyHash_.getSliceCopy(28,4)))
   {
      cout << "***ERROR: header hash does not have leading zeros" << endl;   
      cerr << "***ERROR: header hash does not have leading zeros" << endl;   
      return true;  // no data added, so no reorg
   }

   // Same story with merkle roots in debug mode
   HashString merkleRoot = BtcUtils::calculateMerkleRoot(txHashes);
   if(! (merkleRoot == BinaryDataRef(rawHeader.getPtr() + 36, 32)))
   {
      cout << "***ERROR: merkle root does not match header data" << endl;
      cerr << "***ERROR: merkle root does not match header data" << endl;
      return true;  // no data added, so no reorg
   }
#endif
*/
   



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::reassessAfterReorg( BlockHeader* oldTopPtr,
                                                   BlockHeader* newTopPtr,
                                                   BlockHeader* branchPtr)
{
   SCOPED_TIMER("reassessAfterReorg");
   cout << "Reassessing Tx validity after (after reorg?)" << endl;

   // Walk down invalidated chain first, until we get to the branch point
   // Mark transactions as invalid
   txJustInvalidated_.clear();
   txJustAffected_.clear();
   BlockHeader* thisHeaderPtr = oldTopPtr;
   cout << "Invalidating old-chain transactions..." << endl;
   while(thisHeaderPtr != branchPtr)
   {
      previouslyValidBlockHeaderPtrs_.push_back(thisHeaderPtr);
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef * txptr = thisHeaderPtr->getTxRefPtrList()[i];
         cout << "   Tx: " << txptr->getThisHash().getSliceCopy(0,8).toHexStr() << endl;
         txptr->setHeaderPtr(NULL);
         //txptr->setMainBranch(false);
         txJustInvalidated_.insert(txptr->getThisHash());
         txJustAffected_.insert(txptr->getThisHash());
      }
      thisHeaderPtr = getHeaderByHash(thisHeaderPtr->getPrevHash());
   }

   // Walk down the newly-valid chain and mark transactions as valid.  If 
   // a tx is in both chains, it will still be valid after this process
   thisHeaderPtr = newTopPtr;
   cout << "Marking new-chain transactions valid..." << endl;
   while(thisHeaderPtr != branchPtr)
   {
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef * txptr = thisHeaderPtr->getTxRefPtrList()[i];
         cout << "   Tx: " << txptr->getThisHash().getSliceCopy(0,8).toHexStr() << endl;
         txptr->setHeaderPtr(thisHeaderPtr);
         //txptr->setMainBranch(true);
         txJustInvalidated_.erase(txptr->getThisHash());
         txJustAffected_.insert(txptr->getThisHash());
      }
      thisHeaderPtr = getHeaderByHash(thisHeaderPtr->getPrevHash());
   }

   PDEBUG("Done reassessing tx validity");
}

////////////////////////////////////////////////////////////////////////////////
vector<BlockHeader*> BlockDataManager_LevelDB::getHeadersNotOnMainChain(void)
{
   SCOPED_TIMER("getHeadersNotOnMainChain");
   PDEBUG("Getting headers not on main chain");
   vector<BlockHeader*> out(0);
   map<HashString, BlockHeader>::iterator iter;
   for(iter  = headerMap_.begin(); 
       iter != headerMap_.end(); 
       iter++)
   {
      if( ! iter->second.isMainBranch() )
         out.push_back(&(iter->second));
   }
   PDEBUG("Getting headers not on main chain");
   return out;
}


// This returns false if our new main branch does not include the previous
// topBlock.  If this returns false, that probably means that we have
// previously considered some blocks to be valid that no longer are valid.
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
bool BlockDataManager_LevelDB::organizeChain(bool forceRebuild)
{
   SCOPED_TIMER("organizeChain");
   PDEBUG2("Organizing chain", (forceRebuild ? "w/ rebuild" : ""));
   // If rebuild, we zero out any original organization data and do a 
   // rebuild of the chain from scratch.  This will need to be done in
   // the event that our first call to organizeChain returns false, which
   // means part of blockchain that was previously valid, has become
   // invalid.  Rather than get fancy, just rebuild all which takes less
   // than a second, anyway.
   if(forceRebuild)
   {
      map<HashString, BlockHeader>::iterator iter;
      for( iter  = headerMap_.begin(); 
           iter != headerMap_.end(); 
           iter++)
      {
         iter->second.difficultySum_  = -1;
         iter->second.blockHeight_    =  0;
         iter->second.isFinishedCalc_ =  false;
         iter->second.nextHash_       =  BtcUtils::EmptyHash_;
      }
      topBlockPtr_ = NULL;
   }

   // Set genesis block
   BlockHeader & genBlock = getGenesisBlock();
   genBlock.blockHeight_    = 0;
   genBlock.difficultyDbl_  = 1.0;
   genBlock.difficultySum_  = 1.0;
   genBlock.isMainBranch_   = true;
   genBlock.isOrphan_       = false;
   genBlock.isFinishedCalc_ = true;
   genBlock.isInitialized_  = true; 
   //genBlock.txPtrList_      = vector<TxRef*>(1);
   //genBlock.txPtrList_[0]   = getTxRefByHash(GenesisTxHash_);
   //genBlock.txPtrList_[0]->setMainBranch(true);
   //genBlock.txPtrList_[0]->setHeaderPtr(&genBlock);


   // If this is the first run, the topBlock is the genesis block
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   // Store the old top block so we can later check whether it is included 
   // in the new chain organization
   prevTopBlockPtr_ = topBlockPtr_;

   // Iterate over all blocks, track the maximum difficulty-sum block
   map<HashString, BlockHeader>::iterator iter;
   double   maxDiffSum     = prevTopBlockPtr_->getDifficultySum();
   for( iter = headerMap_.begin(); iter != headerMap_.end(); iter ++)
   {
      // *** Walk down the chain following prevHash fields, until
      //     you find a "solved" block.  Then walk back up and 
      //     fill in the difficulty-sum values (do not set next-
      //     hash ptrs, as we don't know if this is the main branch)
      //     Method returns instantly if block is already "solved"
      double thisDiffSum = traceChainDown(iter->second);
      
      // Determine if this is the top block.  If it's the same diffsum
      // as the prev top block, don't do anything
      if(thisDiffSum > maxDiffSum)
      {
         maxDiffSum     = thisDiffSum;
         topBlockPtr_   = &(iter->second);
      }
   }

   // Walk down the list one more time, set nextHash fields
   // Also set headersByHeight_;
   bool prevChainStillValid = (topBlockPtr_ == prevTopBlockPtr_);
   topBlockPtr_->nextHash_ = BtcUtils::EmptyHash_;
   BlockHeader* thisHeaderPtr = topBlockPtr_;
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisHeaderPtr->isFinishedCalc_ )
   {
      thisHeaderPtr->isFinishedCalc_ = true;
      thisHeaderPtr->isMainBranch_   = true;
      thisHeaderPtr->isOrphan_       = false;
      headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

      // This loop not necessary anymore with the DB implementation
      // We need to guarantee that the txs are pointing to the right block
      // header, because they could've been linked to an invalidated block
      //for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      //{
         //TxRef & tx = *(thisHeaderPtr->getTxRefPtrList()[i]);
         //tx.setHeaderPtr(thisHeaderPtr);
         //tx.setMainBranch(true);
      //}

      HashString & childHash    = thisHeaderPtr->thisHash_;
      thisHeaderPtr             = &(headerMap_[thisHeaderPtr->getPrevHash()]);
      thisHeaderPtr->nextHash_  = childHash;

      if(thisHeaderPtr == prevTopBlockPtr_)
         prevChainStillValid = true;

   }
   // Last header in the loop didn't get added (the genesis block on first run)
   thisHeaderPtr->isMainBranch_ = true;
   headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;


   // Force a full rebuild to make sure everything is marked properly
   // On a full rebuild, prevChainStillValid should ALWAYS be true
   if( !prevChainStillValid )
   {
      PDEBUG("Reorg detected!");
      reorgBranchPoint_ = thisHeaderPtr;

      // There was a dangerous bug -- prevTopBlockPtr_ is set correctly 
      // RIGHT NOW, but won't be once I make the recursive call to organizeChain
      // I need to save it now, and re-assign it after the organizeChain call.
      // (I might consider finding a way to avoid this, but it's fine as-is)
      BlockHeader* prevtopblk = prevTopBlockPtr_;
      organizeChain(true); // force-rebuild blockchain (takes less than 1s)
      prevTopBlockPtr_ = prevtopblk;
      return false;
   }

   // Let the caller know that there was no reorg
   PDEBUG("Done organizing chain");
   return true;
}


/////////////////////////////////////////////////////////////////////////////
// Start from a node, trace down to the highest solved block, accumulate
// difficulties and difficultySum values.  Return the difficultySum of 
// this block.
double BlockDataManager_LevelDB::traceChainDown(BlockHeader & bhpStart)
{
   if(bhpStart.difficultySum_ > 0)
      return bhpStart.difficultySum_;

   // Prepare some data structures for walking down the chain
   vector<BlockHeader*>   headerPtrStack(headerMap_.size());
   vector<double>           difficultyStack(headerMap_.size());
   uint32_t blkIdx = 0;
   double thisDiff;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   BlockHeader* thisPtr = &bhpStart;
   map<HashString, BlockHeader>::iterator iter;
   while( thisPtr->difficultySum_ < 0)
   {
      thisDiff                = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      headerPtrStack[blkIdx]  = thisPtr;
      blkIdx++;

      iter = headerMap_.find(thisPtr->getPrevHash());
      if( iter != headerMap_.end() )
         thisPtr = &(iter->second);
      else
      {
         // We didn't hit a known block, but we don't have this block's
         // ancestor in the memory pool, so this is an orphan chain...
         // at least temporarily
         markOrphanChain(bhpStart);
         return 0.0;
      }
   }


   // Now we have a stack of difficulties and pointers.  Walk back up
   // (by pointer) and accumulate the difficulty values 
   double   seedDiffSum = thisPtr->difficultySum_;
   uint32_t blkHeight   = thisPtr->blockHeight_;
   for(int32_t i=blkIdx-1; i>=0; i--)
   {
      seedDiffSum += difficultyStack[i];
      blkHeight++;
      thisPtr                 = headerPtrStack[i];
      thisPtr->difficultyDbl_ = difficultyStack[i];
      thisPtr->difficultySum_ = seedDiffSum;
      thisPtr->blockHeight_   = blkHeight;
   }
   
   // Finally, we have all the difficulty sums calculated, return this one
   return bhpStart.difficultySum_;
  
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::markOrphanChain(BlockHeader & bhpStart)
{
   PDEBUG("Marking orphan chain");
   bhpStart.isMainBranch_ = true;
   map<HashString, BlockHeader>::iterator iter;
   iter = headerMap_.find(bhpStart.getPrevHash());
   HashStringRef lastHeadHash(32);
   while( iter != headerMap_.end() )
   {
      // I don't see how it's possible to have a header that used to be 
      // in the main branch, but is now an ORPHAN (meaning it has no
      // parent).  It will be good to detect this case, though
      if(iter->second.isMainBranch() == true)
      {
         // NOTE: this actually gets triggered when we scan the testnet
         //       blk0001.dat file on main net, etc
         cout << "***ERROR: Block previously main branch, now orphan!?"
              << iter->second.getThisHash().toHexStr() << endl;
         cerr << "***ERROR: Block previously main branch, now orphan!?"
              << iter->second.getThisHash().toHexStr() << endl;
         previouslyValidBlockHeaderPtrs_.push_back(&(iter->second));
      }
      iter->second.isOrphan_ = true;
      iter->second.isMainBranch_ = false;
      lastHeadHash.setRef(iter->second.thisHash_);
      iter = headerMap_.find(iter->second.getPrevHash());
   }
   orphanChainStartBlocks_.push_back(&(headerMap_[lastHeadHash.copy()]));
   PDEBUG("Done marking orphan chain");
}


////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataManager_LevelDB::getPrevTxOut(TxIn & txin)
{
   if(txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOut(idx);
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataManager_LevelDB::getSenderAddr20(TxIn & txin)
{
   if(txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getRecipientAddr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataManager_LevelDB::getSentValue(TxIn & txin)
{
   if(txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}




////////////////////////////////////////////////////////////////////////////////
// Methods for handling zero-confirmation transactions
////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::enableZeroConf(string zcFilename)
{
   SCOPED_TIMER("enableZeroConf");
   zcEnabled_  = true; 
   zcFilename_ = zcFilename;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::readZeroConfFile(string zcFilename)
{
   SCOPED_TIMER("readZeroConfFile");
   uint64_t filesize = BtcUtils::GetFileSize(zcFilename);
   if(filesize<8 || filesize==FILE_DOES_NOT_EXIST)
      return;

   ifstream zcFile(zcFilename_.c_str(),  ios::in | ios::binary);
   BinaryData zcData(filesize);
   zcFile.read((char*)zcData.getPtr(), filesize);
   zcFile.close();

   // We succeeded opening the file...
   BinaryRefReader brr(zcData);
   while(brr.getSizeRemaining() > 8)
   {
      uint64_t txTime = brr.get_uint64_t();
      uint32_t txSize = BtcUtils::TxCalcLength(brr.getCurrPtr());
      BinaryData rawtx(txSize);
      brr.get_BinaryData(rawtx.getPtr(), txSize);
      addNewZeroConfTx(rawtx, txTime, false);
   }
   purgeZeroConfPool();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::disableZeroConf(string zcFilename)
{
   SCOPED_TIMER("disableZeroConf");
   zcEnabled_  = false; 
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::addNewZeroConfTx(BinaryData const & rawTx, 
                                                 uint64_t txtime,
                                                 bool writeToFile)
{
   SCOPED_TIMER("addNewZeroConfTx");
   // TODO:  We should do some kind of verification check on this tx
   //        to make sure it's potentially valid.  Right now, it doesn't 
   //        matter, because the Satoshi client is sitting between
   //        us and the network and doing the checking for us.

   if(txtime==0)
      txtime = time(NULL);

   HashString txHash = BtcUtils::getHash256(rawTx);
    
   // If this is already in the zero-conf map or in the blockchain, ignore it
   if(zeroConfMap_.find(txHash) != zeroConfMap_.end() || 
      getTxRefPtrByHash(txHash) != NULL)
      return false;
   
   
   zeroConfMap_[txHash] = ZeroConfData();
   ZeroConfData & zc = zeroConfMap_[txHash];
   zc.iter_ = zeroConfRawTxList_.insert(zeroConfRawTxList_.end(), rawTx);
   zc.txobj_.unserialize(*(zc.iter_));
   zc.txtime_ = txtime;

   // Record time.  Write to file
   if(writeToFile)
   {
      // ZERO-CONF TRANSACTION   { "ZCTX"|TXHASH32 --> TXTIME8|RAWTX }
      /*
      BinaryWriter keyWriter(4+32);
      keyWriter.put_BinaryData( string("ZCTX").data(), 4);
      keyWriter.put_BinaryData( txHash );
      
      BinaryWriter valWriter;
      valWriter.put_uint64_t(txtime);
      valWriter.put_BinaryData(rawTx);

      leveldb::Slice key(keyWriter.toString());
      leveldb::Slice val(valWriter.toString());
      leveldb::Status stat = transientDB_->Put(leveldb::WriteOptions(), key, val);
      */
   }
   return true;
}



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::purgeZeroConfPool(void)
{
   SCOPED_TIMER("purgeZeroConfPool");
   list< map<HashString, ZeroConfData>::iterator > mapRmList;

   // Find all zero-conf transactions that made it into the blockchain
   map<HashString, ZeroConfData>::iterator iter;
   for(iter  = zeroConfMap_.begin();
       iter != zeroConfMap_.end();
       iter++)
   {
      if(getTxRefPtrByHash(iter->first) != NULL)
         mapRmList.push_back(iter);
   }

   // We've made a list of the zc tx to remove, now let's remove them
   // I decided this was safer than erasing the data as we were iterating
   // over it in the previous loop
   list< map<HashString, ZeroConfData>::iterator >::iterator rmIter;
   for(rmIter  = mapRmList.begin();
       rmIter != mapRmList.end();
       rmIter++)
   {
      zeroConfRawTxList_.erase( (*rmIter)->second.iter_ );
      zeroConfMap_.erase( *rmIter );
   }

   // Rewrite the zero-conf pool file
   if(mapRmList.size() > 0)
      rewriteZeroConfFile();

}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rewriteZeroConfFile(void)
{
   SCOPED_TIMER("rewriteZeroConfFile");
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      zcFile.write( (char*)(&zcd.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)(zcd.txobj_.getPtr()),  zcd.txobj_.getSize());
   }

   zcFile.close();

}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rescanWalletZeroConf(BtcWallet & wlt)
{
   SCOPED_TIMER("rescanWalletZeroConf");
   // Clear the whole list, rebuild
   wlt.clearZeroConfPool();

   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {

      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];

      if( !isTxFinal(zcd.txobj_) )
         continue;

      wlt.scanTx(zcd.txobj_, 0, zcd.txtime_, UINT32_MAX);
   }
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintZeroConfPool(void)
{
   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      Tx & tx = zcd.txobj_;
      cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
      for(uint32_t i=0; i<tx.getNumTxOut(); i++)
         cout << tx.getTxOut(i).getValue() << " ";
      cout << endl;
   }
}


////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearZeroConfPool(void)
{
   ledgerZC_.clear();
   relevantTxIOPtrsZC_.clear();
}


////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearZeroConfPool(void)
{
   SCOPED_TIMER("clearZeroConfPool");
   ledgerAllAddrZC_.clear();
   for(uint32_t i=0; i<scrAddrMap_.size(); i++)
      addrPtrVect_[i]->clearZeroConfPool();


   // Need to "unlock" the TxIOPairs that were locked with zero-conf txs
   list< map<OutPoint, TxIOPair>::iterator > rmList;
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      iter->second.clearZCFields();
      if(!iter->second.hasTxOut())
         rmList.push_back(iter);
   }

   // If a TxIOPair exists only because of the TxOutZC, then we should 
   // remove to ensure that it won't conflict with any logic that only 
   // checks for the *existence* of a TxIOPair, whereas the TxIOPair might 
   // actually be "empty" but would throw off some other logic.
   list< map<OutPoint, TxIOPair>::iterator >::iterator rmIter;
   for(rmIter  = rmList.begin();
       rmIter != rmList.end();
       rmIter++)
   {
      txioMap_.erase(*rmIter);
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> & BtcWallet::getTxLedger(HashString const * addr160)
{
   SCOPED_TIMER("BtcWallet::getTxLedger");

   // Make sure to rebuild the ZC ledgers before calling this method
   if(addr160==NULL)
      return ledgerAllAddr_;
   else
   {
      if(scrAddrMap_.find(*addr160) == scrAddrMap_.end())
         return getEmptyLedger();
      else
         return scrAddrMap_[*addr160].getTxLedger();
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> & BtcWallet::getZeroConfLedger(HashString const * addr160)
{
   SCOPED_TIMER("BtcWallet::getZeroConfLedger");

   // Make sure to rebuild the ZC ledgers before calling this method
   if(addr160==NULL)
      return ledgerAllAddrZC_;
   else
   {
      if(scrAddrMap_.find(*addr160) == scrAddrMap_.end())
         return getEmptyLedger();
      else
         return scrAddrMap_[*addr160].getZeroConfLedger();
   }
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::isTxFinal(Tx & tx)
{
   // Anything that is replaceable (regular or through blockchain injection)
   // will be considered isFinal==false.  Users shouldn't even see the tx,
   // because the concept may be confusing, and the CURRENT use of non-final
   // tx is most likely for malicious purposes (as of this writing)
   //
   // This will change as multi-sig becomes integrated, and replacement will
   // eventually be enabled (properly), in which case I will expand this
   // to be more rigorous.
   //
   // For now I consider anything time-based locktimes (instead of block-
   // based locktimes) to be final if this is more than one day after the 
   // locktime expires.  This accommodates the most extreme case of silliness
   // due to time-zones (this shouldn't be an issue, but I haven't spent the
   // time to figure out how UTC and local time interact with time.h and 
   // block timestamps).  In cases where locktime is legitimately used, it 
   // is likely to be many days in the future, and one day may not even
   // matter.  I'm erring on the side of safety, not convenience.
   
   if(tx.getLockTime() == 0)
      return true;

   bool allSeqMax = true;
   for(uint32_t i=0; i<tx.getNumTxIn(); i++)
      if(tx.getTxIn(i).getSequence() < UINT32_MAX)
         allSeqMax = false;

   if(allSeqMax)
      return true;

   if(tx.getLockTime() < 500000000)
      return (getTopBlockHeight()>tx.getLockTime());
   else
      return (time(NULL)>tx.getLockTime()+86400);
}



////////////////////////////////////////////////////////////////////////////////
/* just like the addHeadersFirst -- this is changing the fundamental way that
 * we handle blockchain data, and we should avoid doing it on the first major
 * upgrade.  We may come back to tihs code later.
bool BlockDataManager_LevelDB::addRawBlockToDB(BinaryDataRef fullBlock,
                                               bool notNecessarilyValid,
                                               bool withPrefix)
{
   StoredHeader sbh;
   sbh.unserializeFullBlock(fullBlock, true, withPrefix);

   
   bool prevTopBlockStillValid = addHeadersFirst(sbh.dataCopy_);
   if(sbh.duplicateID_==UINT8_MAX)
   {
      LOGERR << "Could not insert header for some reason";
      return false;
   }

   if(!prevTopBlockStillValid)
   {
      LOGWARN << "Reorg detected!";
      purgeZeroConfPool();
   
      vector<StoredHeader> blocksToUndo;
      BlockHeader* bhptr = prevTopBlockPtr_;
      while(bhptr != reorgBranchPoint_)
      {
         StoredHeader sbhTemp;
         iface_->getStoredHeader(sbhTemp, bhptr->getThisHash(), true);
         blocksToUndo.push_back(sbhTemp);
      }

      for(uint32_t i=0; i<blocksToUndo.size(); i++)
      { 
         undoBlockInDatabase(sbh); 
      }
   }

   return insertBlockData(sbh, notNecessarilyValid);
}

////////////////////////////////////////////////////////////////////////////////
// AddRawBlockTODB
//
// Assumptions:
//  -- We have already determined the correct height and dup for the header 
//     and we assume it's part of the sbh object
//  -- It has definitely been added to the headers DB (bail if not)
//  -- We don't know if it's been added to the blkdata DB yet
//
// Things to do when adding a block:
//
//  -- PREPARATION:
//    -- Create list of all OutPoints affected, and scripts touched
//    -- If not supernode, then check above data against registeredSSHs_
//    -- Fetch all StoredTxOuts from DB about to be removed
//    -- Get/create TXHINT entries for all tx in block
//    -- Compute all script keys and get/create all StoredScriptHistory objs
//    -- Check if any multisig scripts are affected, if so get those objs
//    -- If pruning, create StoredUndoData from TxOuts about to be removed
//    -- Modify any Tx/TxOuts in the SBH tree to accommodate any tx in this 
//       block that affect any other tx in this block
//
//
//  -- Check if the block {hgt,dup} has already been written to BLKDATA DB
//  -- Check if the header has already been added to HEADERS DB
//  
//  -- BATCH (HEADERS)
//    -- Add header to HEADHASH list
//    -- Add header to HEADHGT list
//    -- Update validDupByHeight_
//    -- Update DBINFO top block data
//
//  -- BATCH (BLKDATA)
//    -- Modify StoredTxOut with spentness info (or prep a delete operation
//       if pruning).
//    -- Modify StoredScriptHistory objs same as above.  
//    -- Modify StoredScriptHistory multisig objects as well.
//    -- Update SSH objects alreadyScannedUpToBlk_, if necessary
//    -- Write all new TXDATA entries for {hgt,dup}
//    -- If pruning, write StoredUndoData objs to DB
//    -- Update DBINFO top block data
//
// IMPORTANT: we also need to make sure this method does nothing if the
//            block has already been added properly (though, it okay for 
//            it to take time to verify nothing needs to be done).  We may
//            end up replaying some blocks to force consistency of the DB, 
//            and this method needs to be robust to replaying already-added
//            blocks, as well as fixing data if the replayed block appears
//            to have been added already but is different.
//
bool BlockDataManager_LevelDB::insertBlockData(StoredHeader const & sbh, 
                                     bool notNecessarilyValid)
{
   StoredHeader sbhTemp;
   if(!iface_->getBareHeader(sbhTemp, sbh.thisHash_))
   {
      LOGERR << "Cannot add full block until it's added to the HEADERS DB"; 
      return false;
   }

   if(sbh.stxMap_.size() == 0)
   {
      LOGERR << "Cannot add block without transactions!";
      return false;
   }

   // Consider if the block is already in here
   if(sbh.duplicateID_ == UINT8_MAX)
   {
      LOGERR << "Dup ID must be set already before calling insertBlockData";
      return false;
   }
   
   uint32_t height = sbh.blockHeight_;
   uint8_t  dupID  = sbh.duplicateID_;

   map<BinaryData, StoredScriptHistory> sshToModify;
   map<BinaryData, StoredTxHints>       hintsToModify;
   map<BinaryData, StoredTx>            stxToAdd;
   map<BinaryData, StoredTxOut>         stxosToModify;
   set<BinaryData>                      keysToDelete;

   for(uint32_t itx=0; itx<sbh.stxMap_.size(); itx++)
   {

   }
}
*/



////////////////////////////////////////////////////////////////////////////////
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
bool BlockDataManager_LevelDB::applyTxToBatchWriteData(
                        StoredTx &                             thisSTX,
                        map<BinaryData, StoredTx> &            stxToModify,
                        map<BinaryData, StoredScriptHistory> & sshToModify,
                        set<BinaryData> &                      keysToDelete,
                        StoredUndoData *                       sud)
{
   SCOPED_TIMER("applyTxToBatchWriteData");

   Tx tx = thisSTX.getFullTxCopy();

   // We never expect thisSTX to already be in the map (other tx in the map
   // may be affected/retrieved multiple times).  
   if(stxToModify.find(tx.getThisHash()) != stxToModify.end())
      LOGERR << "How did we already add this tx?";

   // I just noticed we never set TxOuts to TXOUT_UNSPENT.  Might as well do 
   // it here -- by definition if we just added this Tx to the DB, it couldn't
   // have been spent yet.
   map<uint16_t, StoredTxOut>::iterator iter;
   for(iter = thisSTX.stxoMap_.begin(); iter != thisSTX.stxoMap_.end(), iter++)
      iter->second.spentness_ = TXOUT_UNSPENT;

   // This tx itself needs to be added to the map, which makes it accessible 
   // to future tx in the same block which spend outputs from this tx, without
   // doing anything crazy in the code here
   stxToModify[tx.getThisHash()] = thisSTX;
   
   // Go through and find all the previous TxOuts that are affected by this tx
   StoredTx stxTemp;
   StoredScriptHistory sshTemp;
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      TxIn txin = tx.getTxIn(iin);
      if(txin.isCoinbase())
         continue;

      // Get the OutPoint data of TxOut being spent
      OutPoint      op       = txin.getOutPoint()
      BinaryDataRef opTxHash = op.getTxHashRef();
      uint32_t      opTxoIdx = op.getTxOutIndex();

      // This will fetch the STX from DB and put it in the stxToModify
      // map if it's not already there.  Or it will do nothing if it's
      // already part of the map.  In both cases, it returns a pointer
      // to the STX that will be written to DB that we can modify.
      StoredTx    * stxptr  = makeSureSTXInMap(opTxHash, stxToModify);
      StoredTxOut & stxo    = stxptr->stxoMap_[opTxoIdx];
      BinaryData    uniqKey = stxo.getScrAddrObj();

      // Update the stxo by marking it spent by this Block:TxIndex:TxInIndex
      map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(opTxoIdx);
      
      // Some sanity checks
      if(iter == stxptr->stxoMap_.end())
      {
         LOGERR << "Needed to get OutPoint for a TxIn, but DNE";
         continue;
      }

      // We're aliasing this because "iter->second" is not clear at all
      StoredTxOut & stxoSpend = iter->second;
   
      if(stxoSpend.spentness_ == TXOUT_SPENT)
      {
         LOGERR << "Trying to mark TxOut spent, but it's already marked";
         continue;
      }

      // Just about to {remove-if-pruning, mark-spent-if-not} STXO
      // Record it in the StoredUndoData object
      if(sud != NULL)
         sud->stxOutsRemovedByBlock_.push_back(stxoSpend);

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxoSpend.spentness_      = TXOUT_SPENT;
      stxoSpend.spentByTxInKey_ = thisSTX.getDBKeyOfChild(iin);

      if(ARMDB.getArmoryDbType() != ARMORY_DB_SUPER)
      {
         LOGERR << "Don't know what to do this in non-supernode mode!";
      }

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      StoredScriptHistory * sshptr = makeSureSSHInMap(uniqKey, sshToModify);

      // Assuming supernode, we don't need to worry about removing references
      // to multisig scripts that reference this script.  Simply find and 
      // update the correct SSH TXIO directly
      markTxOutSpentInSSH(*sshptr, 
                          stxoSpend.getDBKey(false),
                          thisSTX.getDBKeyOfChild(iin));
   }



   // We don't need to update any TXDATA, since it is part of writing thisSTX
   // to the DB ... but we do need to update the StoredScriptHistory objects
   // with references to the new [unspent] TxOuts
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      StoredTxOut & stxoToAdd = thisSTX.stxoMap_[iout];
      BinaryData uniqKey = stxoToAdd.getScrAddrObj();
      StoredScriptHistory* sshptr=makeSureSSHInMap(uniqKey, sshToModify, true);

      if(ARMDB.getArmoryDbType() != ARMORY_DB_SUPER)
      {
         LOGERR << "Figure out how to handle this since not all SSH in DB will";
         LOGERR << "be updated on every tx and block";
      }

      // Add reference to the next STXO to the respective SSH object
      markTxOutUnspentInSSH( *sshptr, 
                             stxoToAdd.getDBKey(false),
                             stxoToAdd.getValue(),
                             stxoToAdd.isCoinbase_,
                             false);
                             
      // If this was a multisig address, add a ref to each individual scraddr
      if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {
         BinaryData thisOutKey = thisSTX.getDBKeyOfChild(iout);

         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxo.getScriptRef(), addr160List);
         for(uint32_t a=0; a<addr160List.size(); i++)
         {
            // Get the existing SSH or make a new one
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];
            StoredScriptHistory* sshms = makeSureSSHInMap(uniqKey,
                                                          sshToModify, 
                                                          true);
            addMultisigEntryToSSH(*sshms, thisSTX.getDBKeyOfChild(iout);
         }
      }
   }
   return true;
}




////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::addRawBlockToDB(BinaryRefReader & brr)
{
   SCOPED_TIMER("addRawBlockToDB");

   if(!sbh.isInitialized())
   {
      LOGERR << "Cannot add raw block to DB when SBH object is uninitialized";
      return false;
   }
   
   if(sbh.stxMap_.size() == 0)
   {
      LOGERR << "Cannot add raw block to DB without any transactions";
      return false;
   }

   if(sbh.blockHeight_==UINT32_MAX || sbh.duplicateID_==UINT8_MAX)
   {
      LOGERR << "Cannot add raw block to DB without hgt & dup";
      return false;
   }

   BinaryDataRef first4 = brr.get_BinaryDataRef(4);
   
   // Skip magic bytes and block sz if exist, put ptr at beginning of header
   if(first4 == READHEX("f9beb4d9"))
      brr.advance(4);
   else
      brr.rewind(4);
   

   StoredHeader sbh;
   sbh.unserializeFullBlock(brr, true, false);
   sbh.blockAppliedToDB_ = false;
   iface_->putStoredHeader(sbh, true);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::applyBlockToDB(uint32_t hgt, 
                                              uint8_t  dup)
{
   StoredHeader sbh;
   iface_->getStoredHeader(sbh, hgt, dup);
   return applyBlockToDB(sbh);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::applyBlockToDB(StoredHeader & sbh)
{
   SCOPED_TIMER("applyBlockToDB");

   if(iface_->getValidDupIDForHeight(hgt) != dup)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return false;
   }

   // Start with some empty maps, and fill them with existing DB data, or 
   // create new data.  Either way, whatever ends up in these maps will
   // but pushed to the backing DB.
   map<BinaryData, StoredTx>              stxToModify;
   map<BinaryData, StoredScriptHistory>   sshToModify;
   set<BinaryData>                        keysToDelete;

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_   = sbh.thisHash_; 
   sud.blockHeight_ = sbh.blockHeight_;
   sud.duplicateID_ = sbh.duplicateID_;

   // Apply all the tx to the update data
   map<uint16_t, StoredTx>::iterator iter;
   for(iter = sbh.stxMap_.begin(); iter != sbh.stxMap_.end(); iter++)
   {
      // This will fetch all the affected [Stored]Tx and modify the maps in 
      // RAM.  It will check the maps first to see if it's already been pulled,
      // and then it will modify either the pulled StoredTx or pre-existing
      // one.  This means that if a single Tx is affected by multiple TxIns
      // or TxOuts, earlier changes will not be overwritten by newer changes.
      applyTxToBatchWriteData(*iter, 
                              stxToModify, 
                              sshToModify, 
                              keysToDelete,
                              &sud);
   }

   // At this point we should have a list of STX and SSH with all the correct
   // modifications (or creations) to represent this block.  Let's apply it.
   iface_->startBatch(BLKDATA)

   sbh.blockAppliedToDB_ = true;
   iface_->putStoredHeader(sbh, false);

   map<BinaryData, StoredTx>::iterator iter_stx;
   for(iter_stx  = stxToModify.begin();
       iter_stx != stxToModify.end();
       iter_stx++)
   {
      iface_->putStoredTx(*iter_stx);
   }
       
   map<BinaryData, StoredScriptHistory>::iterator iter_ssh;
   for(iter_ssh  = sshToModify.begin();
       iter_ssh != sshToModify.end();
       iter_ssh++)
   {
      iface_->putStoredScriptHistory(*iter_ssh);

   }

   set<BinaryData>::iterator iter_del;
   for(iter_del  = keysToDelete.begin();
       iter_del != keysToDelete.end();
       iter_del++)
   {
      iface_->deleteValue(BLKDATA, *iter_del);
   }

   // Only if pruning, we need to store 
   if(ARMDB.getDbPruneType() == DB_PRUNE_ALL)
      iface_->putStoredUndoData(sud);

   iface_->commitBatch(BLKDATA)
   return true;
}



////////////////////////////////////////////////////////////////////////////////
// For now, we will call createUndoDataFromBlock(), and then pass that data to 
// undoBlockFromDB(), even though it will result in accessing the DB data 
// twice --
//    (1) LevelDB does an excellent job caching results, so the second lookup
//        should be instantaneous
//    (2) We prefer to integrate StoredUndoData objects now, which will be 
//        needed for pruning even though we don't strictly need it for no-prune
//        now (and could save a lookup by skipping it).  But I want unified
//        code flow for both pruning and non-pruning. 
bool BlockDataManager_LevelDB::createUndoDataFromBlock(uint32_t hgt, 
                                                       uint8_t  dup,
                                                       StoredUndoData & sud)
{
   SCOPED_TIMER("createUndoDataFromBlock");

   // This is garbage code right here, I haven't actually impl
   StoredUndoData sud;
   StoredHeader sbh;

   // Fetch the full, stored block
   iface_->getStoredHeader(sbh, hgt, dup, true);
   if(!sbh.haveFullBlock())
   {
      LOGERR <<< "Cannot get undo data for block because not full!";
      return false;
   }

   sud.blockHash_   = sbh.thisHash_;
   sud.blockHeight_ = sbh.blockHeight_;
   sud.duplicateID_ = sbh.duplicateID_;

   // Go through tx list, fetch TxOuts that are spent, record OutPoints added
   for(uint32_t itx=0; itx<sbh.numTx_; itx++)
   {
      StoredTx & stx = sbh.stxMap_[itx];
      
      // Convert to a regular tx to make accessing TxIns easier
      Tx regTx = stx.getTxCopy();
      for(uint32_t iin=0; iin<regTx.getNumTxIn(); iin++)
      {
         TxIn txin = regTx.getTxIn(iin);
         BinaryDataRef prevHash  = txin.getOutPoint().getTxHashRef();
         BinaryDataRef prevIndex = txin.getOutPoint().getTxOutIndex();
         
         // Above we checked the block to be undone is full, but we
         // still need to make sure the prevTx we just fetched has our data.
         StoredTx prevStx;
         iface_->getStoredTx(prevStx, prevHash);
         if(prevStx.stxoMap_.find(prevIndex) == prevStx.stxoMap_.end())
         {
            LOGERR << "StoredTx retrieved from DB, but TxOut not with it";
            return false;
         }
         
         // 
         sud.stxOutsRemovedByBlock_.push_back(prevStx.stxoMap_[prevIndex]);
      }
      
      // Use the stxoMap_ to iterate through TxOuts
      for(uint32_t iout=0; iout<stx.numTxOut_; iout++)
      {
         OutPoint op(stx.thisHash_, iout);
         sud.outPointsAddedByBlock_.push_back(op);
      }
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::undoBlockFromDB(StoredUndoData const & sud)
{
   SCOPED_TIMER("undoBlockFromDB");

   StoredHeader sbh;
   iface_->getStoredHeader(sbh, sud.blockHeight_, sud.duplicateID_, false);
   if(!sbh.blockAppliedToDB_)
   {
      LOGERR << "This block was never applied to the DB...can't undo!";
      return false;
   }

   map<BinaryData, StoredTx>              stxToModify;
   map<BinaryData, StoredScriptHistory>   sshToModify;
   set<BinaryData>                        keysToDelete;
    
   // In the future we will accommodate more user modes
   if(ARMDB.getArmoryDbType() != ARMORY_DB_SUPER)
   {
      LOGERR << "Don't know what to do this in non-supernode mode!";
   }
   

   ///// Put the STXOs back into the DB which were removed by this block
   // Process the stxOutsRemovedByBlock_ in reverse order
   for(uint32_t i=sud.stxOutsRemovedByBlock_.size()-1; i>=0; i--)
   {
      StoredTxOut & sudStxo = stxOutsRemovedByBlock_[i];
      StoredTx * stxptr = makeSureSTXInMap( sudStxo.blockHeight_,
                                            sudStxo.duplicateID_,
                                            sudStxo.txIndex_,
                                            sudStxo.parentHash_,
                                            stxToModify);
      
      uint16_t stxoIdx = sudStxo.txOutIndex_;
      map<uint16_t,StoredTxOut>::iterator iter;


      if(ARMDB.getDbPruneType() == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
         iter = stxptr->stxoMap_.find(stxoIdx);
         if(iter == stxptr->stxoMap_.end())
         {
            LOGERR << "Expecting to find existing STXO, but DNE";
            continue;
         }

         StoredTxOut & stxoReAdd = iter->second;
         if(stxoReAdd.spentness_ == TXOUT_UNSPENT || 
            stxoReAdd.spentByTxInKey_.size() == 0 )
         {
            LOGERR << "STXO needs to be re-added/marked-unspent but it";
            LOGERR << "was already declared unspent in the DB";
         }
         
         stxoReAdd.spentness_ = TXOUT_UNSPENT;
         stxoReAdd.spentByTxInKey_ = BinaryData(0);
      }
      else
      {
         // If we're pruning, we should have the Tx in the DB, but without the
         // TxOut because it had been pruned by this block on the forward op
         if(stxptr->stxoMap_[stxoIdx] != stxptr->stxoMap_.end())
            LOGERR << "Somehow this TxOut had not been pruned!" << endl;
         else
            stxptr->stxoMap_[stxoIdx] = sudStxo;

         stxptr->stxoMap_[stxoIdx].spentness_      = TXOUT_UNSPENT;
         stxptr->stxoMap_[stxoIdx].spentByTxInKey_ = BinaryData(0);
      }

      ////// Finished updating STX, now update the SSH in the DB
      // Updating the SSH objects works the same regardless of pruning
      iter = stxptr->stxoMap_.find(stxoIdx);
      if(iter == stxptr->stxoMap_.end())
      {
         LOGERR << "Somehow STXO DNE even though we should've just added it!";
         continue;
      }

      StoredTxOut & stxoReAdd = iter->second;
   
      // Always a primary SSH to update (compared to multisig entries)
      BinaryData uniqKey = stxoReAdd.getScrAddrObj();
      StoredScriptHistory* sshptr = makeSureSSHInMap(uniqKey, sshToModify);
      if(sshptr==NULL)
      {
         LOGERR << "No SSH found for marking TxOut unspent on undo";
         continue;
      }

      // Now get the TxIOPair in the StoredScriptHistory and mark unspent
      markTxOutUnspentInSSH( *sshptr,
                             stxoReAdd.getDBKey(false),
                             stxoReAdd.getValue(),
                             stxoReAdd.isCoinBase_,
                             false);

      
      // If multisig, we need to update the SSHs for individual addresses
      if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {

         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxo.getScriptRef(), addr160List);
         for(uint32_t a=0; a<addr160List.size(); i++)
         {
            // Get the existing SSH or make a new one
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];
            StoredScriptHistory* sshptr = makeSureSSHInMap(uniqKey, sshToModify);
            addMultisigEntryToSSH(*sshptr, stxoReAdd.getDBKey(false));
         }
      }
   }


   // The OutPoint list is every new, unspent TxOut created by this block.
   // When they were added, we updated all the StoredScriptHistory objects
   // to include references to them.  We need to remove them now.
   for(uint32_t i=sud.outPointsAddedByBlock_.size()-1; i>=0; i--)
   {
      BinaryData txHash  = sud.outPointsAddedByBlock_[i].getTxHash();
      uint16_t   txoIdx  = sud.outPointsAddedByBlock_[i].getTxOutIndex();

      // Get the STX (all of which should be from this block we're undoing)
      StoredTx *    stxptr  = makeSureSTXInMap(txHash, stxToModify);
      StoredTxOut & stxo    = stxptr->stxoMap_[txoIdx];
      BinaryData    stxoKey = stxo.getDBKey(false);

      // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
      BinaryData uniq = stxo.getScrAddress();
      StoredScriptHistory * sshptr = makeSureSSHInMap(uniq, sshToModify, false);

      // If we are tracking that SSH, remove the reference to this OutPoint
      if(sshptr != NULL)
         removeTxOutFromSSH(*sshptr, stxoKey);

      // Now remove any multisig entries that were added due to this TxOut
      if(uniq[0] == SCRIPT_PREFIX_MULTISIG)
      {
         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxo.getScriptRef(), addr160List);
         for(uint32_t a=0; a<addr160List.size(); i++)
         {
            // Get the individual address obj for this multisig piece
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];
            StoredScriptHistory* sshms = makeSureSSHInMap(uniqKey,
                                                          sshToModify, 
                                                          true);
            removeMultisigEntryFromSSH(*sshms, stxoKey);
         }
      }
   }



   // Check for any SSH objects that are now completely empty.  If they exist,
   // they should be removed from the DB, instead of simply written as empty
   // objects
   map<BinaryData, StoredScriptHistory>::iterator iter;
   for(iter  = sshToModify.begin(); 
       iter != sshToModify.end();
       iter++)
   {
      if(iter->second.multisigDBKeys_.size() == 0 &&
         iter->second.txioVect_.size() == 0)
         keysToDelete.insert(iter->first);
   }


   // Finally, mark this block as UNapplied.
   sbh.blockAppliedToDB_ = false;
   iface_->putStoredHeader(sbh, false);

   return true;
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::removeTxOutFromSSH(
                                            StoredScriptHistory & ssh,
                                            BinaryData txOutKey8B)
{
   for(uint32_t i=0; i<ssh.txioVect_.size(); i++)
   {
      TxIOPair & txio = ssh.txioVect_[i];
      BinaryData txoKey = txio.getDBKeyOfOutput();
      if(txoKey == ldbKey8B)
      {
         ssh.txioVect_.erase(ssh.txioVect_.begin() + i);
         return true;
      }
   }

   LOGERR << "TxOut did not exist in SSH to be removed";
   return false;
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::markTxOutSpentInSSH(
                                            StoredScriptHistory & ssh,
                                            BinaryData txOutKey8B,
                                            BinaryData txInKey8B)
{
   for(uint32_t i=0; i<ssh.txioVect_.size(); i++)
   {
      TxIOPair & txio = ssh.txioVect_[i];
      BinaryData txoKey = txio.getDBKeyOfOutput();
      if(txoKey == ldbKey8B)
      {
         // We found the TxIO we care about 
         if(ARMDB.getDbPruneType() == DB_PRUNE_NONE)
         {
            // No pruning, Expect unspent, mark it as spent 
            if(txInKey8B.getSize() == 0)
               LOGERR << "Need to mark STXO spent, but no spent-by key given";
            else if(txio.hasTxIn())
               LOGERR << "TxOut is already marked as spent";
            else
            {
               txio.setTxIn(txInKey8B);
               return true;
            }
         }
         else
         {
            // ssh.txioVect_.erase(i);  // ?
            LOGERR << "Have not yet implemented pruning logic yet!";
            return false;
         }
      }
   } 

   // If we got here... then we never found the STXO in the SSH
   if(ARMDB.getDbPruneType() == DB_PRUNE_NONE)
   {
      LOGERR << "We should've found an STXO in the SSH but didn't";
      return false;
   }

   

   return true;
}
                                             
////////////////////////////////////////////////////////////////////////////////
// We only need the last three args (value, isCB, isSelf) if pruning.
// **Will add to the SSH txio list if not present
bool BlockDataManager_LevelDB::markTxOutUnspentInSSH(
                                            StoredScriptHistory & ssh,
                                            BinaryData txOutKey8B,
                                            uint64_t value,
                                            bool isCoinBase,
                                            bool isFromSelf)
{
   for(uint32_t i=0; i<ssh.txioVect_.size(); i++)
   {
      TxIOPair & txio = ssh.txioVect_[i];
      BinaryData txoKey = txio.getDBKeyOfOutput();
      if(txoKey == ldbKey8B)
      {
         if(ARMDB.getDbPruneType() == DB_PRUNE_NONE)
         {
            // Expect spent, mark it as unspent 
            if(!txio.hasTxIn()) 
            {
               LOGERR << "STXO already marked unspent in SSH";
               return false;
            }
            else
            {
               txio.setTxIn(TxRef(), UINT32_MAX);
               return true;
            }
         }
         else
         {
            LOGERR << "Found STXO that we expected to already be pruned...";
            return false;
         }
      }
   }

   // For non-pruning DB, we should never get here
   //if(ARMDB.getDbPruneType() == DB_PRUNE_NONE)
   //{
      //LOGERR << "Somehow STXO-to-mark-unspent did not exist in SSH";
      //return false;
   //}
   // We actually expect to get here non-pruning, because we may be calling
   // this to ADD the TxIO instead of just updating it

   TxIOPair txio = TxIOPair()
   txio.setValue(value);
   txio.setTxOut(txOutKey8B);
   txio.setFromCoinbase(isCoinBase);
   txio.setTxOutFromSelf(isFromSelf);
   ssh.txioVect_.push_back(txio);
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::addMultisigEntryToSSH(
                                            StoredScriptHistory & ssh,
                                            BinaryData txOutKey8B)
{
   for(uint32_t i=0; i<ssh.multisigDBKeys_.size(); i++)
   {
      if(ssh.multisigDBKeys_[i] == txOutKey8B)
      {
         LOGERR << "Already have multisig entry in SSH";
         return false;
      }
   } 

   ssh.multisigDBKeys_.push_back(txOutKey8B);
   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::removeMultisigEntryFromSSH(
                                            StoredScriptHistory & ssh,
                                            BinaryData txOutKey8B)
{
   for(uint32_t i=0; i<ssh.multisigDBKeys_.size(); i++)
   {
      if(ssh.multisigDBKeys_[i] == txOutKey8B)
      {
         ssh.multisigDBKeys_.erase(ssh.multisigDBKeys_.begin() + i);
         return true;
      }
   } 

   
   LOGERR << "Multisig entry in SSH did not exist before, cannot remove!";
   return false;
    
}

////////////////////////////////////////////////////////////////////////////////
StoredScriptHistory* BlockDataManager_LevelDB::makeSureSSHInMap(
                           BinaryDataRef uniqKey,
                           map<BinaryData, StoredScriptHistory> & sshMap,
                           bool createIfDNE)
{
   StoredScriptHistory * sshptr;
   StoredScriptHistory   sshTemp;

   // If already in Map
   if(sshMap.find(uniqKey) != sshMap.end())
      stxptr = &sshToModify[uniqKey];
   else
   {
      iface_->getStoredScriptHistory(sshTemp, uniqKey);
      if(sshTemp.isInitialized())
      {
         // We already have an SSH in DB -- simply modify it
         sshMap[uniqKey] = sshTemp; 
         sshptr = &sshMap[uniqKey];
      }
      else
      {
         if(!createIfDNE)
            return NULL;

         sshMap[uniqKey] = StoredScriptHistory(); 
         sshptr = &sshMap[uniqKey];
         sshptr->uniqueKey_ = uniqKey;

      }
   }

   return sshptr;
}


////////////////////////////////////////////////////////////////////////////////
StoredTx* BlockDataManager_LevelDB::makeSureSTXInMap(
                                       BinaryDataRef txHash,
                                       map<BinaryData, StoredTx> & stxMap);
{
   // TODO:  If we are pruning, we may have completely removed this tx from
   //        the DB, which means that it won't be in the map or the DB.
   //        But this method was written before pruning was ever implemented...
   StoredTx * stxptr;
   StoredTx   stxTemp;

   // Get the existing STX or make a new one
   if(stxMap.find(txHash) != stxMap.end())
      stxptr = &stxMap[txHash];
   else
   {
      iface_->getStoredTx(stxTemp, txHash);
      stxMap[txHash] = stxTemp;
      stxptr = &stxMap[txHash];
   }
   
   return stxptr;
}

////////////////////////////////////////////////////////////////////////////////
// This avoids having to do the double-lookup when fetching by hash.
// We still pass in the hash anyway, because the map is indexed by the hash,
// and we'd like to not have to do a lookup for the hash if only provided
// {hgt, dup, idx}
StoredTx* BlockDataManager_LevelDB::makeSureSTXInMap(
                                       uint32_t hgt,
                                       uint8_t  dup,
                                       uint16_t txIdx,
                                       BinaryDataRef txHash,
                                       map<BinaryData, StoredTx> & stxMap);
{
   StoredTx * stxptr;
   StoredTx   stxTemp;

   // Get the existing STX or make a new one
   if(stxMap.find(txHash) != stxMap.end())
      stxptr = &stxMap[txHash];
   else
   {
      iface_->getStoredTx(stxTemp, hgt, dup, txIdx);
      stxMap[txHash] = stxTemp;
      stxptr = &stxMap[txHash];
   }
   
   return stxptr;
}




