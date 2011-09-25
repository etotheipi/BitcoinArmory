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
#include <bitset>
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

class BlockDataManager_FullRAM;


////////////////////////////////////////////////////////////////////////////////
/*
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
*/




////////////////////////////////////////////////////////////////////////////////
// TxIORefPair
//
// This makes a lot of sense, despite the added complexity.  No TxIn exists
// unless there was a TxOut, and they both have the same value, so we will
// store them together here.
//
// This will provide the future benefit of easily determining what Tx data
// can be pruned.  If a TxIORefPair has both TxIn and TxOut, then the value 
// was received and spent, contributes zero to our balance, and can effectively
// ignored.  For now we will maintain them, but in the future we may decide
// to just start removing TxIORefPairs after they are spent...
//
//
class TxIORefPair
{
public:
   //////////////////////////////////////////////////////////////////////////////
   TxIORefPair(void);
   TxIORefPair(uint64_t  amount);
   TxIORefPair(TxOutRef const &  outref, 
               TxRef          *  txPtr);
   TxIORefPair(TxOutRef  outref, 
               TxRef*    txPtrOut, 
               TxInRef   inref, 
               TxRef*    txPtrIn);


   // Lots of accessors
   bool      hasTxOut(void)       { return (txoutRef_.isInitialized()); }
   bool      hasTxIn(void)        { return (txinRef_.isInitialized()); }
   bool      hasValue(void)       { return (amount_!=0); }
   uint64_t  getValue(void)       { return amount_;}

   //////////////////////////////////////////////////////////////////////////////
   TxOutRef       * getTxOutRefPtr(void)         { return &txoutRef_; }
   TxInRef        * getTxInRefPtr(void)          { return &txinRef_; }
   TxOutRef const & getTxOutRef(void) const      { return txoutRef_; }
   TxInRef  const & getTxInRef(void)  const      { return txinRef_; }
   TxOut            getTxOut(void) const         { return txoutRef_.getCopy(); }
   TxIn             getTxIn(void) const          { return txinRef_.getCopy(); }
   TxRef    const & getTxRefOfOutput(void) const { return *txoutTxRefPtr_; }
   TxRef    const & getTxRefOfInput(void) const  { return *txinTxRefPtr_; }


   //////////////////////////////////////////////////////////////////////////////
   BinaryDataRef getTxHashOfOutput(void);
   BinaryDataRef getTxHashOfInput(void);
   void setTxInRef(TxInRef const & inref, TxRef* intxptr);
   void setTxOutRef(TxOutRef const & outref, TxRef* outtxptr);

   //////////////////////////////////////////////////////////////////////////////
   bool isUnspent(void)       { return (  hasTxOut() && !hasTxIn() ); }
   bool isSpent(void)         { return (  hasTxOut() &&  hasTxIn() ); }
   bool isSourceUnknown(void) { return ( !hasTxOut() &&  hasTxIn() ); }
   bool isStandardTxOutScript(void);

private:
   uint64_t  amount_;
   TxOutRef  txoutRef_;
   TxRef*    txoutTxRefPtr_;
   TxInRef   txinRef_;
   TxRef*    txinTxRefPtr_;

};


////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry  (STRUCT)
//
////////////////////////////////////////////////////////////////////////////////
struct LedgerEntry
{
   LedgerEntry(void) :
      addr20_(0),
      value_(0),
      blockNum_(UINT32_MAX),
      txHash_(BtcUtils::EmptyHash_),
      index_(UINT32_MAX),
      isNowInvalid_(true) {}

   LedgerEntry(BinaryData const & addr20,
               int64_t val, 
               uint32_t blkNum, 
               BinaryData const & txhash, 
               uint32_t idx) :
      addr20_(addr20),
      value_(val),
      blockNum_(blkNum),
      txHash_(txhash),
      index_(idx),
      isNowInvalid_(false) {}
      
   
   bool operator<(LedgerEntry const & le2) const;
   bool operator==(LedgerEntry const & le2) const;

   BinaryData       addr20_;
   int64_t          value_;
   uint32_t         blockNum_;
   BinaryData       txHash_;
   uint32_t         index_;  // either a tx index, txout index or txin index
   bool             isNowInvalid_;


   
}; 


////////////////////////////////////////////////////////////////////////////////
//
// BtcAddress  (STRUCT)
//
////////////////////////////////////////////////////////////////////////////////
struct BtcAddress
{
   BtcAddress(void) : 
      address20_(0), pubKey65_(0), privKey32_(0), isActive_(false),
      createdBlockNum_(0), createdTimestamp_(0), 
      relevantTxIOPtrs_(0), ledger_(0) {}

   BtcAddress(BinaryData    addr, 
              BinaryData    pubKey65  = BinaryData(0),
              BinaryData    privKey32 = BinaryData(0),
              uint32_t      createdBlockNum  = 0,
              uint32_t      createdTimestamp = 0);

   //BtcAddress(BtcAddress const & addr2);
   uint32_t cleanLedger(void);

   bool havePubKey(void) { return pubKey65_.getSize() > 0; }
   bool havePrivKey(void) { return privKey32_.getSize() > 0; }

   uint64_t getBalance(void);

   BinaryData address20_;
   BinaryData pubKey65_;
   BinaryData privKey32_;
   uint32_t   createdBlockNum_;
   uint32_t   createdTimestamp_;
   bool       isActive_; 


   vector<LedgerEntry> const & getTxLedger(void) { return ledger_; }

   // Each address will store a list of pointers to its transactions
   vector<TxIORefPair*>   relevantTxIOPtrs_;
   vector<LedgerEntry>    ledger_;
};




////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet
//
////////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
public:
   BtcWallet(void) {}

   /////////////////////////////////////////////////////////////////////////////
   void addAddress(BtcAddress const & newAddr);
   void addAddress(BinaryData    addr, 
                   BinaryData    pubKey65  = BinaryData(0),
                   BinaryData    privKey32 = BinaryData(0),
                   uint32_t      createdBlockNum  = 0,
                   uint32_t      createdTimestamp = 0);

   bool hasAddr(BinaryData const & addr20);

   // Scan a Tx for our TxIns/TxOuts.  Override default blk vals if you think
   // you will save time by not checking addresses that are much newr than
   // the block
   void       scanTx(TxRef & tx, 
                     uint32_t txIndex = UINT32_MAX,
                     uint32_t blknum = UINT32_MAX,
                     uint32_t blktime = UINT32_MAX);

   uint64_t   getBalance(void);
   uint64_t   getBalance(uint32_t i);
   uint64_t   getBalance(BinaryData const & addr20);

   vector<TxRef> getTxList(void);
   vector<TxRef> getTxList(BinaryData const & addr20);
   
   uint32_t     getNumAddr(void) {return addrMap_.size();}
   BtcAddress & getAddrByIndex(uint32_t i) { return *(addrPtrVect_[i]); }
   BtcAddress & getAddrByHash160(BinaryData const & a) { return addrMap_[a];}

   uint32_t cleanLedger(void);
   vector<LedgerEntry> const & getTxLedger(void) { return ledgerAllAddr_; }

private:
   vector<BtcAddress*>          addrPtrVect_;
   map<BinaryData, BtcAddress>  addrMap_;
   map<OutPoint, TxIORefPair>   txioMap_;
   vector<LedgerEntry>          ledgerAllAddr_;  
   set<OutPoint>                unspentTxOuts_;
   set<OutPoint>                orphanTxIns_;
   vector<TxRef*>               txrefList_;      // aggregation of all relevant Tx
   bitset<32>                   encryptFlags_;    // priv-key-encryp params
   bool                         isLocked_;       // watching only, no spending
   
   // import future
   BinaryData                   privKeyGenerator_;
   BinaryData                   pubKeyGenerator_;
   BinaryData                   chainCode_;
   bitset<32>                   chainFlags_;
   
};




// Some might argue that inheritance would be useful here.  I'm not a software
// guy, and I have to write all the methods for each class anyway.  So I'm 
// foregoing the inheritance.  Just writing each class separately

// FullRAM BDM:
//    Very few use cases, and will be nearly impossible if transaction volume
//    picks up at all.  However, if you need to do TONS of computation on the
//    blockchain very quickly, and you have the RAM, this may be useful for you
//    Headers and BlockData/Tx stored in the same structure
//class BlockDataManager_FullRAM;

// FullHDD BDM:
//    This is the standard full-blockchain node.  It pulls all the blockdata
//    into memory only to scan it and index it.  After that, it stores byte
//    locations of the block chain, and reads the data from file on demand.
//    Headers and BlockData/Tx stored in the same structure
//class BlockDataManager_FullHDD;

// Medium BDM:
//    No storage of the blockchain, only the headers and TxOut/TxIn lists 
//    are stored in memory and blocks data is pulled from the network as needed
//    Headers are stored in their own compact structure
//class BlockDataManager_Medium;

// Connection BDM:
//    Basically a proxy to a BDM on another system to be accessed via sockets
//    This may not actually be needed, as it would probably be easier to 
//    implement in python
//class BlockDataManager_ServerConnection;


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



////////////////////////////////////////////////////////////////////////////////
//
// BlockDataManager is a SINGLETON:  only one is ever created.  
//
// Access it via BlockDataManager_FullRAM::GetInstance();
//
////////////////////////////////////////////////////////////////////////////////
class BlockDataManager_FullRAM
{
private:

   // These four data structures contain all the *real* data.  Everything 
   // else is just references and pointers to this data
   BinaryData                         blockchainData_ALL_;
   BinaryData                         blockchainData_NEW_; // to be added
   map<HashString, BlockHeaderRef>    headerHashMap_;
   map<HashString, TxRef >            txHashMap_;

   // If we are really ambitious and have a lot of RAM, we might save
   // all addresses for super-fast lookup.  The key is the 20B addr
   // and the value is a vector of tx-hashes that include this addr
   map<BinaryData, set<HashString> >  allAddrTxMap_;
   bool                               isAllAddrLoaded_;

   // For the case of keeping tx/header data on disk:
   vector<string>                     blockchainFilenames_;
   map<HashString, pair<int,int> >    txFileRefs_;
   map<HashString, pair<int,int> >    headerFileRefs_;


   // These should be set after the blockchain is organized
   deque<BlockHeaderRef*>            headersByHeight_;
   BlockHeaderRef*                   topBlockPtr_;
   BlockHeaderRef*                   genBlockPtr_;

   vector<BlockHeaderRef*>           previouslyValidBlockHeaderRefs_;
   vector<BlockHeaderRef*>           orphanChainStartBlocks_;

   static BlockDataManager_FullRAM* theOnlyBDM_;
   static bool bdmCreatedYet_;


private:
   // Set the constructor to private so that only one can ever be created
   BlockDataManager_FullRAM(void);

public:

   static BlockDataManager_FullRAM & GetInstance(void);


   /////////////////////////////////////////////////////////////////////////////
   void Reset(void);
   int32_t getNumConfirmations(BinaryData txHash);
   BlockHeaderRef & getTopBlock(void) ;
   BlockHeaderRef & getGenesisBlock(void) ;
   BlockHeaderRef * getHeaderByHeight(int index);
   BlockHeaderRef * getHeaderByHash(BinaryData const & blkHash);
   TxRef *          getTxByHash(BinaryData const & txHash);
   void             addHeader(BinaryData const & binHeader);

   // Prefix searches would be much better if we had an some kind of underlying
   // Trie/PatriciaTrie/DeLaBrandiaTrie instead of std::map<>.  For now this
   // search will simply be suboptimal...
   vector<BinaryData> prefixSearchHeaders(BinaryData const & searchStr);
   vector<BinaryData> prefixSearchTx(BinaryData const & searchStr);
   vector<BinaryData> prefixSearchAddress(BinaryData const & searchStr);

   // Traverse the blockchain and update the wallet[s] with the relevant Tx data
   void scanBlockchainForTx_FromScratch(BtcWallet & myWallet);
   void scanBlockchainForTx_FromScratch(vector<BtcWallet> & walletVect);
 
   // This is extremely slow and RAM-hungry, but may be useful on occasion
   void scanBlockchainForTx_FromScratch_AllAddr(void);


   uint32_t readBlkFile_FromScratch(string filename);


   // After reading in all headers, find the longest chain and set nextHash vals
   // TODO:  Figure out if there is an elegant way to deal with a forked 
   //        blockchain containing two equal-length chains
   bool organizeChain(bool forceRebuild=false);

private:

   /////////////////////////////////////////////////////////////////////////////
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(BlockHeaderRef & bhpStart);
   void   markOrphanChain(BlockHeaderRef & bhpStart);


   
};




#endif
