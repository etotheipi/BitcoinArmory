#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <stdio.h>
#include <iostream>
#ifdef WIN32
   #include <cstdint>
#else
   #include <stdlib.h>
   #include <inttypes.h>
   #include <cstring>
#endif
#include <fstream>
#include <vector>
#include <queue>
#include <deque>
#include <list>
#include <map>
#include <set>
#include <limits>

#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "BlockObjRef.h"

#include "cryptlib.h"
#include "sha.h"
#include "UniversalTimer.h"



#define TX_0_UNCONFIRMED    0 
#define TX_NOT_EXIST       -1
#define TX_OFF_MAIN_BRANCH -2


using namespace std;






////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
/* This class is a solution for a problem I don't have -- commented out for now
class BlockRef
{
   BlockRef(void) :
      headRef_(NULL),
      txList_(0)
   {
      // Nothing to put here
   }

   void setHeadRefPtr(BlockHeaderRef* bhr) {headRef_ = bhr;}
   void addTxRefPtr(TxRef* txr)            { txList_.push_back(txr); }
 
   uint32_t getNumTx(void)            { return (uint32_t)(txList_.size()); }
   void     setNumTx(uint32_t sz)     { txList_.resize(sz); }
   TxRef*   getTxRefPtr(uint32_t i)   { return (i<getNumTx() ? txList_[i] : NULL); }
   BlockHeaderRef* getHeaderRef(void) { return headRef_; }

private:
   BlockHeaderRef*  headRef_;
   vector<TxRef*>   txList_;

};
*/


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// START FILE-REF CLASSES
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

class BlockHeaderFileRef
{
public:
   BlockHeaderFileRef(BinaryData hash, uint64_t fileLoc, uint32_t fileIdx=0) : 
      theHash_(hash),
      fileLoc_(fileLoc),
      fileIndex_(fileIdx) {}


   BinaryData theHash_;
   uint32_t fileIndex_;
   uint64_t fileLoc_;
};

class TxFileRef
{
public:
   TxFileRef(BinaryData hash, uint64_t fileLoc, uint32_t fileIdx=0) : 
      theHash_(hash),
      fileLoc_(fileLoc),
      fileIndex_(fileIdx) {}


   BinaryData theHash_;
   uint32_t fileIndex_;
   uint64_t fileLoc_;
};



////////////////////////////////////////////////////////////////////////////////
// TxIORefPtrPair
//
// There's no point in separating these two objects.  For every TxOut, there 
// will be a TxIn, and they both have the same value.  So we can track ptrs to
// each one, and easily determine, based on which pointers are NULL, whether
// the money is unspent.  
//
class TxIORefPtrPair
{
public:
   TxIORefPtrPair(TxOutRef* outref=NULL, TxInRef* inref=NULL) : 
          txoutrefptr_(outref), 
          txinrefptr_(inref),
          amount_(UINT64_MAX) { }

   bool      hasTxOut(void)       { return (txoutrefptr_!=NULL); }
   bool      hasTxIn(void)        { return (txinrefptr_!=NULL); }
   bool      hasValue(void)       { return (amount_!=UINT64_MAX); }
   uint64_t  getValue(void)       { return amount_;}
   TxOutRef* getTxOutRefPtr(void) { return txoutrefptr_; }
   TxInRef*  getTxInRefPtr(void)  { return txinrefptr_; }

   // UNSAFE:  check hasTxOut/hasTxIn first!
   TxOutRef  getTxOutRef(void)    { return *txoutrefptr_; }
   TxInRef   getTxInRef(void)     { return *txinrefptr_; }
   TxOut     getTxOut(void)       { return txoutrefptr_->getCopy(); }
   TxIn      getTxIn(void)        { return txinrefptr_->getCopy(); }

   void setTxInRefPtr (TxInRef*  inrefptr ) { txinrefptr_  = inrefptr; }
   void setTxOutRefPtr(TxOutRef* outrefptr) 
   {
      txoutrefptr_ = outrefptr; 
      if(hasTxOut())
         amount_ = txoutrefptr_->getValue();
   }

   bool isUnspent(void)       { return (  hasTxOut() && !hasTxIn() ); }
   bool isSpent(void)         { return (  hasTxOut() &&  hasTxIn() ); }
   bool isSourceUnknown(void) { return ( !hasTxOut() &&  hasTxIn() ); }
   bool isStandardTxOutScript(void) 
   { 
      if(hasTxOut()) 
         return txoutrefptr_->isStandard();
      return false;
   }

private:
   TxOutRef* txoutrefptr_;
   TxInRef*  txinrefptr_;
   uint64_t  amount_;

};


// I think this falls under the umbrella of premature optimization...
// Will work on this later if it seems necessary
/*
// Want to reduce access times by only searching for first 4 of 32 bytes,
// but need to handle multiple objects that may be found.  
template<typename KEYTYPE, typename VALUETYPE>
class mmapWrapper
{
private:
   multimap<BinaryData, VALUETYPE> mmap_;
  
public:
   mmapWrapper(void) { mmap_.clear(); }

   VALUETYPE & find(KEYTYPE fullKey)
   {
      BinaryData bd = fullKey.getSliceCopy(0,4);
      if(mmap_.count(bd) == 1)
         return 
   }

};
*/

typedef enum
{
   TXIO_UNSPENT,
   TXIO_SPENT,
}  TXIO_STATUS;

class BtcAddress
{
public:
   BtcAddress(void) :
      address20_(0),
      pubkey65_(0),
      privkey32_(0),
      createdBlockNum_(UINT32_MAX),
      createdTimestamp_(UINT32_MAX)
   {
      // Nothing to do here
   }

   BinaryData address20_;
   BinaryData pubkey65_;
   BinaryData privkey32_;
   uint32_t createdBlockNum_;
   uint32_t createdTimestamp_;

   // The second arg is for whether the money is in (+), out (-), or both (0)
   vector< pair<TxIORefPtrPair*, int> > txioList_;
};


// Some might argue that inheritance would be useful here.  I'm not a software
// guy, and I have to write all the methods for each class anyway.  So I'm 
// foregoing the inheritance.  Just writing each class separately

// FullRAM BDM:
//    Very few use cases, and will be nearly impossible if transaction volume
//    picks up at all.  However, if you need to do TONS of computation on the
//    blockchain very quickly, and you have the RAM, this may be useful for you
//    Headers and BlockData/Tx stored in the same structure
class BlockDataManager_FullRAM;

// FullHDD BDM:
//    This is the standard full-blockchain node.  It pulls all the blockdata
//    into memory only to scan it and index it.  After that, it stores byte
//    locations of the block chain, and reads the data from file on demand.
//    Headers and BlockData/Tx stored in the same structure
class BlockDataManager_FullHDD;

// Medium BDM:
//    No storage of the blockchain, only the headers and TxOut/TxIn lists 
//    are stored in memory and blocks data is pulled from the network as needed
//    Headers are stored in their own compact structure
class BlockDataManager_Medium;

// Connection BDM:
//    Basically a proxy to a BDM on another system to be accessed via sockets
//    This may not actually be needed, as it would probably be easier to 
//    implement in python
class BlockDataManager_ServerConnection;


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// The goal of this class is to create a memory pool in RAM that looks exactly
// the same as the block-headers storage on disk.  There is no serialization
// or unserialization, we just copy back and forth between disk and RAM, and 
// we're done.  So it should be about as fast as theoretically possible, you 
// are limited only by your disk I/O speed.
//
// This is more of a simple test, which will later be applied to the entire
// blockchain.  If it works as expected, then this will potentially be useful
// for the official BTC client which seems to have some speed problems at 
// startup and shutdown.
//
// This class is a singleton -- there can only ever be one, accessed through
// the static method GetInstance().  This method gets the single instantiation
// of the BDM class, and then its public members can be used to access the 
// block data that is sitting in memory.
//
typedef enum
{
   BDM_MODE_FULL_BLOCKCHAIN,
   BDM_MODE_LIGHT_STORAGE,
   BDM_MODE_NO_STORAGE,
   BDM_MODE_COUNT
}  BDM_MODE;

class BlockDataManager_FullRAM
{
private:


   // This binary string and two maps hold EVERYTHING.  All other objects are
   // just informational relationships between stuff we care about and this
   // bulk block data.
   //
   // These four data structures contain all the *real* data.  Everything 
   // else is just references and pointers to this data
   BinaryData                         blockchainData_ALL_;
   BinaryData                         blockchainData_NEW_; // to be added
   map<HashString, BlockHeaderRef>    headerHashMap_;
   map<HashString, TxRef >            txHashMap_;
  
   // We will maintain all transactional information in these maps
   // Only use pointers to the refs
   map<OutPointRef, TxIORefPtrPair>   txioMap_;
   set<OutPointRef>                   myUnspentTxOuts_;
   set<HashString>                    myPendingTxs_;
   set<OutPointRef>                   myTxOutsNonStandard_;
   set<OutPointRef>                   orphanTxIns_;

   // For the case of keeping tx/header data on disk:
   vector<string>                     blockchainFilenames_;
   map<HashString, pair<int,int> >    txFileRefs_;
   map<HashString, pair<int,int> >    headerFileRefs_;


   // These should be set after the blockchain is organized
   deque<BlockHeaderRef*>               headersByHeight_;
   BlockHeaderRef*                      topBlockPtr_;
   BlockHeaderRef*                      genBlockPtr_;

   // The following two maps should be parallel
   map<BinaryData, BtcAddress>       myAccounts_;  
   uint64_t                          totalBalance_;

   vector<BlockHeaderRef*>           previouslyValidBlockHeaderRefs_;
   vector<BlockHeaderRef*>           orphanChainStartBlocks_;

   static BlockDataManager_FullRAM* theOnlyBDM_;
   static bool bdmCreatedYet_;




private:
   // Set the constructor to private so that only one can ever be created
   BlockDataManager_FullRAM(void) : 
         blockchainData_ALL_(0),
         blockchainData_NEW_(0),
         topBlockPtr_(NULL),
         genBlockPtr_(NULL),
         totalBalance_(0)
   {
      headerHashMap_.clear();
      txHashMap_.clear();
      txioMap_.clear();
      myAccounts_.clear();
      headersByHeight_.clear();
      myTxOutsNonStandard_.clear();
      myPendingTxs_.clear();
      blockchainFilenames_.clear();
   }

public:

   /////////////////////////////////////////////////////////////////////////////
   // The only way to "create" a BDM is with this method, which creates it
   // if one doesn't exist yet, or returns a reference to the only one
   // that will ever exist
   static BlockDataManager_FullRAM & GetInstance(void) 
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
   int32_t getNumConfirmations(BinaryData txHash)
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
            int32_t topBlockHeight = getTopBlock().blockHeight_;
            return  topBlockHeight - txBlockHeight + 1;
         }
      }
   }


   /////////////////////////////////////////////////////////////////////////////
   BlockHeaderRef & getTopBlock(void) 
   {
      if(topBlockPtr_ == NULL)
         topBlockPtr_ = &(getGenesisBlock());
      return *topBlockPtr_;
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeaderRef & getGenesisBlock(void) 
   {
      if(genBlockPtr_ == NULL)
         genBlockPtr_ = &(headerHashMap_[BtcUtils::GenesisHash_]);
      return *genBlockPtr_;
   }

   /////////////////////////////////////////////////////////////////////////////
   // Get a blockheader based on its height on the main chain
   BlockHeaderRef & getHeaderByHeight(int index)
   {
      if( index>=0 && index<(int)headersByHeight_.size())
         return *headersByHeight_[index];
   }

   /////////////////////////////////////////////////////////////////////////////
   // The most common access method is to get a block by its hash
   BlockHeaderRef * getHeaderByHash(BinaryData const & blkHash)
   {
      map<BinaryData, BlockHeaderRef>::iterator it = headerHashMap_.find(blkHash);
      if(it==headerHashMap_.end())
         return NULL;
      else
         return &(it->second);
   }

   /////////////////////////////////////////////////////////////////////////////
   // We may add accounts to our address book just for watching purposes.  Hence
   // why you may not have the pub/priv keypair
   void addAccount(BinaryData const * addr, 
                   BinaryData const * pubKey65=NULL,
                   BinaryData const * privKey32=NULL)
   {
      BtcAddress & myAddr = myAccounts_[*addr];
      myAddr.address20_.copyFrom(*addr);
      if(pubKey65 != NULL)
         myAddr.pubkey65_.copyFrom(*pubKey65);
      if(privKey32 != NULL)
         myAddr.privkey32_.copyFrom(*privKey32);
   }

   /////////////////////////////////////////////////////////////////////////////
   //void updateTxIOList(vector<TxRef*> & blkTxList,
                       //vector<BtcAddress> const & accountList)
   //{
      // TODO:  WOW this is a subtle, major problem:
      //              TxIns that are either coinbase TxIn or spending a
      //              coinbase TxIn do not identify the owner -- you have
      //              to look at the corresponding TxOut in order to know
      //              who's spending signing the TxIn.  This means, that 
      //              we cannot identify whether we need to save a TxIn 
      //              until we've seen the corresponding TxOut, but we 
      //              haven't read all the TxOuts yet. 
      //
      //              We will have to do a batch scan after all Tx are
      //              read in, starting with all the TxOuts.  Only after
      //              we have identified all our TxOuts will we be able 
      //              to know whether a given TxIn is ours.  
      //
      //              The exception is if all Tx are in "order" and thus
      //              we would never see a TxIn without having seen its 
      //              TxOut yet, but I can envision circumstances where
      //              this assumption may not be true.
      //
      // It seems, as long as we read in whole blocks at a time, and 
      // the block heights are monotonically increasing, there should be
      // no problem.  So we need to operate on vector<TxRef*> representing
      // full blocks/merkletrees.

      //uint32_t nin  = txref.getNumTxIn();
      //uint32_t nout = txref.getNumTxOut();
      //for(int i=0; i<nin; i++)
      //{
         //TxInRef = txref.getTxInRef(i);
        //
      //}
   //}

   /////////////////////////////////////////////////////////////////////////////
   /*
   void flagTransactions(vector<BinaryData> const & accountList)
   {
      if(accountList.size() == 0)
         return;

      map<HashString, TxRef     >::const_iterator  txIter;
      map<BinaryData, BtcAddress>::const_iterator  addrIter;

     
      TIMER_START("ScanTxOuts");
      // We need to accumulate all TxOuts first
      for( txIter  = txHashMap_.begin();
           txIter != txHashMap_.end();
           txIter++)
      {
         TxRef const & thisTx = txIter->second;
         for( addrIter  = accountList.begin();
              addrIter != accountList.end();
              addrIter++)
         {
            for(uint32_t i=0; i<thisTx.getNumTxOut(); i++)
            {
               TxOutRef const & txout = thisTx.getTxOutRef(i);
               if( txout.getRecipientAddr() == addrIter->first)
               {
                  OutPoint op;
                  op.setTxHash(thisTx.thisHash_);
                  op.setTxOutIndex(i);

                  // Already processed this one, before
                  if( !txout.isMine_ )
                     continue;

                  if( !thisTx.txOutList_[i].isStandard() )
                  {
                     cout << "Non-standard script! "  << endl;
                     cout << "\tTx:       " << thisTx.thisHash_.toHex().c_str() << endl;
                     cout << "\tOutIndex: " << i << endl;
                     myTxOutsNonStandard_[op] = &(thisTx.txOutList_[i]);
                  }
                  else
                  {
                     // We use a map indexed by OutPoint so we can easily iterate
                     // OR find a record to delete it easily from the TxIn record
                     TxOut & txout = thisTx.txOutList_[i];
                     txout.isMine_ = true;
                     txout.isSpent_ = false;
                     myTxOuts_[op]        = &txout;
                     myUnspentTxOuts_[op] = &txout;
                     myBalance_ += txout.value_;
                  }
                  
               }
            }
         }
      }
      TIMER_STOP("ScanTxOuts");

      TIMER_START("ScanTxIns");
      // Next we find all the TxIns and delete TxOuts
      for( txIter  = txHashMap_.begin();
           txIter != txHashMap_.end();
           txIter++)
      {
         Tx const & thisTx = txIter->second;
         for( addrIter  = accountList.begin();
              addrIter != accountList.end();
              addrIter++)
         {
            for(uint32_t i=0; i<thisTx.getNumTxIn(); i++)
            {
               // can start searching for pub key 64 bytes into binScript
               if( thisTx.txInList_[i].binScript_.contains(addrIter->second, 64))
               {
                  OutPoint const & op = thisTx.txInList_[i].outPoint_;
                  TxIn  & txin  = thisTx.txInList_[i];
                  TxOut & txout = thisTx.txOutList_[op.txOutIndex_];
                  myTxIns_[op] = &(txin);
                  myTxOuts_[op]->isSpent_ = true;
                  myUnspentTxOuts_.erase(op);
                  myBalance_ += txout.value_;
               }
            }
         }
      }
      TIMER_STOP("ScanTxIns");

      cout << "Completed full scan of TxOuts (" << TIMER_READ_SEC("ScanTxOuts")
           << " sec) and TxIns (" << TIMER_READ_SEC("ScanTxIns") << " sec)" << endl;
      
      cout << "TxOuts: " << endl;
      map<OutPoint, TxOut*>::iterator outIter;
      for( outIter  = myTxOuts_.begin();
           outIter != myTxOuts_.begin();
           outIter++)
      {
         OutPoint const & outpt = outIter->first;
         TxOut    & txout = *(outIter->second);
         cout << "\t" << outpt.txHash_.toHex().c_str();
         cout << "(" << outpt.txOutIndex_ << ")";
         if(txout.isSpent_)
            cout << "\t(SPENT)";
         cout << endl;
      }

      cout << "TxIns: " << endl;
      map<OutPoint, TxIn*>::iterator inIter;
      for( inIter  = myTxIns_.begin();
           inIter != myTxIns_.begin();
           inIter++)
      {
         OutPoint const & outpt = inIter->first;
         TxIn     & txin  = *(inIter->second);
         cout << "\t" << outpt.txHash_.toHex().c_str();
         cout << "(" << outpt.txOutIndex_ << ")";
         cout << endl;
      }
   }
   */

   // I'm disabling this method, because reading the headers from the 
   // blockchain file is really no slower than reading them from a dedicated
   // header file
   //
   /////////////////////////////////////////////////////////////////////////////
   // Add headers from a file that is serialized identically to the way
   // we have laid it out in memory.  Return the number of bytes read
   /*
   uint64_t importHeadersFromHeaderFile(std::string filename)
   {
      cout << "Reading block headers from file: " << filename.c_str() << endl;
      ifstream is(filename.c_str(), ios::in | ios::binary);
      is.seekg(0, ios::end);
      size_t filesize = (size_t)is.tellg();
      is.seekg(0, ios::beg);
      cout << filename.c_str() << " is " << filesize << " bytes" << endl;
      if((unsigned int)filesize % HEADER_SIZE != 0)
      {
         cout << "filesize=" << filesize << " is not a multiple of header size!" << endl;
         return -1;
      }

      //////////////////////////////////////////////////////////////////////////
      BinaryData allHeaders(filesize);
      uint8_t* front = allHeaders.getPtr();
      is.read((char*)front, filesize);
      //////////////////////////////////////////////////////////////////////////
      
      BinaryData thisHash(32);
      for(int offset=0; offset<(int)filesize; offset+=HEADER_SIZE)
      {
         uint8_t* thisPtr = front + offset;
         BtcUtils::getHash256(thisPtr, HEADER_SIZE, thisHash);
         headerHashMap_[thisHash] = BlockHeader(thisPtr, &thisHash);
      }
      cout << "Done with everything!  " << filesize << " bytes read!" << endl;
      return filesize;      
   }
   */




   /////////////////////////////////////////////////////////////////////////////
   uint32_t readBlockchainFromBlkFile_FullRAM_FromScratch(string filename)
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

         bhInputPair.second.unserialize(brr);
         bhInputPair.first = bhInputPair.second.thisHash_;
         bhInsResult = headerHashMap_.insert(bhInputPair);
         BlockHeaderRef * bhptr = &(bhInsResult.first->second);

         uint32_t nTx = (uint32_t)brr.get_var_int();
         bhptr->numTx_ = nTx;
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

         //updateTxIOList(bhptr->txPtrList_);

         //brr.getSizeRemaining(); 
         nBlkRead++;
      }
      TIMER_STOP("ScanBlockchainInRAM");
      return nBlkRead;

   }

   uint32_t readBlockchainFromBlkFile_FullRAM_UseBlkIndex(string blkfn,
                                                          string idxfn)
   {

   }

   uint32_t readIndexFile(string indexfn)
   {

   }

   void writeBlkIndexFile_Full(std::string filename)
   {

   }

   /*
   /////////////////////////////////////////////////////////////////////////////
   uint32_t importFromBlockFile(std::string filename, bool justHeaders=false)
   {
      // TODO: My original everythingRef solution for headers would save a LOT
      //       of computation here.  At 140k blocks, with 1.1 million Tx's:
      //
      //          txSerial copy:       19s
      //          binaryReader copy:   20s
      //          tx.unserialize:      45s
      //          txMap_[hash] = tx:  115s
      //          &(txMap_[hash]):      0.61s
      //
      //       In other words, we spend a shitload of time copying data around.
      //       If we switch to copying all data once from file, and then only
      //       copy pointers around, we should be in fantastic shape!
      //         
      BinaryStreamBuffer bsb(filename, 25*1024*1024);  // use 25 MB buffer
      
      bool readMagic  = false;
      bool readVarInt = false;
      bool readHeader = false;
      bool readTx     = false;
      uint32_t numBlockBytes;

      BinaryData magicBucket(4);
      BinaryData magicStr(4);
      magicStr.createFromHex(MAGICBYTES);
      BinaryData headHash(32);
      BinaryData headerStr(HEADER_SIZE);

      Tx tempTx;
      BlockHeader tempBH;


      int nBlocksRead = 0;
      // While there is still data left in the stream (file), pull it
      while(bsb.streamPull())
      {
         // Data has been pulled into the buffer, process all of it
         while(bsb.getBufferSizeRemaining() > 1)
         {
            static int i = 0;
            if( !readMagic )
            {
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               bsb.reader().get_BinaryData(magicBucket, 4);
               if( !(magicBucket == magicStr) )
               {
                  //cerr << "Magic string does not match network!" << endl;
                  //cerr << "\tExpected: " << MAGICBYTES << endl;
                  //cerr << "\tReceived: " << magicBucket.toHex() << endl;
                  break;
               }
               readMagic = true;
            }

            // If we haven't read the blockdata-size yet, do it
            if( !readVarInt )
            {
               // TODO:  Whoops, this isn't a VAR_INT, just a 4-byte num
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               numBlockBytes = bsb.reader().get_uint32_t();
               readVarInt = true;
            }


            // If we haven't read the header yet, do it
            uint64_t blkByteOffset = bsb.getFileByteLocation();
            if( !readHeader )
            {
               if(bsb.getBufferSizeRemaining() < HEADER_SIZE)
                  break;

               TIMER_WRAP(bsb.reader().get_BinaryData(headerStr, HEADER_SIZE));

               BtcUtils::getHash256(headerStr, headHash);
               TIMER_WRAP(tempBH = BlockHeader(&headerStr, &headHash, blkByteOffset+HEADER_SIZE));
               TIMER_WRAP(headerHashMap_[headHash] = tempBH);

               //cout << headHash.toHex().c_str() << endl;
               readHeader = true;
            }

            uint32_t txListBytes = numBlockBytes - HEADER_SIZE;
            BlockHeader & blkHead = headerHashMap_[headHash];
            if( !readTx )
            {
               if(bsb.getBufferSizeRemaining() < txListBytes)
                  break;

               if(justHeaders)
                  bsb.reader().advance((uint32_t)txListBytes);
               else
               {
                  uint8_t varIntSz;
                  TIMER_WRAP(blkHead.numTx_ = (uint32_t)bsb.reader().get_var_int(&varIntSz));
                  blkHead.txPtrList_.resize(blkHead.numTx_);
                  txListBytes -= varIntSz;
                  BinaryData allTx(txListBytes);
                  TIMER_WRAP(bsb.reader().get_BinaryData(allTx.getPtr(), txListBytes));
                  TIMER_WRAP(BinaryReader txListReader(allTx));
                  for(uint32_t i=0; i<blkHead.numTx_; i++)
                  {

                     uint32_t readerStartPos = txListReader.getPosition();
                     TIMER_WRAP(tempTx.unserialize(txListReader));
                     uint32_t readerEndPos = txListReader.getPosition();

                     TIMER_WRAP(BinaryData txSerial( allTx.getPtr() + readerStartPos, 
                                                     allTx.getPtr() + readerEndPos    ));
                     tempTx.nBytes_    = readerEndPos - readerStartPos;
                     tempTx.headerPtr_ = &blkHead;

                     // Calculate the hash of the Tx
                     TIMER_START("TxSerial Hash");
                     BinaryData hashOut(32);
                     BtcUtils::getHash256(txSerial, hashOut);
                     tempTx.thisHash_  = hashOut;
                     TIMER_STOP("TxSerial Hash");

                     //cout << "Tx Hash: " << hashOut.toHex().c_str() << endl;

                     ////////////// Debugging Output - DELETE ME ///////////////
                     //Tx newTx;
                     //BinaryData tempTxSer = tempTx.serialize();
                     //newTx.unserialize(tempTxSer);
                     //BinaryData newTxSer = newTx.serialize();
                     //BtcUtils::getHash256(txSerial, hashOut);
                     //cout << "Tx Hash: " << hashOut.toHex().c_str() << endl;
                     ////////////// Debugging Output - DELETE ME ///////////////

                     // Finally, store it in our map.
                     TIMER_WRAP(txHashMap_[hashOut] = tempTx);
                     TIMER_WRAP(Tx * txPtr = &(txHashMap_[hashOut]));
                     

                     if(txPtr == NULL)
                     {
                        cerr << "***Insert Tx Failed! " 
                             << tempTx.thisHash_.toHex().c_str()
                             << endl;
                        // tempTx.print(cout);
                     }

                     TIMER_WRAP(blkHead.txPtrList_[i] = txPtr);

                  }
               }

               readTx = true;
            }

            
            readMagic  = false;
            readVarInt = false;
            readHeader = false;
            readTx     = false;
            nBlocksRead++;

         }
      }

      return (uint32_t)headerHashMap_.size();
   }
   */



   /////////////////////////////////////////////////////////////////////////////
   /////////////////////////////////////////////////////////////////////////////
   //   
   // Attempting the same thing as above, but using refs only.  This should 
   // actually simplify the buffering because there's only a single, massive
   // copy operation.  And there should be very little extra copying after 
   // that.  Only copying pointers around.
   //
   /////////////////////////////////////////////////////////////////////////////
   /////////////////////////////////////////////////////////////////////////////
   
   /*
   uint32_t importRefsFromBlockFile(std::string filename)
   {
      // TODO: My original everythingRef solution for headers would save a LOT
      //       of computation here.  At 140k blocks, with 1.1 million Tx's:
      //
      //          txSerial copy:       19s
      //          binaryReader copy:   20s
      //          tx.unserialize:      45s
      //          txMap_[hash] = tx:  115s
      //          &(txMap_[hash]):      0.61s
      //
      //       In other words, we spend a shitload of time copying data around.
      //       If we switch to copying all data once from file, and then only
      //       copy pointers around, we should be in fantastic shape!
      //         
      BinaryStreamBuffer bsb(filename, 25*1024*1024);  // use 25 MB buffer
      
      bool readMagic  = false;
      bool readVarInt = false;
      bool readHeader = false;
      bool readTx     = false;
      uint32_t numBlockBytes;

      BinaryData magicBucket(4);
      BinaryData magicStr(4);
      magicStr.createFromHex(MAGICBYTES);
      BinaryData headHash(32);
      BinaryData headerStr(HEADER_SIZE);

      Tx tempTx;
      BlockHeader tempBH;


      int nBlocksRead = 0;
      // While there is still data left in the stream (file), pull it
      while(bsb.streamPull())
      {
         // Data has been pulled into the buffer, process all of it
         while(bsb.getBufferSizeRemaining() > 1)
         {
            static int i = 0;
            if( !readMagic )
            {
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               bsb.reader().get_BinaryData(magicBucket, 4);
               if( !(magicBucket == magicStr) )
               {
                  //cerr << "Magic string does not match network!" << endl;
                  //cerr << "\tExpected: " << MAGICBYTES << endl;
                  //cerr << "\tReceived: " << magicBucket.toHex() << endl;
                  break;
               }
               readMagic = true;
            }

            // If we haven't read the blockdata-size yet, do it
            if( !readVarInt )
            {
               // TODO:  Whoops, this isn't a VAR_INT, just a 4-byte num
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               numBlockBytes = bsb.reader().get_uint32_t();
               readVarInt = true;
            }


            // If we haven't read the header yet, do it
            uint64_t blkByteOffset = bsb.getFileByteLocation();
            if( !readHeader )
            {
               if(bsb.getBufferSizeRemaining() < HEADER_SIZE)
                  break;

               TIMER_WRAP(bsb.reader().get_BinaryData(headerStr, HEADER_SIZE));

               BtcUtils::getHash256(headerStr, headHash);
               TIMER_WRAP(tempBH = BlockHeader(&headerStr, &headHash, blkByteOffset+HEADER_SIZE));
               TIMER_WRAP(headerHashMap_[headHash] = tempBH);

               //cout << headHash.toHex().c_str() << endl;
               readHeader = true;
            }

            uint32_t txListBytes = numBlockBytes - HEADER_SIZE;
            BlockHeader & blkHead = headerHashMap_[headHash];
            if( !readTx )
            {
               if(bsb.getBufferSizeRemaining() < txListBytes)
                  break;

               if(justHeaders)
                  bsb.reader().advance((uint32_t)txListBytes);
               else
               {
                  uint8_t varIntSz;
                  TIMER_WRAP(blkHead.numTx_ = (uint32_t)bsb.reader().get_var_int(&varIntSz));
                  blkHead.txPtrList_.resize(blkHead.numTx_);
                  txListBytes -= varIntSz;
                  BinaryData allTx(txListBytes);
                  TIMER_WRAP(bsb.reader().get_BinaryData(allTx.getPtr(), txListBytes));
                  TIMER_WRAP(BinaryReader txListReader(allTx));
                  for(uint32_t i=0; i<blkHead.numTx_; i++)
                  {

                     uint32_t readerStartPos = txListReader.getPosition();
                     TIMER_WRAP(tempTx.unserialize(txListReader));
                     uint32_t readerEndPos = txListReader.getPosition();

                     TIMER_WRAP(BinaryData txSerial( allTx.getPtr() + readerStartPos, 
                                                     allTx.getPtr() + readerEndPos    ));
                     tempTx.nBytes_    = readerEndPos - readerStartPos;
                     tempTx.headerPtr_ = &blkHead;

                     // Calculate the hash of the Tx
                     TIMER_START("TxSerial Hash");
                     BinaryData hashOut(32);
                     BtcUtils::getHash256(txSerial, hashOut);
                     tempTx.thisHash_  = hashOut;
                     TIMER_STOP("TxSerial Hash");

                     //cout << "Tx Hash: " << hashOut.toHex().c_str() << endl;

                     ////////////// Debugging Output - DELETE ME ///////////////
                     //Tx newTx;
                     //BinaryData tempTxSer = tempTx.serialize();
                     //newTx.unserialize(tempTxSer);
                     //BinaryData newTxSer = newTx.serialize();
                     //BtcUtils::getHash256(txSerial, hashOut);
                     //cout << "Tx Hash: " << hashOut.toHex().c_str() << endl;
                     ////////////// Debugging Output - DELETE ME ///////////////

                     // Finally, store it in our map.
                     TIMER_WRAP(txHashMap_[hashOut] = tempTx);
                     TIMER_WRAP(Tx * txPtr = &(txHashMap_[hashOut]));
                     

                     if(txPtr == NULL)
                     {
                        cerr << "***Insert Tx Failed! " 
                             << tempTx.thisHash_.toHex().c_str()
                             << endl;
                        // tempTx.print(cout);
                     }

                     TIMER_WRAP(blkHead.txPtrList_[i] = txPtr);

                  }
               }

               readTx = true;
            }

            
            readMagic  = false;
            readVarInt = false;
            readHeader = false;
            readTx     = false;
            nBlocksRead++;

         }
      }

      return (uint32_t)headerHashMap_.size();
   }
   */



   /////////////////////////////////////////////////////////////////////////////
   // Not sure exactly when this would get used...
   void addHeader(BinaryData const & binHeader)
   {
      BinaryData theHash(32); 
      BtcUtils::getHash256(binHeader, theHash);
      headerHashMap_[theHash] = BlockHeaderRef(binHeader);
   }



   // This returns false if our new main branch does not include the previous
   // topBlock.  If this returns false, that probably means that we have
   // previously considered some blocks to be valid that no longer are valid.
   bool organizeChain(bool forceRebuild=false)
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
            iter->second.difficultyDbl_ = -1;
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
      for( iter = headerHashMap_.begin(); iter != headerHashMap_.end(); iter ++)
      {
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
         headersByHeight_[thisBlockPtr->getBlockHeight()] = thisBlockPtr;

         BinaryData & childHash        = thisBlockPtr->thisHash_;
         thisBlockPtr                  = &(headerHashMap_[thisBlockPtr->getPrevHash()]);
         thisBlockPtr->nextHash_       = childHash;

         if(thisBlockPtr == prevTopBlockPtr)
            prevChainStillValid = true;
      }

      // Not sure if this should be automatic... for now I don't think it hurts
      if( !prevChainStillValid )
      {
         organizeChain(true); // force-rebuild the blockchain
         return false;
      }

      return prevChainStillValid;
   }

private:

   /////////////////////////////////////////////////////////////////////////////
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(BlockHeaderRef & bhpStart)
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
   void markOrphanChain(BlockHeaderRef & bhpStart)
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


   
};



#endif
