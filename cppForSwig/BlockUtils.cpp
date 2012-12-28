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
   txOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txOfInputZC_(NULL),
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
   txOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txOfInputZC_(NULL),
   indexOfInputZC_(0) ,
   isTxOutFromSelf_(false),
   isFromCoinbase_(false) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef* txPtrO, uint32_t txoutIndex) :
   amount_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0) ,
   txOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false)
{ 
   setTxOut(txPtrO, txoutIndex);
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef*    txPtrO,
                   uint32_t  txoutIndex,
                   TxRef*    txPtrI, 
                   uint32_t  txinIndex) :
   amount_(0),
   txOfOutputZC_(NULL),
   indexOfOutputZC_(0),
   txOfInputZC_(NULL),
   indexOfInputZC_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false)
{ 
   setTxOut(txPtrO, txoutIndex);
   setTxIn (txPtrI, txinIndex );
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


//////////////////////////////////////////////////////////////////////////////
TxOut TxIOPair::getTxOut(void) const
{
   // I actually want this to segfault when there is no TxOut... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxOut/hasTxOutZC)
   if(hasTxOut())
      return txPtrOfOutput_->getTxCopy().getTxOut(indexOfOutput_);
   else
      return getTxOutZC();
}


//////////////////////////////////////////////////////////////////////////////
TxIn TxIOPair::getTxIn(void) const
{
   // I actually want this to segfault when there is no TxIn... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxIn/hasTxInZC)
   if(hasTxIn())
      return txPtrOfInput_->getTxCopy().getTxIn(indexOfInput_);
   else
      return getTxInZC();
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxIn(TxRef* txref, uint32_t index)
{ 
   txPtrOfInput_  = txref;
   indexOfInput_  = index;
   txOfInputZC_   = NULL;
   indexOfInputZC_= 0;

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxInZC(Tx* tx, uint32_t index)
{ 
   if(hasTxInInMain() || hasTxInZC())
      return false;
   else
   {
      txPtrOfInput_    = NULL;
      indexOfInput_    = 0;
      txOfInputZC_     = tx;
      indexOfInputZC_  = index;
   }

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxOut(TxRef* txref, uint32_t index)
{
   txPtrOfOutput_   = txref; 
   indexOfOutput_   = index;
   txOfOutputZC_    = NULL;
   indexOfOutputZC_ = 0;
   if(hasTxOut())
      amount_ = getTxOut().getValue();

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxOutZC(Tx* tx, uint32_t index)
{
   if(hasTxOutInMain() || hasTxOutZC())
      return false;
   else
   {
      txPtrOfOutput_   = NULL;
      indexOfOutput_   = 0;
      txOfOutputZC_    = tx;
      indexOfOutputZC_ = index;
      if(hasTxOutZC())
         amount_ = getTxOutZC().getValue();
   }
   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isStandardTxOutScript(void) 
{ 
   if(hasTxOut()) 
      return getTxOut().isStandard();
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

bool TxIOPair::hasTxOutZC(void) const
{ 
   return (txOfOutputZC_!=NULL && txOfOutputZC_->isInitialized()); 
}

bool TxIOPair::hasTxInZC(void) const
{ 
   return (txOfInputZC_!=NULL && txOfInputZC_->isInitialized());
}

void TxIOPair::clearZCFields(void)
{
   txOfOutputZC_ = NULL;
   txOfInputZC_  = NULL;
   indexOfOutputZC_ = 0;
   indexOfInputZC_  = 0;
   //isTxOutFromSelf_ = false;
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

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprint(void)
{
   cout << "LedgerEntry: " << endl;
   cout << "   Addr20  : " << getAddrStr20().toHexStr() << endl;
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
vector<UnspentTxOut> BtcAddress::getFullTxOutList(uint32_t blkNum)
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

   if(addrMap_.find(addr) != addrMap_.end())
      return;

   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, firstTimestamp, firstBlockNum,
                                lastTimestamp,  lastBlockNum);
   addrPtrVect_.push_back(addrPtr);

   // Default behavior is "don't know, must rescan" if no firstBlk is spec'd
   if(bdmPtr_!=NULL)
      bdmPtr_->registerImportedAddress(addr, firstBlockNum);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addNewAddress(BinaryData addr)
{
   if(addrMap_.find(addr) != addrMap_.end())
      return;

   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, 0,0, 0,0); 
   addrPtrVect_.push_back(addrPtr);

   if(bdmPtr_!=NULL)
      bdmPtr_->registerNewAddress(addr);
}

/////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress(BtcAddress const & newAddr)
{
   if(addrMap_.find(newAddr.getAddrStr20()) != addrMap_.end())
      return;

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
pair<bool,bool> BtcWallet::isMineBulkFilter( Tx & tx )
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
         //TxOut txout = tx.getTxOut(iout);
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
// This method is used in the registeredAddrScan to conditionally create and
// insert a transaction into the registered list 
void BlockDataManager_FileRefs::insertRegisteredTxIfNew(HashString txHash)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(txHash).second == true)
   {
      TxRef* tx_ptr = getTxRefPtrByHash(txHash);
      RegisteredTx regTx(tx_ptr,
                         tx_ptr->getThisHash(),
                         tx_ptr->getBlockHeight(),
                         tx_ptr->getBlockTxIndex());
      registeredTxList_.push_back(regTx);
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
void BlockDataManager_FileRefs::registeredAddrScan( uint8_t const * txptr,
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
   

   if(registeredAddrMap_.size() == 0)
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
void BlockDataManager_FileRefs::registeredAddrScan( Tx & theTx )
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

   map<HashString, BtcAddress>::iterator addrIter;
   BtcAddress* thisAddrPtr;
   HashString  addr20;
   //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   //{
      //BtcAddress & thisAddr = *(addrPtrVect_[i]);
      //HashString const & addr20 = thisAddr.getAddrStr20();

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
            addrIter = addrMap_.find(addr20);
            if( addrIter == addrMap_.end())
            {
               // Have TxIO but address is not in the map...?
               cout << "ERROR: TxIn in TxIO map, but addr not in wallet...?" << endl;
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
                  isValidNew = txio.setTxIn(tx.getTxRefPtr(), iin);

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
                  nonStdTxioMap_[outpt].setTxIn(tx.getTxRefPtr(), iin);
               nonStdUnspentOutPoints_.erase(outpt);
            }
         }
      } // loop over TxIns
   //}


   //for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   //{
      //BtcAddress & thisAddr = *(addrPtrVect_[i]);
      //HashString const & addr20 = thisAddr.getAddrStr20();

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
         addrIter = addrMap_.find(addr20);
         if( addrIter != addrMap_.end())
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
                  txioIter->second.setTxOut(tx.getTxRefPtr(), iout);
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
                  newTxio.setTxOut(tx.getTxRefPtr(), iout);
   
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
                             Tx &     tx,
                             uint32_t txoutidx,
                             BtcAddress& thisAddr)
{
   TxOut txout = tx.getTxOut(txoutidx);
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
      pair<OutPoint, TxIOPair> toBeInserted(outpt, TxIOPair(tx.getTxRefPtr(),txoutidx));
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
         if( hasAddr(addr160) || perTxAddrSet.count(addr160)>0)
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
// Start BlockDataManager_FileRefs methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_FileRefs::BlockDataManager_FileRefs(void) : 
      totalBlockchainBytes_(0),
      endOfPrevLastBlock_(0),
      topBlockPtr_(NULL),
      genBlockPtr_(NULL),
      lastBlockWasReorg_(false),
      isInitialized_(false),
      GenesisHash_(0),
      GenesisTxHash_(0),
      MagicBytes_(0),
      allRegAddrScannedUpToBlk_(0)
{
   headerMap_.clear();
   txHintMap_.clear();

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
   PDEBUG("SetBtcNetworkParams");
   GenesisHash_.copyFrom(GenHash);
   GenesisTxHash_.copyFrom(GenTxHash);
   MagicBytes_.copyFrom(MagicBytes);
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
void BlockDataManager_FileRefs::SetBlkFileLocation(string   blkdir,
                                                   uint32_t blkdigits,
                                                   uint32_t blkstartidx)
{
   PDEBUG("SetBlkFileLocation");
   blkFileDir_    = blkdir; 
   blkFileDigits_ = blkdigits; 
   blkFileStart_  = blkstartidx; 
}


/////////////////////////////////////////////////////////////////////////////
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
   SCOPED_TIMER("BDM::Reset");

   // Clear out all the "real" data in the blkfile
   blkFileDir_ = "";
   headerMap_.clear();
   txHintMap_.clear();

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
   registeredAddrMap_.clear();
   registeredTxSet_.clear();
   registeredTxList_.clear(); 
   registeredOutPoints_.clear(); 
   allRegAddrScannedUpToBlk_ = 0;
}



/////////////////////////////////////////////////////////////////////////////
int32_t BlockDataManager_FileRefs::getNumConfirmations(HashString txHash)
{
   TxRef* txrefptr = getTxRefPtrByHash(txHash);
   if(txrefptr == NULL)
      return TX_NOT_EXIST;
   else
   {
      if(txrefptr->getHeaderPtr() == NULL)
         return TX_0_UNCONFIRMED; 
      else
      { 
         BlockHeader & txbh = *(txrefptr->getHeaderPtr());
         if(!txbh.isMainBranch())
            return TX_OFF_MAIN_BRANCH;

         int32_t txBlockHeight  = txbh.getBlockHeight();
         int32_t topBlockHeight = getTopBlockHeight();
         return  topBlockHeight - txBlockHeight + 1;
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
BlockHeader & BlockDataManager_FileRefs::getTopBlockHeader(void) 
{
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &(getGenesisBlock());
   return *topBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
BlockHeader & BlockDataManager_FileRefs::getGenesisBlock(void) 
{
   if(genBlockPtr_ == NULL)
      genBlockPtr_ = &(headerMap_[GenesisHash_]);
   return *genBlockPtr_;
}

/////////////////////////////////////////////////////////////////////////////
// Get a blockheader based on its height on the main chain
BlockHeader * BlockDataManager_FileRefs::getHeaderByHeight(int index)
{
   if( index<0 || index>=(int)headersByHeight_.size())
      return NULL;
   else
      return headersByHeight_[index];
}


/////////////////////////////////////////////////////////////////////////////
// The most common access method is to get a block by its hash
BlockHeader * BlockDataManager_FileRefs::getHeaderByHash(HashString const & blkHash)
{
   map<HashString, BlockHeader>::iterator it = headerMap_.find(blkHash);
   if(it==headerMap_.end())
      return NULL;
   else
      return &(it->second);
}



/////////////////////////////////////////////////////////////////////////////
TxRef* BlockDataManager_FileRefs::getTxRefPtrByHash(HashString const & txhash) 
{
   typedef multimap<HashString,TxRef>::iterator hintMapIter;

   static HashString hash4(4);
   hash4.copyFrom(txhash.getPtr(), 4);
   pair<hintMapIter, hintMapIter> eqRange = txHintMap_.equal_range(hash4);

   if(eqRange.first==eqRange.second)
      return NULL;
   else
   {
      hintMapIter iter;
      for( iter = eqRange.first; iter != eqRange.second; iter++ )
      {
         if(iter->second.getThisHash() == txhash)
            return &(iter->second);
      }

      // If we got here, we have some matching prefixes, but no tx that
      // match the full requested tx-hash
      return NULL;
   }
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
TxRef * BlockDataManager_FileRefs::insertTxRef(HashString const & txHash, 
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

/////////////////////////////////////////////////////////////////////////////
Tx BlockDataManager_FileRefs::getTxByHash(HashString const & txhash)
{

   TxRef* txrefptr = getTxRefPtrByHash(txhash);

   if(txrefptr!=NULL)
      return txrefptr->getTxCopy();
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
int BlockDataManager_FileRefs::hasTxWithHash(BinaryData const & txhash)
{
   if(getTxRefPtrByHash(txhash)==NULL)
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
bool BlockDataManager_FileRefs::hasHeaderWithHash(HashString const & txhash) const
{
   return (headerMap_.find(txhash) != headerMap_.end());
}

/////////////////////////////////////////////////////////////////////////////
vector<BlockHeader*> BlockDataManager_FileRefs::prefixSearchHeaders(BinaryData const & searchStr)
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
vector<TxRef*> BlockDataManager_FileRefs::prefixSearchTx(BinaryData const & searchStr)
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
bool BlockDataManager_FileRefs::registerWallet(BtcWallet* wltPtr, bool wltIsNew)
{
   SCOPED_TIMER("registerWallet");

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
   SCOPED_TIMER("registerAddress");
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
   SCOPED_TIMER("registerNewAddress");
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
   SCOPED_TIMER("registerImportedAddress");
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
   SCOPED_TIMER("unregisterAddress");
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
   SCOPED_TIMER("evalLowestBlockNextScan");

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
   SCOPED_TIMER("evalLowestAddressCreationBlock");

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
// This method needs to be callable from another thread.  Therefore, I don't
// seek an exact answer, instead just estimate it based on the last block, 
// and the set of currently-registered addresses.  The method called
// "evalRescanIsRequired()" answers a different question, and iterates 
// through the list of registered addresses, which may be changing in 
// another thread.  
bool BlockDataManager_FileRefs::isDirty( 
                              uint32_t numBlocksToBeConsideredDirty ) const
{
   if(!isInitialized_)
      return false;
   
   uint32_t numBlocksBehind = lastTopBlock_-allRegAddrScannedUpToBlk_;
   return (numBlocksBehind > numBlocksToBeConsideredDirty);
  
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_FileRefs::numBlocksToRescan( BtcWallet & wlt,
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
   rescanBlocks(allRegAddrScannedUpToBlk_, endBlknum);

   allRegAddrScannedUpToBlk_ = endBlknum;
   updateRegisteredAddresses(endBlknum);


   // *********************************************************************** //
   // Finally, walk through all the registered tx
   scanRegisteredTxForWallet(myWallet, startBlknum, endBlknum);

   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(myWallet);

}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::rescanBlocks(uint32_t blk0, uint32_t blk1)
{
   // TODO:   I am assuming this will be too slow, but I will test/time it
   //         before making that conclusion:  perhaps pre-caching is enough
   //         to avoid complicating this to the level of parseEntireBlockchain
   // UPDATE: (3 months later) It appears to be working fine.  A full rescan
   //         using pre-caching as I have done seems to have no noticeable 
   //         impact on performance.  That means this code block could 
   //         probably be reused, and is fairly simple.

   blk1 = min(blk1, getTopBlockHeight()+1);

   SCOPED_TIMER("rescanBlocks");
   for(uint32_t h=blk0; h<blk1; h++)
   {
      BlockHeader & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      // This call simply pulls the entire block into cache, so that 
      // all the subsequent TxRef dereferences will be super fast.
      bhr.getBlockFilePtr().preCacheThisChunk();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         Tx thisTx = txlist[itx]->getTxCopy();
         registeredAddrScan(thisTx);
      }
   }

   allRegAddrScannedUpToBlk_ = blk1;
   updateRegisteredAddresses(blk1);
}


/////////////////////////////////////////////////////////////////////////////
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
         cout << "***WARNING: How did we get a NULL tx?" << endl;
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
vector<TxRef*> BlockDataManager_FileRefs::findAllNonStdTx(void)
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
uint32_t BlockDataManager_FileRefs::parseEntireBlockchain(uint32_t cacheSize)
{
   SCOPED_TIMER("parseEntireBlockchain");
   cout << "Number of registered addr: " << registeredAddrMap_.size() << endl;

   // Initialize a global cache that will be used...
   FileDataCache & globalCache = FileDataPtr::getGlobalCacheRef();
   globalCache.setCacheSize(cacheSize);

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
      cout << "Error finding blockchain files (blkXXXX.dat)" << endl;
      return 0;
   }
   cout << "Highest blkXXXX.dat file: " << numBlkFiles_ << endl;



   if(GenesisHash_.getSize() == 0)
   {
      cout << "***ERROR:  Must set network params before loading blockchain!" << endl;
      cerr << "***ERROR:  Must set network params before loading blockchain!" << endl;
      return 0;
   }


   /////////////////////////////////////////////////////////////////////////////
   // Now we start the meat of this process...
   uint32_t blocksReadSoFar_ = 0;
   uint32_t bytesReadSoFar_ = 0;
   for(uint32_t fnum=1; fnum<=numBlkFiles_; fnum++)
   {
      string blkfile = blkFileList_[fnum-1];
      cout << "Attempting to read blockchain from file: " << blkfile.c_str() << endl;
      uint64_t filesize = globalCache.getFileSize(fnum-1);

      // Open the file, and check the magic bytes on the first block
      ifstream is(blkfile.c_str(), ios::in | ios::binary);
      BinaryData fileMagic(4);
      is.read((char*)(fileMagic.getPtr()), 4);
      is.seekg(0, ios::beg);
      cout << blkfile.c_str() << " is " << BtcUtils::numToStrWCommas(filesize).c_str() << " bytes" << endl;

      if( !(fileMagic == MagicBytes_ ) )
      {
         cerr << "***ERROR:  Block file is for the wrong network!" << endl;
         cerr << "           MagicBytes of this file: " << fileMagic.toHexStr().c_str() << endl;
         return 0;
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
            parseNewBlock(brr, fnum-1, bsb.getFileByteLocation(), nextBlkSize);
            blocksReadSoFar_++;
            bytesReadSoFar_ += nextBlkSize;
            bsb.reader().advance(nextBlkSize);
         }
   
         if(isEOF) 
            break;
      }
   }


   
   // We now have a map of all blocks, let's organize them into a chain.
   organizeChain(true);


   // We need to maintain the physical size of all blkXXXX.dat files together
   totalBlockchainBytes_ = globalCache.getCumulFileSize();



   // Update registered address list so we know what's already been scanned
   lastTopBlock_ = getTopBlockHeight() + 1;
   allRegAddrScannedUpToBlk_ = lastTopBlock_;
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
uint32_t BlockDataManager_FileRefs::readBlkFileUpdate(void)
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
      cout << "***ERROR:  Cannot open " << filename.c_str() << endl;
      cerr << "***ERROR:  Cannot open " << filename.c_str() << endl;
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
            endOfNewLastBlock += *(uint32_t*)(fourBytes.getPtr()) + 8;
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
   
   // Force the caching code to close and re-open block file to see new data
   FileDataPtr::getGlobalCacheRef().refreshLastFile();

   // Observe if everything was up to date when we started, because we're 
   // going to add new blockchain data and don't want to trigger a rescan 
   // if this is just a normal update.
   uint32_t nextBlk = getTopBlockHeight() + 1;
   bool prevRegisteredUpToDate = allRegAddrScannedUpToBlk_==nextBlk;
   
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
      uint32_t blockHeaderOffset = endOfPrevLastBlock_ + brr.getPosition() + 8;
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
      blockAddResults = addNewBlockData( brr,
                                         useFileIndex0Idx,
                                         blockHeaderOffset,
                                         nextBlockSize);


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
            // TODO:  Any other processing to do on reorg?
         }
      }
      
      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }
   lastTopBlock_ = getTopBlockHeight()+1;


   if(prevRegisteredUpToDate)
   {
      allRegAddrScannedUpToBlk_ = getTopBlockHeight()+1;
      updateRegisteredAddresses(allRegAddrScannedUpToBlk_);
   }

   // If the blk file split, switch to tracking it
   cout << "Added new blocks to memory pool: " << nBlkRead << endl;
   if(nextBlkBytesToRead>0)
   {
      FileDataPtr::getGlobalCacheRef().openFile(numBlkFiles_, nextFilename);
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
void BlockDataManager_FileRefs::updateWalletAfterReorg(BtcWallet & wlt)
{
   SCOPED_TIMER("updateWalletAfterReorg");

   // Fix the wallet's ledger
   for(uint32_t i=0; i<wlt.getTxLedger().size(); i++)
   {
      HashString const & txHash = wlt.getTxLedger()[i].getTxHash();
      if(txJustInvalidated_.count(txHash) > 0)
         wlt.getTxLedger()[i].setValid(false);

      if(txJustAffected_.count(txHash) > 0)
         wlt.getTxLedger()[i].changeBlkNum(getTxRefPtrByHash(txHash)->getBlockHeight());
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
            addr.getTxLedger()[i].changeBlkNum(getTxRefPtrByHash(txHash)->getBlockHeight());
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
bool BlockDataManager_FileRefs::parseNewBlock(BinaryRefReader & brr,
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

   // The pointer will be going out of scope, but keep the file location data
   FileDataPtr fdpThisBlock(fileIndex0Idx, thisHeaderOffset-8, blockSize+8); 
   bhptr->setBlockFilePtr(fdpThisBlock);

   // Note where we will start looking for the next block, later
   endOfPrevLastBlock_ = thisHeaderOffset + blockSize;

   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brr.get_var_int(&viSize);

   // The file offset of the first tx in this block is after the var_int
   uint32_t txOffset = thisHeaderOffset + HEADER_SIZE + viSize; 

   // Read each of the Tx
   bhptr->txPtrList_.resize(nTx);
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

      FileDataPtr fdpThisTx(fileIndex0Idx, txOffset, txSize);
      txInputPair.second.setBlkFilePtr(fdpThisTx);

      // Insert the FileDataPtr into the multimap
      BtcUtils::getHash256_NoSafetyCheck(ptrToRawTx, txSize, hashResult);

      // Insert TxRef into txHintMap_, making sure there's no duplicates 
      // of this exactly transaction (which happens on one-block forks).
      // Store the pointer to the newly-added txref, save it with the header
      bhptr->txPtrList_[i] = insertTxRef(hashResult, fdpThisTx, NULL);

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
vector<bool> BlockDataManager_FileRefs::addNewBlockData(BinaryRefReader & brrRawBlock,
                                                        uint32_t fileIndex0Idx,
                                                        uint32_t thisHeaderOffset,
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
void BlockDataManager_FileRefs::reassessAfterReorg( BlockHeader* oldTopPtr,
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
vector<BlockHeader*> BlockDataManager_FileRefs::getHeadersNotOnMainChain(void)
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
bool BlockDataManager_FileRefs::organizeChain(bool forceRebuild)
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
   genBlock.txPtrList_      = vector<TxRef*>(1);
   genBlock.txPtrList_[0]   = getTxRefPtrByHash(GenesisTxHash_);
   //genBlock.txPtrList_[0]->setMainBranch(true);
   genBlock.txPtrList_[0]->setHeaderPtr(&genBlock);


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

      // We need to guarantee that the txs are pointing to the right block
      // header, because they could've been linked to an invalidated block
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef & tx = *(thisHeaderPtr->getTxRefPtrList()[i]);
         tx.setHeaderPtr(thisHeaderPtr);
         //tx.setMainBranch(true);
      }

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
double BlockDataManager_FileRefs::traceChainDown(BlockHeader & bhpStart)
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
void BlockDataManager_FileRefs::markOrphanChain(BlockHeader & bhpStart)
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
TxOut BlockDataManager_FileRefs::getPrevTxOut(TxIn & txin)
{
   if(txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOut(idx);
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataManager_FileRefs::getSenderAddr20(TxIn & txin)
{
   if(txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getRecipientAddr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataManager_FileRefs::getSentValue(TxIn & txin)
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
   SCOPED_TIMER("enableZeroConf");
   zcEnabled_  = true; 
   zcFilename_ = zcFilename;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::readZeroConfFile(string zcFilename)
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
void BlockDataManager_FileRefs::disableZeroConf(string zcFilename)
{
   SCOPED_TIMER("disableZeroConf");
   zcEnabled_  = false; 
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FileRefs::addNewZeroConfTx(BinaryData const & rawTx, 
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
      ofstream zcFile(zcFilename_.c_str(), ios::app | ios::binary);
      zcFile.write( (char*)(&zc.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)zc.txobj_.getPtr(),  zc.txobj_.getSize());
      zcFile.close();
   }
   return true;
}



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FileRefs::purgeZeroConfPool(void)
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
void BlockDataManager_FileRefs::rewriteZeroConfFile(void)
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
void BlockDataManager_FileRefs::rescanWalletZeroConf(BtcWallet & wlt)
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
      Tx & tx = zcd.txobj_;
      cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
      for(uint32_t i=0; i<tx.getNumTxOut(); i++)
         cout << tx.getTxOut(i).getValue() << " ";
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
   SCOPED_TIMER("clearZeroConfPool");
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
   SCOPED_TIMER("BtcWallet::getTxLedger");

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
   SCOPED_TIMER("BtcWallet::getZeroConfLedger");

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
bool BlockDataManager_FileRefs::isTxFinal(Tx & tx)
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






















