////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "BlockUtils.h"


BlockDataManager_FullRAM* BlockDataManager_FullRAM::theOnlyBDM_ = NULL;

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxIOPair Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(void) : 
   amount_(0),
   txPtrOfOutput_(NULL),
   indexOfOutput_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0),
   txPtrOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txPtrOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(uint64_t  amount) :
   amount_(amount),
   txPtrOfOutput_(NULL),
   indexOfOutput_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0),
   txPtrOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txPtrOfInputZC_(NULL),
   indexOfInputZC_(0) ,
   isTxOutFromSelf_(false) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef* txPtrO, uint32_t txoutIndex) :
   amount_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0) ,
   txPtrOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txPtrOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false)
{ 
   setTxOutRef(txPtrO, txoutIndex);
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef*    txPtrO,
                   uint32_t  txoutIndex,
                   TxRef*    txPtrI, 
                   uint32_t  txinIndex) :
   amount_(0),
   txPtrOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txPtrOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false)
{ 
   setTxOutRef(txPtrO, txoutIndex);
   setTxInRef (txPtrI, txinIndex );
}


//////////////////////////////////////////////////////////////////////////////
BinaryData TxIOPair::getTxHashOfOutput(void)
{
   if(!hasTxOut())
      return BtcUtils::EmptyHash_;
   else
      return txPtrOfOutput_->getThisHash();
}

//////////////////////////////////////////////////////////////////////////////
BinaryData TxIOPair::getTxHashOfInput(void)
{
   if(!hasTxIn())
      return BtcUtils::EmptyHash_;
   else
      return txPtrOfInput_->getThisHash();
}

TxOutRef TxIOPair::getTxOutRef(void) const
{
   // I actually want this to segfault when there is no TxOutRef... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code
   if(hasTxOut())
      return txPtrOfOutput_->getTxOutRef(indexOfOutput_);
   else
      return getTxOutRefZC();
}

TxInRef TxIOPair::getTxInRef(void) const
{
   if(hasTxIn())
      return txPtrOfInput_->getTxInRef(indexOfInput_);
   else
      return getTxInRefZC();
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxInRef(TxRef* txref, uint32_t index, bool isZeroConf)
{ 
   if(isZeroConf)
   {
      if(hasTxInInMain() || hasTxInZC())
         return false;
      else
      {
         txPtrOfInput_    = NULL;
         indexOfInput_    = 0;
         txPtrOfInputZC_  = txref;
         indexOfInputZC_  = index;
      }
   }
   else
   {
      txPtrOfInput_  = txref;
      indexOfInput_  = index;
      txPtrOfInputZC_  = NULL;
      indexOfInputZC_  = 0;
   }

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxOutRef(TxRef* txref, uint32_t index, bool isZeroConf)
{
   if(isZeroConf)
   {
      if(hasTxOutInMain() || hasTxOutZC())
         return false;
      else
      {
         txPtrOfOutput_   = NULL;
         indexOfOutput_   = 0;
         txPtrOfOutputZC_ = txref; 
         indexOfOutputZC_ = index;
         if(hasTxOutZC())
            amount_ = getTxOutRefZC().getValue();
      }
   }
   else
   {
      txPtrOfOutput_ = txref; 
      indexOfOutput_ = index;
      txPtrOfOutputZC_ = NULL;
      indexOfOutputZC_ = 0;
      if(hasTxOut())
         amount_ = getTxOutRef().getValue();
   }
   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isStandardTxOutScript(void) 
{ 
   if(hasTxOut()) 
      return getTxOutRef().isStandard();
   return false;
}

//////////////////////////////////////////////////////////////////////////////
pair<bool,bool> TxIOPair::reassessValidity(void)
{
   pair<bool,bool> result;
   result.first  = hasTxOutInMain();
   result.second = hasTxInInMain();
   return result;
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpent(void)
{ 
   // Not sure whether we should verify hasTxOut.  It wouldn't make much 
   // sense to have TxIn but not TxOut, but there might be a preferred 
   // behavior in such awkward circumstances
   return (hasTxInInMain() || hasTxInZC());
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isUnspent(void)
{ 
   return ( (hasTxOut() || hasTxOutZC()) && !isSpent());

}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpendable(void) 
{ 
   // Spendable TxOuts are ones with at least 1 confirmation, or zero-conf
   // TxOuts that were sent-to-self.  Obviously, they should be unspent, too
   if( hasTxInInMain() || hasTxInZC() )
      return false;
   
   if( hasTxOutInMain() )
      return true;

   if( hasTxOutZC() && isTxOutFromSelf() )
      return true;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isMineButUnconfirmed(uint32_t currBlk, uint32_t minConf)
{
   // Only zero-conf Tx can be unconfirmed
   if( (hasTxIn() && txPtrOfInput_->isMainBranch()) || hasTxInZC() )
      return false;

   if( hasTxOut() && txPtrOfOutput_->isMainBranch() )
   {
      uint32_t nConf = currBlk - txPtrOfOutput_->getBlockHeight() + 1;
      if(nConf<minConf)
         return true;
   }
   else if( hasTxOutZC() && !isTxOutFromSelf() )
   {
      return true;
   }


   return false;
}

bool TxIOPair::hasTxOutInMain(void) const
{
   return (hasTxOut() && txPtrOfOutput_->isMainBranch());
}

bool TxIOPair::hasTxInInMain(void) const
{
   return (hasTxIn() && txPtrOfInput_->isMainBranch());
}

void TxIOPair::clearZCFields(void)
{
   txPtrOfOutputZC_ = NULL;
   txPtrOfInputZC_  = NULL;
   indexOfOutputZC_ = 0;
   indexOfInputZC_  = 0;
   isTxOutFromSelf_ = false;
}


void TxIOPair::pprintOneLine(void)
{
   printf("   Val:(%0.3f)\t  (STS, O,I, Omb,Imb, Oz,Iz)  %d  %d%d %d%d %d%d\n", 
           (double)getValue()/1e8,
           (isTxOutFromSelf() ? 1 : 0),
           (hasTxOut() ? 1 : 0),
           (hasTxIn() ? 1 : 0),
           (hasTxOutInMain() ? 1 : 0),
           (hasTxInInMain() ? 1 : 0),
           (hasTxOutZC() ? 1 : 0),
           (hasTxInZC() ? 1 : 0));

}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator<(LedgerEntry const & le2) const
{
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
   return (blockNum_ == le2.blockNum_ && index_ == le2.index_);
}

void LedgerEntry::pprint(void)
{
   cout << "LedgerEntry: " << endl;
   cout << "   Addr20  : " << getAddrStr20().toHexStr() << endl;
   cout << "   Value   : " << getValue()/1e8 << endl;
   cout << "   BlkNum  : " << getBlockNum() << endl;
   cout << "   TxHash  : " << getTxHash().toHexStr() << endl;
   cout << "   TxIndex : " << getIndex() << endl;
   cout << "   isValid : " << (isValid() ? 1 : 0) << endl;
   cout << "   sentSelf: " << (isSentToSelf() ? 1 : 0) << endl;
   cout << "   isChange: " << (isChangeBack() ? 1 : 0) << endl;
   cout << endl;
}

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
// BtcAddress Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BtcAddress::BtcAddress(BinaryData    addr, 
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp,
                       uint32_t      lastBlockNum,
                       uint32_t      lastTimestamp) :
      address20_(addr), 
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp),
      lastBlockNum_(lastBlockNum), 
      lastTimestamp_(lastTimestamp)
{ 
   relevantTxIOPtrs_.clear();
   relevantTxIOPtrsZC_.clear();
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t BtcAddress::getSpendableBalance(void)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isSpendable())
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      if(relevantTxIOPtrsZC_[i]->isSpendable())
         balance += relevantTxIOPtrsZC_[i]->getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcAddress::getUnconfirmedBalance(uint32_t currBlk)
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
uint64_t BtcAddress::getFullBalance(void)
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
vector<UnspentTxOut> BtcAddress::getSpendableTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isSpendable())
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back( UnspentTxOut(txoutref, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isSpendable())
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back( UnspentTxOut(txoutref, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BtcAddress::getFullTxOutList(uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isUnspent())
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back( UnspentTxOut(txoutref, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isUnspent())
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back( UnspentTxOut(txoutref, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BtcAddress::removeInvalidEntries(void)   
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
void BtcAddress::sortLedger(void)
{
   sort(ledger_.begin(), ledger_.end());
}

////////////////////////////////////////////////////////////////////////////////
void BtcAddress::addLedgerEntry(LedgerEntry const & le, bool isZeroConf)
{ 
   if(isZeroConf)
      ledgerZC_.push_back(le);
   else
      ledger_.push_back(le);
}

////////////////////////////////////////////////////////////////////////////////
void BtcAddress::addTxIO(TxIOPair * txio, bool isZeroConf)
{ 
   if(isZeroConf)
      relevantTxIOPtrsZC_.push_back(txio);
   else
      relevantTxIOPtrs_.push_back(txio);
}

////////////////////////////////////////////////////////////////////////////////
void BtcAddress::addTxIO(TxIOPair & txio, bool isZeroConf)
{ 
   if(isZeroConf)
      relevantTxIOPtrsZC_.push_back(&txio);
   else
      relevantTxIOPtrs_.push_back(&txio);
}

////////////////////////////////////////////////////////////////////////////////
void BtcAddress::pprintLedger(void)
{ 
   cout << "Address Ledger: " << getAddrStr20().toHexStr() << endl;
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
void BtcWallet::addAddress(BinaryData    addr, 
                           uint32_t      firstTimestamp,
                           uint32_t      firstBlockNum,
                           uint32_t      lastTimestamp,
                           uint32_t      lastBlockNum)
{

   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, firstTimestamp, firstBlockNum,
                               lastTimestamp,  lastBlockNum);
   addrPtrVect_.push_back(addrPtr);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress(BtcAddress const & newAddr)
{
   if(newAddr.getAddrStr20().getSize() > 0)
   {            
      BtcAddress * addrPtr = &(addrMap_[newAddr.getAddrStr20()]);
      *addrPtr = newAddr;
      addrPtrVect_.push_back(addrPtr);
   }
}


/////////////////////////////////////////////////////////////////////////////
// SWIG has some serious problems with typemaps and variable arg lists
// Here I just create some extra functions that sidestep all the problems
// but it would be nice to figure out "typemap typecheck" in SWIG...
void BtcWallet::addAddress_BtcAddress_(BtcAddress const & newAddr)
{ 
   addAddress(newAddr); 
}
void BtcWallet::addAddress_1_(BinaryData    addr)
{  
   PDEBUG("Adding address to BtcWallet");
   addAddress(addr); 
} 
void BtcWallet::addAddress_3_(BinaryData    addr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum)
{  
   addAddress(addr, firstBlockNum, firstTimestamp); 
}

void BtcWallet::addAddress_5_(BinaryData    addr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum,
                              uint32_t      lastTimestamp,
                              uint32_t      lastBlockNum)
{  
   addAddress(addr, firstBlockNum, firstTimestamp, lastBlockNum, lastTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasAddr(BinaryData const & addr20)
{
   return addrMap_.find(addr20) != addrMap_.end();
}

/////////////////////////////////////////////////////////////////////////////
// Determine, as fast as possible, whether this tx is relevant to us
// Return  <IsOurs, InputIsOurs>
pair<bool,bool> BtcWallet::isMineBulkFilter( TxRef & tx )
{
   // Since 99.999%+ of all transactions are not ours, let's do the 
   // fastest bulk filter possible, even though it will add 
   // redundant computation to the tx that are ours.  In fact,
   // we will skip the TxInRef/TxOutRef convenience methods and follow the
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
      static BinaryData addr20(20);

      uint8_t const * ptr = (txStartPtr + tx.getTxOutOffset(iout) + 8);
      scriptLenFirstByte = *(uint8_t*)ptr;
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         addr20.copyFrom(ptr+4, 20);
         if( hasAddr(addr20) )
            return pair<bool,bool>(true,false);
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         static BinaryData addr20(20);
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 65, addr20);
         if( hasAddr(addr20) )
            return pair<bool,bool>(true,false);
      }
      else
      {
         TxOutRef txout = tx.getTxOutRef(iout);
         for(uint32_t i=0; i<addrPtrVect_.size(); i++)
         {
            BtcAddress & thisAddr = *(addrPtrVect_[i]);
            BinaryData const & addr20 = thisAddr.getAddrStr20();
            if(txout.getScriptRef().find(thisAddr.getAddrStr20()) > -1)
               scanNonStdTx(0, 0, tx, iout, thisAddr);
            continue;
         }
         break;
      }
   }

   // If we got here, it's either non std or not ours
   return pair<bool,bool>(false,false);

}

/////////////////////////////////////////////////////////////////////////////
// Pass this wallet a TxRef and current time/blknumber.  I used to just pass
// in the BlockHeaderRef with it, but this may be a Tx not in a block yet, 
// but I still need the time/num 
//
// You must clear the zero-conf pool for this address, before you do a 
// rescan of the wallet (it's done in rescanWalletZeroConf)
void BtcWallet::scanTx(TxRef & tx, 
                       uint32_t txIndex,
                       uint32_t txtime,
                       uint32_t blknum)
{
   
   int64_t totalLedgerAmt = 0;
   bool isZeroConf      = blknum==UINT32_MAX;

   vector<bool> thisTxOutIsOurs(tx.getNumTxOut(), false);


   pair<bool,bool> boolPair = isMineBulkFilter(tx);
   bool txIsRelevant  = boolPair.first;
   bool anyTxInIsOurs = boolPair.second;

   if( !txIsRelevant )
      return;

   // TODO: If this tx is relevant but one of the TxIns or TxOuts is not 
   //       valid, we need to avoid modifying the wallet AT ALL and return
   //       to the calling function.  Unfortunately, this is complicated
   //       because the function was originally written under the assumption
   //       that it is valid...

   // We distinguish "any" from "anyNew" because we want to avoid re-adding
   // transactions/TxIOPairs that are already part of the our tx list/ledger
   // but we do need to determine if this was sent-to-self, regardless of 
   // whether it was new.
   bool anyNewTxInIsOurs   = false;
   bool anyNewTxOutIsOurs  = false;
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      BtcAddress & thisAddr = *(addrPtrVect_[i]);
      BinaryData const & addr20 = thisAddr.getAddrStr20();

      ///// LOOP OVER ALL TXIN IN BLOCK /////
      for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
      {
         TxInRef txin = tx.getTxInRef(iin);
         OutPoint outpt = txin.getOutPoint();
         // Empty hash in Outpoint means it's a COINBASE tx --> no addr inputs
         if(outpt.getTxHashRef() == BtcUtils::EmptyHash_)
            continue;

         // We have the txin, now check if it contains one of our TxOuts
         map<OutPoint, TxIOPair>::iterator txioIter = txioMap_.find(outpt);
         bool txioWasInMapAlready = (txioIter != txioMap_.end());
         if(txioWasInMapAlready)
         {
            // If we are here, we know that this input is spending an 
            // output owned by this wallet (though this address may not
            // be the one affected)
            // We need to make sure the ledger entry makes sense, and make
            // sure we update TxIO objects appropriately
            TxIOPair & txio  = txioIter->second;
            TxOutRef const & txout = txio.getTxOutRef();

            // Skip if this TxIO is not for this address
            if(!(txout.getRecipientAddr()==thisAddr.getAddrStr20()))
               continue;

            int64_t thisVal = (int64_t)txout.getValue();
            totalLedgerAmt -= thisVal;

            // Skip, if this is a zero-conf-spend, but it's already got a zero-conf
            if( isZeroConf && txio.hasTxInZC() )
               return; // this tx can't be valid, might as well bail now

            if( !txio.hasTxInInMain() && !(isZeroConf && txio.hasTxInZC())  )
            {
               // The legit var only identifies whether this set-call succeeded
               // If it didn't, it's because this is from a zero-conf tx but this 
               // TxIn already exists in the blockchain spending the same output.
               // (i.e. we have a ref to the prev output, but it's been spent!)
               bool isValidNew = txio.setTxInRef(&tx, iin, isZeroConf);
               if(!isValidNew)
                  continue;

               anyNewTxInIsOurs = true;

               LedgerEntry newEntry(addr20, 
                                   -(int64_t)thisVal,
                                    blknum, 
                                    tx.getThisHash(), 
                                    iin,
                                    txtime,
                                    false,  // SentToSelf is meaningless for addr ledger
                                    false); // "isChangeBack" is meaningless for TxIn
               thisAddr.addLedgerEntry(newEntry, isZeroConf);

               // Update last seen on the network
               thisAddr.setLastTimestamp(txtime);
               thisAddr.setLastBlockNum(blknum);
            }
         }
         else
         {
            // Lots of txins that we won't have, this is a normal conditional
            // But we should check the non-std txio list since it may actually
            // be there
            if(nonStdTxioMap_.find(outpt) != nonStdTxioMap_.end())
            {
               nonStdTxioMap_[outpt].setTxInRef(&tx, iin, isZeroConf);
               nonStdUnspentOutPoints_.erase(outpt);
            }
         }
      } // loop over TxIns


      ///// LOOP OVER ALL TXOUT IN TX /////
      for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
      {
         TxOutRef txout = tx.getTxOutRef(iout);
         if( txout.getScriptType() == TXOUT_SCRIPT_UNKNOWN )
         {
            if(txout.getScriptRef().find(thisAddr.getAddrStr20()) > -1)
               scanNonStdTx(blknum, txIndex, tx, iout, thisAddr);
            continue;
         }

         if( txout.getRecipientAddr() == thisAddr.getAddrStr20() )
         {
            // If we got here, at least this TxOut is for this address.
            // But we still need to find out if it's new and update
            // ledgers/TXIOs appropriately
            
            // TODO:  Verify this logic is correct:  totalLedgerAmt will
            //        be used in the wallet-level ledgerEntry.  There are 
            //        a variety of conditions under which we skip processing
            //        the addr-level LE, but we probably still need to keep
            //        an accurate totalLedgerAmt for this tx as a whole
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
                  txioIter->second.setTxOutRef(&tx, iout, isZeroConf);
                  thisAddr.addTxIO( txioIter->second, isZeroConf);
                  doAddLedgerEntry = true;
               }
               else
               {
                  if(txioIter->second.hasTxOutInMain()) // ...but we already have one
                     continue;

                  // If we got here, we have a in-blockchain TxOut that is 
                  // replacing a zero-conf txOut.  Reset the txio to have 
                  // only this real TxOut, blank ZC TxOut.  And the addr 
                  // relevantTxIOPtrs_ does not have this yet so it needs 
                  // to be added (it's already part of the relevantTxIOPtrsZC_
                  // but that will be removed)
                  txioIter->second.setTxOutRef(&tx, iout, isZeroConf);
                  thisAddr.addTxIO( txioIter->second, isZeroConf);
                  doAddLedgerEntry = true;
               }
            }
            else
            {
               // TxIO is not in the map yet -- create and add it
               TxIOPair newTxio;
               newTxio.setTxOutRef(&tx, iout, isZeroConf);
   
               pair<OutPoint, TxIOPair> toBeInserted(outpt, newTxio);
               txioIter = txioMap_.insert(toBeInserted).first;
               thisAddr.addTxIO( txioIter->second, isZeroConf);
               doAddLedgerEntry = true;
            }

            if(anyTxInIsOurs)
               txioIter->second.setTxOutFromSelf();
           
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
                                     false,   // sentToSelf meaningless for addr ledger
                                     false);  // we don't actually know
               thisAddr.addLedgerEntry(newLedger, isZeroConf);
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

   } // loop over all wallet addresses

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
      txrefSet_.insert(&tx);
      LedgerEntry le( BinaryData(0),
                      totalLedgerAmt, 
                      blknum, 
                      tx.getThisHash(), 
                      txIndex,
                      txtime,
                      isSentToSelf,
                      isChangeBack);

      if(isZeroConf)
         ledgerAllAddrZC_.push_back(le);
      else
         ledgerAllAddr_.push_back(le);

   }
}


////////////////////////////////////////////////////////////////////////////////
// This is kind of a hack:  I forgot the possibility that we might need
// to do temporary scan of some Tx data without actually adding it to
// the wallet yet (because we need to process zero-conf transactions,
// but can't update the wallets until we have a verified blk number).
// Perhaps this was an oversight to not design the wallets and Ledger
// Entry objects to handle this situation, but for now we will leave
// what's working alone, and outsource a solution to this method:
//
// (1)  Create a new wallet
// (2)  Copy in all the addresses of this wallet
// (3)  Run scanTx on all the zero-conf tx, using 0xffffffff for blknum
// (4)  Return the combined ledger for the zero-conf addresses
// (5)  Maintain this ledger separately in the calling calling code
// (6)  Throw away this ledger whenever a new block is received, rescan
//vector<LedgerEntry> BtcWallet::getLedgerEntriesForZeroConfTxList(
                                              //vector<TxRef*> zcList)
//{
   //// Prepare fresh, temporary wallet with same addresses
   //BtcWallet tempWlt;
   //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
      //tempWlt.addAddress( addrPtrVect_[i]->getAddrStr20() );
//
   //for(uint32_t i=0; i<zcList.size(); i++)
      //tempWlt.scanTx(*zcList[i], 0, UINT32_MAX, UINT32_MAX);
//
   //return tempWlt.ledgerAllAddr_;
//}





////////////////////////////////////////////////////////////////////////////////
// Need to copy the TxIOMap (objects) to the new wallet, then update the child
// addresses with pointers to the new TxIO objects, not the old ones.  This 
// allows us to scan new transactions in a temporary wallet, without affecting
// the original wallet
/*
void BtcWallet::makeTempCopyForZcScan(BtcWallet & tempWlt)
{

   tempWlt.txioMap_          = txioMap_;
   tempWlt.unspentOutPoints_ = unspentOutPoints_;
   tempWlt.lockedTxOuts_     = lockedTxOuts_;
   tempWlt.orphanTxIns_      = orphanTxIns_;
   tempWlt.txrefSet_         = txrefSet_;

   tempWlt.nonStdTxioMap_    = nonStdTxioMap_;
   tempWlt.nonStdUnspentOutPoints_ = nonStdUnspentOutPoints_;

   // Need to copy the address objects, but with TxIOPair* to the temp-wlt TxIOs
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      BtcAddress & origAddr = *addrPtrVect_[i];
      tempWlt.addAddress( origAddr.getAddrStr20() );

      vector<TxIOPair*> & origTxioList = origAddr.getTxIOList();
      for(uint32_t j=0; j<origTxioList.size(); j++)
      {
         TxIOPair * txioPtr = origTxioList[j];
         OutPoint op = txioPtr->getOutPoint();
         BtcAddress & newAddr = tempWlt.getAddrByHash160(origAddr.getAddrStr20());
         newAddr.addTxIO(tempWlt.txioMap_[op]);
      }
   }
}



////////////////////////////////////////////////////////////////////////////////
// The above method didn't work... python memory management is weirder than 
// I thought.  However, I know I can pass BinaryData in, and so I will just 
// copy it locally and then I don't have to worry about memory mgmt.
LedgerEntry BtcWallet::getWalletLedgerEntryForTx(BinaryData const & zcBin)
{
   // Prepare fresh, temporary wallet with same addresses
   BtcWallet tempWlt;
   makeTempCopyForZcScan(tempWlt);

   BinaryData txBin(zcBin);
   TxRef txref(txBin);
   tempWlt.scanTx(txref, 0, UINT32_MAX, UINT32_MAX);

   if(tempWlt.ledgerAllAddr_.size() > 0)
      return tempWlt.ledgerAllAddr_[0];
   else
      return LedgerEntry();
}

////////////////////////////////////////////////////////////////////////////////
// The above method didn't work... python memory management is weirder than 
// I thought.  However, I know I can pass BinaryData in, and so I will just 
// copy it locally and then I don't have to worry about memory mgmt.
vector<LedgerEntry> BtcWallet::getAddrLedgerEntriesForTx(BinaryData const & zcBin)
{
   // Prepare fresh, temporary wallet with same addresses
   BtcWallet tempWlt;
   makeTempCopyForZcScan(tempWlt);

   BinaryData txBin(zcBin);
   TxRef txref(txBin);
   tempWlt.scanTx(txref, 0, UINT32_MAX, UINT32_MAX);

   vector<LedgerEntry> leVect(0);
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      vector<LedgerEntry> & les = addrPtrVect_[i]->getTxLedger();
      for(uint32_t j=0; j<les.size(); j++)
      {
         les[j].setAddr20(addrPtrVect_[i]->getAddrStr20());
         leVect.push_back(les[j]);
      }
   }

   return leVect;
}
*/

////////////////////////////////////////////////////////////////////////////////
// Make a separate method here so we can get creative with how to handle these
// scripts and not clutter the regular scanning code
void BtcWallet::scanNonStdTx(uint32_t blknum, 
                             uint32_t txidx, 
                             TxRef&   tx,
                             uint32_t txoutidx,
                             BtcAddress& thisAddr)
{
   TxOutRef txout = tx.getTxOutRef(txoutidx);
   int findIdx = txout.getScriptRef().find(thisAddr.getAddrStr20());
   if(findIdx > -1)
   {
      cout << "ALERT:  Found non-standard transaction referencing" << endl;
      cout << "        an address in your wallet.  There is no way" << endl;
      cout << "        for this program to determine if you can" << endl;
      cout << "        spend these BTC or not.  Please email the" << endl;
      cout << "        following information to etotheipi@gmail.com" << endl;
      cout << "        for help identifying the transaction and how" << endl;
      cout << "        to spend it:" << endl;
      cout << endl;
      cout << "   Block Number: " << blknum << endl;
      cout << "   Tx Hash:      " << tx.getThisHash().copySwapEndian().toHexStr() 
                               << " (BE)" << endl;
      cout << "   TxOut Index:  " << txoutidx << endl;
      cout << "   PubKey Hash:  " << thisAddr.getAddrStr20().toHexStr() 
                               << " (LE)" << endl;
      cout << "   RawScript:    " << endl;
      BinaryDataRef scr = txout.getScriptRef();
      uint32_t sz = scr.getSize(); 
      for(uint32_t i=0; i<sz; i+=32)
      {
         if( i < sz-32 )
            cout << "      " << scr.getSliceCopy(i,sz-i).toHexStr();
         else
            cout << "      " << scr.getSliceCopy(i,32).toHexStr();
      }
      cout << endl;
      cout << "   Attempting to interpret script:" << endl;
      BtcUtils::pprintScript(scr);
      cout << endl;


      OutPoint outpt(tx.getThisHash(), txoutidx);      
      nonStdUnspentOutPoints_.insert(outpt);
      pair< map<OutPoint, TxIOPair>::iterator, bool> insResult;
      pair<OutPoint, TxIOPair> toBeInserted(outpt, TxIOPair(&tx,txoutidx));
      insResult = nonStdTxioMap_.insert(toBeInserted);
      //insResult = txioMap_.insert(toBeInserted);
   }

}

////////////////////////////////////////////////////////////////////////////////
//uint64_t BtcWallet::getBalance(bool blockchainOnly)

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getSpendableBalance(void)
{
   uint64_t balance = 0;
   map<OutPoint, TxIOPair>::iterator iter;
   for(iter  = txioMap_.begin();
       iter != txioMap_.end();
       iter++)
   {
      if(iter->second.isSpendable())
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
      if(txio.isSpendable())
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back(UnspentTxOut(txoutref, blkNum) );
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
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back(UnspentTxOut(txoutref, blkNum) );
      }
   }
   return utxoList;
}



   
////////////////////////////////////////////////////////////////////////////////
//uint64_t BtcWallet::getBalance(uint32_t i)
//{
   //return addrPtrVect_[i]->getBalance();
//}

//////////////////////////////////////////////////////////////////////////////////
//uint64_t BtcWallet::getBalance(BinaryData const & addr20)
//{
   //assert(hasAddr(addr20)); 
   //return addrMap_[addr20].getBalance();
//}

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



bool BtcWallet::isOutPointMine(BinaryData const & hsh, uint32_t idx)
{
   OutPoint op(hsh, idx);
   return (txioMap_.find(op)!=txioMap_.end());
}

////////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintLedger(void)
{ 
   cout << "Wallet Ledger:" << endl;
   for(uint32_t i=0; i<ledgerAllAddr_.size(); i++)
      ledgerAllAddr_[i].pprintOneLine();
   for(uint32_t i=0; i<ledgerAllAddrZC_.size(); i++)
      ledgerAllAddrZC_[i].pprintOneLine();
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start BlockDataManager_FullRAM methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_FullRAM::BlockDataManager_FullRAM(void) : 
      blockchainData_ALL_(0),
      lastEOFByteLoc_(0),
      totalBlockchainBytes_(0),
      isAllAddrLoaded_(false),
      topBlockPtr_(NULL),
      genBlockPtr_(NULL),
      lastBlockWasReorg_(false),
      isInitialized_(false),
      GenesisHash_(0),
      GenesisTxHash_(0),
      MagicBytes_(0)
{
   blockchainData_NEW_.clear();
   headerHashMap_.clear();
   txHashMap_.clear();

   zeroConfRawTxList_.clear();
   zeroConfMap_.clear();
   zcEnabled_ = false;
   zcFilename_ = string("");

   headersByHeight_.clear();
   txFileRefs_.clear();
   headerFileRefs_.clear();
   blockchainFilenames_.clear();
   previouslyValidBlockHeaderPtrs_.clear();
   orphanChainStartBlocks_.clear();
}


/////////////////////////////////////////////////////////////////////////////
// We must set the network-specific data for this blockchain
//
// bdm.SetBtcNetworkParams( 
//       BinaryData::CreateFromHex(MAINNET_GENESIS_HASH_HEX),
//       BinaryData::CreateFromHex(MAINNET_GENESIS_TX_HASH_HEX),
//       BinaryData::CreateFromHex(MAINNET_MAGIC_BYTES));
//
// The above call will work 
void BlockDataManager_FullRAM::SetBtcNetworkParams(
                                    BinaryData const & GenHash,
                                    BinaryData const & GenTxHash,
                                    BinaryData const & MagicBytes)
{
   GenesisHash_.copyFrom(GenHash);
   GenesisTxHash_.copyFrom(GenTxHash);
   MagicBytes_.copyFrom(MagicBytes);
}



void BlockDataManager_FullRAM::SelectNetwork(string netName)
{
   if(netName.compare("Main") == 0)
   {
      SetBtcNetworkParams( 
         BinaryData::CreateFromHex(MAINNET_GENESIS_HASH_HEX),
         BinaryData::CreateFromHex(MAINNET_GENESIS_TX_HASH_HEX),
         BinaryData::CreateFromHex(MAINNET_MAGIC_BYTES));
   }
   else if(netName.compare("Test") == 0)
   {
      SetBtcNetworkParams( 
         BinaryData::CreateFromHex(TESTNET_GENESIS_HASH_HEX),
         BinaryData::CreateFromHex(TESTNET_GENESIS_TX_HASH_HEX),
         BinaryData::CreateFromHex(TESTNET_MAGIC_BYTES));
   }
   else
   {
      cout << "ERROR: Unrecognized network name" << endl;
      cerr << "ERROR: Unrecognized network name" << endl;
   }
}

/////////////////////////////////////////////////////////////////////////////
// The only way to "create" a BDM is with this method, which creates it
// if one doesn't exist yet, or returns a reference to the only one
// that will ever exist
BlockDataManager_FullRAM & BlockDataManager_FullRAM::GetInstance(void) 
{
   static bool bdmCreatedYet_ = false;
   if( !bdmCreatedYet_ )
   {
      theOnlyBDM_ = new BlockDataManager_FullRAM;
      bdmCreatedYet_ = true;
   }
   return (*theOnlyBDM_);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::Reset(void)
{
   // Clear out all the "real" data in the blkfile
   blkfilePath_ = "";
   blockchainData_ALL_.clear();
   blockchainData_NEW_.clear();
   headerHashMap_.clear();
   txHashMap_.clear();

   // If we decided to store ALL addresses
   allAddrTxMap_.clear();
   isAllAddrLoaded_ = false;

   // These are not used at the moment, but we should clear them anyway
   blockchainFilenames_.clear();
   txFileRefs_.clear();
   headerFileRefs_.clear();


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
   
   lastEOFByteLoc_ = 0;
   totalBlockchainBytes_ = 0;

   isInitialized_ = false;

   zcEnabled_ = false;
   zcFilename_ = "";
   zeroConfMap_.clear();
   zeroConfRawTxList_.clear();
}



/////////////////////////////////////////////////////////////////////////////
int32_t BlockDataManager_FullRAM::getNumConfirmations(BinaryData txHash)
{
   map<HashString, TxRef>::iterator findResult = txHashMap_.find(txHash); 
   if(findResult == txHashMap_.end())
      return TX_NOT_EXIST;
   else
   {
      if(findResult->second.headerPtr_ == NULL)
         return TX_0_UNCONFIRMED; 
      else
      { 
         BlockHeaderRef & txbh = *(findResult->second.headerPtr_);
         if(!txbh.isMainBranch_)
            return TX_OFF_MAIN_BRANCH;

         int32_t txBlockHeight  = txbh.getBlockHeight();
         int32_t topBlockHeight = getTopBlockHeader().blockHeight_;
         return  topBlockHeight - txBlockHeight + 1;
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
BlockHeaderRef & BlockDataManager_FullRAM::getTopBlockHeader(void) 
{
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &(getGenesisBlock());
   return *topBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
BlockHeaderRef & BlockDataManager_FullRAM::getGenesisBlock(void) 
{
   if(genBlockPtr_ == NULL)
      genBlockPtr_ = &(headerHashMap_[GenesisHash_]);
   return *genBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
BlockHeaderRef * BlockDataManager_FullRAM::getHeaderByHeight(int index)
{
   if( index<0 || index>=(int)headersByHeight_.size())
      return NULL;
   else
      return headersByHeight_[index];
}


/////////////////////////////////////////////////////////////////////////////
// The most common access method is to get a block by its hash
BlockHeaderRef * BlockDataManager_FullRAM::getHeaderByHash(BinaryData const & blkHash)
{
   map<BinaryData, BlockHeaderRef>::iterator it = headerHashMap_.find(blkHash);
   if(it==headerHashMap_.end())
      return NULL;
   else
      return &(it->second);
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
TxRef* BlockDataManager_FullRAM::getTxByHash(BinaryData const & txhash)
{
   map<HashString, TxRef>::iterator it = txHashMap_.find(txhash);
   if(it==txHashMap_.end())
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      map<HashString, ZeroConfData>::iterator iter = zeroConfMap_.find(txhash);
      if(iter==zeroConfMap_.end())
         return NULL;
      else
         return &(iter->second.txref_);
   }
   else
      return &(it->second);
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FullRAM::hasTxWithHash(BinaryData const & txhash,
                                             bool includeZeroConf) const
{
   if(txHashMap_.find(txhash) == txHashMap_.end())
   {
      if(zeroConfMap_.find(txhash)==zeroConfMap_.end() || !includeZeroConf)
         return false;
      else
         return true;
   }
   else
      return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FullRAM::hasHeaderWithHash(BinaryData const & txhash) const
{
   return (headerHashMap_.find(txhash) != headerHashMap_.end());
}

/////////////////////////////////////////////////////////////////////////////
vector<BlockHeaderRef*> BlockDataManager_FullRAM::prefixSearchHeaders(BinaryData const & searchStr)
{
   vector<BlockHeaderRef*> outList(0);
   map<HashString, BlockHeaderRef>::iterator iter;
   for(iter  = headerHashMap_.begin();
       iter != headerHashMap_.end();
       iter++)
   {
      if(iter->first.startsWith(searchStr))
         outList.push_back(&(iter->second));
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
vector<TxRef*> BlockDataManager_FullRAM::prefixSearchTx(BinaryData const & searchStr)
{
   vector<TxRef*> outList(0);
   map<HashString, TxRef>::iterator iter;
   for(iter  = txHashMap_.begin();
       iter != txHashMap_.end();
       iter++)
   {
      if(iter->first.startsWith(searchStr))
         outList.push_back(&(iter->second));
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
// Since the cpp code doesn't have full addresses (only 20-byte hashes),
// that's all we can search for.  
vector<BinaryData> BlockDataManager_FullRAM::prefixSearchAddress(BinaryData const & searchStr)
{
   // Actually, we can't even search for this, because we don't have a list
   // of addresses in the blockchain.  We could construct one, but it would
   // take up a lot of RAM (and time)... I will need to create a separate 
   // call to allow the caller to create a set<BinaryData> of addresses 
   // before calling this method
   return vector<BinaryData>(0);
}



/////////////////////////////////////////////////////////////////////////////
void BtcWallet::pprintAlot(uint32_t topBlk, bool withAddr)
{
   uint32_t numLedg = ledgerAllAddr_.size();
   uint32_t numLedgZC = ledgerAllAddrZC_.size();
   uint32_t numTxIO = txioMap_.size();

   cout << "Wallet PPRINT:" << endl;
   cout << "Tot: " << getFullBalance() << endl;
   cout << "Spd: " << getSpendableBalance() << endl;
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
      for(uint32_t i=0; i<getNumAddr(); i++)
      {
         BtcAddress & addr = getAddrByIndex(i);
         BinaryData addr160 = addr.getAddrStr20();
         cout << "\nAddress: " << addr160.toHexStr().c_str() << endl;
         cout << "   Tot: " << addr.getFullBalance() << endl;
         cout << "   Spd: " << addr.getSpendableBalance() << endl;
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
// This is an intense search, using every tool we've created so far!
void BlockDataManager_FullRAM::scanBlockchainForTx(BtcWallet & myWallet,
                                                   uint32_t startBlknum,
                                                   uint32_t endBlknum)
{
   PDEBUG("Scanning blockchain for tx");

   ////////////////////////////////////////////////////////////////////////////
   // DEBUGGING CODE:
   //cout << "Scanning blockchain for tx: " << startBlknum << " to " << endBlknum << endl;
   //cout << "Before Scan Blkchain:" << endl;
   //myWallet.pprintAlot();
   // END DEBUGGING CODE
   ////////////////////////////////////////////////////////////////////////////

   uint32_t nHeaders = headersByHeight_.size();
   endBlknum = (endBlknum > nHeaders ? nHeaders : endBlknum);
   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=startBlknum; h<endBlknum; h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);
         myWallet.scanTx(tx, itx, bhr.getTimestamp(), bhr.getBlockHeight());
      }
   }

   myWallet.sortLedger(); // removes invalid tx and sorts

   ////////////////////////////////////////////////////////////////////////////
   // DEBUGGING CODE:
   //cout << "BEFORE CLEAN Scan Blkchain:" << endl;
   //myWallet.pprintAlot();
   ////////////////////////////////////////////////////////////////////////////
   
   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(myWallet);

   PDEBUG("Done scanning blockchain for tx");

   ////////////////////////////////////////////////////////////////////////////
   // DEBUGGING CODE:
   //cout << "Scanning blockchain for tx: " << startBlknum << " to " << endBlknum << endl;
   //cout << "AFTER Scan Blkchain:" << endl;
   //myWallet.pprintAlot();
   // END DEBUGGING CODE
   ////////////////////////////////////////////////////////////////////////////
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::scanBlockchainForTx(vector<BtcWallet*> walletVect,
                                                   uint32_t startBlknum,
                                                   uint32_t endBlknum)
{
   PDEBUG("Scanning blockchain for tx, from scratch");

   uint32_t nHeaders = headersByHeight_.size();
   endBlknum = (endBlknum > nHeaders ? nHeaders : endBlknum);
   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=startBlknum; h<endBlknum; h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         for(uint32_t w=0; w<walletVect.size(); w++)
            walletVect[w]->scanTx(tx, itx, bhr.getTimestamp(), bhr.getBlockHeight());
      }
   }
 
   // Removes any invalid tx and sorts
   for(uint32_t w=0; w<walletVect.size(); w++)
      walletVect[w]->sortLedger();

   PDEBUG("Done scanning blockchain for tx");
}


// **** THIS METHOD IS NOT MAINTAINED ANYMORE **** //
/////////////////////////////////////////////////////////////////////////////
// This is an intense search, using every tool we've created so far!
// This also should only be used in special circumstances because it's 
// extremely slow and can use 2-3 GB of RAM to hold all the data
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch_AllAddr(void)
{
   uint32_t nHeaders = headersByHeight_.size();

   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<nHeaders; h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX /////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         ///// LOOP OVER ALL TXOUT IN BLOCK /////
         for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
         {
            
            TxOutRef txout = tx.getTxOutRef(iout);
            BinaryData recipAddr20 = txout.getRecipientAddr();
            map<BinaryData, set<HashString> >::iterator iter = 
                                  allAddrTxMap_.find(recipAddr20);
            if(iter==allAddrTxMap_.end())
            {
               pair<BinaryData, set<HashString> > 
                        toIns( recipAddr20, set<HashString>());
               pair< map<BinaryData, set<HashString> >::iterator, bool> insResult =
                                                      allAddrTxMap_.insert(toIns);
               insResult.first->second.insert(tx.getThisHash());
            }
            else
            {
               iter->second.insert(tx.getThisHash());
            }
            
            /*  // This code was used when we wanted to maintain a global txioMap
            // Add address to address map
            // If address is already there, this will leave it untouched
            pair< map<BinaryData, BtcAddress>::iterator, bool> insAddrResult; 
            pair<BinaryData, BtcAddress> toInsert(recipAddr20, BtcAddress(&recipAddr20));
            insAddrResult = allAddresses_.insert(toInsert);
            BtcAddress & thisAddr = insAddrResult.first->second;

            OutPoint outpt(tx.getHash(), iout);      

            // The new TxIO to be inserted only has a TxOut right now
            pair< map<OutPoint, TxIOPair>::iterator, bool> insTxioResult;
            pair<OutPoint, TxIOPair> newTxio(outpt, TxIOPair(txout, &tx));
            insTxioResult = txioMap_.insert(newTxio);

            TxIOPair & thisTxio = insTxioResult.first->second;
            if(insTxioResult.second == true)
            {
               thisAddr.relevantTxIOPtrs_.push_back( &thisTxio );
               if(thisAddr.createdBlockNum_ == 0)
               {
                  thisAddr.createdBlockNum_ = blkHeight;
                  thisAddr.createdTimestamp_ = blkTimestamp;
               }
            }
            else
            {
               cout << "***WARNING: Found TxOut that already has TxIO" << endl;
            }
            */

         }

         ///// LOOP OVER ALL TXIN IN BLOCK /////
         for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
         {
            TxInRef txin = tx.getTxInRef(iin);
            BinaryData prevOutHash = txin.getOutPointRef().getTxHash();
            if(prevOutHash == BtcUtils::EmptyHash_)
               continue;

            OutPoint outpt = txin.getOutPoint();
            // We have the tx, now check if it contains one of our TxOuts
            BinaryData recip = txHashMap_[prevOutHash].getTxOutRef(outpt.getTxOutIndex()).getRecipientAddr();
            allAddrTxMap_[recip].insert(tx.getThisHash());
         }
      }
   }

   isAllAddrLoaded_ = true;
}


/////////////////////////////////////////////////////////////////////////////
vector<TxRef*> BlockDataManager_FullRAM::findAllNonStdTx(void)
{
   PDEBUG("Finding all non-std tx");
   vector<TxRef*> txVectOut(0);
   uint32_t nHeaders = headersByHeight_.size();

   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<nHeaders; h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX /////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         ///// LOOP OVER ALL TXIN IN BLOCK /////
         for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
         {
            TxInRef txin = tx.getTxInRef(iin);
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
            
            TxOutRef txout = tx.getTxOutRef(iout);
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


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_FullRAM::readBlkFile_FromScratch(string filename,
                                                           bool doOrganize)
{
   if(filename.compare(blkfilePath_) == 0)
   {
      cout << "Call to load a blockchain file that is already loaded!" << endl;
      return 0;
   }

   if(GenesisHash_.getSize() == 0)
   {
      cout << "***ERROR:  Must set network params before loading blockchain!"
           << endl;
      cerr << "***ERROR:  Must set network params before loading blockchain!"
           << endl;
      return 0;
   }

   PDEBUG("Read blkfile from scratch");
   blkfilePath_ = filename;
   cout << "Attempting to read blockchain from file: " << blkfilePath_.c_str() << endl;
   ifstream is(blkfilePath_.c_str(), ios::in | ios::binary);
   if( !is.is_open() )
   {
      cout << "***ERROR:  Cannot open " << blkfilePath_.c_str() << endl;
      cerr << "***ERROR:  Cannot open " << blkfilePath_.c_str() << endl;
      return 0;
   }

   // We succeeded opening the file...
   is.seekg(0, ios::end);
   uint64_t filesize = (size_t)is.tellg();
   is.seekg(0, ios::beg);
   cout << blkfilePath_.c_str() << " is " << filesize/(float)(1024*1024) << " MB" << endl;

   //////////////////////////////////////////////////////////////////////////
   TIMER_START("ReadBlockchainIntoRAM");
   blockchainData_ALL_.resize(filesize);
   is.read((char*)blockchainData_ALL_.getPtr(), filesize);
   is.close();
   TIMER_STOP("ReadBlockchainIntoRAM");
   //////////////////////////////////////////////////////////////////////////



   PDEBUG("Scanning all block data currently in RAM");

   // Blockchain data is now in its permanent location in memory
   BinaryRefReader brr(blockchainData_ALL_);
   uint32_t nBlkRead = 0;
   bool keepGoing = true;

   TIMER_START("ScanBlockchainInRAM");
   while(keepGoing)
   {
      keepGoing = parseNewBlockData(brr, totalBlockchainBytes_);
      nBlkRead++;
   }
   TIMER_STOP("ScanBlockchainInRAM");

   // We need to maintain the physical size of blk0001.dat (lastEOFByteLoc_)
   // separately from the total size of the blockchain, which may include
   // new bytes not in the blk0001.dat yet
   totalBlockchainBytes_ = blockchainData_ALL_.getSize();
   lastEOFByteLoc_       = blockchainData_ALL_.getSize();;

   // Organize the chain by default--it takes less than 1s.  I can't really
   // think of a use case where you would want only an unorganized blockchain
   // in memory (except for timing the two ops separately)
   if(doOrganize)
      organizeChain();

   // Return the number of blocks read from blkfile (this includes invalids)
   isInitialized_ = true;
   purgeZeroConfPool();
   return nBlkRead;
}


////////////////////////////////////////////////////////////////////////////////
// This method checks whether your blk0001.dat file is bigger than it was when
// we first read in the blockchain.  If so, we read the new data and add it to
// the memory pool.  Return value is how many blocks were added.
//
// NOTE:  You might want to check lastBlockWasReorg_ variable to know whether 
//        to expect some previously valid headers/txs to still be valid
//
uint32_t BlockDataManager_FullRAM::readBlkFileUpdate(string filename)
{
   TIMER_START("getBlockfileUpdates");

   // The only real use for this arg is for unit-testing, I have two
   // copies of the blockchain one with an extra block or two in it.
   if(filename.size() == 0)
      filename = blkfilePath_;

   PDEBUG2("Update blkfile from ", filename);

   // Try opening the blkfile for reading
   ifstream is(filename.c_str(), ios::in | ios::binary);
   if( !is.is_open() )
   {
      cout << "***ERROR:  Cannot open " << filename.c_str() << endl;
      cerr << "***ERROR:  Cannot open " << filename.c_str() << endl;
      return 0;
   }

   // We succeeded opening the file, check to see if there's new data
   is.seekg(0, ios::end);
   uint32_t filesize = (size_t)is.tellg();
   uint32_t nBytesToRead = (uint32_t)(filesize - lastEOFByteLoc_);
   if(nBytesToRead == 0)
   {
      is.close();
      return 0;
   }

   
   // Seek to the beginning of the new data and read it
   // TODO:  Check why we need the -1 on lastEOFByteLoc_.  And if it is 
   //        necessary, do we need it elsewhere, too?
   BinaryData newBlockDataRaw(nBytesToRead);
   is.seekg(lastEOFByteLoc_, ios::beg);
   is.read((char*)newBlockDataRaw.getPtr(), nBytesToRead);
   is.close();

   cout << newBlockDataRaw.getSliceCopy(0,4).toHexStr() << endl;
    
   // Use the specialized "addNewBlockData()" methods to add the data
   // to the permanent memory pool and parse it into our header/tx maps
   BinaryRefReader brr(newBlockDataRaw);
   uint32_t nBlkRead = 0;
   vector<bool> blockAddResults;
   bool keepGoing = true;
   while(keepGoing)
   {
      ////////////
      // The reader should be at the start of magic bytes of the new block
      uint32_t nextBlockSize = *(uint32_t*)(brr.getCurrPtr()+4);
      BinaryDataRef nextRawBlockRef(brr.getCurrPtr(), nextBlockSize+8);
      blockAddResults = addNewBlockDataRef( nextRawBlockRef );
      brr.advance(nextBlockSize+8);
      ////////////

      bool blockAddSucceeded = blockAddResults[0];
      bool blockIsNewTop     = blockAddResults[1];
      bool blockchainReorg   = blockAddResults[2];

      if(blockAddSucceeded)
         nBlkRead++;
      else
      {
         if(!blockIsNewTop)
         {
            cout << "Block data did not extend the main chain!" << endl;
            // TODO:  add anything extra to do here (is there anything?)
         }
   
         if(blockchainReorg)
         {
            cout << "This block forced a reorg!  (and we're going to do nothing else...)" << endl;
            // TODO:  add anything extra to do here (is there anything?)
         }
      }
      

      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }
   TIMER_STOP("getBlockfileUpdates");



   // Finally, update the last known blkfile size and return nBlks added
   //PDEBUG2("Added new blocks to memory pool: ", nBlkRead);
   cout << "Added new blocks to memory pool: " << nBlkRead << endl;
   lastEOFByteLoc_ = filesize;
   return nBlkRead;
}

////////////////////////////////////////////////////////////////////////////////
// BDM detects the reorg, but is wallet-agnostic so it can't update any wallets
// You have to call this yourself after you check whether the last organizeChain
// call indicated that a reorg happened
void BlockDataManager_FullRAM::updateWalletAfterReorg(BtcWallet & wlt)
{
   // Fix the wallet's ledger
   for(uint32_t i=0; i<wlt.getTxLedger().size(); i++)
   {
      HashString const & txHash = wlt.getTxLedger()[i].getTxHash();
      if(txJustInvalidated_.count(txHash) > 0)
         wlt.getTxLedger()[i].setValid(false);

      if(txJustAffected_.count(txHash) > 0)
         wlt.getTxLedger()[i].changeBlkNum(getTxByHash(txHash)->getBlockHeight());
   }


   // UPDATE JAN 2012:  I don't think this part is necessary anymore.
   //                   The decision was made not to bother with maintaining
   //                   an unspent list anymore, since it can be done on the 
   //                   fly from the txioMap.  Mainly because it's extra work
   //                   to maintain the synchronous list, it's easy to generate
   //                   on the fly, and it doesn't actually help us distinguish
   //                   "spendable" or "unconfirmed."
   /*
   // Need to fix the TxIO pairs, and recompute unspentTxOuts
   // All addresses point to the wallet's TxIOPairs, so we only need 
   // to do this check on the wallet -- no need on the individual addrs
   map<OutPoint, TxIOPair>::iterator txioIter;
   for(txioIter  = wlt.getTxIOMap().begin();
       txioIter != wlt.getTxIOMap().end();
       txioIter++)
   {
      pair<bool, bool> reassessValid = txioIter->second.reassessValidity();
      bool txoutIsValid = reassessValid.first;
      bool txinIsValid  = reassessValid.second;

      if(txoutIsValid)
      {
         if(txinIsValid)
            wlt.getUnspentOutPoints().erase(txioIter->first);
         else
            wlt.getUnspentOutPoints().insert(txioIter->first);
      }
      else
      {
         if(txinIsValid)
            cout << "***ERROR: Invalid TxOut but valid TxIn!?" << endl;
         else
            wlt.getUnspentOutPoints().erase(txioIter->first);
      }
   }
   */

   // Now fix the individual address ledgers
   for(uint32_t a=0; a<wlt.getNumAddr(); a++)
   {
      BtcAddress & addr = wlt.getAddrByIndex(a);
      for(uint32_t i=0; i<addr.getTxLedger().size(); i++)
      {
         HashString const & txHash = addr.getTxLedger()[i].getTxHash();
         if(txJustInvalidated_.count(txHash) > 0)
            addr.getTxLedger()[i].setValid(false);
   
         if(txJustAffected_.count(txHash) > 0) 
            addr.getTxLedger()[i].changeBlkNum(getTxByHash(txHash)->getBlockHeight());
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::updateWalletsAfterReorg(vector<BtcWallet*> wltvect)
{
   for(uint32_t i=0; i<wltvect.size(); i++)
      updateWalletAfterReorg(*wltvect[i]);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FullRAM::verifyBlkFileIntegrity(void)
{
   PDEBUG("Verifying blk0001.dat integrity");
   bool isGood = true;
   map<HashString, BlockHeaderRef>::iterator headIter;
   for(headIter  = headerHashMap_.begin();
       headIter != headerHashMap_.end();
       headIter++)
   {
      BlockHeaderRef & bhr = headIter->second;
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
// Pass in a BRR that starts at the beginning of the blockdata THAT IS 
// ALREADY AT IT'S PERMANENT LOCATION IN MEMORY (before magic bytes)
bool BlockDataManager_FullRAM::parseNewBlockData(BinaryRefReader & brr,
                                                 uint64_t & currBlockchainSize)
{
   if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
      return false;

   brr.advance(4); // magic bytes
   uint32_t nBytes = brr.get_uint32_t();

   // For some reason, my blockfile sometimes has some extra bytes
   // If failed we return reorgHappened==false;
   if(brr.isEndOfStream() || brr.getSizeRemaining() < nBytes)
      return false;

   // Create the objects once that will be used for insertion
   static pair<HashString, TxRef>                               txInputPair;
   static pair<HashString, BlockHeaderRef>                      bhInputPair;
   static pair<map<HashString, TxRef>::iterator, bool>          txInsResult;
   static pair<map<HashString, BlockHeaderRef>::iterator, bool> bhInsResult;

   
   // Read off the header 
   bhInputPair.second.unserialize(brr);
   bhInputPair.first = bhInputPair.second.getThisHash();
   bhInsResult = headerHashMap_.insert(bhInputPair);
   BlockHeaderRef * bhptr = &(bhInsResult.first->second);

   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brr.get_var_int(&viSize);
   bhptr->blockNumBytes_ = nBytes;
   bhptr->blkByteLoc_    = currBlockchainSize;
   uint64_t txOffset = 8 + HEADER_SIZE + viSize; // usually 89

   // Read each of the Tx
   bhptr->txPtrList_.clear();
   for(uint32_t i=0; i<nTx; i++)
   {
      txInputPair.second.unserialize(brr);
      txInputPair.first = txInputPair.second.getThisHash();
      txInsResult = txHashMap_.insert(txInputPair);
      TxRef * txptr = &(txInsResult.first->second);

      // Add a pointer to this tx to the header's tx-ptr-list
      bhptr->txPtrList_.push_back( txptr );

      txptr->setTxStartByte(txOffset+currBlockchainSize);
      txOffset += txptr->getSize();
      // We don't set this tx's headerPtr because there could be multiple
      // headers that reference this tx... we will wait until the chain
      // is organized and make sure this tx points to the header that 
      // is on the main chain.
   }
   currBlockchainSize += nBytes+8;
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
vector<bool> BlockDataManager_FullRAM::addNewBlockData(BinaryData rawBlock,
                                                       bool writeToBlk0001)
{
   // TODO:  maybe we should check whether we already have this block...?
   vector<bool> vb(3);
   blockchainData_NEW_.push_back(rawBlock);
   list<BinaryData>::iterator listEnd = blockchainData_NEW_.end();
   listEnd--;
   BinaryRefReader newBRR( listEnd->getPtr(), rawBlock.getSize() );
   bool addDataSucceeded = parseNewBlockData(newBRR, totalBlockchainBytes_);

   if( ! addDataSucceeded ) 
   {
      cout << "Adding new block data to memory pool failed!";
      vb[ADD_BLOCK_SUCCEEDED]     = false;  // Added to memory pool
      vb[ADD_BLOCK_NEW_TOP_BLOCK] = false;  // New block is new top of chain
      vb[ADD_BLOCK_CAUSED_REORG]  = false;  // Add caused reorganization
      return vb;
   }

   // Finally, let's re-assess the state of the blockchain with the new data
   // Check the lastBlockWasReorg_ variable to see if there was a reorg
   // TODO: Check to see if the organizeChain call, perhaps does a lot of what
   //       I was plannign to do already
   PDEBUG("New block!  Re-assess blockchain state after adding new data...");
   bool prevTopBlockStillValid = organizeChain(); 

   // I cannot just do a rescan:  the user needs this to be done manually so
   // that we can identify headers/txs that were previously valid, but no more
   if(!prevTopBlockStillValid)
   {
      cout << "Blockchain Reorganization detected!" << endl;
      // *** If there was a reorg, we must make take appropriate action! ***
      //     The organizeChain call already set the headers in the 
      //     invalid branch to !isMainBranch and updated nextHash_
      //     pointers to reflect the new organization.  But we also
      //     need to update transactions that may have been affected
      //     (do that next), and YOU need to run a post-reorg check
      //     on your wallet (hopefully implemented soon).
      reassessAfterReorg(prevTopBlockPtr_, topBlockPtr_, reorgBranchPoint_);
      // TODO:  It might also be necessary to look at the specific
      //        block headers that were invalidated, to make sure 
      //        we aren't using stale data somewhere that copied it
      cout << "Done reassessing tx validity " << endl;
   }

   // Since this method only adds one block, if it's not on the main branch,
   // then it's not the new head
   BinaryData newHeadHash = BtcUtils::getHash256(rawBlock.getSliceRef(8,80));
   bool newBlockIsNewTop = getHeaderByHash(newHeadHash)->isMainBranch();

   // Write this block to file if is on the main chain and we requested it
   // TODO: this isn't right, because this logic won't write any blocks that
   //       that might eventually be in the main chain but aren't currently.
   if(newBlockIsNewTop && writeToBlk0001)
   {
      ofstream fileAppend(blkfilePath_.c_str(), ios::app | ios::binary);
      fileAppend.write((char const *)(rawBlock.getPtr()), rawBlock.getSize());
      fileAppend.close();
   }

   purgeZeroConfPool();

   vb[ADD_BLOCK_SUCCEEDED]     =  addDataSucceeded;
   vb[ADD_BLOCK_NEW_TOP_BLOCK] =  newBlockIsNewTop;
   vb[ADD_BLOCK_CAUSED_REORG]  = !prevTopBlockStillValid;
   return vb;
}

////////////////////////////////////////////////////////////////////////////////
// This method returns two booleans:
//    (1)  Block data was added to memory pool successfully
//    (2)  Adding block data caused blockchain reorganization
vector<bool> BlockDataManager_FullRAM::addNewBlockDataRef(BinaryDataRef bdr,
                                                          bool writeToBlk0001)
{
   return addNewBlockData(bdr.copy());
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
   BinaryData merkleRoot = BtcUtils::calculateMerkleRoot(txHashes);
   if(! (merkleRoot == BinaryDataRef(rawHeader.getPtr() + 36, 32)))
   {
      cout << "***ERROR: merkle root does not match header data" << endl;
      cerr << "***ERROR: merkle root does not match header data" << endl;
      return true;  // no data added, so no reorg
   }
#endif
*/
   



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::reassessAfterReorg( BlockHeaderRef* oldTopPtr,
                                                   BlockHeaderRef* newTopPtr,
                                                   BlockHeaderRef* branchPtr)
{
   cout << "Reassessing Tx validity after (after reorg?)" << endl;

   // Walk down invalidated chain first, until we get to the branch point
   // Mark transactions as invalid
   txJustInvalidated_.clear();
   txJustAffected_.clear();
   BlockHeaderRef* thisHeaderPtr = oldTopPtr;
   cout << "Invalidating old-chain transactions..." << endl;
   while(thisHeaderPtr != branchPtr)
   {
      previouslyValidBlockHeaderPtrs_.push_back(thisHeaderPtr);
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef * txptr = thisHeaderPtr->getTxRefPtrList()[i];
         cout << "   Tx: " << txptr->getThisHash().getSliceCopy(0,8).toHexStr() << endl;
         txptr->setHeaderPtr(NULL);
         txptr->setMainBranch(false);
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
         txptr->setMainBranch(true);
         txJustInvalidated_.erase(txptr->getThisHash());
         txJustAffected_.insert(txptr->getThisHash());
      }
      thisHeaderPtr = getHeaderByHash(thisHeaderPtr->getPrevHash());
   }

   PDEBUG("Done reassessing tx validity");
}

////////////////////////////////////////////////////////////////////////////////
vector<BlockHeaderRef*> BlockDataManager_FullRAM::getHeadersNotOnMainChain(void)
{
   PDEBUG("Getting headers not on main chain");
   vector<BlockHeaderRef*> out(0);
   map<HashString, BlockHeaderRef>::iterator iter;
   for(iter  = headerHashMap_.begin(); 
       iter != headerHashMap_.end(); 
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
//
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
bool BlockDataManager_FullRAM::organizeChain(bool forceRebuild)
{
   PDEBUG2("Organizing chain", (forceRebuild ? "w/ rebuild" : ""));
   // If rebuild, we zero out any original organization data and do a 
   // rebuild of the chain from scratch.  This will need to be done in
   // the event that our first call to organizeChain returns false, which
   // means part of blockchain that was previously valid, has become
   // invalid.  Rather than get fancy, just rebuild all which takes less
   // than a second, anyway.
   if(forceRebuild)
   {
      map<BinaryData, BlockHeaderRef>::iterator iter;
      for( iter  = headerHashMap_.begin(); 
           iter != headerHashMap_.end(); 
           iter++)
      {
         iter->second.difficultySum_  = -1;
         iter->second.blockHeight_    =  0;
         iter->second.isFinishedCalc_ = false;
         iter->second.nextHash_       =  BtcUtils::EmptyHash_;
      }
      topBlockPtr_ = NULL;
   }

   // Set genesis block
   BlockHeaderRef & genBlock = getGenesisBlock();
   genBlock.blockHeight_    = 0;
   genBlock.difficultyDbl_  = 1.0;
   genBlock.difficultySum_  = 1.0;
   genBlock.isMainBranch_   = true;
   genBlock.isOrphan_       = false;
   genBlock.isFinishedCalc_ = true;
   genBlock.isInitialized_  = true; 
   genBlock.txPtrList_      = vector<TxRef*>(1);
   genBlock.txPtrList_[0]   = getTxByHash(GenesisTxHash_);
   genBlock.txPtrList_[0]->setMainBranch(true);
   genBlock.txPtrList_[0]->setHeaderPtr(&genBlock);


   // If this is the first run, the topBlock is the genesis block
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   // Store the old top block so we can later check whether it is included 
   // in the new chain organization
   prevTopBlockPtr_ = topBlockPtr_;

   // Iterate over all blocks, track the maximum difficulty-sum block
   map<BinaryData, BlockHeaderRef>::iterator iter;
   double   maxDiffSum     = prevTopBlockPtr_->getDifficultySum();
   for( iter = headerHashMap_.begin(); iter != headerHashMap_.end(); iter ++)
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
   BlockHeaderRef* thisHeaderPtr = topBlockPtr_;
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisHeaderPtr->isFinishedCalc_ )
   {
      thisHeaderPtr->isFinishedCalc_ = true;
      thisHeaderPtr->isMainBranch_   = true;
      thisHeaderPtr->isOrphan_       = false;
      headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

      // We need to guarantee that the txs are pointing to the right block
      // header, because they could've been linked to an invalidated block
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef & tx = *(thisHeaderPtr->getTxRefPtrList()[i]);
         tx.setHeaderPtr(thisHeaderPtr);
         tx.setMainBranch(true);
      }

      BinaryData & childHash    = thisHeaderPtr->thisHash_;
      thisHeaderPtr             = &(headerHashMap_[thisHeaderPtr->getPrevHash()]);
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

      // This is a dangerous bug -- I should probably consider rewriting this
      // method to avoid this problem:  prevTopBlockPtr_ is set correctly 
      // RIGHT NOW, but won't be once I make the recursive call to organizeChain
      // I need to save it now, and re-assign it after the organizeChain call.
      BlockHeaderRef* prevtopblk = prevTopBlockPtr_;
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
double BlockDataManager_FullRAM::traceChainDown(BlockHeaderRef & bhpStart)
{
   if(bhpStart.difficultySum_ > 0)
      return bhpStart.difficultySum_;

   // Prepare some data structures for walking down the chain
   vector<BlockHeaderRef*>   headerPtrStack(headerHashMap_.size());
   vector<double>           difficultyStack(headerHashMap_.size());
   uint32_t blkIdx = 0;
   double thisDiff;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   BlockHeaderRef* thisPtr = &bhpStart;
   map<BinaryData, BlockHeaderRef>::iterator iter;
   while( thisPtr->difficultySum_ < 0)
   {
      thisDiff                = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      headerPtrStack[blkIdx]  = thisPtr;
      blkIdx++;

      iter = headerHashMap_.find(thisPtr->getPrevHash());
      if( iter != headerHashMap_.end() )
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
void BlockDataManager_FullRAM::markOrphanChain(BlockHeaderRef & bhpStart)
{
   PDEBUG("Marking orphan chain");
   bhpStart.isMainBranch_ = true;
   map<BinaryData, BlockHeaderRef>::iterator iter;
   iter = headerHashMap_.find(bhpStart.getPrevHash());
   HashStringRef lastHeadHash(32);
   while( iter != headerHashMap_.end() )
   {
      // I don't see how it's possible to have a header that used to be 
      // in the main branch, but is now an ORPHAN (meaning it has no
      // parent).  It will be good to detect this case, though
      if(iter->second.isMainBranch() == true)
      {
         cout << "***ERROR: Block previously main branch, now orphan!?"
              << iter->second.getThisHash().toHexStr() << endl;
         cerr << "***ERROR: Block previously main branch, now orphan!?"
              << iter->second.getThisHash().toHexStr() << endl;
         previouslyValidBlockHeaderPtrs_.push_back(&(iter->second));
      }
      iter->second.isOrphan_ = true;
      iter->second.isMainBranch_ = false;
      lastHeadHash.setRef(iter->second.thisHash_);
      iter = headerHashMap_.find(iter->second.getPrevHash());
   }
   orphanChainStartBlocks_.push_back(&(headerHashMap_[lastHeadHash.copy()]));
   PDEBUG("Done marking orphan chain");
}


////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
TxOutRef BlockDataManager_FullRAM::getPrevTxOut(TxInRef & txin)
{
   if(txin.isCoinbase())
      return TxOutRef();

   OutPointRef opr = txin.getOutPointRef();
   TxRef & tx = *(getTxByHash(opr.getTxHash()));
   uint32_t idx = opr.getTxOutIndex();
   return tx.getTxOutRef(idx);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockDataManager_FullRAM::getSenderAddr20(TxInRef & txin)
{
   if(txin.isCoinbase())
      return BinaryData(0);

   return getPrevTxOut(txin).getRecipientAddr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataManager_FullRAM::getSentValue(TxInRef & txin)
{
   if(txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}




////////////////////////////////////////////////////////////////////////////////
// Methods for handling zero-confirmation transactions
////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::enableZeroConf(string zcFilename)
{
   zcEnabled_  = true; 
   zcFilename_ = zcFilename;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::readZeroConfFile(string zcFilename)
{
   ifstream zcFile(zcFilename_.c_str(),  ios::in | ios::binary);
   if(zcFile)
   {
      zcFile.seekg(0, ios::end);
      uint64_t filesize = (size_t)zcFile.tellg();
      if(filesize < 8)
      {
         zcFile.close();
         return;
      }
      zcFile.seekg(0, ios::beg);
      BinaryData zcData(filesize);
      zcFile.read((char*)zcData.getPtr(), filesize);

      // We succeeded opening the file...
      BinaryRefReader brr(zcData);
      while(brr.getSizeRemaining() > 8)
      {
         uint64_t txTime = brr.get_uint64_t();
         uint32_t txLen = BtcUtils::TxCalcLength(brr.getCurrPtr());
         BinaryData rawtx(txLen);
         brr.get_BinaryData(rawtx.getPtr(), txLen);
         addNewZeroConfTx(rawtx, txTime, false);
      }
      zcFile.close();
   }
   purgeZeroConfPool();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::disableZeroConf(string zcFilename)
{
   zcEnabled_  = false; 
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FullRAM::addNewZeroConfTx(BinaryData const & rawTx, 
                                                uint64_t txtime,
                                                bool writeToFile)
{
   // TODO:  We should do some kind of verification check on this tx
   //        to make sure it's potentially valid.  Right now, it doesn't 
   //        matter, because the Satoshi client is sitting between
   //        us and the network and doing the checking for us.

   if(txtime==0)
      txtime = time(NULL);

   BinaryData txHash = BtcUtils::getHash256(rawTx);
   if(zeroConfMap_.find(txHash) != zeroConfMap_.end() ||
      txHashMap_.find(txHash)   != txHashMap_.end())
      return false;
   
   
   zeroConfMap_[txHash] = ZeroConfData();
   ZeroConfData & zc = zeroConfMap_[txHash];
   zc.iter_ = zeroConfRawTxList_.insert(zeroConfRawTxList_.end(), rawTx);
   zc.txref_.unserialize(*(zc.iter_));
   zc.txtime_ = txtime;

   // Record time.  Write to file
   if(writeToFile)
   {
      ofstream zcFile(zcFilename_.c_str(), ios::app | ios::binary);
      zcFile.write( (char*)(&zc.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)zc.txref_.getPtr(),  zc.txref_.getSize());
      zcFile.close();
   }
   return true;
}



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::purgeZeroConfPool(void)
{
   list< map<HashString, ZeroConfData>::iterator > mapRmList;

   // Find all zero-conf transactions that made it into the blockchain
   map<HashString, ZeroConfData>::iterator iter;
   for(iter  = zeroConfMap_.begin();
       iter != zeroConfMap_.end();
       iter++)
   {
      // txHashMap_ holds only blocks in the blockchain
      if(txHashMap_.find(iter->first) != txHashMap_.end())
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
void BlockDataManager_FullRAM::rewriteZeroConfFile(void)
{
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   map<HashString, ZeroConfData>::iterator iter;
   for(iter  = zeroConfMap_.begin();
       iter != zeroConfMap_.end();
       iter++)
   {
      ZeroConfData & zc = iter->second;
      zcFile.write( (char*)(&zc.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)(zc.txref_.getPtr()),  zc.txref_.getSize());
   }

   zcFile.close();
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::rescanWalletZeroConf(BtcWallet & wlt)
{
   // Clear the whole list, rebuild
   wlt.clearZeroConfPool();

   //cout << "Pre rescan:" << endl;
   //wlt.pprintAlot();

   // We used to iterate over the zeroConfMap_ to do the scan, but if there 
   // are ZC tx that spend other ZC tx, then iterating over the map might lead
   // to processing them out of order -- we really need to process them in the
   // order they were received.  (otherwise, we don't recognize the second tx 
   // as our own, and the first one (processed second) doesn't get updated by
   // appropriately).  However, to avoid complicating the two structs
   // zeroConfMap_ and zeroConfRawTxList_, we simply iterate over the list, 
   // recompute the hash, and find the ZC in the map.  
   //
   // This is kind of inefficient, but really only matters if we have
   // millions of tx-per sec coming in over the network... I'll take the
   // risk :)
   static BinaryData txHash(32);
   list<BinaryData>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      wlt.scanTx(zcd.txref_, 0, zcd.txtime_, UINT32_MAX);
   }

   //cout << "After rescan:" << endl;
   //wlt.pprintAlot();
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::pprintZeroConfPool(void)
{
   map<HashString, ZeroConfData>::iterator iter;
   for(iter  = zeroConfMap_.begin();
       iter != zeroConfMap_.end();
       iter++)
   {
      TxRef & txref = iter->second.txref_;
      cout << txref.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
      for(uint32_t i=0; i<txref.getNumTxOut(); i++)
         cout << txref.getTxOutRef(i).getValue() << " ";
      cout << endl;
   }
}


////////////////////////////////////////////////////////////////////////////////
void BtcAddress::clearZeroConfPool(void)
{
   ledgerZC_.clear();
   relevantTxIOPtrsZC_.clear();
}


////////////////////////////////////////////////////////////////////////////////
void BtcWallet::clearZeroConfPool(void)
{
   ledgerAllAddrZC_.clear();
   for(uint32_t i=0; i<addrMap_.size(); i++)
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
vector<LedgerEntry> BtcWallet::getTxLedger(BinaryData const * addr160)
{
   // Make sure to rebuild the ZC ledgers before calling this method
   if(addr160==NULL)
      return ledgerAllAddr_;
   else
   {
      if(addrMap_.find(*addr160) == addrMap_.end())
         return vector<LedgerEntry>(0);
      else
         return addrMap_[*addr160].getTxLedger();
   }
}
////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> BtcWallet::getZeroConfLedger(BinaryData const * addr160)
{
   // Make sure to rebuild the ZC ledgers before calling this method
   if(addr160==NULL)
      return ledgerAllAddrZC_;
   else
   {
      if(addrMap_.find(*addr160) == addrMap_.end())
         return vector<LedgerEntry>(0);
      else
         return addrMap_[*addr160].getZeroConfLedger();
   }
}
























