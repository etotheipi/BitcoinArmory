////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
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
   indexOfInput_(0) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(uint64_t  amount) :
   amount_(amount),
   txPtrOfOutput_(NULL),
   indexOfOutput_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0) {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef* txPtrO, uint32_t txoutIndex) :
   amount_(0),
   txPtrOfInput_(NULL),
   indexOfInput_(0) 
{ 
   setTxOutRef(txPtrO, txoutIndex);
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef*    txPtrO,
                   uint32_t  txoutIndex,
                   TxRef*    txPtrI, 
                   uint32_t  txinIndex) :
   amount_(0)
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

//////////////////////////////////////////////////////////////////////////////
void TxIOPair::setTxInRef(TxRef* txref, uint32_t index)
{ 
   txPtrOfInput_  = txref;
   indexOfInput_  = index;
}

//////////////////////////////////////////////////////////////////////////////
void TxIOPair::setTxOutRef(TxRef* txref, uint32_t index)
{
   txPtrOfOutput_ = txref; 
   indexOfOutput_ = index;
   if(hasTxOut())
      amount_ = getTxOutRef().getValue();
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isStandardTxOutScript(void) 
{ 
   if(hasTxOut()) 
      return getTxOutRef().isStandard();
   return false;
}

pair<bool,bool> TxIOPair::reassessValidity(void)
{
   pair<bool,bool> result;
   result.first  = (hasTxOut() && txPtrOfOutput_->isMainBranch());
   result.second = (hasTxIn()  && txPtrOfInput_->isMainBranch());
   return result;
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
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t BtcAddress::getBalance(void)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isUnspent() &&
         relevantTxIOPtrs_[i]->getTxRefOfOutput().isMainBranch())
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   return balance;
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
////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void BtcWallet::addAddress(BinaryData    addr, 
                           BinaryData    pubKey65,
                           BinaryData    privKey32,
                           uint32_t      firstBlockNum,
                           uint32_t      firstTimestamp)
{

   BtcAddress* addrPtr = &(addrMap_[addr]);
   *addrPtr = BtcAddress(addr, pubKey65, privKey32, 
                         firstBlockNum, firstTimestamp);
   addrPtrVect_.push_back(addrPtr);
   isLocked_ = false;
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
void BtcWallet::addAddress_2_(BinaryData    addr, 
                              BinaryData    pubKey65)
{  
   addAddress(addr, pubKey65); 
} 
void BtcWallet::addAddress_3_(BinaryData    addr, 
                              BinaryData    pubKey65,
                              BinaryData    privKey32)
{  
   addAddress(addr, pubKey65, privKey32); 
} 
void BtcWallet::addAddress_4_(BinaryData    addr, 
                              BinaryData    pubKey65,
                              BinaryData    privKey32,
                              uint32_t      firstBlockNum)
{  
   addAddress(addr, pubKey65, privKey32, firstBlockNum); 
} 
void BtcWallet::addAddress_5_(BinaryData    addr, 
                              BinaryData    pubKey65,
                              BinaryData    privKey32,
                              uint32_t      firstBlockNum,
                              uint32_t      firstTimestamp)
{  
   addAddress(addr, pubKey65, privKey32, firstBlockNum, firstTimestamp); 
}

/////////////////////////////////////////////////////////////////////////////
bool BtcWallet::hasAddr(BinaryData const & addr20)
{
   map<BinaryData, BtcAddress>::iterator addrIter = addrMap_.find(addr20);
   return addrIter != addrMap_.end();
}

/////////////////////////////////////////////////////////////////////////////
// Pass this wallet a TxRef and current time/blknumber.  I used to just pass
// in the BlockHeaderRef with it, but this may be a Tx not in a block yet, 
// but I still need the time/num 
void BtcWallet::scanTx(TxRef & tx, 
                       uint32_t txIndex,
                       uint32_t blknum, 
                       uint32_t blktime)
{
   int64_t totalLedgerAmt = 0;
   bool anyTxInIsOurs   = false;
   bool anyTxOutIsOurs  = false;

   vector<bool> thisTxInIsOurs (tx.getNumTxIn(),  false);
   vector<bool> thisTxOutIsOurs(tx.getNumTxOut(), false);

   ///// LOOP OVER ALL ADDRESSES ////
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      BtcAddress & thisAddr = *(addrPtrVect_[i]);
      BinaryData const & addr20 = thisAddr.getAddrStr20();

      // If this block is before known addr creation time, no point in scanning
      // If this block is before last addr seen time, already seen it!
      // Added a week or 1000 blocks buffer to be safe, and make sure I don't
      // discard a reorg block or some other silly boundary case
      if(  blktime+(3600*24*7) < thisAddr.getLastTimestamp() ||
           blknum+1000         < thisAddr.getLastBlockNum()           )
         continue;  


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
         if(txioIter != txioMap_.end())
         {
            TxIOPair & txio  = txioIter->second;
            TxOutRef const  & txout = txio.getTxOutRef();
            //if(!txio.hasTxIn() && txout.getRecipientAddr()==thisAddr.getAddrStr20())
            if(txout.getRecipientAddr()==thisAddr.getAddrStr20()  && 
               (!txio.hasTxIn() || !txio.getTxRefOfInput().isMainBranch()) )
            {
               anyTxInIsOurs = true;
               thisTxInIsOurs[iin] = true;

               unspentOutPoints_.erase(outpt);
               txio.setTxInRef(&tx, iin);

               int64_t thisVal = (int64_t)txout.getValue();
               LedgerEntry newEntry(addr20, 
                                   -(int64_t)thisVal,
                                    blknum, 
                                    tx.getThisHash(), 
                                    iin,
                                    false,  // actually we don't know yet if sent to self
                                    false); // "isChangeBack" is meaningless for TxIn
               thisAddr.addLedgerEntry(newEntry);
               totalLedgerAmt -= thisVal;

               // Update last seen on the network
               thisAddr.setLastTimestamp(blktime);
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
               nonStdTxioMap_[outpt].setTxInRef(&tx, iin);
               nonStdUnspentOutPoints_.erase(outpt);
            }
         }
      } // loop over TxIns


      ///// LOOP OVER ALL TXOUT IN BLOCK /////
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
            OutPoint outpt(tx.getThisHash(), iout);      
            pair< map<OutPoint, TxIOPair>::iterator, bool> insResult;
            pair<OutPoint, TxIOPair> toBeInserted(outpt, TxIOPair(&tx, iout));
            insResult = txioMap_.insert(toBeInserted);

            TxIOPair & thisTxio = insResult.first->second;
            if(insResult.second == true)
            {
               unspentOutPoints_.insert(outpt);
               anyTxOutIsOurs = true;
               thisTxOutIsOurs[iout] = true;

               thisAddr.addTxIO( thisTxio );

               int64_t thisVal = (int64_t)(txout.getValue());
               LedgerEntry newLedger(addr20, 
                                     thisVal, 
                                     blknum, 
                                     tx.getThisHash(), 
                                     iout,
                                     anyTxInIsOurs,
                                     false);  // we don't actually know
               thisAddr.addLedgerEntry(newLedger);
               totalLedgerAmt += thisVal;
               // Check if this is the first time we've seen this
               if(thisAddr.getFirstTimestamp() == 0)
               {
                  thisAddr.setFirstBlockNum( blknum );
                  thisAddr.setFirstTimestamp( blktime );
               }
               // Update last seen on the network
               thisAddr.setLastTimestamp(blktime);
               thisAddr.setLastBlockNum(blknum);
            }
            else
            {
               //cout << "***WARNING: searchTx: new TxOut already exists!" << endl;
               //cerr << "***WARNING: searchTx: new TxOut already exists!" << endl;
            }
         }
      } // loop over TxOuts



   } // loop over all wallet addresses

   bool allTxOutIsOurs = true;
   for(int i=0; i<tx.getNumTxOut(); i++)
      allTxOutIsOurs = allTxOutIsOurs && thisTxOutIsOurs[i];

   // TODO:  Unfortunately, "isChangeBack" is only meaningful in the 
   //        txOut ledger entry, but we don't know until we have scanned
   //        all the txOuts, whether it's sentToSelf, or only change
   //        returned.  At some point, I put in the effort to be more
   //        rigorous with these
   bool isSentToSelf = (anyTxInIsOurs && allTxOutIsOurs);
   bool isChangeBack = (anyTxInIsOurs && anyTxOutIsOurs && !isSentToSelf);

   if(anyTxInIsOurs || anyTxOutIsOurs)
   {
      txrefList_.push_back(&tx);
      ledgerAllAddr_.push_back(LedgerEntry( BinaryData(0),
                                            totalLedgerAmt, 
                                            blknum, 
                                            tx.getThisHash(), 
                                            txIndex,
                                            isSentToSelf,
                                            isChangeBack));

   }
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
      insResult = txioMap_.insert(toBeInserted);
   }

}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getBalance(void)
{
   uint64_t balance = 0;
   set<OutPoint>::iterator unspentIter;
   for( unspentIter  = unspentOutPoints_.begin(); 
        unspentIter != unspentOutPoints_.end(); 
        unspentIter++)
   {
      TxIOPair & txio = txioMap_[*unspentIter];
      if(txio.getTxRefOfOutput().isMainBranch())
         balance += txioMap_[*unspentIter].getValue();
   }
   return balance;
}

   
////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getBalance(uint32_t i)
{
   return addrPtrVect_[i]->getBalance();
}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getBalance(BinaryData const & addr20)
{
   assert(hasAddr(addr20)); 
   return addrMap_[addr20].getBalance();
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
      isInitialized_(false)
{
   blockchainData_NEW_.clear();
   headerHashMap_.clear();
   txHashMap_.clear();
   headersByHeight_.clear();
   txFileRefs_.clear();
   headerFileRefs_.clear();
   blockchainFilenames_.clear();
   previouslyValidBlockHeaderPtrs_.clear();
   orphanChainStartBlocks_.clear();
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
      genBlockPtr_ = &(headerHashMap_[BtcUtils::GenesisHash_]);
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
   map<BinaryData, TxRef>::iterator it = txHashMap_.find(txhash);
   if(it==txHashMap_.end())
      return NULL;
   else
      return &(it->second);
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_FullRAM::hasTxWithHash(BinaryData const & txhash) const
{
   return (txHashMap_.find(txhash) != txHashMap_.end());
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
// This is an intense search, using every tool we've created so far!
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch(BtcWallet & myWallet)
{
   PDEBUG("Scanning blockchain for tx, from scratch");
   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<headersByHeight_.size(); h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);
         myWallet.scanTx(tx, itx, bhr.getBlockHeight(), bhr.getTimestamp());
      }
   }
   myWallet.sortLedger(); // removes invalid tx and sorts
   PDEBUG("Done scanning blockchain for tx");
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch(vector<BtcWallet*> walletVect)
{
   PDEBUG("Scanning blockchain for tx, from scratch");
   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<headersByHeight_.size(); h++)
   {
      BlockHeaderRef & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX FOR THIS HEADER/////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         for(uint32_t w=0; w<walletVect.size(); w++)
            walletVect[w]->scanTx(tx, itx, bhr.getBlockHeight(), bhr.getTimestamp());
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
uint32_t BlockDataManager_FullRAM::readBlkFileUpdate(void)
{
   PDEBUG2("Update blkfile from ", blkfilePath_);
   TIMER_START("getBlockfileUpdates");

   // Try opening the blkfile for reading
   ifstream is(blkfilePath_.c_str(), ios::in | ios::binary);
   if( !is.is_open() )
   {
      cout << "***ERROR:  Cannot open " << blkfilePath_.c_str() << endl;
      cerr << "***ERROR:  Cannot open " << blkfilePath_.c_str() << endl;
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
            // TODO:  Not sure if there's anything we need to do if this block
            //        didn't extend the main chain.
         }
   
         if(blockchainReorg)
         {
            cout << "This block forced a reorg!  (and we're going to do nothing...)" << endl;
            //TODO:  do something important (besides seg-faulting)
         }
      }
      

      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }
   TIMER_STOP("getBlockfileUpdates");



   // Finally, update the last known blkfile size and return nBlks added
   PDEBUG2("Added new blocks to memory pool: ", nBlkRead);
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
   genBlock.txPtrList_[0]   = getTxByHash(BtcUtils::GenesisTxHash_);
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
vector<UnspentTxOut> 
BlockDataManager_FullRAM::getUnspentTxOutsForWallet( BtcWallet & wlt, int sortType)
{
   vector<UnspentTxOut> result(0);
   set<OutPoint> & unspentOps = wlt.getUnspentOutPoints();
   set<OutPoint>::iterator opIter;
   for(opIter  = unspentOps.begin();
       opIter != unspentOps.end();
       opIter++)
   {
      TxRef & tx = *(getTxByHash(opIter->getTxHash()));
      uint32_t currBlk = getTopBlockHeader().getBlockHeight();
      TxOutRef txout = tx.getTxOutRef(opIter->getTxOutIndex());
      UnspentTxOut uto(txout, currBlk);
      result.push_back(uto);
   }

   if(sortType != -1)
   {
      UnspentTxOut::sortTxOutVect(result, sortType);
      reverse(result.begin(), result.end());
   }
   return result;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> 
BlockDataManager_FullRAM::getNonStdUnspentTxOutsForWallet( BtcWallet & wlt)
{
   return vector<UnspentTxOut>(0);
}


