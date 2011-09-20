#include <iostream>
#include <string>
#include <vector>
#include <map>
#include "BinaryData.h"
#include "BlockUtils.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Wrapper for the BlockDataManager classes.  Need a "simple" interface to
// simplify the wrapping as much as possible.  ALL python calls should be 
// here, using nothing but simple C++ types (int, double, string, vector, etc)
//
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

using namespace std;

////////////////////////////////////////////////////////////////////////////////
class SWIG_BlockHeader
{
   SWIG_BlockHeader(void);

   

private:
   BlockHeaderRef* bhr_;
};

////////////////////////////////////////////////////////////////////////////////
class SWIG_BlockchainManager
{
public:
   BlockchainManager(void);

   void loadBlockchain(string filename);
   bool organizeBlockchain(void);

   void addPublicKey(string binPubKeyStr65B);
   void addPrivPubKeyPair(string binPrivStr32B, string binPubStr65B);
   

private:
   BlockDataManager_FullRAM bdm_;
};
