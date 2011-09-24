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
   SWIG_BlockHeader(void) : bh_() { }
   SWIG_BlockHeader(string const & header80B) : bh_(header80B) { }

   unsigned int  getVersion(void) const       {return (unsigned int)bh_.getVersion();}
   string        getPrevHash(void) const      {return bh_.getPrevHash().toString();}
   string        getThisHash(void) const      {return bh_.getThisHash().toString();}
   string        getMerkleRoot(void) const    {return bh_.getMerkleRoot().toString();}
   unsigned int  getTimestamp(void) const     {return (unsigned int)bh_.getTimestamp();}
   string        getDiffBits(void) const      {return bh_.getDiffBits().toString();}
   unsigned int  getNonce(void) const         {return (unsigned int)bh_.getNonce();}
   double        getDifficulty(void) const    {return bh_.getDifficulty();}
   double        getDifficultySum(void) const {return bh_.getDifficultySum();}
   unsigned int  getBlockHeight(void) const   {return (unsigned int)bh_.getBlockHeight();}
   unsigned int  isMainBranch(void) const     {return (unsigned int)bh_.isMainBranch();}
   unsigned int  isOrphan(void) const         {return (unsigned int)bh_.isOrphan();}
   void          printHeader(ostream & os=cout)      {bh_.printBlockHeader(os);}

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


class SWIG_Wallet
{

};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class SWIG_BlockchainManager
{
public:
   SWIG_BlockchainManager(void) : isBlockChainLoaded_(false) {}

   void loadBlockchain(char* filename);
   void resetBlockchainData(void);

   void addAddress(BinaryData address20B);
   void addPublicKey(BinaryData binPubKeyStr65B);
   void addPrivPubKeyPair(BinaryData binPrivStr32B, BinaryData  binPubStr65B);
   
   SWIG_BlockHeader getHeaderByHeight(uint32_t height);
   SWIG_BlockHeader getHeaderByHash(BinaryData const & theHash);
   SWIG_BlockHeader getTopBlockHeader(void);
   uint32_t         getTopBlockHeight(void);

   vector<int>        getTop10BlockHeights(void);
   vector<BinaryData> getTop10BlockHashes(void);

private:
   // BlockDataManager_FullRAM is a singleton class, so don't need anything here
   bool isBlockChainLoaded_;
};











