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
// TxIORefPair Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
TxIORefPair::TxIORefPair(void) : 
   amount_(0),
   txoutRef_(), 
   txoutTxRefPtr_(NULL),
   txinRef_(),
   txinTxRefPtr_(NULL) {}

//////////////////////////////////////////////////////////////////////////////
TxIORefPair::TxIORefPair(uint64_t  amount) :
   amount_(amount),
   txoutRef_(), 
   txoutTxRefPtr_(NULL),
   txinRef_(),
   txinTxRefPtr_(NULL) {}

//////////////////////////////////////////////////////////////////////////////
TxIORefPair::TxIORefPair(TxOutRef const &  outref, 
                         TxRef          *  txPtr) :
   amount_(0),
   txinRef_(),
   txinTxRefPtr_(NULL) 
{ 
   setTxOutRef(outref, txPtr);
}

//////////////////////////////////////////////////////////////////////////////
TxIORefPair::TxIORefPair(TxOutRef  outref, 
                         TxRef*    txPtrOut, 
                         TxInRef   inref, 
                         TxRef*    txPtrIn) :
   amount_(0)
{ 
   setTxOutRef(outref, txPtrOut);
   setTxInRef(inref, txPtrIn);
}

//////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxIORefPair::getTxHashOfOutputRef(void)
{
   if(txoutTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txoutTxRefPtr_->getThisHashRef();
}

//////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxIORefPair::getTxHashOfInputRef(void)
{
   if(txinTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txinTxRefPtr_->getThisHashRef();
}

//////////////////////////////////////////////////////////////////////////////
BinaryData TxIORefPair::getTxHashOfOutput(void)
{
   if(txoutTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txoutTxRefPtr_->getThisHash();
}

//////////////////////////////////////////////////////////////////////////////
BinaryData TxIORefPair::getTxHashOfInput(void)
{
   if(txinTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txinTxRefPtr_->getThisHash();
}

//////////////////////////////////////////////////////////////////////////////
void TxIORefPair::setTxInRef(TxInRef const & inref, TxRef* intxptr)
{ 
   txinRef_  = inref;
   txinTxRefPtr_  = intxptr;
}

//////////////////////////////////////////////////////////////////////////////
void TxIORefPair::setTxOutRef(TxOutRef const & outref, TxRef* outtxptr)
{
   txoutRef_ = outref; 
   txoutTxRefPtr_ = outtxptr;
   if(txoutRef_.isInitialized())
      amount_ = txoutRef_.getValue();
}

bool TxIORefPair::isStandardTxOutScript(void) 
{ 
   if(hasTxOut()) 
      return txoutRef_.isStandard();
   return false;
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
                       BinaryData    pubKey65,
                       BinaryData    privKey32,
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp) :
      address20_(addr), 
      pubKey65_(pubKey65),
      privKey32_(privKey32),
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp)
{ 
   relevantTxIOPtrs_.clear();
} 



uint64_t BtcAddress::getBalance(void)
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isUnspent())
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   return balance;
}

uint32_t BtcAddress::cleanLedger(void)
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
   
   sort(ledger_.begin(), ledger_.end());
   return leRemoved;
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
   bool txIsOurs = false;

   ///// LOOP OVER ALL ADDRESSES ////
   for(uint32_t i=0; i<addrPtrVect_.size(); i++)
   {
      BtcAddress & thisAddr = *(addrPtrVect_[i]);
      BinaryData const & addr20 = thisAddr.getAddrStr20();

      // TODO:  for some reason, this conditional stopped working!
      // If this block is before known addr creation time, no point in scanning
      // If this block is before last addr seen time, already seen it!
      //if(  blktime < thisAddr.getFirstTimestamp()-(3600*24*7) ||
           //blknum  < thisAddr.getFirstBlockNum()-1000            )
         //continue;  

      ///// LOOP OVER ALL TXIN IN BLOCK /////
      uint64_t valueIn = 0;
      bool txInIsOurs = false;
      for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
      {
         TxInRef txin = tx.getTxInRef(iin);
         OutPoint outpt = txin.getOutPoint();
         if(outpt.getTxHashRef() == BtcUtils::EmptyHash_)
            continue;

         // We have the tx, now check if it contains one of our TxOuts
         map<OutPoint, TxIORefPair>::iterator txioIter = txioMap_.find(outpt);
         if(txioIter != txioMap_.end())
         {
            TxIORefPair     & txio  = txioIter->second;
            TxOutRef const  & txout = txioIter->second.getTxOutRef();
            if(!txio.hasTxIn() && txout.getRecipientAddr()==thisAddr.getAddrStr20())
            {
               txIsOurs   = true;
               txInIsOurs = true;

               unspentTxOuts_.erase(outpt);
               txio.setTxInRef(txin, &tx);

               int64_t thisVal = (int64_t)txout.getValue();
               LedgerEntry newEntry(addr20, 
                                   -(int64_t)thisVal,
                                    blknum, 
                                    tx.getThisHash(), 
                                    iin);
               thisAddr.addLedgerEntry(newEntry);
               valueIn += thisVal;

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
               nonStdTxioMap_[outpt].setTxInRef(txin, &tx);
               nonStdUnspentTxOuts_.erase(outpt);
            }
         }
      } // loop over TxIns

      // Add to ledger if this TxIn is ours
      if(txInIsOurs)
      {
         ledgerAllAddr_.push_back(LedgerEntry(addr20, 
                                             -(int64_t)valueIn, 
                                              blknum, 
                                              tx.getThisHash(), 
                                              txIndex));
      }

      ///// LOOP OVER ALL TXOUT IN BLOCK /////
      uint64_t valueOut = 0;
      bool txOutIsOurs = false;
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
            unspentTxOuts_.insert(outpt);
            pair< map<OutPoint, TxIORefPair>::iterator, bool> insResult;
            pair<OutPoint, TxIORefPair> toBeInserted(outpt, TxIORefPair(txout, &tx));
            insResult = txioMap_.insert(toBeInserted);

            TxIORefPair & thisTxio = insResult.first->second;
            if(insResult.second == true)
            {
               txIsOurs    = true;
               txOutIsOurs = true;

               thisAddr.addTxIO( thisTxio );

               int64_t thisVal = (int64_t)(txout.getValue());
               LedgerEntry newLedger(addr20, 
                                     thisVal, 
                                     blknum, 
                                     tx.getThisHash(), 
                                     iout);
               thisAddr.addLedgerEntry(newLedger);
               valueOut += thisVal;
               // Check if this is the first time we've seen this
               if(thisAddr.getFirstBlockNum() == 0)
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


      if(txOutIsOurs)
      {
         ledgerAllAddr_.push_back(LedgerEntry( addr20, 
                                               valueOut, 
                                               blknum, 
                                               tx.getThisHash(), 
                                               txIndex));
      }

   } // loop over all wallet addresses

   if(txIsOurs)
      txrefList_.push_back(&tx);
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
      nonStdUnspentTxOuts_.insert(outpt);
      pair< map<OutPoint, TxIORefPair>::iterator, bool> insResult;
      pair<OutPoint, TxIORefPair> toBeInserted(outpt, TxIORefPair(txout, &tx));
      insResult = nonStdTxioMap_.insert(toBeInserted);
      insResult = txioMap_.insert(toBeInserted);
   }

}

////////////////////////////////////////////////////////////////////////////////
uint64_t BtcWallet::getBalance(void)
{
   uint64_t balance = 0;
   set<OutPoint>::iterator unspentIter;
   for( unspentIter  = unspentTxOuts_.begin(); 
        unspentIter != unspentTxOuts_.end(); 
        unspentIter++)
      balance += txioMap_[*unspentIter].getValue();
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

uint32_t BtcWallet::cleanLedger(void)
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
   sort(ledgerAllAddr_.begin(), ledgerAllAddr_.end());
   return leRemoved;
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
      lastBlockWasReorg_(false)
{
   blockchainData_NEW_.clear();
   headerHashMap_.clear();
   txHashMap_.clear();
   headersByHeight_.clear();
   txFileRefs_.clear();
   headerFileRefs_.clear();
   blockchainFilenames_.clear();
   previouslyValidBlockHeaderRefs_.clear();
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
   previouslyValidBlockHeaderRefs_.clear();
   orphanChainStartBlocks_.clear();
   
   lastEOFByteLoc_ = 0;
   totalBlockchainBytes_ = 0;

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
   myWallet.cleanLedger(); // removes invalid tx and sorts
   PDEBUG("Done scanning blockchain for tx");
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch(vector<BtcWallet> & walletVect)
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
            walletVect[w].scanTx(tx, itx, bhr.getBlockHeight(), bhr.getTimestamp());
      }
   }
 
   // Removes any invalid tx and sorts
   for(uint32_t w=0; w<walletVect.size(); w++)
      walletVect[w].cleanLedger();

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
            pair< map<OutPoint, TxIORefPair>::iterator, bool> insTxioResult;
            pair<OutPoint, TxIORefPair> newTxio(outpt, TxIORefPair(txout, &tx));
            insTxioResult = txioMap_.insert(newTxio);

            TxIORefPair & thisTxio = insTxioResult.first->second;
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
               cout << "Attempting to interpret script:" << endl;
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
               cout << "Attempting to interpret script:" << endl;
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
uint32_t BlockDataManager_FullRAM::readBlkFile_FromScratch(string filename)
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
   pair<bool,bool> blockAddResults;
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

      bool blockAddSucceeded = blockAddResults.first;
      bool blockchainReorg   = blockAddResults.second;

      if(blockAddSucceeded)
         nBlkRead++;

      if( blockchainReorg)
      {
          //TODO:  checkwhether there was a 
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
// Pass in a BRR that starts at the beginning of the blockdata (before magic
// bytes) THAT IS ALREADY AT IT'S PERMANENT LOCATION IN MEMORY
bool BlockDataManager_FullRAM::parseNewBlockData(BinaryRefReader & brr,
                                                 uint64_t & currBlockchainSize)
{
   if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
      return false;

   brr.advance(4); // magic bytes
   uint32_t nBytes = brr.get_uint32_t();

   // For some reason, my blockfile sometimes has some extra bytes
   // If failed we return prevTopBlockStillValid==true;
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
   uint32_t nTx = (uint32_t)brr.get_var_int();
   bhptr->blockNumBytes_ = nBytes;
   bhptr->blkByteLoc_    = currBlockchainSize;

   // Read each of the Tx
   bhptr->txPtrList_.clear();
   for(uint32_t i=0; i<nTx; i++)
   {
      uint64_t txStartByte = brr.getPosition();
      txInputPair.second.unserialize(brr);
      txInputPair.first = txInputPair.second.getThisHash();
      txInsResult = txHashMap_.insert(txInputPair);
      TxRef * txptr = &(txInsResult.first->second);

      // Add a pointer to this tx to the header's tx-ptr-list
      bhptr->txPtrList_.push_back( txptr );

      txptr->setTxStartByte(txStartByte+currBlockchainSize);
      // We don't set this tx's headerPtr because we're not sure
      // yet that this block is on the main chain ... if there was
      // a reorg, this tx could end up being referenced by multiple
      // headers

   }
   currBlockchainSize += nBytes+8;
   return true;
}
   


////////////////////////////////////////////////////////////////////////////////
// This method returns two booleans:
//    (1)  Block data was added to memory pool successfully
//    (2)  Adding block data caused blockchain reorganization
//
// This method assumes the data is not in the permanent memory pool yet, and
// we will need to copy it to its permanent memory location before parsing it.
pair<bool,bool> BlockDataManager_FullRAM::addNewBlockData(BinaryData rawBlock,
                                                          bool writeToBlk0001)
{
   blockchainData_NEW_.push_back(rawBlock);
   list<BinaryData>::iterator listEnd = blockchainData_NEW_.end();
   listEnd--;
   BinaryRefReader newBRR( listEnd->getPtr(), rawBlock.getSize() );
   bool didSucceed = parseNewBlockData(newBRR, totalBlockchainBytes_);

   if( ! didSucceed ) 
   {
      cout << "Adding new block data to memory pool failed!";
      return pair<bool, bool>(false, false);
   }

   // Finally, let's re-assess the state of the blockchain with the new data
   // Check the lastBlockWasReorg_ variable to see if there was a reorg
   PDEBUG("New block!  Re-assess blockchain state after adding new data...");
   bool prevTopBlockStillValid = organizeChain(); 

   // If there was a reorganization, we're going to have to do a bit of work
   // to make sure everything is updated properly
   // 
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
      reassessTxValidityOnReorg(prevTopBlockPtr_,
                                topBlockPtr_, 
                                reorgBranchPoint_);
      // TODO:  It might also be necessary to look at the specific
      //        block headers that were invalidated, to make sure 
      //        we aren't using stale data somewhere that copied it
   }

   // Write this block to file if is on the main chain and we requested it
   BinaryData newHeadHash = BtcUtils::getHash256(rawBlock.getSliceRef(8,80));
   if(getHeaderByHash(newHeadHash)->isMainBranch() && writeToBlk0001)
   {
      ofstream fileAppend(blkfilePath_.c_str(), ios::app | ios::binary);
      fileAppend.write((char const *)(rawBlock.getPtr()), rawBlock.getSize());
      fileAppend.close();
   }

   // Block data was successfully added, and there might've been a reorg
   return pair<bool, bool>(true, !prevTopBlockStillValid);
}

////////////////////////////////////////////////////////////////////////////////
// This method returns two booleans:
//    (1)  Block data was added to memory pool successfully
//    (2)  Adding block data caused blockchain reorganization
pair<bool,bool> BlockDataManager_FullRAM::addNewBlockDataRef( BinaryDataRef bdr,
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
void BlockDataManager_FullRAM::reassessTxValidityOnReorg(
                                              BlockHeaderRef* oldTopPtr,
                                              BlockHeaderRef* newTopPtr,
                                              BlockHeaderRef* branchPtr)
{
   PDEBUG("Reassessing Tx validity after (after reorg?)");
   // Walk down invalidated chain first, until we get to the branch point
   // Mark transactions as invalid
   txJustInvalidated_.clear();
   txJustAffected_.clear();
   BlockHeaderRef* thisHeaderPtr = oldTopPtr;
   while(oldTopPtr != branchPtr)
   {
      
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef * txptr = thisHeaderPtr->getTxRefPtrList()[i];
         txptr->setHeaderPtr(NULL);
         txptr->setMainBranch(false);
         txJustInvalidated_.insert(txptr->getThisHash());
         txJustAffected_.insert(txptr->getThisHash());
      }
      thisHeaderPtr = getHeaderByHash(oldTopPtr->getPrevHash());
   }

   // Walk down the newly-valid chain and mark transactions as valid.  If 
   // a tx is in both chains, it will still be valid after this process
   thisHeaderPtr = newTopPtr;
   while(newTopPtr != branchPtr)
   {
      for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      {
         TxRef * txptr = thisHeaderPtr->getTxRefPtrList()[i];
         txptr->setHeaderPtr(thisHeaderPtr);
         txptr->setMainBranch(true);
         txJustInvalidated_.erase(txptr->getThisHash());
         txJustAffected_.insert(txptr->getThisHash());
      }
      thisHeaderPtr = getHeaderByHash(oldTopPtr->getPrevHash());
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
         iter->second.difficultySum_ = -1;
         iter->second.blockHeight_   =  0;
         iter->second.isFinishedCalc_ = false;
      }
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
   genBlock.txPtrList_[0]->setHeaderPtr(&genBlock);


   // If this is the first run, the topBlock is the genesis block
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   // Store the old top block so we can later check whether it is included 
   // in the new chain organization
   BlockHeaderRef* prevTopBlockPtr_ = topBlockPtr_;

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
      organizeChain(true); // force-rebuild blockchain (takes less than 1s)
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
         previouslyValidBlockHeaderRefs_.push_back(&(iter->second));
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


int64_t BlockDataManager_FullRAM::getSentValue(TxInRef & txin)
{
   if(txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}


