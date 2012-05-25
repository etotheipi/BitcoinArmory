////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "BlockUtils.h"




BlockDataManager_FileRefs* BlockDataManager_FileRefs::theOnlyBDM_ = NULL;

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
   isTxOutFromSelf_(false),
   isFromCoinbase_(false) {}

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
   isTxOutFromSelf_(false),
   isFromCoinbase_(false) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef* txPtrO, uint32_t txoutIndex) :
   amount_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0) ,
   txPtrOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txPtrOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false)
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
   isTxOutFromSelf_(false),
   isFromCoinbase_(false)
{ 
   setTxOutRef(txPtrO, txoutIndex);
   setTxInRef (txPtrI, txinIndex );
}


//////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfOutput(void)
{
   if(!hasTxOut())
      return BtcUtils::EmptyHash_;
   else
      return txPtrOfOutput_->getThisHash();
}

//////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfInput(void)
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
bool TxIOPair::isSpendable(uint32_t currBlk)
{ 
   // Spendable TxOuts are ones with at least 1 confirmation, or zero-conf
   // TxOuts that were sent-to-self.  Obviously, they should be unspent, too
   if( hasTxInInMain() || hasTxInZC() )
      return false;
   
   if( hasTxOutInMain() )
   {
      uint32_t nConf = currBlk - txPtrOfOutput_->getBlockHeight() + 1;
      if(isFromCoinbase_ && nConf<=COINBASE_MATURITY)
         return false;
      else
         return true;
   }

   if( hasTxOutZC() && isTxOutFromSelf() )
      return true;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isMineButUnconfirmed(uint32_t currBlk)
{
   // All TxOuts that were from our own transactions are always confirmed
   if(isTxOutFromSelf())
      return false;   

   if( (hasTxIn() && txPtrOfInput_->isMainBranch()) || hasTxInZC() )
      return false;

   if(hasTxOutInMain())
   {
      uint32_t nConf = currBlk - txPtrOfOutput_->getBlockHeight() + 1;
      if(isFromCoinbase_)
         return (nConf<COINBASE_MATURITY);
      else 
         return (nConf<MIN_CONFIRMATIONS);
   }

   else if( hasTxOutZC() && !isTxOutFromSelf() )
      return true;


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
BtcAddress::BtcAddress(HashString    addr, 
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
uint64_t BtcAddress::getSpendableBalance(uint32_t currBlk)
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
      if(txio.isSpendable(blkNum))
      {
         TxOutRef txoutref = txio.getTxOutRef();
         utxoList.push_back( UnspentTxOut(txoutref, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isSpendable(blkNum))
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

// If the wallet is not registered with the BDM, the following two methods do
// the exact same thing.  The only difference is to tell the BDM whether it 
// should do a rescan of the blockchain, or if we know there's nothing to find
// so don't bother (perhaps because we just created the address)...
void BtcWallet::addAddress(HashString    addr, 
                           uint32_t      firstTimestamp,
                           uint32_t      firstBlockNum,
                           uint32_t      lastTimestamp,
                           uint32_t      lastBlockNum)
{

   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, firstTimestamp, firstBlockNum,
                                lastTimestamp,  lastBlockNum);
   addrPtrVect_.push_back(addrPtr);

   // Default behavior is "don't know, must rescan" if no firstBlk is spec'd
   if(bdmPtr_!=NULL)
      bdmPtr_->registerImportedAddress(addr, firstBlockNum);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewAddress(HashString addr)
{
   // TODO: figure out how I might intelligently synchronize 
   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, 0,0, 0,0); 
   addrPtrVect_.push_back(addrPtr);

   if(bdmPtr_!=NULL)
      bdmPtr_->registerNewAddress(addr);
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

   if(bdmPtr_!=NULL)
      bdmPtr_->registerImportedAddress(newAddr.getAddrStr20(), 
                                       newAddr.getFirstBlockNum());
}


/////////////////////////////////////////////////////////////////////////////
// SWIG has some serious problems with typemaps and variable arg lists
// Here I just create some extra functions that sidestep all the problems
// but it would be nice to figure out "typemap typecheck" in SWIG...
void BtcWallet::addAddress_BtcAddress_(BtcAddress const & newAddr)
{ 
   addAddress(newAddr); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_1_(HashString addr)
{  
   PDEBUG("Adding address to BtcWallet");
   addAddress(addr); 
} 

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_3_(HashString    addr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum)
{  
   addAddress(addr, firstBlockNum, firstTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress_5_(HashString    addr, 
                              uint32_t      firstTimestamp,
                              uint32_t      firstBlockNum,
                              uint32_t      lastTimestamp,
                              uint32_t      lastBlockNum)
{  
   addAddress(addr, firstBlockNum, firstTimestamp, lastBlockNum, lastTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasAddr(HashString const & addr20)
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
      static HashString addr20(20);

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
         static HashString addr20(20);
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 65, addr20);
         if( hasAddr(addr20) )
            return pair<bool,bool>(true,false);
      }
      else
      {
         //TxOutRef txout = tx.getTxOutRef(iout);
         //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
         //{
            //BtcAddress & thisAddr = *(addrPtrVect_[i]);
            //HashString const & addr20 = thisAddr.getAddrStr20();
            //if(txout.getScriptRef().find(thisAddr.getAddrStr20()) > -1)
               //scanNonStdTx(0, 0, tx, iout, thisAddr);
            //continue;
         //}
         //break;
      }
   }

   // If we got here, it's either non std or not ours
   return pair<bool,bool>(false,false);
}



/////////////////////////////////////////////////////////////////////////////
// This method is used in the registeredAddrScan to conditionally create and
// insert a transaction into the registered list 
void BlockDataManager_FileRefs::insertRegisteredTxIfNew(HashString txHash)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(txHash).second == true)
   {
      TxRef* tx_ptr = getTxByHash(txHash);
      uint32_t tx_blknum = tx_ptr->getBlockHeight();
      uint32_t tx_blkidx = tx_ptr->getBlockTxIndex();
      RegisteredTx regTx(txHash, tx_blknum, tx_blkidx);
      registeredTxList_.push_back(regTx);
   }
}



/////////////////////////////////////////////////////////////////////////////
//  This basically does the same thing as the bulk filter, but it's for the
//  BDM to collect data on registered wallets/addresses during the initial
//  blockchain scan.  It needs to track relevant OutPoints and produce a 
//  list of transactions that are relevant to the registered wallets.
void BlockDataManager_FileRefs::registeredAddrScan( TxRef & tx )
{
   if(registeredAddrMap_.size() == 0)
      return;

   uint8_t const * txStartPtr = tx.getPtr();
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + tx.getTxInOffset(iin));
      if(registeredOutPoints_.count(op) > 0)
      {
         insertRegisteredTxIfNew(tx.getThisHash());
         break; // we only care if ANY txIns are ours, not which ones
      }
   }

   // We have to scan all TxOuts regardless, to make sure our list of 
   // registeredOutPoints_ is up-to-date so that we can identify TxIns that are
   // ours on future to-be-scanned transactions
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      static uint8_t scriptLenFirstByte;
      static HashString addr20(20);

      uint8_t const * ptr = (txStartPtr + tx.getTxOutOffset(iout) + 8);
      scriptLenFirstByte = *(uint8_t*)ptr;
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         addr20.copyFrom(ptr+4, 20);
         if( addressIsRegistered(addr20) )
         {
            HashString txHash = tx.getThisHash();
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
            HashString txHash = tx.getThisHash();
            insertRegisteredTxIfNew(txHash);
            registeredOutPoints_.insert(OutPoint(txHash, iout));
         }
      }
      else
      {
         /* TODO:  Right now we will just ignoring non-std tx
                   I don't do anything with them right now, anyway
         TxOutRef txout = tx.getTxOutRef(iout);
         for(uint32_t i=0; i<addrPtrVect_.size(); i++)
         {
            BtcAddress & thisAddr = *(addrPtrVect_[i]);
            HashString const & addr20 = thisAddr.getAddrStr20();
            if(txout.getScriptRef().find(thisAddr.getAddrStr20()) > -1)
               scanNonStdTx(0, 0, tx, iout, thisAddr);
            continue;
         }
         //break;
         */
      }
   }
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
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      BtcAddress & thisAddr = *(addrPtrVect_[i]);
      HashString const & addr20 = thisAddr.getAddrStr20();

      ///// LOOP OVER ALL TXIN IN BLOCK /////
      for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
      {
         TxInRef txin = tx.getTxInRef(iin);
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
               // isValidNew only identifies whether this set-call succeeded
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
           
            if(isCoinbaseTx)
               txioIter->second.setFromCoinbase();

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
// Soft calculation:  does not affect the wallet at all
//
// I really need a method to scan an arbitrary tx, regardless of whether it
// is new, and return the LedgerEntry it would've created as if it were new.  
// This is mostly a rewrite of the isMineBulkFilter, and kind of replicates
// the behavior of ScanTx.  But scanTx has been exhaustively tested with all
// the crazy input variations and conditional paths, I don't want to touch 
// it to try to accommodate this use case.
LedgerEntry BtcWallet::calcLedgerEntryForTx(TxRef & tx)
{
   int64_t totalValue = 0;
   uint8_t const * txStartPtr = tx.getPtr();
   bool anyTxInIsOurs = false;
   bool allTxOutIsOurs = true;
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + tx.getTxInOffset(iin));
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
         if( hasAddr(addr20) )
            totalValue += *(uint64_t*)ptr;
         else
            allTxOutIsOurs = false;
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         BtcUtils::getHash160_NoSafetyCheck(ptr+10, 65, addr20);
         if( hasAddr(addr20) )
            totalValue += *(uint64_t*)ptr;
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
                      isSentToSelf,
                      false);
}


////////////////////////////////////////////////////////////////////////////////
LedgerEntry BtcWallet::calcLedgerEntryForTxStr(BinaryData txStr)
{
   TxRef tx(txStr);
   return calcLedgerEntryForTx(tx);
}


////////////////////////////////////////////////////////////////////////////////
void BtcAddress::clearBlkData(void)
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

      TxRef & tx = txio.getTxRefOfInput();
      HashString txHash = tx.getThisHash();

      if(allTxList.count(txHash) > 0)
         continue;
      else
         allTxList.insert(txHash);


      // Iterate over all TxOut in this Tx for recipients
      perTxAddrSet.clear();
      for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
      {
         HashString addr160 = tx.getTxOutRef(iout).getRecipientAddr();

         // Skip this address if it's in our wallet (usually change addr)
         if( hasAddr(addr160) || perTxAddrSet.count(addr160)>0)
            continue; 

         // It's someone else's address for sure, add it to the map if necessary
         if(sentToMap.count(addr160)==0)
            sentToMap[addr160] = AddressBookEntry(addr160);

         sentToMap[addr160].addTx(tx);
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
// Start BlockDataManager_FileRefs methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_FileRefs::BlockDataManager_FileRefs(void) : 
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
      MagicBytes_(0),
      allRegAddrScannedUpToBlk_(0)
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
void BlockDataManager_FileRefs::SetBtcNetworkParams(
                                    BinaryData const & GenHash,
                                    BinaryData const & GenTxHash,
                                    BinaryData const & MagicBytes)
{
   GenesisHash_.copyFrom(GenHash);
   GenesisTxHash_.copyFrom(GenTxHash);
   MagicBytes_.copyFrom(MagicBytes);
}



void BlockDataManager_FileRefs::SelectNetwork(string netName)
{
   if(netName.compare("Main") == 0)
   {
      SetBtcNetworkParams( 
         BinaryData::CreateFromHex(MAINNET_GENESIS_HASH_HEX),
         BinaryData::CreateFromHex(MAINNET_GENESIS_TX_HASH_HEX),
         BinaryData::CreateFromHex(MAINNET_MAGIC_BYTES)         );
   }
   else if(netName.compare("Test") == 0)
   {
      SetBtcNetworkParams( 
         BinaryData::CreateFromHex(TESTNET_GENESIS_HASH_HEX),
         BinaryData::CreateFromHex(TESTNET_GENESIS_TX_HASH_HEX),
         BinaryData::CreateFromHex(TESTNET_MAGIC_BYTES)         );
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
BlockDataManager_FileRefs & BlockDataManager_FileRefs::GetInstance(void) 
{
   static bool bdmCreatedYet_ = false;
   if( !bdmCreatedYet_ )
   {
      theOnlyBDM_ = new BlockDataManager_FileRefs;
      bdmCreatedYet_ = true;
   }
   return (*theOnlyBDM_);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::Reset(void)
{
   // Clear out all the "real" data in the blkfile
   blkFileDir_ = "";
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

   // Clear out any of the registered tx data we have collected so far.
   // Doesn't take any time to recollect if it we have to rescan, anyway.
   registeredTxList_.clear(); 
   registeredOutPoints_.clear(); 
}



/////////////////////////////////////////////////////////////////////////////
int32_t BlockDataManager_FileRefs::getNumConfirmations(HashString txHash)
{
   map<HashString, TxRef>::iterator findResult = txHashMap_.find(txHash); 
   if(findResult == txHashMap_.end())
      return TX_NOT_EXIST;
   else
   {
      if(findResult->second.getHeaderPtr() == NULL)
         return TX_0_UNCONFIRMED; 
      else
      { 
         BlockHeaderRef & txbh = *(findResult->second.getHeaderPtr());
         if(!txbh.isMainBranch())
            return TX_OFF_MAIN_BRANCH;

         int32_t txBlockHeight  = txbh.getBlockHeight();
         int32_t topBlockHeight = getTopBlockHeight();
         return  topBlockHeight - txBlockHeight + 1;
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
BlockHeaderRef & BlockDataManager_FileRefs::getTopBlockHeader(void) 
{
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &(getGenesisBlock());
   return *topBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
BlockHeaderRef & BlockDataManager_FileRefs::getGenesisBlock(void) 
{
   if(genBlockPtr_ == NULL)
      genBlockPtr_ = &(headerHashMap_[GenesisHash_]);
   return *genBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
BlockHeaderRef * BlockDataManager_FileRefs::getHeaderByHeight(int index)
{
   if( index<0 || index>=(int)headersByHeight_.size())
      return NULL;
   else
      return headersByHeight_[index];
}


/////////////////////////////////////////////////////////////////////////////
// The most common access method is to get a block by its hash
BlockHeaderRef * BlockDataManager_FileRefs::getHeaderByHash(HashString const & blkHash)
{
   map<HashString, BlockHeaderRef>::iterator it = headerHashMap_.find(blkHash);
   if(it==headerHashMap_.end())
      return NULL;
   else
      return &(it->second);
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
TxRef* BlockDataManager_FileRefs::getTxByHash(HashString const & txhash)
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
bool BlockDataManager_FileRefs::hasTxWithHash(HashString const & txhash,
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
bool BlockDataManager_FileRefs::hasHeaderWithHash(HashString const & txhash) const
{
   return (headerHashMap_.find(txhash) != headerHashMap_.end());
}

/////////////////////////////////////////////////////////////////////////////
vector<BlockHeaderRef*> BlockDataManager_FileRefs::prefixSearchHeaders(BinaryData const & searchStr)
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
vector<TxRef*> BlockDataManager_FileRefs::prefixSearchTx(BinaryData const & searchStr)
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
vector<BinaryData> BlockDataManager_FileRefs::prefixSearchAddress(BinaryData const & searchStr)
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
      for(uint32_t i=0; i<getNumAddr(); i++)
      {
         BtcAddress & addr = getAddrByIndex(i);
         HashString addr160 = addr.getAddrStr20();
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
bool BlockDataManager_FileRefs::registerWallet(BtcWallet* wltPtr, bool wltIsNew)
{
   // Check if the wallet is already registered
   if(registeredWallets_.find(wltPtr) != registeredWallets_.end())
      return false;

   // Add it to the list of wallets to watch
   registeredWallets_.insert(wltPtr);

   // Now add all the individual addresses from the wallet
   for(uint32_t i=0; i<wltPtr->getNumAddr(); i++)
   {
      // If this is a new wallet, the value of getFirstBlockNum is irrelevant
      BtcAddress & addr = wltPtr->getAddrByIndex(i);

      if(wltIsNew)
         registerNewAddress(addr.getAddrStr20());
      else
         registerImportedAddress(addr.getAddrStr20(), addr.getFirstBlockNum());
   }

   // We need to make sure the wallet can tell the BDM when an address is added
   wltPtr->setBdmPtr(this);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::registerAddress(HashString addr160, 
                                            bool addrIsNew,
                                            uint32_t firstBlk)
{
   if(registeredAddrMap_.find(addr160) != registeredAddrMap_.end())
   {
      // Address is already registered.  Don't think there's anything to do 
      return false;
   }

   if(addrIsNew)
      firstBlk = getTopBlockHeight() + 1;

   registeredAddrMap_[addr160] = RegisteredAddress(addr160, firstBlk);
   allRegAddrScannedUpToBlk_  = min(firstBlk, allRegAddrScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::registerNewAddress(HashString addr160)
{
   if(registeredAddrMap_.find(addr160) != registeredAddrMap_.end())
      return false;

   uint32_t currBlk = getTopBlockHeight();
   registeredAddrMap_[addr160] = RegisteredAddress(addr160, currBlk);

   // New address cannot affect allRegAddrScannedUpToBlk_, so don't bother
   //allRegAddrScannedUpToBlk_  = min(currBlk, allRegAddrScannedUpToBlk_);
   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::registerImportedAddress(HashString addr160,
                                                    uint32_t createBlk)
{
   if(registeredAddrMap_.find(addr160) != registeredAddrMap_.end())
      return false;

   // In some cases we may have used UINT32_MAX to specify "don't know"
   if(createBlk==UINT32_MAX)
      createBlk = 0;

   registeredAddrMap_[addr160] = RegisteredAddress(addr160, createBlk);
   allRegAddrScannedUpToBlk_ = min(createBlk, allRegAddrScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::unregisterAddress(HashString addr160)
{
   if(registeredAddrMap_.find(addr160) == registeredAddrMap_.end())
      return false;
   
   registeredAddrMap_.erase(addr160);
   allRegAddrScannedUpToBlk_ = evalLowestBlockNextScan();
   return true;
}


/////////////////////////////////////////////////////////////////////////////
BtcWallet::~BtcWallet(void)
{
   if(bdmPtr_!=NULL)
      bdmPtr_->unregisterWallet(this);
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_FileRefs::evalLowestBlockNextScan(void)
{
   uint32_t lowestBlk = UINT32_MAX;
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredAddrMap_.begin();
       raIter != registeredAddrMap_.end();
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
uint32_t BlockDataManager_FileRefs::evalLowestAddressCreationBlock(void)
{
   uint32_t lowestBlk = UINT32_MAX;
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredAddrMap_.begin();
       raIter != registeredAddrMap_.end();
       raIter++)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, raIter->second.blkCreated_);
   }
   return lowestBlk;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::evalRescanIsRequired(void)
{
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   allRegAddrScannedUpToBlk_ = evalLowestBlockNextScan();
   return (allRegAddrScannedUpToBlk_ < getTopBlockHeight()+1);
}

/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_FileRefs::numBlocksToRescan( BtcWallet & wlt,
                                               uint32_t endBlk)
{

   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   uint32_t currNextBlk = getTopBlockHeight() + 1;
   endBlk = min(endBlk, currNextBlk);

   // If wallet is registered and current, no rescan necessary
   if(walletIsRegistered(wlt))
      return (endBlk - allRegAddrScannedUpToBlk_);

   // The wallet isn't registered with the BDM, but there's a chance that 
   // each of its addresses are -- if any one is not, do rescan
   uint32_t maxAddrBehind = 0;
   for(uint32_t i=0; i<wlt.getNumAddr(); i++)
   {
      BtcAddress & addr = wlt.getAddrByIndex(i);

      // If any address is not registered, will have to do a full scan
      if(registeredAddrMap_.find(addr.getAddrStr20()) == registeredAddrMap_.end())
         return endBlk;  // Gotta do a full rescan!

      RegisteredAddress & ra = registeredAddrMap_[addr.getAddrStr20()];
      maxAddrBehind = max(maxAddrBehind, endBlk-ra.alreadyScannedUpToBlk_);
      cout << maxAddrBehind << " ";
   }

   // If we got here, then all addr are already registered and current
   
   return maxAddrBehind;
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::updateRegisteredAddresses(uint32_t newTopBlk)
{
   map<HashString, RegisteredAddress>::iterator raIter;
   for(raIter  = registeredAddrMap_.begin();
       raIter != registeredAddrMap_.end();
       raIter++)
   {
      raIter->second.alreadyScannedUpToBlk_ = newTopBlk;
   }
   
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::resetRegisteredWallets(void)
{
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
bool BlockDataManager_FileRefs::walletIsRegistered(BtcWallet & wlt)
{
   return (registeredWallets_.find(&wlt)!=registeredWallets_.end());
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::addressIsRegistered(HashString addr160)
{
   return (registeredAddrMap_.find(addr160)!=registeredAddrMap_.end());
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
//     If allRegAddrScannedUpToBlk_==1500:
//
//     registeredAddrScan from 1500-->2000
//     sort registered list
//     scanTx all tx in registered list between 1000 and 2000
void BlockDataManager_FileRefs::scanBlockchainForTx(BtcWallet & myWallet,
                                                uint32_t startBlknum,
                                                uint32_t endBlknum)
{

   // The BDM knows the highest block to which ALL CURRENT REGISTERED ADDRESSES
   // are up-to-date in the registeredTxList_ list.  
   // If this wallet is not registered, it needs to be, before we start
   if(!walletIsRegistered(myWallet))
      registerWallet( &myWallet );

   
   // Check whether we can get everything we need from the registered tx list
   endBlknum = min(endBlknum, getTopBlockHeight()+1);
   uint32_t numRescan = numBlocksToRescan(myWallet, endBlknum);


   // *********************************************************************** //
   // First make sure that the registered txList is up to date
   // startBlknum might have to be set to 0 if any addr need full rescan
   for(uint32_t h=allRegAddrScannedUpToBlk_; h<endBlknum; h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);
         registeredAddrScan(tx);
      }
   }

   allRegAddrScannedUpToBlk_ = endBlknum;
   updateRegisteredAddresses(endBlknum);


   // *********************************************************************** //
   // Sort the list of transactions:  if we had to rescan parts of the chain,
   // then the registeredTxList_ will probably be out of order
   registeredTxList_.sort();


   // *********************************************************************** //
   // Finally, walk through all the registered tx
   scanRegisteredTxForWallet(myWallet, startBlknum, endBlknum);



   myWallet.sortLedger(); // removes invalid tx and sorts

   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(myWallet);

   PDEBUG("Done scanning blockchain for tx");
}


void BlockDataManager_FileRefs::pprintRegisteredWallets(void)
{
   set<BtcWallet*>::iterator iter;
   for(iter  = registeredWallets_.begin(); 
       iter != registeredWallets_.end(); 
       iter++)
   {
      cout << "Wallet:";
      cout << "\tBalance: " << (*iter)->getFullBalance();
      cout << "\tNAddr:   " << (*iter)->getNumAddr();
      cout << "\tNTxio:   " << (*iter)->getTxIOMap().size();
      cout << "\tNLedg:   " << (*iter)->getTxLedger().size();
      cout << "\tNZC:     " << (*iter)->getZeroConfLedger().size() << endl;      
   }
}



/////////////////////////////////////////////////////////////////////////////
// This assumes that registeredTxList_ has already been populated from 
// the initial blockchain scan.  The blockchain contains millions of tx,
// but this list will at least 3 orders of magnitude smaller
void BlockDataManager_FileRefs::scanRegisteredTxForWallet( BtcWallet & wlt,
                                                       uint32_t blkStart,
                                                       uint32_t blkEnd)
{
   PDEBUG("Scanning relevant tx list for wallet");

   ///// LOOP OVER ALL RELEVANT TX ////
   list<RegisteredTx>::iterator txIter;
   for(txIter  = registeredTxList_.begin();
       txIter != registeredTxList_.end();
       txIter++)
   {
      // Skip transactions if they exist only on an invalid block
      TxRef* txptr = getTxByHash(txIter->txHash_);
      if( txptr==NULL )
      {
         cout << "***WARNING: How did we get a NULL tx?" << endl;
         continue;
      }

      BlockHeaderRef* bhr = txptr->getHeaderPtr();
      if( bhr==NULL )
      {
         cout << "***WARNING: How did we get a tx without a header?" << endl;
         continue;
      }

      if( !bhr->isMainBranch() )
         continue;

      uint32_t thisBlk = bhr->getBlockHeight();
      if(thisBlk < blkStart || thisBlk>=blkEnd)
         continue;

      if( !isTxFinal(*txptr) )
         continue;

      // If we made it here, we want to scan this tx!
      wlt.scanTx(*txptr, txptr->getBlockTxIndex(), bhr->getTimestamp(), thisBlk);
   }
 
   wlt.sortLedger();


   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(wlt);

   PDEBUG("Done scanning blockchain for tx");
}



/////////////////////////////////////////////////////////////////////////////
vector<TxRef*> BlockDataManager_FileRefs::findAllNonStdTx(void)
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
uint32_t BlockDataManager_FileRefs::parseEntireBlockchain(string blkdir)
{
   // First thing we need to do is find all the blk000X.dat files.
   // To avoid branching the code based on OS, I do something slightly
   // awkward but will work on all systems.  I can do this because I know
   // exactly what files I'm looking for...
   // Also initialize a global cache that will be used...
   uint32_t highestBlkFileIndex=0;
   uint64_t totalBlkBytes = 0;
   blkFileList_.clear();
   while(highestBlkFileIndex < UINT16_MAX)
   {
      highestBlkFileIndex++;
      char path[256];
      sprintf(path, "%s/blk%04d.dat", blkdir, highestBlkFileIndex);
      ifstream is(path, ios::in);
      if(!is.is_open())
         break;

      blkFileList_.push_back(string(path));
      totalBlkBytes += fdcache.openFile(highestBlkFileIndex, path);
      is.close();
   }
   highestBlkFileIndex--;

   if(highestBlkFileIndex==UINT16_MAX)
   {
      cout << "Error finding blockchain files (blk000X.dat)" << endl;
      return 0;
   }
   cout << "Highest blkXXXX.dat file: " << highestBlkFileIndex << endl;




   // If we want to force a rescan, just pass in "" for filename
   if(filename.size()==0)
      filename = blkFileDir_;

   if(filename.compare(blkfilePath_)==0)
   {
      cout << "Call to load a blockchain that is already loaded!  Skipping..." << endl;
      return 0;
   }

   if(GenesisHash_.getSize() == 0)
   {
      cout << "***ERROR:  Must set network params before loading blockchain!" << endl;
      cerr << "***ERROR:  Must set network params before loading blockchain!" << endl;
      return 0;
   }

   for(uint32_t fidx=1; fidx<=highestBlkFileIndex; fidx++)
   {
      string blkfile = blkFileList_[fidx];
      cout << "Attempting to read blockchain from file: " << blkfile.c_str() << endl;
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
      BinaryData fileMagic(4);
      is.read((char*)(fileMagic.getPtr()), 4);
      is.seekg(0, ios::beg);
      cout << blkfile.c_str() << " is " << filesize/(float)(1024*1024) << " MB" << endl;

      if( !(fileMagic == MagicBytes_ ) )
      {
         cerr << "***ERROR:  Block file is for the wrong network!" << endl;
         return 0;
      }


      // Blockchain data is now in its permanent location in memory
      BinaryStreamBuffer bsb;
      bsb.attachAsStreamBuffer(is, filesize);
   
      uint32_t nBlkRead = 0;
      uint32_t nBytesRead = 0;
   
      bool alreadyRead8B = false;
      uint32_t nextBlkSize;
      TIMER_START("ScanBlockchain");
      while(bsb.streamPull())
      {
         while(bsb.getBufferSizeRemaining() > 8)
         {
   
            if(!alreadyRead8B)
            {
               bsb.reader().advance(4);
               nextBlkSize = bsb.reader().get_uint32_t()
               nBytesRead += 8;
            }
   
            if(bsb.getBufferSizeRemaining() < nextBlkSize)
            {
               alreadyRead8B = true;
               continue;
            }
            alreadyRead8B = false;
   
            BinaryRefReader brr(bsb.reader().getCurrPtr(), nextBlkSize);
            parseNewBlockData(brr, fidx, nBytesRead, nextBlkSize);
            nBlkRead++;
            nBytesRead += nextBlkSize;
         }
      }
      TIMER_STOP("ScanBlockchain");

   }


   // We need to maintain the physical size of blk0001.dat (lastEOFByteLoc_)
   // separately from the total size of the blockchain, which may include
   // new bytes not in the blk0001.dat yet
   totalBlockchainBytes_ = blockchainData_ALL_.getSize();
   lastEOFByteLoc_       = blockchainData_ALL_.getSize();

   // We now have a map of all blocks, let's organize them into a chain.
   organizeChain();

   // Update registered address list so we know what's already been scanned
   uint32_t topBlk = getTopBlockHeight() + 1;
   allRegAddrScannedUpToBlk_ = topBlk;
   updateRegisteredAddresses(topBlk);
   
   
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
uint32_t BlockDataManager_FileRefs::readBlkFileUpdate(string filename)
{
   TIMER_START("getBlockfileUpdates");

   // The only real use for this arg is for unit-testing, I have two
   // copies of the blockchain one with an extra block or two in it.
   if(filename.size() == 0)
      filename = blkfilePath_;

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

   // If everything was up to date when we started, mark it up to 
   // date after we're done.  But, if we receive a new block after
   // importing an address requiring rescan, we don't want to mark
   // it as up-to-date at the end of adding new blocks
   uint32_t nextBlk = getTopBlockHeight() + 1;
   bool prevRegisteredUpToDate = allRegAddrScannedUpToBlk_==nextBlk;
   
   // Seek to the beginning of the new data and read it
   // TODO:  Check why we need the -1 on lastEOFByteLoc_.  And if it is 
   //        necessary, do we need it elsewhere, too?
   BinaryData newBlockDataRaw(nBytesToRead);
   is.seekg(lastEOFByteLoc_, ios::beg);
   is.read((char*)newBlockDataRaw.getPtr(), nBytesToRead);
   is.close();

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
            // Update all the registered wallets...
            cout << "This block forced a reorg!" << endl;
            updateWalletsAfterReorg(registeredWallets_);
         }
      }
      

      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }
   TIMER_STOP("getBlockfileUpdates");

   if(prevRegisteredUpToDate)
      updateRegisteredAddresses(getTopBlockHeight()+1);

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
void BlockDataManager_FileRefs::updateWalletAfterReorg(BtcWallet & wlt)
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
void BlockDataManager_FileRefs::updateWalletsAfterReorg(vector<BtcWallet*> wltvect)
{
   for(uint32_t i=0; i<wltvect.size(); i++)
      updateWalletAfterReorg(*wltvect[i]);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::updateWalletsAfterReorg(set<BtcWallet*> wltset)
{
   set<BtcWallet*>::iterator iter;
   for(iter = wltset.begin(); iter != wltset.end(); iter++)
      updateWalletAfterReorg(**iter);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::verifyBlkFileIntegrity(void)
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
bool BlockDataManager_FileRefs::parseNewBlockData(BinaryRefReader & brr,
                                                  uint32_t fileIndex,
                                                  uint32_t blockHeaderOffset,
                                                  uint32_t blockSize)
{
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

   // The key is to keep the file ref... the pointer will be going out of scope
   FileDataRef fdrThisHeader(fileIndex, blockHeaderOffset, HEADER_SIZE); 
   bhptr->setBlkFileRef(fdrThisHeader);

   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brr.get_var_int(&viSize);
   bhptr->blockNumBytes_ = nBytes;
   bhptr->blkByteLoc_    = currBlockchainSize;

   uint32_t txOffset = blockHeaderOffset + HEADER_SIZE + viSize; 

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

      FileDataRef fdrThisTx(fileIndex, txOffset, txptr->getSize());
      txptr->setBlkFileRef(fdrdThisTx);
      txOffset += txptr->getSize();
      // We don't set this tx's headerPtr because there could be multiple
      // headers that reference this tx... we will wait until the chain
      // is organized and make sure this tx points to the header that 
      // is on the main chain.


      // UPDATED FOR MMAP BLOCKCHAIN:  
      // We will have wallets registered so the BDM can be "on the look
      // out" for wallet-relevant transactions during its initial scan.
      // It won't process any tx, because we don't know if they are on
      // the main chain or not, but they will be collected and then 
      // processed later when we know more.
      registeredAddrScan(*txptr);
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
vector<bool> BlockDataManager_FileRefs::addNewBlockData(BinaryData rawBlock,
                                                    bool writeToBlk0001)
{
   // TODO:  maybe we should check whether we already have this block...?
   vector<bool> vb(3);
   blockchainData_NEW_.push_back(rawBlock);
   list<BinaryData>::iterator listEnd = blockchainData_NEW_.end();
   listEnd--;
   BinaryRefReader newBRR( listEnd->getPtr(), rawBlock.getSize() );
   bool addDataSucceeded = parseNewBlockData(newBRR, totalBlockchainBytes_);

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
      // Mar 2012 TODO:  
      //     With the MMAP update, we now have registered wallets tracked
      //     by BDM, which means that the BDM could actually set the
      //     wallet straight... I just haven't figured out exactly what 
      //     I need to do
      reassessAfterReorg(prevTopBlockPtr_, topBlockPtr_, reorgBranchPoint_);
      // TODO:  It might also be necessary to look at the specific
      //        block headers that were invalidated, to make sure 
      //        we aren't using stale data somewhere that copied it
      cout << "Done reassessing tx validity " << endl;
   }

   // Since this method only adds one block, if it's not on the main branch,
   // then it's not the new head
   HashString newHeadHash = BtcUtils::getHash256(rawBlock.getSliceRef(8,80));
   bool newBlockIsNewTop = getHeaderByHash(newHeadHash)->isMainBranch();

   // Write this block to file if is on the main chain and we requested it
   // TODO: this isn't right, because this logic won't write any blocks that
   //       that might eventually be in the main chain but aren't currently.
   //       Luckily this is never used, because we never writeToBlk0001
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
vector<bool> BlockDataManager_FileRefs::addNewBlockDataRef(BinaryDataRef bdr,
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
void BlockDataManager_FileRefs::reassessAfterReorg( BlockHeaderRef* oldTopPtr,
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
vector<BlockHeaderRef*> BlockDataManager_FileRefs::getHeadersNotOnMainChain(void)
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
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
bool BlockDataManager_FileRefs::organizeChain(bool forceRebuild)
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
      map<HashString, BlockHeaderRef>::iterator iter;
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
   map<HashString, BlockHeaderRef>::iterator iter;
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

      HashString & childHash    = thisHeaderPtr->thisHash_;
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

      // This is a dangerous bug -- prevTopBlockPtr_ is set correctly 
      // RIGHT NOW, but won't be once I make the recursive call to organizeChain
      // I need to save it now, and re-assign it after the organizeChain call.
      // (I might consider finding a way to avoid this, but it's fine as-is)
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
double BlockDataManager_FileRefs::traceChainDown(BlockHeaderRef & bhpStart)
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
   map<HashString, BlockHeaderRef>::iterator iter;
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
void BlockDataManager_FileRefs::markOrphanChain(BlockHeaderRef & bhpStart)
{
   PDEBUG("Marking orphan chain");
   bhpStart.isMainBranch_ = true;
   map<HashString, BlockHeaderRef>::iterator iter;
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
TxOutRef BlockDataManager_FileRefs::getPrevTxOut(TxInRef & txin)
{
   if(txin.isCoinbase())
      return TxOutRef();

   OutPointRef opr = txin.getOutPointRef();
   TxRef & tx = *(getTxByHash(opr.getTxHash()));
   uint32_t idx = opr.getTxOutIndex();
   return tx.getTxOutRef(idx);
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataManager_FileRefs::getSenderAddr20(TxInRef & txin)
{
   if(txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getRecipientAddr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataManager_FileRefs::getSentValue(TxInRef & txin)
{
   if(txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}




////////////////////////////////////////////////////////////////////////////////
// Methods for handling zero-confirmation transactions
////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::enableZeroConf(string zcFilename)
{
   zcEnabled_  = true; 
   zcFilename_ = zcFilename;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::readZeroConfFile(string zcFilename)
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
void BlockDataManager_FileRefs::disableZeroConf(string zcFilename)
{
   zcEnabled_  = false; 
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::addNewZeroConfTx(BinaryData const & rawTx, 
                                                uint64_t txtime,
                                                bool writeToFile)
{
   // TODO:  We should do some kind of verification check on this tx
   //        to make sure it's potentially valid.  Right now, it doesn't 
   //        matter, because the Satoshi client is sitting between
   //        us and the network and doing the checking for us.

   if(txtime==0)
      txtime = time(NULL);

   HashString txHash = BtcUtils::getHash256(rawTx);
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
void BlockDataManager_FileRefs::purgeZeroConfPool(void)
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
void BlockDataManager_FileRefs::rewriteZeroConfFile(void)
{
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
      zcFile.write( (char*)(zcd.txref_.getPtr()),  zcd.txref_.getSize());
   }

   zcFile.close();
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::rescanWalletZeroConf(BtcWallet & wlt)
{
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

      if( !isTxFinal(zcd.txref_) )
         continue;

      wlt.scanTx(zcd.txref_, 0, zcd.txtime_, UINT32_MAX);
   }
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::pprintZeroConfPool(void)
{
   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      TxRef & txref = zcd.txref_;
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
vector<LedgerEntry> BtcWallet::getTxLedger(HashString const * addr160)
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
vector<LedgerEntry> BtcWallet::getZeroConfLedger(HashString const * addr160)
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


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::isTxFinal(TxRef & tx)
{
   // Anything that is replaceable (regular or through blockchain injection)
   // will be considered isFinal==false.  Users shouldn't even see the tx,
   // because the concept may be confusing, and the current use of non-final
   // tx is most likely for malicious purposes.
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
      if(tx.getTxInRef(i).getSequence() < UINT32_MAX)
         allSeqMax = false;

   if(allSeqMax)
      return true;

   if(tx.getLockTime() < 500000000)
      return (getTopBlockHeight()>tx.getLockTime());
   else
      return (time(NULL)>tx.getLockTime()+7200);
}






















