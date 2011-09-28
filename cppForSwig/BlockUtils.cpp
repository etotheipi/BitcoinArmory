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
BinaryDataRef TxIORefPair::getTxHashOfOutput(void)
{
   if(txoutTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txoutTxRefPtr_->getThisHashRef();
}

//////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxIORefPair::getTxHashOfInput(void)
{
   if(txinTxRefPtr_ == NULL)
      return BtcUtils::EmptyHash_;
   else
      return txinTxRefPtr_->getThisHashRef();
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

      // Ignore if addr was created at one week or 1000 blocks after this tx
      if( thisAddr.getFirstTimestamp() > blktime + (3600*24*7) ||
          thisAddr.getFirstBlockNum()  > blknum  +  1000          )
         continue;  

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
            }
         }
         else
         {
            // Lots of txins that we won't have, this is a normal conditional
            //cout << "***WARNING: found a relevant TxIn but not seen TxOut" << endl;
            //cerr << "***WARNING: found a relevant TxIn but not seen TxOut" << endl;
            //txioMap_[outpt].setTxInRef(txin, &tx);
            //orphanTxIns_.insert(outpt);
         }
      } // loop over TxIns
      if(txInIsOurs)
         ledgerAllAddr_.push_back(LedgerEntry(addr20, 
                                             -(int64_t)valueIn, 
                                              blknum, 
                                              tx.getThisHash(), 
                                              txIndex));

      ///// LOOP OVER ALL TXOUT IN BLOCK /////
      uint64_t valueOut = 0;
      bool txOutIsOurs = false;
      for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
      {
         TxOutRef txout = tx.getTxOutRef(iout);
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
               if(thisAddr.getFirstBlockNum() == 0)
               {
                  thisAddr.setFirstBlockNum( blknum );
                  thisAddr.setFirstTimestamp( blktime );
               }
            }
            else
            {
               //cout << "***WARNING: searchTx: new TxOut already exists!" << endl;
               //cerr << "***WARNING: searchTx: new TxOut already exists!" << endl;
            }

         }
      } // loop over TxOuts
      if(txOutIsOurs)
         ledgerAllAddr_.push_back(LedgerEntry( addr20, 
                                               valueOut, 
                                               blknum, 
                                               tx.getThisHash(), 
                                               txIndex));

   } // loop over all wallet addresses

   if(txIsOurs)
      txrefList_.push_back(&tx);
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
      blockchainData_NEW_(0),
      isAllAddrLoaded_(false),
      topBlockPtr_(NULL),
      genBlockPtr_(NULL)
{
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
   blockchainData_ALL_.clear();
   blockchainData_NEW_.clear();

   headerHashMap_.clear();
   txHashMap_.clear();
   headersByHeight_.clear();
   txFileRefs_.clear();
   headerFileRefs_.clear();
   blockchainFilenames_.clear();
   previouslyValidBlockHeaderRefs_.clear();
   orphanChainStartBlocks_.clear();
   isAllAddrLoaded_ = false;
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
vector<BinaryData> BlockDataManager_FullRAM::prefixSearchHeaders(BinaryData const & searchStr)
{
   vector<BinaryData> outList(0);
   map<HashString, BlockHeaderRef>::iterator iter;
   for(iter  = headerHashMap_.begin();
       iter != headerHashMap_.end();
       iter++)
   {
      if(iter->first.startsWith(searchStr))
         outList.push_back(iter->first);
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockDataManager_FullRAM::prefixSearchTx(BinaryData const & searchStr)
{
   vector<BinaryData> outList(0);
   map<HashString, TxRef>::iterator iter;
   for(iter  = txHashMap_.begin();
       iter != txHashMap_.end();
       iter++)
   {
      if(iter->first.startsWith(searchStr))
         outList.push_back(iter->first); 
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockDataManager_FullRAM::prefixSearchAddress(BinaryData const & searchStr)
{
   return vector<BinaryData>(0);
}


/////////////////////////////////////////////////////////////////////////////
// This is an intense search, using every tool we've created so far!
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch(BtcWallet & myWallet)
{
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
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_FullRAM::scanBlockchainForTx_FromScratch(vector<BtcWallet> & walletVect)
{
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
               txVectOut.push_back(&tx);
         }

         ///// LOOP OVER ALL TXOUT IN BLOCK /////
         for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
         {
            
            TxOutRef txout = tx.getTxOutRef(iout);
            if(txout.getScriptType() == TXOUT_SCRIPT_UNKNOWN)
               txVectOut.push_back(&tx);               

         }
      }
   }

   return txVectOut;
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_FullRAM::readBlkFile_FromScratch(string filename)
{
   cout << "Reading block data from file: " << filename.c_str() << endl;
   ifstream is(filename.c_str(), ios::in | ios::binary);
   is.seekg(0, ios::end);
   size_t filesize = (size_t)is.tellg();
   is.seekg(0, ios::beg);
   cout << filename.c_str() << " is " << filesize/(float)(1024*1024) << " MB" << endl;

   //////////////////////////////////////////////////////////////////////////
   TIMER_START("ReadBlockchainIntoRAM");
   blockchainData_ALL_.resize(filesize);
   uint8_t* front = blockchainData_ALL_.getPtr();
   is.read((char*)front, filesize);
   is.close();
   TIMER_STOP("ReadBlockchainIntoRAM");
   //////////////////////////////////////////////////////////////////////////

   // Going ot use the following four objects for efficient insertions
   pair<HashString, TxRef>  txInputPair;
   pair<HashString, BlockHeaderRef>  bhInputPair;
   pair<map<HashString, TxRef>::iterator, bool>          txInsResult;
   pair<map<HashString, BlockHeaderRef>::iterator, bool> bhInsResult;

   cout << "Scanning all block data currently in RAM" << endl;
   TIMER_START("ScanBlockchainInRAM");
   BinaryRefReader brr(blockchainData_ALL_);
   uint32_t nBlkRead = 0;
   while(!brr.isEndOfStream())
   {
      brr.advance(4); // magic bytes
      uint32_t nBytes = brr.get_uint32_t();
      uint64_t fileByteLoc = brr.getPosition();

      // For some reason, my blockfile sometimes has some extra bytes
      if(brr.isEndOfStream() || brr.getSizeRemaining() < nBytes)
         break;

      bhInputPair.second.unserialize(brr);
      bhInputPair.first = bhInputPair.second.thisHash_;


      bhInsResult = headerHashMap_.insert(bhInputPair);
      BlockHeaderRef * bhptr = &(bhInsResult.first->second);

      uint32_t nTx = (uint32_t)brr.get_var_int();
      bhptr->numTx_ = nTx;
      bhptr->blockNumBytes_ = nBytes;
      bhptr->fileByteLoc_ = fileByteLoc;
      bhptr->txPtrList_.clear();

      for(uint64_t i=0; i<nTx; i++)
      {
         txInputPair.second.unserialize(brr);
         txInputPair.first = txInputPair.second.thisHash_;
         txInsResult = txHashMap_.insert(txInputPair);
         TxRef * txptr = &(txInsResult.first->second);

         txptr->headerPtr_ = bhptr;
         bhptr->txPtrList_.push_back( txptr );
      }
      nBlkRead++;
   }
   TIMER_STOP("ScanBlockchainInRAM");
   return nBlkRead;

}


bool BlockDataManager_FullRAM::verifyBlkFileIntegrity(void)
{
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
         cout << "    " << bhr.getThisHash().copySwapEndian().toHexString() << endl;
         cout << "  Num Tx :         " << bhr.getNumTx() << endl;
         cout << "  Tx Hash List: (compare to raw tx data on blockexplorer)" << endl;
         for(uint32_t t=0; t<bhr.getNumTx(); t++)
            cout << "    " << bhr.getTxRefPtrList()[t]->getThisHash().copySwapEndian().toHexString() << endl;
      }
      isGood = isGood && thisHeaderIsGood;
   }
   return isGood;
}


/////////////////////////////////////////////////////////////////////////////
// Not sure exactly when this would get used...
void BlockDataManager_FullRAM::addHeader(BinaryData const & binHeader)
{
   BinaryData theHash(32); 
   BtcUtils::getHash256(binHeader, theHash);
   headerHashMap_[theHash] = BlockHeaderRef(binHeader);
}



// This returns false if our new main branch does not include the previous
// topBlock.  If this returns false, that probably means that we have
// previously considered some blocks to be valid that no longer are valid.
//
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
bool BlockDataManager_FullRAM::organizeChain(bool forceRebuild)
{
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

   BinaryData const & GenesisHash_ = BtcUtils::GenesisHash_;
   BinaryData const & EmptyHash_   = BtcUtils::EmptyHash_;
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   // Store the old top block so we can later check whether it is included 
   // in the new chain organization
   BlockHeaderRef* prevTopBlockPtr = topBlockPtr_;

   // Iterate over all blocks, track the maximum difficulty-sum block
   map<BinaryData, BlockHeaderRef>::iterator iter;
   uint32_t maxBlockHeight = 0;
   double   maxDiffSum = 0;
   uint32_t niter =0;
   for( iter = headerHashMap_.begin(); iter != headerHashMap_.end(); iter ++)
   {
      niter++;
      // *** The magic happens here
      double thisDiffSum = traceChainDown(iter->second);
      // ***
      
      if(thisDiffSum > maxDiffSum)
      {
         maxDiffSum     = thisDiffSum;
         topBlockPtr_   = &(iter->second);
      }
   }

   // Walk down the list one more time, set nextHash fields
   // Also set headersByHeight_;
   topBlockPtr_->nextHash_ = EmptyHash_;
   BlockHeaderRef* thisBlockPtr = topBlockPtr_;
   bool prevChainStillValid = (thisBlockPtr == prevTopBlockPtr);
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisBlockPtr->isFinishedCalc_ )
   {
      thisBlockPtr->isFinishedCalc_ = true;
      thisBlockPtr->isMainBranch_   = true;
      thisBlockPtr->isOrphan_       = false;
      headersByHeight_[thisBlockPtr->getBlockHeight()] = thisBlockPtr;

      BinaryData & childHash        = thisBlockPtr->thisHash_;
      thisBlockPtr                  = &(headerHashMap_[thisBlockPtr->getPrevHash()]);
      thisBlockPtr->nextHash_       = childHash;

      if(thisBlockPtr == prevTopBlockPtr)
         prevChainStillValid = true;
   }
   // Last block in the while loop didn't get added (usually genesis block)
   thisBlockPtr->isMainBranch_   = true;
   headersByHeight_[thisBlockPtr->getBlockHeight()] = thisBlockPtr;

   // Not sure if this should be automatic... for now I don't think it hurts
   if( !prevChainStillValid )
   {
      organizeChain(true); // force-rebuild the blockchain
      return false;
   }

   return prevChainStillValid;
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
   vector<double>          difficultyStack(headerHashMap_.size());
   vector<BlockHeaderRef*>     bhpPtrStack(headerHashMap_.size());
   uint32_t blkIdx = 0;
   double thisDiff;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   BlockHeaderRef* thisPtr = &bhpStart;
   map<BinaryData, BlockHeaderRef>::iterator iter;
   while( thisPtr->difficultySum_ < 0)
   {
      thisDiff = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      bhpPtrStack[blkIdx]     = thisPtr;
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
      thisPtr                 = bhpPtrStack[i];
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
   bhpStart.isOrphan_ = true;
   bhpStart.isMainBranch_ = false;
   map<BinaryData, BlockHeaderRef>::iterator iter;
   iter = headerHashMap_.find(bhpStart.getPrevHash());
   HashStringRef lastHeadHash(32);
   // TODO: I believe here we can check whether the block was previously
   //       marked isMainBranch_ and if so, we can add it to a "previously-
   //       but-no-longer-valid" block list.  This allows us to flag txs
   //       that might have been included in the wallet, but should be removed.
   while( iter != headerHashMap_.end() )
   {
      if(iter->second.isMainBranch_ == true)
         previouslyValidBlockHeaderRefs_.push_back(&(iter->second));
      iter->second.isOrphan_ = true;
      iter->second.isMainBranch_ = false;
      lastHeadHash.setRef(iter->second.thisHash_);
      iter = headerHashMap_.find(iter->second.getPrevHash());
   }
   orphanChainStartBlocks_.push_back(&(headerHashMap_[lastHeadHash.copy()]));
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


