#include <iostream>
#include <string>
#include <vector>
#include <map>
#include "BinaryData.h"
#include "BlockUtils.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
//  Create a simplified interface for SWIG/python to access the blockchain
//  after the C++ has done the heavy lifting.
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////



class SWIG_BlockchainManager;  // Forward declaration


using namespace std;

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class SWIG_BlockHeader
{
friend class SWIG_BlockchainManager;

public:
   SWIG_BlockHeader(void);
   SWIG_BlockHeader(string const & header80B);

   uint32_t   getVersion(void) const        {return bh_.getVersion();}
   string     getPrevHash(void) const       {return bh_.getPrevHash().toString();}
   string     getMerkleRoot(void) const     {return bh_.getMerkleRoot().toString();}
   uint32_t   getTimestamp(void) const      {return bh_.getTimestamp();}
   string     getDiffBits(void) const       {return bh_.getDiffBits().toString();}
   uint32_t   getNonce(void) const          {return bh_.getNonce();}
   double     getDifficulty(void) const     {return bh_.getDifficulty();}
   double     getDifficultySum(void) const  {return bh_.getDifficultySum();}
   uint32_t   getBlockHeight(void) const    {return bh_.getBlockHeight();}
   uint32_t   isMainBranch(void) const      {return bh_.isMainBranch();}
   uint32_t   isOrphan(void) const          {return bh_.isOrphan();}


private:
   SWIG_BlockHeader(BlockHeaderRef const & bhr) { bh_ = bhr.getCopy();}
private:
   BlockHeader bh_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class SWIG_BtcAddress
{
public:
   SWIG_BtcAddress(void) {}
   
   


private:
   SWIG_BtcAddress(map<BinaryData, BtcAddress>::iterator iter) {addrIter_=iter;}
private:
   map<BinaryData, BtcAddress>::iterator addrIter_; 

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class SWIG_BlockchainManager
{
public:
   SWIG_BlockchainManager(void) : isBlockChainLoaded_(false) {}

   void loadBlockchain(string filename);
   bool organizeBlockchain(void);

   void addAddress(string address20B);
   void addPublicKey(string binPubKeyStr65B);
   void addPrivPubKeyPair(string binPrivStr32B, string binPubStr65B);
   
   SWIG_BlockHeader getHeaderByHeight(uint32_t height);
   SWIG_BlockHeader getHeaderByHash(string theHash);

private:
   // BlockDataManager_FullRAM is a singleton class, so don't need anything here
   bool isBlockChainLoaded_;
};











