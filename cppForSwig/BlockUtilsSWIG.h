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
   SWIG_BlockHeader(char * header80B);

   uint32_t   getVersion(void) const        {return bh_.getVersion();}
   char*      getPrevHash(void) const       {return bh_.getPrevHash().toCharPtr();}
   char*      getMerkleRoot(void) const     {return bh_.getMerkleRoot().toCharPtr();}
   uint32_t   getTimestamp(void) const      {return bh_.getTimestamp();}
   char*      getDiffBits(void) const       {return bh_.getDiffBits().toCharPtr();}
   uint32_t   getNonce(void) const          {return bh_.getNonce();}
   double     getDifficulty(void) const     {return bh_.getDifficulty();}
   double     getDifficultySum(void) const  {return bh_.getDifficultySum();}
   uint32_t   getBlockHeight(void) const    {return bh_.getBlockHeight();}
   uint32_t   isMainBranch(void) const      {return bh_.isMainBranch();}
   uint32_t   isOrphan(void) const          {return bh_.isOrphan();}

   void       print(ostream & os=cout)      {bh_.printBlockHeader(os);}

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

   void loadBlockchain(char* filename);
   void resetBlockchainData(void);

   void addAddress(char* address20B);
   void addPublicKey(char* binPubKeyStr65B);
   void addPrivPubKeyPair(char* binPrivStr32B, char*  binPubStr65B);
   
   SWIG_BlockHeader getHeaderByHeight(uint32_t height);
   SWIG_BlockHeader getHeaderByHash(char* theHash);
   SWIG_BlockHeader getTopBlockHeader(void);
   uint32_t         getTopBlockHeight(void);

private:
   // BlockDataManager_FullRAM is a singleton class, so don't need anything here
   bool isBlockChainLoaded_;
};











